from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.schemas import PendingAction, RiskLevel
from hermes_app.services.memory import MemoryService
from hermes_app.services.tools import ToolRegistry


class ActionService:
    def __init__(self, db: Database, memory_service: MemoryService, tool_registry: ToolRegistry | None = None):
        self.db = db
        self.memory_service = memory_service
        self.tool_registry = tool_registry or ToolRegistry(db, memory_service)

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
        return self.tool_registry.execute(action.action_type, action.payload)

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
