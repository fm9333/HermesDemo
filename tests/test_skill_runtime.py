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


def test_todo_extract_skill_extracts_action_items(tmp_path):
    db = Database(tmp_path / "skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())

    result = runtime.run("work.todo_extract", "请小王明天确认发布清单；需要修复登录失败问题。")

    todos = result["output"]["todos"]
    assert result["status"] == "ok"
    assert len(todos) == 2
    assert "确认发布清单" in todos[0]["title"]
    assert "修复登录失败" in todos[1]["title"]


def test_list_generate_skill_uses_release_template(tmp_path):
    db = Database(tmp_path / "skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())

    result = runtime.run("content.list_generate", "帮我生成上线清单")

    output = result["output"]
    assert output["list_type"] == "release"
    assert output["items"][0]["title"] == "确认发布范围"
