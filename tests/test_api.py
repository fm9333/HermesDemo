import os

os.environ["HERMES_DB"] = ":memory:"

from fastapi.testclient import TestClient

from hermes_app.main import app, weather_service


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_reminder_action_flow():
    response = client.post("/api/chat", json={"message": "明天早上提醒我带伞"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "create_reminder"
    assert data["actions"][0]["action_type"] == "reminder.create"

    action_id = data["actions"][0]["id"]
    confirmed = client.post(f"/api/actions/{action_id}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["result"]["status"] == "created"

    reminders = client.get("/api/reminders").json()
    assert any("带伞" in item["title"] for item in reminders)


def test_memory_action_flow():
    response = client.post("/api/chat", json={"message": "记住我喜欢科技新闻"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "memory_update"
    assert data["memory_candidates"][0]["memory_type"] == "preference"

    action_id = data["actions"][0]["id"]
    confirmed = client.post(f"/api/actions/{action_id}/confirm")
    assert confirmed.status_code == 200

    memory_items = client.get("/api/memory").json()
    assert any("科技新闻" in item["value"] for item in memory_items)


def test_weather_chat_flow(monkeypatch):
    monkeypatch.setattr(
        weather_service,
        "lookup",
        lambda location: {
            "status": "ok",
            "summary": f"{location} 当前 20°C，晴。",
            "current": {"temperature": 20, "summary": "晴"},
        },
    )

    response = client.post("/api/chat", json={"message": "北京天气"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "weather_query"
    assert data["cards"][0]["type"] == "weather"
    assert "北京 当前 20°C" in data["reply"]
