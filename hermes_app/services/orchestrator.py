from __future__ import annotations

import re
from uuid import uuid4

from hermes_app.schemas import ChatRequest, ChatResponse
from hermes_app.services.actions import ActionService
from hermes_app.services.inspiration import InspirationService
from hermes_app.services.intent_router import IntentRouter
from hermes_app.services.llm_client import LLMClient
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.memory import MemoryService
from hermes_app.services.scenes import SceneService
from hermes_app.services.safety import SafetyService
from hermes_app.services.skills import SkillRegistry
from hermes_app.services.skill_runtime import SkillRuntime
from hermes_app.services.task_decomposer import TaskDecomposer
from hermes_app.services.weather import WeatherService


class HermesOrchestrator:
    def __init__(
        self,
        intent_router: IntentRouter,
        task_decomposer: TaskDecomposer,
        safety: SafetyService,
        memory: MemoryService,
        actions: ActionService,
        skills: SkillRegistry,
        skill_runtime: SkillRuntime,
        scenes: SceneService,
        inspiration: InspirationService,
        weather: WeatherService,
        logs: ExecutionLogService,
        llm_client: LLMClient | None = None,
    ):
        self.intent_router = intent_router
        self.task_decomposer = task_decomposer
        self.safety = safety
        self.memory = memory
        self.actions = actions
        self.skills = skills
        self.skill_runtime = skill_runtime
        self.scenes = scenes
        self.inspiration = inspiration
        self.weather = weather
        self.logs = logs
        self.llm_client = llm_client

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        message = request.message.strip()
        intent = self.intent_router.route(message)
        risk_level = self.safety.classify(message, intent)
        task_plan = self.task_decomposer.decompose(message, intent, risk_level)

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
            candidate_record = self.memory.create_candidate(
                candidate,
                source="chat",
                reason="用户表达了需要 Hermes 记住的信息。",
            )
            memory_candidates.append(candidate)
            pending_actions.append(
                self.actions.create_pending(
                    "memory.confirm_candidate",
                    {"candidate_id": candidate_record["id"]},
                    risk_level,
                    "写入长期记忆需要用户可见、可撤销。",
                )
            )
            reply = "我提取了一条记忆候选，确认后会保存到记忆中心。"
            cards.append({"type": "memory_candidate", "title": "记忆候选", "payload": candidate_record})

        elif intent == "weather_query":
            location = self._parse_weather_location(message)
            if not location:
                reply = "你想查询哪个城市或地点的天气？"
                cards.append({"type": "needs_input", "title": "天气查询", "payload": {"field": "location"}})
            else:
                weather = self.weather.lookup(location)
                reply = weather.get("summary") or weather.get("message") or "天气查询已完成。"
                cards.append({"type": "weather", "title": "天气", "payload": weather})

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

        elif intent == "create_scene":
            scene = self.scenes.create(
                name=self._parse_scene_name(message),
                source="user",
                context_signal="conversation",
                user_state="unknown",
                opportunity="user_requested_scene",
                decision_policy="confirm_before_interrupt",
                output_type="recommendation",
                status="active",
            )
            reply = "我已创建一个场景草案，并加入 Scene Registry。"
            cards.append({"type": "scene", "title": "场景草案", "payload": scene})

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
            result = self.skill_runtime.run(skill_id, message)
            reply = f"已通过 `{skill_id}` 生成草案。"
            cards.append({"type": "skill_result", "skill_id": skill_id, "payload": result})

        else:
            llm_result = self._handle_llm_chat(message, intent, risk_level)
            if llm_result:
                reply = llm_result["reply"]
                cards.append({"type": "llm", "title": "LLM Provider", "payload": llm_result})
            else:
                reply = "我会把这个请求作为普通对话处理。当前未配置可用的大模型 Provider，请在“模型”面板配置 OpenAI-compatible 接口、API Key 和模型名。"
                cards.append({"type": "system", "title": "模型未配置", "payload": {"next": "配置 LLM Provider"}})

        response_payload = {
            "reply": reply,
            "intent": intent,
            "risk_level": risk_level,
            "task_plan": task_plan.model_dump(),
            "cards": cards,
            "memory_candidates": [candidate.model_dump() for candidate in memory_candidates],
            "actions": [action.model_dump() for action in pending_actions],
        }
        execution_id = self.logs.record(intent, risk_level, "planned", request.model_dump(), response_payload)
        return ChatResponse(execution_id=execution_id, **response_payload)

    def _handle_llm_chat(self, message: str, intent: str, risk_level: str) -> dict | None:
        if not self.llm_client:
            return None
        result = self.llm_client.chat(
            message,
            prompt_id="hermes.agent.core",
            context={
                "intent": intent,
                "risk_level": risk_level,
                "available_skills": ", ".join(skill.skill_id for skill in self.skills.list()),
                "safety_boundary": "LLM only drafts replies and plans; backend executes through Tool Registry and Action Gate.",
            },
        )
        if result.get("status") != "ok" or not result.get("reply"):
            return None
        return {
            "status": result["status"],
            "provider_id": result.get("provider_id"),
            "model": result.get("model"),
            "prompt_id": result.get("prompt_id"),
            "call_id": result.get("call_id"),
            "latency_ms": result.get("latency_ms"),
            "reply": result["reply"],
        }

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

    def _parse_weather_location(self, message: str) -> str:
        value = message.strip()
        for token in ("帮我看看", "查询", "查一下", "看看", "天气", "下雨", "降雨", "气温", "怎么样", "如何"):
            value = value.replace(token, "")
        return value.strip(" ，。？?：:")

    def _parse_scene_name(self, message: str) -> str:
        value = message.strip()
        for token in ("帮我", "创建", "新建", "一个", "场景", "scene"):
            value = value.replace(token, "")
        return value.strip(" ，。？?：:") or "Hermes 场景"
