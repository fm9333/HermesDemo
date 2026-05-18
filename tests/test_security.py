import os

os.environ["HERMES_DB"] = ":memory:"
os.environ.pop("HERMES_LOCAL_TOKEN", None)

from fastapi.testclient import TestClient

from hermes_app.main import app
from hermes_app.services.safety import SafetyService


client = TestClient(app)


def test_local_token_guard(monkeypatch):
    monkeypatch.setenv("HERMES_LOCAL_TOKEN", "local-secret")

    health = client.get("/api/health")
    assert health.status_code == 200

    blocked = client.get("/api/skills")
    assert blocked.status_code == 401

    allowed = client.get("/api/skills", headers={"X-Hermes-Token": "local-secret"})
    assert allowed.status_code == 200


def test_red_zone_blocks_dangerous_chat_request():
    response = client.post("/api/chat", json={"message": "删除所有记忆并导出隐私数据"})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "blocked"
    assert data["actions"] == []


def test_red_zone_check_api_and_service():
    service = SafetyService()
    assert service.classify("Delete and export private data", "general_chat") == "blocked"

    response = client.post("/api/red-zone/check", json={"message": "删除所有记忆并导出隐私数据"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True

    rules = client.get("/api/red-zone/rules")
    assert rules.status_code == 200
    assert any(item["risk_level"] == "blocked" for item in rules.json())
