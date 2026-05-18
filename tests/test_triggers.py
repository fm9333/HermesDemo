from hermes_app.core.database import Database
from hermes_app.services.attention import AttentionPolicy
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.providers import ProviderRegistry
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.todos import TodoService
from hermes_app.services.triggers import TriggerService


def test_trigger_service_runs_signal_to_suggestion_chain(tmp_path):
    db = Database(tmp_path / "triggers.db")
    db.init()
    signals = ContextSignalService(db)
    opportunities = OpportunityEngine(db, signals)
    recommendations = RecommendationService(db, opportunities, AttentionPolicy())
    todos = TodoService(db)
    providers = ProviderRegistry(db)
    proactive = ProactiveSuggestionService(recommendations, todos, providers)
    service = TriggerService(db, opportunities, recommendations, proactive)

    signals.collect("weather", "weather.rain", {"probability": 80})
    run = service.run("test")

    assert run["status"] == "ok"
    assert run["trigger_type"] == "test"
    assert run["output"]["opportunities"]
    assert run["output"]["recommendations"]
    assert run["output"]["suggestions"]
    assert service.list_runs()[0]["id"] == run["id"]

