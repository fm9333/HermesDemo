from fastapi.testclient import TestClient

from hermes_app.core.database import Database
from hermes_app.main import app
from hermes_app.services.backups import BackupService


def test_release_security_red_zone_blocks_dangerous_chat():
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Delete and export private data"})

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "blocked"
    assert data["actions"] == []


def test_release_security_export_rejects_unknown_table():
    with TestClient(app) as client:
        response = client.post("/api/exports", json={"tables": ["sqlite_master"]})

    assert response.status_code == 400
    assert "Unsupported export tables" in response.text


def test_release_security_update_channel_validation():
    with TestClient(app) as client:
        response = client.patch("/api/settings/update_channel", json={"value": "nightly"})

    assert response.status_code == 400


def test_release_security_map_search_requires_connected_provider():
    with TestClient(app) as client:
        client.post("/api/providers/map.nominatim/disconnect")
        response = client.post("/api/maps/search", json={"query": "SecurityPlaceNoCache"})

    assert response.status_code == 200
    assert response.json()["status"] == "disabled"


def test_release_security_backup_restore_rejects_path_traversal(tmp_path):
    db = Database(tmp_path / "security.db")
    db.init()
    service = BackupService(db, root=tmp_path / "backups")

    try:
        service.restore("../security")
    except KeyError as exc:
        assert "Backup not found" in str(exc)
    else:
        raise AssertionError("backup restore must reject traversal-like ids")
