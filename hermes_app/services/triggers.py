from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.recommendations import RecommendationService


class TriggerService:
    def __init__(
        self,
        db: Database,
        opportunities: OpportunityEngine,
        recommendations: RecommendationService,
        proactive: ProactiveSuggestionService,
    ):
        self.db = db
        self.opportunities = opportunities
        self.recommendations = recommendations
        self.proactive = proactive

    def run(self, trigger_type: str = "manual") -> dict:
        opportunities = self.opportunities.generate()
        recommendations = self.recommendations.generate()
        suggestions = self.proactive.list()
        output = {
            "opportunities": opportunities,
            "recommendations": recommendations,
            "suggestions": suggestions,
        }
        run_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO trigger_runs (id, trigger_type, status, output_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, trigger_type, "ok", json.dumps(output, ensure_ascii=False), _now()),
        )
        return self.get(run_id) or {}

    def list_runs(self) -> list[dict]:
        rows = self.db.query("SELECT * FROM trigger_runs ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["output"] = json.loads(row.pop("output_json"))
        return rows

    def get(self, run_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM trigger_runs WHERE id = ?", (run_id,))
        if row:
            row["output"] = json.loads(row.pop("output_json"))
        return row


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
