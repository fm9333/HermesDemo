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
    assert data["task_plan"]["intent"] == "create_reminder"
    assert data["actions"][0]["action_type"] == "reminder.create"

    action_id = data["actions"][0]["id"]
    confirmed = client.post(f"/api/actions/{action_id}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["result"]["status"] == "created"

    reminders = client.get("/api/reminders").json()
    reminder = next(item for item in reminders if "带伞" in item["title"])

    detail = client.get(f"/api/reminders/{reminder['id']}")
    assert detail.status_code == 200

    updated = client.patch(f"/api/reminders/{reminder['id']}", json={"title": "明天带伞和雨衣"})
    assert updated.status_code == 200
    assert updated.json()["title"] == "明天带伞和雨衣"

    completed = client.post(f"/api/reminders/{reminder['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_memory_action_flow():
    response = client.post("/api/chat", json={"message": "记住我喜欢科技新闻"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "memory_update"
    assert data["memory_candidates"][0]["memory_type"] == "preference"
    assert data["actions"][0]["action_type"] == "memory.confirm_candidate"

    action_id = data["actions"][0]["id"]
    confirmed = client.post(f"/api/actions/{action_id}/confirm")
    assert confirmed.status_code == 200

    memory_items = client.get("/api/memory").json()
    assert any("科技新闻" in item["value"] for item in memory_items)

    candidates = client.get("/api/memory/candidates").json()
    assert any(item["status"] == "confirmed" and "科技新闻" in item["value"] for item in candidates)


def test_reject_memory_candidate_api():
    response = client.post("/api/chat", json={"message": "记住我最近少吃辣"})
    assert response.status_code == 200
    candidate_id = response.json()["actions"][0]["payload"]["candidate_id"]

    rejected = client.post(f"/api/memory/candidates/{candidate_id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


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
    assert data["task_plan"]["steps"][1]["target"] == "weather.lookup"
    assert data["cards"][0]["type"] == "weather"
    assert "北京 当前 20°C" in data["reply"]


def test_decompose_api():
    response = client.post("/api/decompose", json={"message": "记住我喜欢科技新闻"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "memory_update"
    assert data["steps"][0]["target"] == "memory_candidate_pipeline"


def test_tools_api_lists_action_tool_registry():
    response = client.get("/api/tools")
    assert response.status_code == 200
    tool_ids = {tool["tool_id"] for tool in response.json()}
    assert "reminder.create" in tool_ids
    assert "wardrobe.add" in tool_ids
