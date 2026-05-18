import os
from io import BytesIO

os.environ["HERMES_DB"] = ":memory:"
os.environ.pop("HERMES_LOCAL_TOKEN", None)

from PIL import Image
from fastapi.testclient import TestClient

from hermes_app.main import (
    app,
    backup_service,
    export_service,
    llm_client,
    map_service,
    news_service,
    weather_service,
)


client = TestClient(app)


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 3), color=(255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


NEWS_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>API news headline</title>
      <link>https://example.com/api-news</link>
      <description>API news summary</description>
      <pubDate>Mon, 18 May 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


MAP_JSON = b"""[
  {
    "place_id": 2,
    "osm_type": "node",
    "osm_id": 456,
    "display_name": "Shanghai, China",
    "lat": "31.2322758",
    "lon": "121.4692071",
    "category": "place",
    "type": "city",
    "importance": 0.8,
    "boundingbox": ["30.66", "31.87", "120.85", "122.12"],
    "address": {"city": "Shanghai", "country": "China"}
  }
]"""


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_contains_recommendation_controls():
    response = client.get("/")
    assert response.status_code == 200
    assert 'data-panel="homeCards"' in response.text
    assert 'data-panel="recommendations"' in response.text
    assert 'data-panel="proactive"' in response.text
    assert 'data-panel="triggerRuns"' in response.text
    assert 'data-panel="weeklyReviews"' in response.text
    assert 'data-panel="news"' in response.text
    assert 'data-panel="maps"' in response.text
    assert 'data-panel="sceneFeedback"' in response.text
    assert 'data-panel="todos"' in response.text
    assert 'data-panel="prdDrafts"' in response.text
    assert 'data-panel="yellowQueue"' in response.text
    assert 'data-panel="autonomy"' in response.text
    assert 'data-panel="redZone"' in response.text
    assert 'data-panel="evalRuns"' in response.text
    assert 'data-panel="growthLog"' in response.text
    assert 'data-panel="settings"' in response.text
    assert 'data-panel="databaseMigrations"' in response.text
    assert 'data-panel="runtimeRecovery"' in response.text
    assert 'data-panel="updates"' in response.text
    assert 'data-panel="performance"' in response.text
    assert 'data-panel="providers"' in response.text
    assert 'data-panel="personalSkills"' in response.text
    assert 'data-panel="skillPatches"' in response.text
    assert 'data-panel="skillCurator"' in response.text
    assert 'data-panel="llmProviders"' in response.text
    assert 'data-panel="llmFilePolicy"' in response.text
    assert 'data-panel="prompts"' in response.text
    assert 'data-panel="llmCalls"' in response.text
    assert 'data-panel="backups"' in response.text
    assert 'data-panel="exports"' in response.text
    assert 'id="panel-action"' in response.text


def test_home_cards_api():
    response = client.get("/api/home/cards")
    assert response.status_code == 200
    cards = response.json()
    assert cards
    assert {"id", "type", "title", "priority", "route", "payload"}.issubset(cards[0])


def test_backup_api(tmp_path, monkeypatch):
    backup_root = tmp_path / "api-backups"
    backup_root.mkdir()
    monkeypatch.setattr(backup_service, "root", backup_root)

    created = client.post("/api/backups", json={"note": "api-test"})
    assert created.status_code == 200
    backup = created.json()
    assert backup["note"] == "api-test"

    listed = client.get("/api/backups")
    assert listed.status_code == 200
    assert any(item["id"] == backup["id"] for item in listed.json())


def test_database_migrations_api():
    response = client.get("/api/database/migrations")
    assert response.status_code == 200
    migration_ids = [item["id"] for item in response.json()]
    assert "0001_core_schema" in migration_ids
    assert "0004_release_backups" in migration_ids


def test_runtime_recovery_api():
    response = client.get("/api/runtime/recovery")
    assert response.status_code == 200
    data = response.json()
    assert data["state"]["status"] == "running"
    assert data["recovery"]["status"] in {"clean", "recovered"}
    assert data["state_path"]


def test_updates_api(tmp_path):
    manifest = tmp_path / "update-manifest.json"
    manifest.write_text('{"version":"0.2.0","channel":"stable","url":"https://example.com/Hermes.exe"}')
    client.patch("/api/settings/update_manifest_url", json={"value": str(manifest)})

    status = client.get("/api/updates/status")
    assert status.status_code == 200
    assert status.json()["manifest_url"] == str(manifest)

    checked = client.post("/api/updates/check")
    assert checked.status_code == 200
    assert checked.json()["status"] == "update_available"


def test_performance_indexes_api():
    response = client.get("/api/performance/indexes")
    assert response.status_code == 200
    index_names = {item["name"] for item in response.json()}
    assert "idx_pending_actions_status_created" in index_names
    assert "idx_map_places_query_created" in index_names


def test_export_api(tmp_path, monkeypatch):
    export_root = tmp_path / "api-exports"
    export_root.mkdir()
    monkeypatch.setattr(export_service, "root", export_root)

    created = client.post("/api/exports", json={"note": "api-test", "tables": ["schema_migrations"]})
    assert created.status_code == 200
    export = created.json()
    assert export["note"] == "api-test"
    assert export["tables"] == ["schema_migrations"]

    listed = client.get("/api/exports")
    assert listed.status_code == 200
    assert any(item["id"] == export["id"] for item in listed.json())


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


def test_news_api(monkeypatch):
    monkeypatch.setattr(news_service, "_fetch", lambda url: NEWS_RSS)

    refreshed = client.post("/api/news/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["status"] == "ok"
    assert refreshed.json()["count"] >= 1

    listed = client.get("/api/news")
    assert listed.status_code == 200
    article = next(item for item in listed.json() if item["title"] == "API news headline")

    detail = client.get(f"/api/news/{article['id']}")
    assert detail.status_code == 200
    assert detail.json()["url"] == "https://example.com/api-news"


def test_maps_api(monkeypatch):
    client.post("/api/providers/map.nominatim/connect", json={"config": {"consent": "unit-test"}})
    monkeypatch.setattr(map_service, "_fetch", lambda query, limit, provider: MAP_JSON)

    searched = client.post("/api/maps/search", json={"query": "Shanghai", "limit": 1})
    assert searched.status_code == 200
    assert searched.json()["status"] in {"ok", "cached"}
    place = searched.json()["places"][0]
    assert place["display_name"] == "Shanghai, China"

    listed = client.get("/api/maps/places")
    assert listed.status_code == 200
    assert any(item["id"] == place["id"] for item in listed.json())

    detail = client.get(f"/api/maps/places/{place['id']}")
    assert detail.status_code == 200
    assert detail.json()["address"]["country"] == "China"


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


def test_provider_registry_api():
    listed = client.get("/api/providers")
    assert listed.status_code == 200
    providers = {item["provider_id"]: item for item in listed.json()}
    assert providers["weather.open_meteo"]["status"] == "connected"

    connected = client.post("/api/providers/calendar.local/connect", json={"config": {"account": "local"}})
    assert connected.status_code == 200
    assert connected.json()["status"] == "connected"
    assert connected.json()["config"]["account"] == "local"

    disconnected = client.post("/api/providers/calendar.local/disconnect")
    assert disconnected.status_code == 200
    assert disconnected.json()["status"] == "disconnected"


def test_llm_provider_api_and_chat(monkeypatch):
    created = client.post(
        "/api/llm/providers",
        json={
            "provider_id": "api.llm.test",
            "name": "API LLM Test",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "test-model",
            "api_key": "secret-key",
            "is_default": True,
        },
    )
    assert created.status_code == 200
    provider = created.json()
    assert provider["api_key_set"] is True
    assert provider["secret_backend"] in {"windows_dpapi", "local_obfuscation"}
    assert "secret-key" not in str(provider)

    monkeypatch.setattr(
        llm_client,
        "_post_json",
        lambda provider, payload: {"choices": [{"message": {"content": "模型回复"}}]},
    )

    tested = client.post("/api/llm/providers/api.llm.test/test")
    assert tested.status_code == 200
    assert tested.json()["status"] == "ok"

    chatted = client.post("/api/llm/chat", json={"message": "你好"})
    assert chatted.status_code == 200
    assert chatted.json()["reply"] == "模型回复"

    general = client.post("/api/chat", json={"message": "帮我分析这个产品下一步怎么做"})
    assert general.status_code == 200
    data = general.json()
    assert data["intent"] == "general_chat"
    assert data["reply"] == "模型回复"
    assert data["cards"][0]["type"] == "llm"

    calls = client.get("/api/llm/calls")
    assert calls.status_code == 200
    assert any(item["provider_id"] == "api.llm.test" for item in calls.json())


def test_llm_file_policy_api():
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "api.file.policy",
            "name": "File Policy",
            "base_url": "https://api.openai.com/v1",
            "model": "test-model",
            "api_key": "secret",
            "allow_file_context": False,
        },
    )

    policy = client.get("/api/llm/file-policy")
    assert policy.status_code == 200
    assert policy.json()["secret_protection"]["backend"] in {"windows_dpapi", "local_obfuscation"}
    provider = next(item for item in policy.json()["providers"] if item["provider_id"] == "api.file.policy")
    assert provider["effective_file_context_allowed"] is False

    secret_policy = client.get("/api/llm/secret-policy")
    assert secret_policy.status_code == 200
    assert secret_policy.json()["backend"] in {"windows_dpapi", "local_obfuscation"}

    rotated = client.post("/api/llm/secret-policy/rotate")
    assert rotated.status_code == 200
    assert rotated.json()["backend"] in {"windows_dpapi", "local_obfuscation"}

    client.patch("/api/settings/llm_allow_cloud_file_context", json={"value": True})
    client.patch("/api/llm/providers/api.file.policy", json={"allow_file_context": True})
    allowed_policy = client.get("/api/llm/file-policy")
    allowed_provider = next(
        item for item in allowed_policy.json()["providers"] if item["provider_id"] == "api.file.policy"
    )
    assert allowed_provider["effective_file_context_allowed"] is True


def test_prompt_library_api():
    prompts = client.get("/api/prompts")
    assert prompts.status_code == 200
    assert any(item["prompt_id"] == "hermes.agent.core" for item in prompts.json())

    detail = client.get("/api/prompts/hermes.agent.core")
    assert detail.status_code == 200
    assert "Hermes" in detail.json()["system_prompt"]


def test_file_summarize_blocks_cloud_llm_without_consent(monkeypatch):
    client.post(
        "/api/llm/providers",
        json={
            "provider_id": "api.file.cloud",
            "name": "File Cloud",
            "base_url": "https://api.openai.com/v1",
            "model": "test-model",
            "api_key": "secret",
            "allow_file_context": False,
            "is_default": True,
        },
    )

    def fail_post(provider, payload):
        raise AssertionError("file text must not be sent to cloud LLM without explicit consent")

    monkeypatch.setattr(llm_client, "_post_json", fail_post)

    uploaded = client.post(
        "/api/files/upload",
        files={"file": ("private.txt", b"private file text", "text/plain")},
    )
    assert uploaded.status_code == 200

    summarized = client.post(f"/api/files/{uploaded.json()['id']}/summarize")
    assert summarized.status_code == 200
    data = summarized.json()
    assert data["status"] == "ok"
    assert data["output"]["title"] == "文档总结草案"
    assert "_llm" not in data["output"]


def test_proactive_suggestions_api():
    suggestions = client.get("/api/proactive/suggestions")
    assert suggestions.status_code == 200
    assert isinstance(suggestions.json(), list)
    assert any(item["type"] == "provider_setup" for item in suggestions.json())


def test_trigger_run_api():
    client.post(
        "/api/context-signals",
        json={"source": "weather", "signal_type": "weather.rain", "payload": {"probability": 80}},
    )
    run = client.post("/api/triggers/run", json={"trigger_type": "test"})
    assert run.status_code == 200
    assert run.json()["status"] == "ok"
    assert run.json()["output"]["suggestions"]

    history = client.get("/api/triggers/history")
    assert history.status_code == 200
    assert any(item["id"] == run.json()["id"] for item in history.json())


def test_weekly_review_api():
    response = client.post("/api/chat", json={"message": "帮我反方挑战 每周灵感复盘"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "inspiration"

    confirmed = client.post(f"/api/actions/{data['actions'][0]['id']}/confirm")
    assert confirmed.status_code == 200

    generated = client.post("/api/weekly-reviews/generate")
    assert generated.status_code == 200
    review = generated.json()
    assert review["summary"]
    assert review["highlights"]
    assert review["next_actions"]

    listed = client.get("/api/weekly-reviews")
    assert listed.status_code == 200
    assert any(item["id"] == review["id"] for item in listed.json())


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


def test_skill_run_api_records_result(monkeypatch):
    monkeypatch.setattr(llm_client, "_post_json", lambda provider, payload: (_ for _ in ()).throw(RuntimeError("skip llm")))
    response = client.post("/api/skills/content.list_generate/run", json={"message": "帮我生成上线清单"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["output"]["title"] == "清单草案"

    runs = client.get("/api/skills/runs").json()
    assert any(run["skill_id"] == "content.list_generate" for run in runs)


def test_expanded_system_skills_are_listed_and_runnable(monkeypatch):
    monkeypatch.setattr(llm_client, "_post_json", lambda provider, payload: (_ for _ in ()).throw(RuntimeError("skip llm")))
    response = client.get("/api/skills")
    assert response.status_code == 200
    skill_ids = {skill["skill_id"] for skill in response.json()}
    expected = {
        "document.contract_extract",
        "document.bill_analyze",
        "image.photo_classify",
        "work.meeting_minutes",
        "work.weekly_report",
        "content.prd_generate",
        "content.copy_generate",
        "content.travel_plan",
        "data.table_analyze",
        "file.archive_plan",
        "calendar.schedule_plan",
        "email.reply_draft",
    }
    assert expected.issubset(skill_ids)

    table = client.post("/api/skills/data.table_analyze/run", json={"message": "name,amount\nA,10\nB,20"})
    assert table.status_code == 200
    assert table.json()["output"]["row_count"] == 2


def test_expanded_skill_chat_routes(monkeypatch):
    monkeypatch.setattr(llm_client, "_post_json", lambda provider, payload: (_ for _ in ()).throw(RuntimeError("skip llm")))

    prd = client.post("/api/chat", json={"message": "帮我生成桌面智能体任务中心 PRD"})
    assert prd.status_code == 200
    assert prd.json()["intent"] == "prd_generate"
    assert prd.json()["cards"][0]["skill_id"] == "content.prd_generate"

    meeting = client.post("/api/chat", json={"message": "整理会议纪要：会议决定上线，请小王明天修复登录问题"})
    assert meeting.status_code == 200
    assert meeting.json()["intent"] == "meeting_minutes"
    assert meeting.json()["cards"][0]["skill_id"] == "work.meeting_minutes"

    contract = client.post("/api/chat", json={"message": "分析合同：甲方A，乙方B，金额 1000 元"})
    assert contract.status_code == 200
    assert contract.json()["intent"] == "contract_extract"
    assert contract.json()["task_plan"]["steps"][0]["target"] == "document.contract_extract"


def test_personal_skill_api_flow(monkeypatch):
    monkeypatch.setattr(llm_client, "_post_json", lambda provider, payload: (_ for _ in ()).throw(RuntimeError("skip llm")))
    skill_run = client.post("/api/skills/content.list_generate/run", json={"message": "帮我生成上线清单"})
    assert skill_run.status_code == 200

    created = client.post(
        "/api/personal-skills/drafts",
        json={"source_run_id": skill_run.json()["run_id"], "title": "上线清单个人技能"},
    )
    assert created.status_code == 200
    draft = created.json()
    assert draft["status"] == "draft"
    assert draft["eval_status"] == "not_run"

    blocked = client.post(f"/api/personal-skills/{draft['id']}/activate")
    assert blocked.status_code == 409

    evaluated = client.post(f"/api/personal-skills/{draft['id']}/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["eval_status"] == "passed"

    activated = client.post(f"/api/personal-skills/{draft['id']}/activate")
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    listed = client.get("/api/personal-skills?status=active")
    assert listed.status_code == 200
    assert any(item["id"] == draft["id"] for item in listed.json())

    versions = client.get(f"/api/personal-skills/{draft['id']}/versions")
    assert versions.status_code == 200
    assert versions.json()[0]["version"] == 1

    archived = client.post(f"/api/personal-skills/{draft['id']}/archive")
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


def test_personal_skill_patch_api_flow(monkeypatch):
    monkeypatch.setattr(llm_client, "_post_json", lambda provider, payload: (_ for _ in ()).throw(RuntimeError("skip llm")))
    skill_run = client.post("/api/skills/content.list_generate/run", json={"message": "帮我生成上线清单"})
    draft = client.post(
        "/api/personal-skills/drafts",
        json={"source_run_id": skill_run.json()["run_id"], "title": "上线补丁技能"},
    ).json()
    client.post(f"/api/personal-skills/{draft['id']}/evaluate")
    active = client.post(f"/api/personal-skills/{draft['id']}/activate").json()

    created = client.post(
        f"/api/personal-skills/{active['id']}/patches",
        json={
            "reason": "加入发布后监控",
            "proposed_prompt_template": active["prompt_template"] + "\n补充发布后监控。",
        },
    )
    assert created.status_code == 200
    patch = created.json()
    assert patch["status"] == "draft"

    evaluated = client.post(f"/api/personal-skill-patches/{patch['id']}/evaluate")
    assert evaluated.status_code == 200
    assert evaluated.json()["eval_status"] == "passed"

    applied = client.post(f"/api/personal-skill-patches/{patch['id']}/apply")
    assert applied.status_code == 200
    assert applied.json()["skill"]["version"] == active["version"] + 1

    patches = client.get(f"/api/personal-skills/{active['id']}/patches")
    assert patches.status_code == 200
    assert any(item["id"] == patch["id"] and item["status"] == "applied" for item in patches.json())

    rolled_back = client.post(f"/api/personal-skills/{active['id']}/rollback")
    assert rolled_back.status_code == 200
    assert rolled_back.json()["version"] == active["version"] + 2


def test_skill_curator_api_flow():
    created = client.post(
        "/api/personal-skills/drafts",
        json={
            "title": "治理测试技能",
            "description": "curator api",
            "prompt_template": "输出治理测试。",
            "output_contract": {"format": "json"},
        },
    )
    assert created.status_code == 200

    suggestions = client.get("/api/skill-curator/suggestions")
    assert suggestions.status_code == 200
    assert any(item["type"] == "unevaluated_draft" and created.json()["id"] in item["skill_ids"] for item in suggestions.json())

    run = client.post("/api/skill-curator/run")
    assert run.status_code == 200
    assert run.json()["status"] == "attention_needed"

    runs = client.get("/api/skill-curator/runs")
    assert runs.status_code == 200
    assert any(item["id"] == run.json()["id"] for item in runs.json())


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
