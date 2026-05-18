from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class WeeklyReviewService:
    def __init__(self, db: Database):
        self.db = db

    def generate(self) -> dict:
        week_start = _week_start()
        ideas = self.db.query("SELECT * FROM idea_cards ORDER BY created_at DESC LIMIT 20")
        highlights = [self._highlight_from_idea(idea) for idea in ideas[:5]]
        next_actions = self._next_actions(ideas)
        title = f"\u6bcf\u5468\u7075\u611f\u590d\u76d8 {week_start}"
        summary = (
            f"\u672c\u5468\u6c89\u6dc0 {len(ideas)} \u5f20 Idea Card\uff0c"
            f"\u4f18\u5148\u63a8\u8fdb {len(next_actions)} \u4e2a\u884c\u52a8\u3002"
        )

        review_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO weekly_reviews
                (id, week_start, title, summary, highlights_json, next_actions_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                week_start,
                title,
                summary,
                json.dumps(highlights, ensure_ascii=False),
                json.dumps(next_actions, ensure_ascii=False),
                _now(),
            ),
        )
        return self.get(review_id) or {}

    def list(self) -> list[dict]:
        rows = self.db.query("SELECT * FROM weekly_reviews ORDER BY created_at DESC LIMIT 100")
        return [self._deserialize(row) for row in rows]

    def get(self, review_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM weekly_reviews WHERE id = ?", (review_id,))
        return self._deserialize(row) if row else None

    def _highlight_from_idea(self, idea: dict) -> dict:
        return {
            "idea_id": idea["id"],
            "title": idea["title"],
            "direction": idea.get("direction", ""),
            "score": idea.get("score", 0),
        }

    def _next_actions(self, ideas: list[dict]) -> list[str]:
        actions: list[str] = []
        for idea in ideas[:3]:
            raw = idea.get("next_steps_json") or "[]"
            try:
                steps = json.loads(raw)
            except json.JSONDecodeError:
                steps = []
            if steps:
                actions.append(str(steps[0]))
            elif idea.get("mvp_plan"):
                actions.append(str(idea["mvp_plan"]))
        if not actions:
            return ["\u8865\u5145\u672c\u5468\u503c\u5f97\u63a8\u8fdb\u7684 Idea Card"]
        return actions

    def _deserialize(self, row: dict) -> dict:
        row["highlights"] = json.loads(row.pop("highlights_json"))
        row["next_actions"] = json.loads(row.pop("next_actions_json"))
        return row


def _week_start() -> str:
    now = datetime.now(timezone.utc).date()
    monday = now - timedelta(days=now.weekday())
    return monday.isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
