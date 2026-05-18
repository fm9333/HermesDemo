from hermes_app.core.database import Database
from hermes_app.services.attention import AttentionPolicy
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.recommendations import RecommendationService


def test_attention_policy_routes_by_priority():
    policy = AttentionPolicy()

    high = policy.decide({"priority": 0.8})
    assert high["channel"] == "interrupt"
    assert high["requires_confirmation"] is True

    medium = policy.decide({"priority": 0.5})
    assert medium["channel"] == "summary"
    assert medium["requires_confirmation"] is False

    low = policy.decide({"priority": 0.2})
    assert low["channel"] == "silent"
    assert low["requires_confirmation"] is False


def test_recommendation_service_generates_idempotent_cards(tmp_path):
    db = Database(tmp_path / "recommendations.db")
    db.init()
    signals = ContextSignalService(db)
    opportunities = OpportunityEngine(db, signals)
    service = RecommendationService(db, opportunities, AttentionPolicy())

    opportunity = opportunities.create(
        signal_id=None,
        title="High priority recommendation",
        opportunity_type="test",
        priority=0.91,
        payload={"reason": "unit-test"},
    )

    first = service.generate()
    second = service.generate()

    assert len(first) == 1
    assert len(second) == 1
    assert first[0]["id"] == second[0]["id"]
    assert first[0]["opportunity_id"] == opportunity["id"]
    assert first[0]["channel"] == "interrupt"
    assert first[0]["payload"]["attention"]["requires_confirmation"] is True

    dismissed = service.dismiss(first[0]["id"])
    assert dismissed["status"] == "dismissed"
    assert service.list(status="open") == []

