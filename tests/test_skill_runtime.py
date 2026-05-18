from hermes_app.core.database import Database
from hermes_app.services.skill_runtime import SkillRuntime
from hermes_app.services.skills import SkillRegistry


def test_skill_runtime_records_run(tmp_path):
    db = Database(tmp_path / "skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())

    result = runtime.run("content.list_generate", "帮我生成上线清单")

    assert result["status"] == "ok"
    assert result["output"]["title"] == "清单草案"
    runs = runtime.list_runs()
    assert len(runs) == 1
    assert runs[0]["skill_id"] == "content.list_generate"

