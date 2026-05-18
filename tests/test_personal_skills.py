from hermes_app.core.database import Database
from hermes_app.services.personal_skills import PersonalSkillService
from hermes_app.services.skill_runtime import SkillRuntime
from hermes_app.services.skills import SkillRegistry


def test_personal_skill_draft_requires_eval_before_activation(tmp_path):
    db = Database(tmp_path / "personal-skills.db")
    db.init()
    service = PersonalSkillService(db)

    draft = service.create_draft(
        title="会议纪要格式",
        description="按固定结构生成会议纪要",
        prompt_template="输出结论、待办、风险、待确认问题。",
        output_contract={"format": "json", "required": ["summary", "todos"]},
    )

    assert draft["status"] == "draft"
    assert draft["eval_status"] == "not_run"

    try:
        service.activate(draft["id"])
    except ValueError:
        pass
    else:
        raise AssertionError("Draft must not activate before evaluation.")

    evaluated = service.evaluate(draft["id"])
    assert evaluated["eval_status"] == "passed"

    active = service.activate(draft["id"])
    assert active["status"] == "active"
    assert active["activated_at"]

    archived = service.archive(draft["id"])
    assert archived["status"] == "archived"


def test_personal_skill_can_be_created_from_skill_run(tmp_path):
    db = Database(tmp_path / "personal-skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())
    run = runtime.run("content.list_generate", "帮我生成上线清单")
    service = PersonalSkillService(db)

    draft = service.create_from_skill_run(run["run_id"])

    assert draft["source_run_id"] == run["run_id"]
    assert draft["output_contract"]["source_skill_id"] == "content.list_generate"
    assert service.versions(draft["id"])[0]["version"] == 1


def test_personal_skill_patch_apply_and_rollback(tmp_path):
    db = Database(tmp_path / "personal-skills.db")
    db.init()
    service = PersonalSkillService(db)
    draft = service.create_draft(
        title="周报模板",
        description="稳定输出周报",
        prompt_template="输出本周完成和下周计划。",
        output_contract={"format": "json", "required": ["done", "next"]},
    )
    service.evaluate(draft["id"])
    active = service.activate(draft["id"])

    patch = service.create_patch(
        active["id"],
        reason="增加风险字段",
        proposed_prompt_template="输出本周完成、风险和下周计划。",
        proposed_output_contract={"format": "json", "required": ["done", "risks", "next"]},
    )
    assert patch["target_version"] == 1
    assert patch["status"] == "draft"

    evaluated = service.evaluate_patch(patch["id"])
    assert evaluated["eval_status"] == "passed"

    applied = service.apply_patch(patch["id"])
    assert applied["patch"]["status"] == "applied"
    assert applied["skill"]["version"] == 2
    assert "风险" in applied["skill"]["prompt_template"]

    rolled_back = service.rollback(active["id"])
    assert rolled_back["version"] == 3
    assert "风险" not in rolled_back["prompt_template"]
    assert service.versions(active["id"])[0]["status"] == "rollback"


def test_stale_personal_skill_patch_fails_eval(tmp_path):
    db = Database(tmp_path / "personal-skills.db")
    db.init()
    service = PersonalSkillService(db)
    draft = service.create_draft(
        title="清单模板",
        description="稳定输出清单",
        prompt_template="输出清单。",
        output_contract={"format": "json", "required": ["items"]},
    )
    service.evaluate(draft["id"])
    service.activate(draft["id"])
    stale = service.create_patch(draft["id"], reason="第一次优化", proposed_prompt_template="输出详细清单。")
    fresh = service.create_patch(draft["id"], reason="第二次优化", proposed_prompt_template="输出分组清单。")
    service.evaluate_patch(fresh["id"])
    service.apply_patch(fresh["id"])

    evaluated_stale = service.evaluate_patch(stale["id"])

    assert evaluated_stale["eval_status"] == "failed"
    assert any(check["id"] == "target_version_current" and not check["passed"] for check in evaluated_stale["eval_report"]["checks"])
