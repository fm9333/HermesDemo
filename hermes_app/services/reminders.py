from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class ReminderService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, title: str, due_at_text: str, source: str = "hermes") -> dict:
        reminder_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO reminders (id, title, due_at_text, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reminder_id,
                title.strip() or "未命名提醒",
                due_at_text.strip() or "待补充时间",
                source,
                "active",
                _now(),
            ),
        )
        return self.get(reminder_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query(
                "SELECT * FROM reminders WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        return self.db.query("SELECT * FROM reminders ORDER BY created_at DESC LIMIT 100")

    def get(self, reminder_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM reminders WHERE id = ?", (reminder_id,))

    def update(self, reminder_id: str, title: str | None = None, due_at_text: str | None = None) -> dict:
        current = self.get(reminder_id)
        if not current:
            raise KeyError(f"Reminder not found: {reminder_id}")
        self.db.execute(
            "UPDATE reminders SET title = ?, due_at_text = ? WHERE id = ?",
            (
                title if title is not None else current["title"],
                due_at_text if due_at_text is not None else current["due_at_text"],
                reminder_id,
            ),
        )
        return self.get(reminder_id) or {}

    def set_status(self, reminder_id: str, status: str) -> dict:
        if status not in {"active", "completed", "paused", "deleted"}:
            raise ValueError(f"Unsupported reminder status: {status}")
        if not self.get(reminder_id):
            raise KeyError(f"Reminder not found: {reminder_id}")
        self.db.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
        return self.get(reminder_id) or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

