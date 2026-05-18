from __future__ import annotations

import re
from uuid import uuid4

from hermes_app.schemas import ChatRequest, ChatResponse
from hermes_app.services.actions import ActionService
from hermes_app.services.inspiration import InspirationService
from hermes_app.services.intent_router import IntentRouter
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.memory import MemoryService
from hermes_app.services.safety import SafetyService
from hermes_app.services.skills import SkillRegistry


class HermesOrchestrator:
    def __init__(
        self,
        intent_router: IntentRouter,
        safety: SafetyService,
        memory: MemoryService,
        actions: ActionService,
        skills: SkillRegistry,
        inspiration: InspirationService,
        logs: ExecutionLogService,
    ):
        self.intent_router = intent_router
        self.safety = safety
        self.memory = memory
        self.actions = actions
        self.skills = skills
        self.inspiration = inspiration
        self.logs = logs

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        message = request.message.strip()
        intent = self.intent_router.route(message)
        risk_level = self.safety.classify(message, intent)

        cards: list[dict] = []
        memory_candidates = []
        pending_actions = []

        if risk_level == "blocked":
            reply = "这个请求越过了当前权限边界，我不会执行。"
        elif intent == "create_reminder":
            payload = self._parse_reminder(message)
            pending_actions.append(
                self.actions.create_pending(
                    "reminder.create",
                    payload,
                    risk_level,
                    "创建提醒会改变 App 状态，需要确认后执行。",
                )
            )
            reply = "我已生成提醒创建计划，确认后会写入提醒列表。"
            cards.append({"type": "plan", "title": "提醒计划", "payload": payload})

        elif intent == "memory_update":
            candidate = self.memory.extract_candidate(message)
            memory_candidates.append(candidate)
            pending_actions.append(
                self.actions.create_pending(
                    "memory.write",
                    candidate.model_dump(),
                    risk_level,
                    "写入长期记忆需要用户可见、可撤销。",
                )
            )
            reply = "我提取了一条记忆候选，确认后会保存到记忆中心。"

        elif intent == "weather_query":
            reply = "天气查询能力已预留为外部服务 Skill。当前 MVP 返回查询计划，不直接访问第三方天气源。"
            cards.append(
                {
                    "type": "external_service",
                    "title": "weather.lookup",
                    "payload": {"query": message, "status": "provider_pending"},
                }
            )

        elif intent == "wardrobe_add":
            payload = self._parse_wardrobe(message)
            pending_actions.append(
                self.actions.create_pending(
                    "wardrobe.add",
                    payload,
                    risk_level,
                    "新增衣橱条目会改变用户数据，需要确认后执行。",
                )
            )
            reply = "我已生成衣橱条目草案，确认后会加入衣橱。"
            cards.append({"type": "wardrobe_candidate", "title": "衣橱草案", "payload": payload})

        elif intent == "inspiration":
            idea = self.inspiration.generate_card(message)
            pending_actions.append(
                self.actions.create_pending(
                    "idea.save",
                    idea,
                    "low",
                    "保存 Idea Card 属于低风险沉淀，可由用户确认执行。",
                )
            )
            reply = "我生成了一张 Idea Card，并准备好保存到灵感库。"
            cards.append({"type": "idea_card", **idea})

        elif intent in {"document_summarize", "todo_extract", "list_generate"}:
            skill_id = {
                "document_summarize": "document.summarize",
                "todo_extract": "work.todo_extract",
                "list_generate": "content.list_generate",
            }[intent]
            result = self.skills.run(skill_id, message)
            reply = f"已通过 `{skill_id}` 生成草案。"
            cards.append({"type": "skill_result", "skill_id": skill_id, "payload": result})

        else:
            reply = "我会把这个请求作为普通对话处理。当前 MVP 已搭好意图路由、记忆、Action 和 Skill 管线。"
            cards.append({"type": "system", "title": "Hermes MVP", "payload": {"next": "接入真实 LLM Adapter"}})

        response_payload = {
            "reply": reply,
            "intent": intent,
            "risk_level": risk_level,
            "cards": cards,
            "memory_candidates": [candidate.model_dump() for candidate in memory_candidates],
            "actions": [action.model_dump() for action in pending_actions],
        }
        execution_id = self.logs.record(intent, risk_level, "planned", request.model_dump(), response_payload)
        return ChatResponse(execution_id=execution_id, **response_payload)

    def _parse_reminder(self, message: str) -> dict:
        title = message
        for prefix in ("提醒我", "叫我", "帮我"):
            title = title.replace(prefix, "")
        title = title.strip(" ，。")

        time_patterns = [
            r"(今天[^，。]*)",
            r"(明天[^，。]*)",
            r"(后天[^，。]*)",
            r"(\d{1,2}[点:：]\d{0,2}[^，。]*)",
        ]
        due_at_text = "待补充时间"
        for pattern in time_patterns:
            match = re.search(pattern, message)
            if match:
                due_at_text = match.group(1)
                break

        return {"title": title or "未命名提醒", "due_at_text": due_at_text}

    def _parse_wardrobe(self, message: str) -> dict:
        category = "clothing"
        if "外套" in message:
            category = "outerwear"
        elif "衬衫" in message:
            category = "shirt"
        elif "鞋" in message:
            category = "shoes"

        color = "unknown"
        for candidate in ("黑色", "白色", "蓝色", "灰色", "红色", "绿色", "黄色"):
            if candidate in message:
                color = candidate
                break

        return {"name": message.strip(" ，。"), "category": category, "color": color}

