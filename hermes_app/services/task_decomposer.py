from __future__ import annotations

from uuid import uuid4

from hermes_app.schemas import RiskLevel, TaskPlan, TaskStep


class TaskDecomposer:
    def decompose(self, message: str, intent: str, risk_level: RiskLevel) -> TaskPlan:
        steps = self._steps_for_intent(intent, risk_level)
        return TaskPlan(
            plan_id=str(uuid4()),
            intent=intent,
            summary=self._summary_for_intent(intent, message),
            risk_level=risk_level,
            steps=steps,
        )

    def _steps_for_intent(self, intent: str, risk_level: RiskLevel) -> list[TaskStep]:
        confirmation = risk_level in {"medium", "high", "sensitive", "blocked"}
        if intent == "create_reminder":
            return [
                self._step("理解提醒内容", "analyze", "intent_router", "low"),
                self._step("生成提醒执行计划", "plan", "action.reminder.create", risk_level, confirmation),
                self._step("等待用户确认", "gate", "action_gate", risk_level, confirmation),
            ]
        if intent == "memory_update":
            return [
                self._step("提取记忆候选", "extract", "memory_candidate_pipeline", "low"),
                self._step("判断敏感性与置信度", "classify", "memory_pipeline", risk_level),
                self._step("等待用户确认写入", "gate", "action.memory.write", risk_level, confirmation),
            ]
        if intent == "weather_query":
            return [
                self._step("解析天气查询地点", "parse", "weather.location", "low"),
                self._step("调用天气 Provider", "tool", "weather.lookup", "low"),
                self._step("缓存天气结果", "persist", "weather_cache", "low"),
            ]
        if intent == "wardrobe_add":
            return [
                self._step("解析衣物信息", "parse", "wardrobe.candidate", "low"),
                self._step("生成衣橱条目草案", "plan", "wardrobe.add", risk_level, confirmation),
                self._step("等待用户确认加入衣橱", "gate", "action_gate", risk_level, confirmation),
            ]
        if intent == "inspiration":
            return [
                self._step("进入灵感模式", "route", "inspiration_agent", "low"),
                self._step("生成 Idea Card", "generate", "idea_card", "low"),
                self._step("准备保存到灵感库", "plan", "idea.save", "low"),
            ]
        if intent == "document_summarize":
            return [self._skill_step("调用文档总结 Skill", "document.summarize")]
        if intent == "todo_extract":
            return [self._skill_step("调用待办提取 Skill", "work.todo_extract")]
        if intent == "list_generate":
            return [self._skill_step("调用清单生成 Skill", "content.list_generate")]
        return [self._step("普通对话回复", "reply", "hermes_agent", risk_level)]

    def _summary_for_intent(self, intent: str, message: str) -> str:
        labels = {
            "create_reminder": "创建提醒计划",
            "memory_update": "写入记忆候选计划",
            "weather_query": "天气查询计划",
            "wardrobe_add": "衣橱条目草案计划",
            "inspiration": "灵感碰撞计划",
            "document_summarize": "文档总结计划",
            "todo_extract": "待办提取计划",
            "list_generate": "清单生成计划",
            "general_chat": "普通对话计划",
        }
        return f"{labels.get(intent, 'Hermes 任务计划')}：{message[:80]}"

    def _skill_step(self, title: str, target: str) -> TaskStep:
        return self._step(title, "skill", target, "low")

    def _step(
        self,
        title: str,
        kind: str,
        target: str,
        risk_level: RiskLevel,
        requires_confirmation: bool = False,
    ) -> TaskStep:
        return TaskStep(
            id=str(uuid4()),
            title=title,
            kind=kind,
            target=target,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            status="blocked" if risk_level == "blocked" else "planned",
        )

