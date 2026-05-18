from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.schemas import MemoryCandidate, PendingAction, RiskLevel
from hermes_app.services.memory import MemoryService


class ActionService:
    def __init__(self, db: Database, memory_service: MemoryService):
        self.db = db
        self.memory_service = memory_service

    def create_pending(self, action_type: str, payload: dict, risk_level: RiskLevel, reason: str) -> PendingAction:
        now = datetime.now(timezone.utc).isoformat()
        action_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO pending_actions
                (id, action_type, risk_level, status, payload_json, reason, created_at, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (action_id, action_type, risk_level, "pending", json.dumps(payload, ensure_ascii=False), reason, now, None),
        )
        return self.get(action_id)

    def get(self, action_id: str) -> PendingAction:
        row = self.db.query_one("SELECT * FROM pending_actions WHERE id = ?", (action_id,))
        if not row:
            raise KeyError(f"Action not found: {action_id}")
        return self._to_action(row)

    def list_pending(self) -> list[PendingAction]:
        rows = self.db.query("SELECT * FROM pending_actions WHERE status = 'pending' ORDER BY created_at DESC")
        return [self._to_action(row) for row in rows]

    def confirm(self, action_id: str) -> tuple[PendingAction, dict]:
        action = self.get(action_id)
        if action.status != "pending":
            return action, {"status": action.status, "message": "Action already handled."}

        result = self._execute(action)
        executed_at = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE pending_actions SET status = ?, executed_at = ? WHERE id = ?",
            ("executed", executed_at, action_id),
        )
        return self.get(action_id), result

    def reject(self, action_id: str) -> PendingAction:
        action = self.get(action_id)
        if action.status == "pending":
            self.db.execute("UPDATE pending_actions SET status = ? WHERE id = ?", ("rejected", action_id))
        return self.get(action_id)

    def _execute(self, action: PendingAction) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        payload = action.payload

        if action.action_type == "reminder.create":
            reminder_id = str(uuid4())
            self.db.execute(
                """
                INSERT INTO reminders (id, title, due_at_text, source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    reminder_id,
                    payload.get("title", "未命名提醒"),
                    payload.get("due_at_text", "待补充时间"),
                    "hermes",
                    "active",
                    now,
                ),
            )
            return {"reminder_id": reminder_id, "status": "created"}

        if action.action_type == "memory.write":
            candidate = MemoryCandidate(**payload)
            item = self.memory_service.save(candidate, source="action_confirmation")
            return {"memory_id": item.get("id"), "status": "saved"}

        if action.action_type == "idea.save":
            idea_id = str(uuid4())
            self.db.execute(
                """
                INSERT INTO idea_cards (id, title, body, tags_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    idea_id,
                    payload.get("title", "Untitled Idea"),
                    payload.get("body", ""),
                    json.dumps(payload.get("tags", []), ensure_ascii=False),
                    now,
                ),
            )
            return {"idea_id": idea_id, "status": "saved"}

        if action.action_type == "wardrobe.add":
            item_id = str(uuid4())
            self.db.execute(
                """
                INSERT INTO wardrobe_items (id, name, category, color, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    payload.get("name", "未命名衣物"),
                    payload.get("category", "unknown"),
                    payload.get("color", "unknown"),
                    "hermes",
                    now,
                ),
            )
            return {"wardrobe_item_id": item_id, "status": "created"}

        return {"status": "noop", "message": f"No executor registered for {action.action_type}"}

    def _to_action(self, row: dict) -> PendingAction:
        return PendingAction(
            id=row["id"],
            action_type=row["action_type"],
            risk_level=row["risk_level"],
            status=row["status"],
            payload=json.loads(row["payload_json"]),
            reason=row["reason"],
            created_at=row["created_at"],
        )

