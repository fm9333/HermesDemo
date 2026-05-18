from hermes_app.services.task_decomposer import TaskDecomposer


def test_task_decomposer_marks_reminder_confirmation_gate():
    plan = TaskDecomposer().decompose("明天提醒我带伞", "create_reminder", "medium")

    assert plan.intent == "create_reminder"
    assert plan.risk_level == "medium"
    assert len(plan.steps) == 3
    assert plan.steps[-1].target == "action_gate"
    assert plan.steps[-1].requires_confirmation is True


def test_task_decomposer_weather_plan_is_low_risk():
    plan = TaskDecomposer().decompose("北京天气", "weather_query", "low")

    assert [step.target for step in plan.steps] == ["weather.location", "weather.lookup", "weather_cache"]
    assert all(step.risk_level == "low" for step in plan.steps)
