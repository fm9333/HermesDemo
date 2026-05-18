from __future__ import annotations

import json

from hermes_app.core.database import Database
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.weekly_reviews import WeeklyReviewService


class HomeCardService:
    def __init__(
        self,
        db: Database,
        proactive: ProactiveSuggestionService,
        weekly_reviews: WeeklyReviewService,
    ):
        self.db = db
        self.proactive = proactive
        self.weekly_reviews = weekly_reviews

    def list(self, limit: int = 12) -> list[dict]:
        cards: list[dict] = []
        cards.extend(self._pending_action_cards())
        cards.extend(self._memory_candidate_cards())

        latest_review = next(iter(self.weekly_reviews.list()), None)
        if latest_review:
            cards.append(self._weekly_review_card(latest_review))

        cards.extend(self._suggestion_cards(limit))
        if not cards:
            cards.append(self._empty_state_card())
        return sorted(cards, key=lambda item: (item["priority"], item.get("created_at", "")), reverse=True)[:limit]

    def _pending_action_cards(self) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM pending_actions WHERE status = ? ORDER BY created_at DESC LIMIT 5",
            ("pending",),
        )
        cards = []
        for row in rows:
            payload = _json_object(row.pop("payload_json"))
            cards.append(
                {
                    "id": f"home:action:{row['id']}",
                    "type": "pending_action",
                    "title": "\u9700\u8981\u786e\u8ba4\u7684\u52a8\u4f5c",
                    "subtitle": row["action_type"],
                    "priority": _risk_priority(row["risk_level"]),
                    "route": "yellowQueue",
                    "action_label": "\u53bb\u786e\u8ba4",
                    "source_id": row["id"],
                    "created_at": row["created_at"],
                    "payload": {**row, "payload": payload},
                }
            )
        return cards

    def _memory_candidate_cards(self) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM memory_candidates WHERE status = ? ORDER BY created_at DESC LIMIT 3",
            ("pending",),
        )
        return [
            {
                "id": f"home:memory:{row['id']}",
                "type": "memory_candidate",
                "title": "\u8bb0\u5fc6\u5019\u9009\u5f85\u786e\u8ba4",
                "subtitle": row["key"],
                "priority": 0.72,
                "route": "memoryCandidates",
                "action_label": "\u67e5\u770b\u5019\u9009",
                "source_id": row["id"],
                "created_at": row["created_at"],
                "payload": row,
            }
            for row in rows
        ]

    def _weekly_review_card(self, review: dict) -> dict:
        return {
            "id": f"home:weekly-review:{review['id']}",
            "type": "weekly_review",
            "title": review["title"],
            "subtitle": review["summary"],
            "priority": 0.78,
            "route": "weeklyReviews",
            "action_label": "\u67e5\u770b\u590d\u76d8",
            "source_id": review["id"],
            "created_at": review["created_at"],
            "payload": review,
        }

    def _suggestion_cards(self, limit: int) -> list[dict]:
        cards = []
        for suggestion in self.proactive.list(limit=limit):
            route = {
                "recommendation": "recommendations",
                "todo": "todos",
                "provider_setup": "providers",
            }.get(suggestion["type"], "proactive")
            cards.append(
                {
                    "id": f"home:suggestion:{suggestion['type']}:{suggestion['source_id']}",
                    "type": f"suggestion:{suggestion['type']}",
                    "title": suggestion["title"],
                    "subtitle": "\u4e3b\u52a8\u5efa\u8bae",
                    "priority": suggestion["priority"],
                    "route": route,
                    "action_label": "\u67e5\u770b",
                    "source_id": suggestion["source_id"],
                    "created_at": suggestion.get("payload", {}).get("created_at", ""),
                    "payload": suggestion,
                }
            )
        return cards

    def _empty_state_card(self) -> dict:
        return {
            "id": "home:empty:start",
            "type": "empty_state",
            "title": "\u5f00\u59cb\u6c89\u6dc0\u7b2c\u4e00\u4e2a\u63d0\u9192\u6216\u7075\u611f",
            "subtitle": "\u9996\u9875\u4f1a\u6839\u636e\u4f60\u7684\u5f85\u529e\u3001\u590d\u76d8\u548c\u4e3b\u52a8\u5efa\u8bae\u81ea\u52a8\u8c03\u6574\u3002",
            "priority": 0.1,
            "route": "ideas",
            "action_label": "\u53bb\u521b\u5efa",
            "source_id": "",
            "created_at": "",
            "payload": {},
        }


def _json_object(value: str | None) -> dict:
    try:
        data = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _risk_priority(risk_level: str) -> float:
    return {"high": 0.98, "medium": 0.92, "low": 0.5}.get(risk_level, 0.4)
