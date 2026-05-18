import os

os.environ["HERMES_DB"] = ":memory:"
os.environ.pop("HERMES_LOCAL_TOKEN", None)

from fastapi.testclient import TestClient

from hermes_app.main import app


client = TestClient(app)


def test_local_token_guard(monkeypatch):
    monkeypatch.setenv("HERMES_LOCAL_TOKEN", "local-secret")

    health = client.get("/api/health")
    assert health.status_code == 200

    blocked = client.get("/api/skills")
    assert blocked.status_code == 401

    allowed = client.get("/api/skills", headers={"X-Hermes-Token": "local-secret"})
    assert allowed.status_code == 200

