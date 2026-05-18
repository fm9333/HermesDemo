import os
from io import BytesIO

os.environ["HERMES_DB"] = ":memory:"
os.environ.pop("HERMES_LOCAL_TOKEN", None)

from PIL import Image
from fastapi.testclient import TestClient

from hermes_app.main import app, weather_service


client = TestClient(app)


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 3), color=(255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_contains_recommendation_controls():
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-panel="recommendations"' in response.text
    assert 'data-panel="sceneFeedback"' in response.text
    assert 'data-panel="todos"' in response.text
    assert 'data-panel="prdDrafts"' in response.text
    assert 'data-panel="yellowQueue"' in response.text
    assert 'data-panel="autonomy"' in response.text
    assert 'data-panel="redZone"' in response.text
    assert 'data-panel="evalRuns"' in response.text
    assert 'data-panel="growthLog"' in response.text
    assert 'data-panel="settings"' in response.text
    assert 'id="panel-action"' in response.text


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


def test_autonomy_zone_api():
    zones = client.get("/api/autonomy/zones")
    assert zones.status_code == 200
    assert {item["zone"] for item in zones.json()} == {"green", "yellow", "red"}

    classified = client.post(
        "/api/autonomy/classify",
        json={"proposal_type": "tool_plan", "risk_level": "low", "summary": "导出并分享隐私数据"},
    )
    assert classified.status_code == 200
    assert classified.json()["zone"] == "red"
    assert classified.json()["allowed_actions"] == ["suggest_only"]


def test_eval_runner_api():
    suites = client.get("/api/eval/suites")
    assert suites.status_code == 200
    assert any(item["suite_id"] == "autonomy.zone.basic" for item in suites.json())

    run = client.post("/api/eval/suites/autonomy.zone.basic/run")
    assert run.status_code == 200
    assert run.json()["status"] == "passed"
    assert run.json()["score"] == 1

    runs = client.get("/api/eval/runs?suite_id=autonomy.zone.basic")
    assert runs.status_code == 200
    assert any(item["id"] == run.json()["id"] for item in runs.json())


def test_growth_log_api():
    created = client.post(
        "/api/growth-log",
        json={
            "title": "优化摘要模板",
            "zone": "green",
            "source_task": "manual",
            "impact": "提升摘要稳定性",
            "payload": {"note": "unit-test"},
        },
    )
    assert created.status_code == 200
    assert created.json()["status"] == "active"
    assert created.json()["payload"]["note"] == "unit-test"

    listed = client.get("/api/growth-log?status=active")
    assert listed.status_code == 200
    assert any(item["id"] == created.json()["id"] for item in listed.json())

    rolled_back = client.post(f"/api/growth-log/{created.json()['id']}/rollback")
    assert rolled_back.status_code == 200
    assert rolled_back.json()["status"] == "rolled_back"


def test_settings_api():
    listed = client.get("/api/settings")
    assert listed.status_code == 200
    assert any(item["key"] == "autonomy_enabled" for item in listed.json())

    updated = client.patch("/api/settings/autonomy_enabled", json={"value": False})
    assert updated.status_code == 200
    assert updated.json()["value"] is False

    invalid = client.patch("/api/settings/red_zone_policy", json={"value": "unsafe"})
    assert invalid.status_code == 400


def test_tools_api_lists_action_tool_registry():
    response = client.get("/api/tools")
    assert response.status_code == 200
    tool_ids = {tool["tool_id"] for tool in response.json()}
    assert "reminder.create" in tool_ids
    assert "wardrobe.add" in tool_ids


def test_yellow_zone_pending_queue():
    response = client.post("/api/chat", json={"message": "明天上午提醒我确认合同"})
    assert response.status_code == 200
    action = response.json()["actions"][0]
    assert action["risk_level"] == "medium"

    pending = client.get("/api/yellow-zone/pending")
    assert pending.status_code == 200
    assert any(item["id"] == action["id"] for item in pending.json())

    rejected = client.post(f"/api/actions/{action['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


def test_skill_run_api_records_result():
    response = client.post("/api/skills/content.list_generate/run", json={"message": "帮我生成上线清单"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["output"]["title"] == "清单草案"

    runs = client.get("/api/skills/runs").json()
    assert any(run["skill_id"] == "content.list_generate" for run in runs)


def test_file_upload_api():
    response = client.post(
        "/api/files/upload",
        files={"file": ("meeting.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "meeting.txt"
    assert data["size"] == 5

    files = client.get("/api/files").json()
    assert any(item["id"] == data["id"] for item in files)

    summary = client.post(f"/api/files/{data['id']}/summarize")
    assert summary.status_code == 200
    assert summary.json()["skill_id"] == "document.summarize"
    assert summary.json()["status"] == "ok"


def test_image_upload_api():
    response = client.post(
        "/api/images/upload",
        files={"file": ("coat.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "coat.png"
    assert data["width"] == 2
    assert data["height"] == 3

    images = client.get("/api/images").json()
    assert any(item["id"] == data["id"] for item in images)

    recognized = client.post(f"/api/images/{data['id']}/recognize-clothing")
    assert recognized.status_code == 200
    result = recognized.json()
    assert result["candidate"]["category"] == "outerwear"
    assert result["action"]["action_type"] == "wardrobe.add"


def test_inspiration_chat_saves_structured_idea_card():
    response = client.post("/api/chat", json={"message": "帮我反方挑战 桌面智能体灵感工作室"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "inspiration"
    assert data["actions"][0]["action_type"] == "idea.save"
    card = data["cards"][0]
    assert card["type"] == "idea_card"
    assert card["mode"] == "challenge"
    assert card["risks"]
    assert card["next_steps"]

    confirmed = client.post(f"/api/actions/{data['actions'][0]['id']}/confirm")
    assert confirmed.status_code == 200
    idea_id = confirmed.json()["result"]["idea_id"]

    detail = client.get(f"/api/ideas/{idea_id}")
    assert detail.status_code == 200
    idea = detail.json()
    assert idea["id"] == idea_id
    assert idea["direction"] == "桌面智能体工作室"
    assert idea["risks"]
    assert idea["next_steps"]
    assert "idea-card" in idea["tags"]

    converted = client.post(f"/api/ideas/{idea_id}/to-todo")
    assert converted.status_code == 200
    todos = converted.json()["todos"]
    assert len(todos) == len(idea["next_steps"])
    assert all(item["source"] == "idea" and item["source_id"] == idea_id for item in todos)

    converted_again = client.post(f"/api/ideas/{idea_id}/to-todo")
    assert [item["id"] for item in converted_again.json()["todos"]] == [item["id"] for item in todos]

    listed = client.get("/api/todos?status=open")
    assert listed.status_code == 200
    assert any(item["id"] == todos[0]["id"] for item in listed.json())

    completed = client.post(f"/api/todos/{todos[0]['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    prd = client.post(f"/api/ideas/{idea_id}/to-prd")
    assert prd.status_code == 200
    assert prd.json()["idea_id"] == idea_id
    assert "## MVP 范围" in prd.json()["body"]

    prd_again = client.post(f"/api/ideas/{idea_id}/to-prd")
    assert prd_again.status_code == 200
    assert prd_again.json()["id"] == prd.json()["id"]

    prd_detail = client.get(f"/api/prd-drafts/{prd.json()['id']}")
    assert prd_detail.status_code == 200
    assert prd_detail.json()["id"] == prd.json()["id"]

    scene = client.post(f"/api/ideas/{idea_id}/to-scene")
    assert scene.status_code == 200
    assert scene.json()["source"] == "idea"
    assert scene.json()["context_signal"] == f"idea:{idea_id}"

    scene_again = client.post(f"/api/ideas/{idea_id}/to-scene")
    assert scene_again.status_code == 200
    assert scene_again.json()["id"] == scene.json()["id"]

    preference = client.post(f"/api/ideas/{idea_id}/preference-candidate")
    assert preference.status_code == 200
    preference_data = preference.json()
    assert preference_data["candidate"]["status"] == "pending"
    assert preference_data["candidate"]["key"] == "inspiration_preference"
    assert preference_data["action"]["action_type"] == "memory.confirm_candidate"

    confirmed_preference = client.post(f"/api/actions/{preference_data['action']['id']}/confirm")
    assert confirmed_preference.status_code == 200
    memory_id = confirmed_preference.json()["result"]["memory_id"]
    memories = client.get("/api/memory").json()
    assert any(item["id"] == memory_id and item["key"] == "inspiration_preference" for item in memories)


def test_scene_api_and_chat_flow():
    response = client.post("/api/scenes", json={"name": "雨天通勤提醒", "output_type": "reminder"})
    assert response.status_code == 200
    scene = response.json()
    assert scene["name"] == "雨天通勤提醒"

    run = client.post(f"/api/scenes/{scene['id']}/run")
    assert run.status_code == 200
    assert run.json()["status"] == "ok"

    feedback = client.post(
        f"/api/scenes/{scene['id']}/feedback",
        json={"rating": "misfire", "reason": "too early", "run_id": run.json()["run_id"]},
    )
    assert feedback.status_code == 200
    assert feedback.json()["rating"] == "misfire"

    feedback_items = client.get(f"/api/scenes/{scene['id']}/feedback")
    assert feedback_items.status_code == 200
    assert any(item["id"] == feedback.json()["id"] for item in feedback_items.json())

    all_feedback = client.get("/api/scene-feedback")
    assert all_feedback.status_code == 200
    assert any(item["id"] == feedback.json()["id"] for item in all_feedback.json())

    chat = client.post("/api/chat", json={"message": "创建雨天通勤提醒场景"})
    assert chat.status_code == 200
    data = chat.json()
    assert data["intent"] == "create_scene"
    assert data["cards"][0]["type"] == "scene"


def test_context_signal_api_flow():
    response = client.post(
        "/api/context-signals",
        json={"source": "weather", "signal_type": "weather.rain", "payload": {"probability": 80}},
    )
    assert response.status_code == 200
    signal = response.json()
    assert signal["payload"]["probability"] == 80

    listed = client.get("/api/context-signals?signal_type=weather.rain")
    assert listed.status_code == 200
    assert any(item["id"] == signal["id"] for item in listed.json())

    archived = client.post(f"/api/context-signals/{signal['id']}/archive")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


def test_opportunity_api_flow():
    signal = client.post(
        "/api/context-signals",
        json={"source": "weather", "signal_type": "weather.rain", "payload": {"probability": 80}},
    ).json()
    generated = client.post("/api/opportunities/generate")
    assert generated.status_code == 200
    assert any(item["signal_id"] == signal["id"] for item in generated.json())

    listed = client.get("/api/opportunities")
    assert listed.status_code == 200
    opportunity = next(item for item in listed.json() if item["signal_id"] == signal["id"])

    closed = client.post(f"/api/opportunities/{opportunity['id']}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"


def test_recommendation_api_flow():
    signal = client.post(
        "/api/context-signals",
        json={"source": "weather", "signal_type": "weather.rain", "payload": {"probability": 85}},
    ).json()
    client.post("/api/opportunities/generate")
    opportunity = next(
        item for item in client.get("/api/opportunities").json() if item["signal_id"] == signal["id"]
    )

    generated = client.post("/api/recommendations/generate")
    assert generated.status_code == 200
    recommendation = next(
        item for item in generated.json() if item["opportunity_id"] == opportunity["id"]
    )
    assert recommendation["channel"] == "interrupt"
    assert recommendation["payload"]["attention"]["requires_confirmation"] is True

    listed = client.get("/api/recommendations?status=open")
    assert listed.status_code == 200
    assert any(item["id"] == recommendation["id"] for item in listed.json())

    dismissed = client.post(f"/api/recommendations/{recommendation['id']}/dismiss")
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"


def test_wardrobe_action_and_crud_flow():
    response = client.post("/api/chat", json={"message": "把这件黑色外套加入衣橱"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "wardrobe_add"
    assert data["actions"][0]["action_type"] == "wardrobe.add"

    action_id = data["actions"][0]["id"]
    confirmed = client.post(f"/api/actions/{action_id}/confirm")
    assert confirmed.status_code == 200

    items = client.get("/api/wardrobe").json()
    item = next(item for item in items if "黑色外套" in item["name"])

    updated = client.patch(f"/api/wardrobe/{item['id']}", json={"name": "黑色通勤外套"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "黑色通勤外套"

    archived = client.delete(f"/api/wardrobe/{item['id']}")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
