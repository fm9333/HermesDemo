from hermes_app.services.autonomy import AutonomyZoneClassifier


def test_autonomy_zone_classifier_green_yellow_red():
    classifier = AutonomyZoneClassifier()

    green = classifier.classify({"proposal_type": "skill_draft", "risk_level": "low", "summary": "优化摘要模板"})
    assert green["zone"] == "green"
    assert green["requires_confirmation"] is False
    assert green["requires_eval"] is True

    yellow = classifier.classify({"proposal_type": "memory_write", "risk_level": "medium", "summary": "写入偏好"})
    assert yellow["zone"] == "yellow"
    assert yellow["requires_confirmation"] is True

    red = classifier.classify({"proposal_type": "tool_plan", "risk_level": "low", "summary": "导出并分享隐私数据"})
    assert red["zone"] == "red"
    assert red["allowed_actions"] == ["suggest_only"]

    zones = {item["zone"] for item in classifier.list_zones()}
    assert zones == {"green", "yellow", "red"}

