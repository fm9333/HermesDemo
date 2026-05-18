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
