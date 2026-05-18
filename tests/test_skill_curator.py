from hermes_app.core.database import Database
from hermes_app.services.personal_skills import PersonalSkillService
from hermes_app.services.skill_curator import SkillCuratorService


def test_skill_curator_detects_duplicate_and_unevaluated_drafts(tmp_path):
    db = Database(tmp_path / "curator.db")
    db.init()
    skills = PersonalSkillService(db)
    first = skills.create_draft(
        title="会议纪要模板",
        description="first",
        prompt_template="输出结论和待办。",
        output_contract={"format": "json"},
    )
    second = skills.create_draft(
        title="会议纪要模板",
        description="second",
        prompt_template="输出结论、待办和风险。",
        output_contract={"format": "json"},
    )
    curator = SkillCuratorService(db)

    suggestions = curator.suggest()

    assert any(item["type"] == "duplicate_skill" for item in suggestions)
    assert any(item["type"] == "unevaluated_draft" and first["id"] in item["skill_ids"] for item in suggestions)
    assert any(item["type"] == "unevaluated_draft" and second["id"] in item["skill_ids"] for item in suggestions)

    run = curator.run()
    assert run["status"] == "attention_needed"
    assert "duplicate_skill" in run["summary"]
    assert curator.list_runs()[0]["id"] == run["id"]


def test_skill_curator_detects_failed_patch_and_churn(tmp_path):
    db = Database(tmp_path / "curator.db")
    db.init()
    skills = PersonalSkillService(db)
    draft = skills.create_draft(
        title="周报模板",
        description="source",
        prompt_template="输出本周完成和下周计划。",
        output_contract={"format": "json"},
    )
    skills.evaluate(draft["id"])
    active = skills.activate(draft["id"])
    for index in range(3):
        patch = skills.create_patch(
            active["id"],
            reason=f"优化 {index}",
            proposed_prompt_template=f"输出本周完成、风险和下周计划 {index}",
        )
        skills.evaluate_patch(patch["id"])
        skills.apply_patch(patch["id"])
    stale = skills.create_patch(active["id"], reason="过期补丁", proposed_prompt_template="旧补丁")
    newer = skills.create_patch(active["id"], reason="新补丁", proposed_prompt_template="新补丁")
    skills.evaluate_patch(newer["id"])
    skills.apply_patch(newer["id"])
    skills.evaluate_patch(stale["id"])

    suggestions = SkillCuratorService(db).suggest()

    assert any(item["type"] == "high_churn_skill" for item in suggestions)
    assert any(item["type"] == "failed_patch" and item["patch_id"] == stale["id"] for item in suggestions)
