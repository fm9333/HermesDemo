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


def test_expanded_system_skills_have_local_outputs(tmp_path):
    db = Database(tmp_path / "skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())

    samples = {
        "document.contract_extract": "甲方：上海甲公司；乙方：北京乙公司；2026年6月1日付款 12000 元，逾期违约赔偿。",
        "document.bill_analyze": "5月云服务账单 299.50 元，6月10日到期，重复收费待确认。",
        "image.photo_classify": "旅行照片，北京景点，适合相册整理。",
        "work.meeting_minutes": "会议决定本周上线；请小王明天修复登录问题；风险是接口延期。",
        "work.weekly_report": "本周完成登录修复并发布；下周计划补齐报表；风险是接口延期。",
        "content.prd_generate": "帮我生成桌面智能体任务中心 PRD",
        "content.copy_generate": "写一段桌面智能体营销文案",
        "content.travel_plan": "帮我做去杭州旅行计划",
        "data.table_analyze": "name,amount\nA,10\nB,20\nC,",
        "file.archive_plan": "把合同和发票文件整理归档",
        "calendar.schedule_plan": "明天和小王安排会议讨论上线",
        "email.reply_draft": "回复客户邮件：我们会确认合同付款时间。",
    }

    for skill_id, message in samples.items():
        result = runtime.run(skill_id, message)
        assert result["status"] == "ok"
        assert result["output"]["title"] != "Skill 未注册"

    runs = runtime.list_runs()
    assert len(runs) == len(samples)


def test_contract_bill_and_table_skills_extract_key_fields(tmp_path):
    db = Database(tmp_path / "skills.db")
    db.init()
    runtime = SkillRuntime(db, SkillRegistry())

    contract = runtime.run(
        "document.contract_extract",
        "甲方：上海甲公司；乙方：北京乙公司；2026年6月1日付款 12000 元，逾期违约赔偿。",
    )["output"]
    assert contract["parties"]["party_a"] == "上海甲公司"
    assert "12000 元" in contract["key_terms"]["amounts"]
    assert contract["risks"]

    bill = runtime.run("document.bill_analyze", "5月账单 299.50 元，6月10日到期，重复收费待确认。")["output"]
    assert "299.50 元" in bill["detected_amounts"]
    assert "6月10日" in bill["due_dates"]
    assert bill["anomalies"]

    table = runtime.run("data.table_analyze", "name,amount\nA,10\nB,20\nC,")["output"]
    assert table["row_count"] == 3
    assert table["numeric_columns"][0]["sum"] == 30
    assert table["quality_issues"]
