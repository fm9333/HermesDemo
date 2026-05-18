from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.schemas import MemoryCandidate, ToolDefinition
from hermes_app.services.memory import MemoryService
from hermes_app.services.reminders import ReminderService
from hermes_app.services.wardrobe import WardrobeService


class ToolRegistry:
    def __init__(
        self,
        db: Database,
        memory_service: MemoryService,
        reminder_service: ReminderService | None = None,
        wardrobe_service: WardrobeService | None = None,
    ):
        self.db = db
        self.memory_service = memory_service
        self.reminder_service = reminder_service or ReminderService(db)
        self.wardrobe_service = wardrobe_service or WardrobeService(db)
        self._definitions = {
            "reminder.create": ToolDefinition(
                tool_id="reminder.create",
                title="创建提醒",
                description="在 Hermes 本地提醒列表中创建一条提醒。",
                risk_level="medium",
                requires_confirmation=True,
                rollback_supported=True,
            ),
            "memory.write": ToolDefinition(
                tool_id="memory.write",
                title="写入记忆",
                description="将一条已确认的普通记忆写入记忆中心。",
                risk_level="medium",
                requires_confirmation=True,
                rollback_supported=True,
            ),
            "memory.confirm_candidate": ToolDefinition(
                tool_id="memory.confirm_candidate",
                title="确认记忆候选",
                description="确认一条待写入记忆候选并写入长期记忆。",
                risk_level="medium",
                requires_confirmation=True,
                rollback_supported=True,
            ),
            "idea.save": ToolDefinition(
                tool_id="idea.save",
                title="保存 Idea Card",
                description="将灵感智能体生成的 Idea Card 保存到灵感库。",
                risk_level="low",
                requires_confirmation=False,
                rollback_supported=True,
            ),
            "wardrobe.add": ToolDefinition(
                tool_id="wardrobe.add",
                title="加入衣橱",
                description="将衣物草案加入本地衣橱。",
                risk_level="medium",
                requires_confirmation=True,
                rollback_supported=True,
            ),
        }

    def list(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    def get(self, tool_id: str) -> ToolDefinition | None:
        return self._definitions.get(tool_id)

    def execute(self, tool_id: str, payload: dict) -> dict:
        definition = self.get(tool_id)
        if not definition or not definition.enabled:
            return {"status": "blocked", "message": f"Tool is not registered or disabled: {tool_id}"}

        executors = {
            "reminder.create": self._create_reminder,
            "memory.write": self._write_memory,
            "memory.confirm_candidate": self._confirm_memory_candidate,
            "idea.save": self._save_idea,
            "wardrobe.add": self._add_wardrobe_item,
        }
        executor = executors.get(tool_id)
        if not executor:
            return {"status": "noop", "message": f"No executor registered for {tool_id}"}
        return executor(payload)

    def _create_reminder(self, payload: dict) -> dict:
        reminder = self.reminder_service.create(
            payload.get("title", "未命名提醒"),
            payload.get("due_at_text", "待补充时间"),
            source="hermes",
        )
        return {"reminder_id": reminder.get("id"), "status": "created"}

    def _write_memory(self, payload: dict) -> dict:
        candidate = MemoryCandidate(**payload)
        item = self.memory_service.save(candidate, source="action_confirmation")
        return {"memory_id": item.get("id"), "status": "saved"}

    def _confirm_memory_candidate(self, payload: dict) -> dict:
        item = self.memory_service.confirm_candidate(payload["candidate_id"])
        return {"memory_id": item.get("id"), "status": "saved"}

    def _save_idea(self, payload: dict) -> dict:
        idea_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO idea_cards
                (id, title, body, tags_json, direction, target_user, pain_point, core_assumption,
                 counter_challenge, analogy, mvp_plan, risks_json, next_steps_json, score, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea_id,
                payload.get("title", "Untitled Idea"),
                payload.get("body", ""),
                json.dumps(payload.get("tags", []), ensure_ascii=False),
                payload.get("direction", ""),
                payload.get("target_user", ""),
                payload.get("pain_point", ""),
                payload.get("core_assumption", ""),
                payload.get("counter_challenge", ""),
                payload.get("analogy", ""),
                payload.get("mvp_plan", ""),
                json.dumps(payload.get("risks", []), ensure_ascii=False),
                json.dumps(payload.get("next_steps", []), ensure_ascii=False),
                float(payload.get("score", 0) or 0),
                payload.get("status", "active"),
                _now(),
            ),
        )
        return {"idea_id": idea_id, "status": "saved"}

    def _add_wardrobe_item(self, payload: dict) -> dict:
        item = self.wardrobe_service.create(
            payload.get("name", "未命名衣物"),
            category=payload.get("category", "unknown"),
            color=payload.get("color", "unknown"),
            source="hermes",
        )
        return {"wardrobe_item_id": item.get("id"), "status": "created"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
