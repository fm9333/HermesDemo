from hermes_app.core.database import Database
from hermes_app.services.todos import TodoService


def test_todo_service_create_list_complete(tmp_path):
    db = Database(tmp_path / "todos.db")
    db.init()
    service = TodoService(db)

    todo = service.create("验证灵感卡片", source="idea", source_id="idea-1")
    assert todo["status"] == "open"
    assert todo["source"] == "idea"

    listed = service.list(status="open")
    assert len(listed) == 1
    assert listed[0]["id"] == todo["id"]
    assert service.get_by_source_title("idea", "idea-1", "验证灵感卡片")["id"] == todo["id"]

    completed = service.complete(todo["id"])
    assert completed["status"] == "completed"
    assert completed["completed_at"]
