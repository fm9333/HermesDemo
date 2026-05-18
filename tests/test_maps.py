import json

from hermes_app.core.database import Database
from hermes_app.services.maps import MapService
from hermes_app.services.providers import ProviderRegistry


MAP_RESPONSE = [
    {
        "place_id": 1,
        "osm_type": "node",
        "osm_id": 123,
        "display_name": "Berlin, Germany",
        "lat": "52.5173885",
        "lon": "13.3951309",
        "category": "place",
        "type": "city",
        "importance": 0.9,
        "boundingbox": ["52.33", "52.67", "13.08", "13.76"],
        "address": {"city": "Berlin", "country": "Germany"},
    }
]


def test_map_service_requires_connected_provider(tmp_path, monkeypatch):
    db = Database(tmp_path / "maps_disabled.db")
    db.init()
    service = MapService(db, ProviderRegistry(db))
    monkeypatch.setattr(service, "_fetch", lambda query, limit, provider: json.dumps(MAP_RESPONSE).encode())

    result = service.search("Berlin")

    assert result == {"status": "disabled", "places": [], "count": 0}
    assert service.list() == []


def test_map_service_searches_and_caches_results(tmp_path, monkeypatch):
    db = Database(tmp_path / "maps.db")
    db.init()
    providers = ProviderRegistry(db)
    providers.connect("map.nominatim", {"consent": "unit-test"})
    service = MapService(db, providers)
    calls = []

    def fake_fetch(query: str, limit: int, provider: dict) -> bytes:
        calls.append((query, limit, provider["provider_id"]))
        return json.dumps(MAP_RESPONSE).encode()

    monkeypatch.setattr(service, "_fetch", fake_fetch)

    first = service.search("Berlin", limit=3)
    second = service.search("Berlin", limit=3)

    assert first["status"] == "ok"
    assert second["status"] == "cached"
    assert len(calls) == 1
    assert first["places"][0]["display_name"] == "Berlin, Germany"
    assert first["places"][0]["lat"] == 52.5173885
    assert first["places"][0]["address"]["city"] == "Berlin"
    assert service.get(first["places"][0]["id"])["lon"] == 13.3951309
