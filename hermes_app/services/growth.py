from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class GrowthLogService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, title: str, zone: str, source_task: str, impact: str, payload: dict | None = None) -> dict:
        log_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO growth_logs
                (id, title, zone, source_task, impact, status, payload_json, created_at, rolled_back_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                title.strip() or "未命名优化",
                zone,
                source_task,
                impact,
                "active",
                json.dumps(payload or {}, ensure_ascii=False),
                _now(),
                None,
            ),
        )
        return self.get(log_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.db.query(
                "SELECT * FROM growth_logs WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        else:
            rows = self.db.query("SELECT * FROM growth_logs ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def get(self, log_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM growth_logs WHERE id = ?", (log_id,))
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def rollback(self, log_id: str) -> dict:
        if not self.get(log_id):
            raise KeyError(f"Growth log not found: {log_id}")
        self.db.execute(
            "UPDATE growth_logs SET status = ?, rolled_back_at = ? WHERE id = ?",
            ("rolled_back", _now(), log_id),
        )
        return self.get(log_id) or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
