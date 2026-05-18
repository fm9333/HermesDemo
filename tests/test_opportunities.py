from hermes_app.core.database import Database
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.opportunities import OpportunityEngine


def test_opportunity_engine_generates_rain_reminder(tmp_path):
    db = Database(tmp_path / "opportunities.db")
    db.init()
    signals = ContextSignalService(db)
    engine = OpportunityEngine(db, signals)

    signals.collect("weather", "weather.rain", {"probability": 80})
    opportunities = engine.generate()

    assert len(opportunities) == 1
    assert opportunities[0]["opportunity_type"] == "reminder_recommendation"
    assert opportunities[0]["payload"]["recommendation"] == "建议创建带伞提醒"

