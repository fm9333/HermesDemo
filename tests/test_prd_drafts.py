from hermes_app.core.database import Database
from hermes_app.services.prd_drafts import PrdDraftService


def test_prd_draft_service_creates_idempotent_draft_from_idea(tmp_path):
    db = Database(tmp_path / "prd.db")
    db.init()
    service = PrdDraftService(db)
    db.execute(
        "INSERT INTO idea_cards (id, title, body, tags_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("idea-1", "灵感工作室", "", "[]", "2026-05-18T00:00:00+00:00"),
    )
    idea = {
        "id": "idea-1",
        "title": "灵感工作室",
        "pain_point": "想法难以落地",
        "target_user": "独立开发者",
        "core_assumption": "结构化后更容易行动",
        "mvp_plan": "先生成一个 PRD 草案",
        "counter_challenge": "不要只做漂亮文档",
        "risks": ["范围过大"],
        "next_steps": ["验证草案是否可执行"],
    }

    draft = service.create_from_idea(idea)
    again = service.create_from_idea(idea)

    assert draft["id"] == again["id"]
    assert draft["idea_id"] == "idea-1"
    assert "## MVP 范围" in draft["body"]
    assert "范围过大" in draft["body"]
