from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.schemas import RiskLevel


class ExecutionLogService:
    def __init__(self, db: Database):
        self.db = db

    def record(self, intent: str, risk_level: RiskLevel, status: str, request: dict, response: dict) -> str:
        log_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO execution_logs
                (id, intent, risk_level, status, request_json, response_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                intent,
                risk_level,
                status,
                json.dumps(request, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return log_id

    def list(self) -> list[dict]:
        return self.db.query("SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT 80")

