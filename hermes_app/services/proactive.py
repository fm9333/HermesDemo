from __future__ import annotations

from hermes_app.services.providers import ProviderRegistry
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.todos import TodoService


class ProactiveSuggestionService:
    def __init__(
        self,
        recommendations: RecommendationService,
        todos: TodoService,
        providers: ProviderRegistry,
    ):
        self.recommendations = recommendations
        self.todos = todos
        self.providers = providers

    def list(self, limit: int = 20) -> list[dict]:
        suggestions: list[dict] = []
        suggestions.extend(self._recommendation_cards())
        suggestions.extend(self._todo_cards())
        suggestions.extend(self._provider_cards())
        return suggestions[:limit]

    def _recommendation_cards(self) -> list[dict]:
        cards = []
        for item in self.recommendations.list(status="open"):
            cards.append(
                {
                    "type": "recommendation",
                    "title": item["title"],
                    "priority": self._priority_for_channel(item["channel"]),
                    "source_id": item["id"],
                    "payload": item,
                }
            )
        return cards

    def _todo_cards(self) -> list[dict]:
        cards = []
        for item in self.todos.list(status="open"):
            cards.append(
                {
                    "type": "todo",
                    "title": item["title"],
                    "priority": 0.55,
                    "source_id": item["id"],
                    "payload": item,
                }
            )
        return cards

    def _provider_cards(self) -> list[dict]:
        cards = []
        for item in self.providers.list():
            if item["status"] != "connected":
                cards.append(
                    {
                        "type": "provider_setup",
                        "title": f"连接 {item['name']}",
                        "priority": 0.35,
                        "source_id": item["provider_id"],
                        "payload": item,
                    }
                )
        return cards

    def _priority_for_channel(self, channel: str) -> float:
        if channel == "interrupt":
            return 0.9
        if channel == "summary":
            return 0.65
        return 0.3
