from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class ContextSignalService:
    def __init__(self, db: Database):
        self.db = db

    def collect(self, source: str, signal_type: str, payload: dict, expires_at: str | None = None) -> dict:
        signal_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO context_signals (id, source, signal_type, payload_json, status, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                source,
                signal_type,
                json.dumps(payload, ensure_ascii=False),
                "active",
                datetime.now(timezone.utc).isoformat(),
                expires_at,
            ),
        )
        return self.get(signal_id) or {}

    def list(self, status: str | None = None, signal_type: str | None = None) -> list[dict]:
        sql = "SELECT * FROM context_signals"
        params = []
        clauses = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if signal_type:
            clauses.append("signal_type = ?")
            params.append(signal_type)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT 100"
        rows = self.db.query(sql, tuple(params))
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def get(self, signal_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM context_signals WHERE id = ?", (signal_id,))
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def archive(self, signal_id: str) -> dict:
        if not self.get(signal_id):
            raise KeyError(f"Context signal not found: {signal_id}")
        self.db.execute("UPDATE context_signals SET status = ? WHERE id = ?", ("archived", signal_id))
        return self.get(signal_id) or {}

