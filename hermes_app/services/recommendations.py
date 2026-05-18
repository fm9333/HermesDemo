from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.attention import AttentionPolicy
from hermes_app.services.opportunities import OpportunityEngine


class RecommendationService:
    def __init__(self, db: Database, opportunities: OpportunityEngine, attention: AttentionPolicy):
        self.db = db
        self.opportunities = opportunities
        self.attention = attention

    def generate(self) -> list[dict]:
        cards = []
        for opportunity in self.opportunities.list(status="open"):
            decision = self.attention.decide(opportunity)
            existing = self.get_open_by_opportunity(opportunity["id"])
            cards.append(existing or self.create(opportunity, decision))
        return cards

    def create(self, opportunity: dict, decision: dict) -> dict:
        recommendation_id = str(uuid4())
        payload = {
            "opportunity": opportunity,
            "attention": decision,
        }
        self.db.execute(
            """
            INSERT INTO recommendations (id, opportunity_id, title, channel, payload_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation_id,
                opportunity["id"],
                opportunity["title"],
                decision["channel"],
                json.dumps(payload, ensure_ascii=False),
                "open",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return self.get(recommendation_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.db.query(
                "SELECT * FROM recommendations WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        else:
            rows = self.db.query("SELECT * FROM recommendations ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def get(self, recommendation_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def get_open_by_opportunity(self, opportunity_id: str) -> dict | None:
        row = self.db.query_one(
            "SELECT * FROM recommendations WHERE opportunity_id = ? AND status = ? ORDER BY created_at DESC LIMIT 1",
            (opportunity_id, "open"),
        )
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def dismiss(self, recommendation_id: str) -> dict:
        if not self.get(recommendation_id):
            raise KeyError(f"Recommendation not found: {recommendation_id}")
        self.db.execute("UPDATE recommendations SET status = ? WHERE id = ?", ("dismissed", recommendation_id))
        return self.get(recommendation_id) or {}
