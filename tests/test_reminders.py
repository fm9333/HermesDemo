from hermes_app.core.database import Database
from hermes_app.services.reminders import ReminderService


def test_reminder_service_crud_status_flow(tmp_path):
    db = Database(tmp_path / "reminders.db")
    db.init()
    service = ReminderService(db)

    reminder = service.create("带伞", "明天早上")
    assert reminder["status"] == "active"

    updated = service.update(reminder["id"], title="带伞和雨衣")
    assert updated["title"] == "带伞和雨衣"

    completed = service.set_status(reminder["id"], "completed")
    assert completed["status"] == "completed"

    deleted = service.set_status(reminder["id"], "deleted")
    assert deleted["status"] == "deleted"

