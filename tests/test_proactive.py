from hermes_app.core.database import Database
from hermes_app.services.attention import AttentionPolicy
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.providers import ProviderRegistry
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.todos import TodoService


def test_proactive_suggestions_aggregate_recommendations_todos_and_providers(tmp_path):
    db = Database(tmp_path / "proactive.db")
    db.init()
    signals = ContextSignalService(db)
    opportunities = OpportunityEngine(db, signals)
    recommendations = RecommendationService(db, opportunities, AttentionPolicy())
    todos = TodoService(db)
    providers = ProviderRegistry(db)
    service = ProactiveSuggestionService(recommendations, todos, providers)

    opportunities.create(None, "主动提醒机会", "test", 0.9, {"reason": "unit-test"})
    recommendations.generate()
    todos.create("完成主动建议测试", source="manual")

    suggestions = service.list()
    types = {item["type"] for item in suggestions}
    assert "recommendation" in types
    assert "todo" in types
    assert "provider_setup" in types

