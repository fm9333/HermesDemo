import json

from hermes_app.core.database import Database
from hermes_app.services.attention import AttentionPolicy
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.home_cards import HomeCardService
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.providers import ProviderRegistry
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.todos import TodoService
from hermes_app.services.weekly_reviews import WeeklyReviewService


def _service(db: Database) -> HomeCardService:
    signals = ContextSignalService(db)
    opportunities = OpportunityEngine(db, signals)
    recommendations = RecommendationService(db, opportunities, AttentionPolicy())
    todos = TodoService(db)
    providers = ProviderRegistry(db)
    proactive = ProactiveSuggestionService(recommendations, todos, providers)
    weekly_reviews = WeeklyReviewService(db)
    return HomeCardService(db, proactive, weekly_reviews)


def test_home_cards_aggregate_personal_state(tmp_path):
    db = Database(tmp_path / "home_cards.db")
    db.init()
    todos = TodoService(db)
    todos.create("Ship weekly review", source="manual")
    db.execute(
        """
        INSERT INTO idea_cards
            (id, title, body, tags_json, direction, score, next_steps_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "idea-home-1",
            "Personal dashboard",
            "Body",
            '["inspiration"]',
            "desktop",
            0.7,
            '["Review card order"]',
            "2026-05-18T00:00:00+00:00",
        ),
    )
    WeeklyReviewService(db).generate()
    service = _service(db)

    cards = service.list()

    card_types = {card["type"] for card in cards}
    assert "weekly_review" in card_types
    assert "suggestion:todo" in card_types
    assert "suggestion:provider_setup" in card_types
    assert cards == sorted(cards, key=lambda item: (item["priority"], item.get("created_at", "")), reverse=True)
    assert next(card for card in cards if card["type"] == "weekly_review")["route"] == "weeklyReviews"


def test_home_cards_prioritize_pending_actions(tmp_path):
    db = Database(tmp_path / "home_cards_actions.db")
    db.init()
    db.execute(
        """
        INSERT INTO pending_actions
            (id, action_type, risk_level, status, payload_json, reason, created_at, executed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "action-1",
            "memory.confirm_candidate",
            "medium",
            "pending",
            json.dumps({"candidate_id": "candidate-1"}),
            "unit-test",
            "2026-05-18T00:00:00+00:00",
            None,
        ),
    )
    service = _service(db)

    cards = service.list()

    assert cards[0]["type"] == "pending_action"
    assert cards[0]["route"] == "yellowQueue"
    assert cards[0]["payload"]["payload"]["candidate_id"] == "candidate-1"
