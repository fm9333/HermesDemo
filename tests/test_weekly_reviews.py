from hermes_app.core.database import Database
from hermes_app.services.weekly_reviews import WeeklyReviewService


def test_weekly_review_generates_from_recent_ideas(tmp_path):
    db = Database(tmp_path / "weekly_reviews.db")
    db.init()
    db.execute(
        """
        INSERT INTO idea_cards
            (id, title, body, tags_json, direction, score, next_steps_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "idea-1",
            "Desk agent studio",
            "Body",
            '["inspiration", "idea-card"]',
            "desktop agent",
            0.81,
            '["Validate review flow"]',
            "2026-05-18T00:00:00+00:00",
        ),
    )
    service = WeeklyReviewService(db)

    review = service.generate()

    assert review["title"].startswith("\u6bcf\u5468\u7075\u611f\u590d\u76d8")
    assert review["summary"]
    assert review["highlights"][0]["title"] == "Desk agent studio"
    assert review["highlights"][0]["score"] == 0.81
    assert review["next_actions"] == ["Validate review flow"]
    assert service.list()[0]["id"] == review["id"]


def test_weekly_review_has_fallback_action_without_ideas(tmp_path):
    db = Database(tmp_path / "weekly_reviews_empty.db")
    db.init()
    service = WeeklyReviewService(db)

    review = service.generate()

    assert review["highlights"] == []
    assert review["next_actions"] == ["\u8865\u5145\u672c\u5468\u503c\u5f97\u63a8\u8fdb\u7684 Idea Card"]
