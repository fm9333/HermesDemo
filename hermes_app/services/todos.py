from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class TodoService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, title: str, source: str = "manual", source_id: str | None = None) -> dict:
        todo_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO todo_items (id, title, source, source_id, status, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (todo_id, title.strip() or "未命名待办", source, source_id, "open", _now(), None),
        )
        return self.get(todo_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query(
                "SELECT * FROM todo_items WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        return self.db.query("SELECT * FROM todo_items ORDER BY created_at DESC LIMIT 100")

    def get(self, todo_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM todo_items WHERE id = ?", (todo_id,))

    def get_by_source_title(self, source: str, source_id: str | None, title: str) -> dict | None:
        return self.db.query_one(
            """
            SELECT * FROM todo_items
            WHERE source = ? AND (source_id = ? OR (source_id IS NULL AND ? IS NULL)) AND title = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (source, source_id, source_id, title),
        )

    def complete(self, todo_id: str) -> dict:
        if not self.get(todo_id):
            raise KeyError(f"Todo not found: {todo_id}")
        self.db.execute(
            "UPDATE todo_items SET status = ?, completed_at = ? WHERE id = ?",
            ("completed", _now(), todo_id),
        )
        return self.get(todo_id) or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
