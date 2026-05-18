from hermes_app.core.database import Database
from hermes_app.services.providers import ProviderRegistry


def test_provider_registry_defaults_connect_disconnect(tmp_path):
    db = Database(tmp_path / "providers.db")
    db.init()
    registry = ProviderRegistry(db)

    providers = {item["provider_id"]: item for item in registry.list()}
    assert providers["weather.open_meteo"]["status"] == "connected"
    assert providers["calendar.local"]["status"] == "disconnected"

    connected = registry.connect("calendar.local", {"account": "local"})
    assert connected["status"] == "connected"
    assert connected["config"]["account"] == "local"

    disconnected = registry.disconnect("calendar.local")
    assert disconnected["status"] == "disconnected"

