from hermes_app.services.inspiration import InspirationService


def test_inspiration_service_generates_structured_challenge_card():
    service = InspirationService()

    card = service.generate_card("帮我反方挑战 桌面智能体灵感工作室")

    assert card["mode"] == "challenge"
    assert card["direction"] == "桌面智能体工作室"
    assert card["target_user"]
    assert card["pain_point"]
    assert card["core_assumption"]
    assert card["counter_challenge"]
    assert card["mvp_plan"]
    assert card["risks"]
    assert card["next_steps"]
    assert card["score"] > 0
    assert "方向：" in card["body"]

