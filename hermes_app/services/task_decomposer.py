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
        if intent == "create_scene":
            return [
                self._step("解析场景目标", "parse", "scene.intent", "low"),
                self._step("生成 Scene Registry 草案", "plan", "scene.registry", risk_level, confirmation),
                self._step("设置打扰策略", "policy", "attention_policy", risk_level, confirmation),
            ]
        if intent == "inspiration":
            return [
                self._step("进入灵感模式", "route", "inspiration_agent", "low"),
                self._step("生成 Idea Card", "generate", "idea_card", "low"),
                self._step("准备保存到灵感库", "plan", "idea.save", "low"),
            ]
        skill_targets = {
            "document_summarize": ("调用文档总结 Skill", "document.summarize"),
            "contract_extract": ("调用合同要点提取 Skill", "document.contract_extract"),
            "bill_analyze": ("调用账单票据分析 Skill", "document.bill_analyze"),
            "photo_classify": ("调用照片分类 Skill", "image.photo_classify"),
            "todo_extract": ("调用待办提取 Skill", "work.todo_extract"),
            "meeting_minutes": ("调用会议纪要生成 Skill", "work.meeting_minutes"),
            "weekly_report": ("调用周报生成 Skill", "work.weekly_report"),
            "list_generate": ("调用清单生成 Skill", "content.list_generate"),
            "prd_generate": ("调用 PRD 草案生成 Skill", "content.prd_generate"),
            "copy_generate": ("调用文案生成 Skill", "content.copy_generate"),
            "travel_plan": ("调用旅行计划生成 Skill", "content.travel_plan"),
            "table_analyze": ("调用表格数据分析 Skill", "data.table_analyze"),
            "file_archive": ("调用文件归档方案 Skill", "file.archive_plan"),
            "schedule_plan": ("调用日程安排草案 Skill", "calendar.schedule_plan"),
            "email_reply": ("调用邮件回复草案 Skill", "email.reply_draft"),
        }
        if intent in skill_targets:
            title, target = skill_targets[intent]
            return [self._skill_step(title, target)]
        return [self._step("普通对话回复", "reply", "hermes_agent", risk_level)]

    def _summary_for_intent(self, intent: str, message: str) -> str:
        labels = {
            "create_reminder": "创建提醒计划",
            "memory_update": "写入记忆候选计划",
            "weather_query": "天气查询计划",
            "wardrobe_add": "衣橱条目草案计划",
            "create_scene": "场景创建计划",
            "inspiration": "灵感碰撞计划",
            "document_summarize": "文档总结计划",
            "contract_extract": "合同要点提取计划",
            "bill_analyze": "账单票据分析计划",
            "photo_classify": "照片分类计划",
            "todo_extract": "待办提取计划",
            "meeting_minutes": "会议纪要生成计划",
            "weekly_report": "周报生成计划",
            "list_generate": "清单生成计划",
            "prd_generate": "PRD 草案生成计划",
            "copy_generate": "文案生成计划",
            "travel_plan": "旅行计划生成计划",
            "table_analyze": "表格数据分析计划",
            "file_archive": "文件归档方案计划",
            "schedule_plan": "日程安排草案计划",
            "email_reply": "邮件回复草案计划",
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
