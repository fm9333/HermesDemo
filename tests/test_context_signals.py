from hermes_app.core.database import Database
from hermes_app.services.context_signals import ContextSignalService


def test_context_signal_collect_list_archive(tmp_path):
    db = Database(tmp_path / "signals.db")
    db.init()
    service = ContextSignalService(db)

    signal = service.collect("weather", "weather.rain", {"probability": 80})
    assert signal["payload"]["probability"] == 80

    signals = service.list(signal_type="weather.rain")
    assert len(signals) == 1

    archived = service.archive(signal["id"])
    assert archived["status"] == "archived"

