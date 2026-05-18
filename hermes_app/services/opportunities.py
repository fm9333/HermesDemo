from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.context_signals import ContextSignalService


class OpportunityEngine:
    def __init__(self, db: Database, context_signals: ContextSignalService):
        self.db = db
        self.context_signals = context_signals

    def generate(self) -> list[dict]:
        created = []
        for signal in self.context_signals.list(status="active"):
            opportunity = self._opportunity_from_signal(signal)
            if opportunity:
                created.append(self.create(signal["id"], **opportunity))
        return created

    def create(
        self,
        signal_id: str | None,
        title: str,
        opportunity_type: str,
        priority: float,
        payload: dict,
    ) -> dict:
        opportunity_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO opportunities
                (id, signal_id, title, opportunity_type, priority, payload_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id,
                signal_id,
                title,
                opportunity_type,
                priority,
                json.dumps(payload, ensure_ascii=False),
                "open",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return self.get(opportunity_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.db.query(
                "SELECT * FROM opportunities WHERE status = ? ORDER BY priority DESC, created_at DESC LIMIT 100",
                (status,),
            )
        else:
            rows = self.db.query("SELECT * FROM opportunities ORDER BY priority DESC, created_at DESC LIMIT 100")
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def get(self, opportunity_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,))
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def close(self, opportunity_id: str) -> dict:
        if not self.get(opportunity_id):
            raise KeyError(f"Opportunity not found: {opportunity_id}")
        self.db.execute("UPDATE opportunities SET status = ? WHERE id = ?", ("closed", opportunity_id))
        return self.get(opportunity_id) or {}

    def _opportunity_from_signal(self, signal: dict) -> dict | None:
        signal_type = signal["signal_type"]
        payload = signal["payload"]
        if signal_type == "weather.rain" and payload.get("probability", 0) >= 50:
            return {
                "title": "雨天出行提醒机会",
                "opportunity_type": "reminder_recommendation",
                "priority": 0.86,
                "payload": {
                    "recommendation": "建议创建带伞提醒",
                    "reason": f"降雨概率 {payload.get('probability')}%",
                },
            }
        if signal_type == "file.uploaded":
            return {
                "title": "文件处理 Skill 推荐机会",
                "opportunity_type": "skill_recommendation",
                "priority": 0.62,
                "payload": {
                    "skill_id": "document.summarize",
                    "reason": "检测到新上传文件，可生成摘要。",
                },
            }
        return None

