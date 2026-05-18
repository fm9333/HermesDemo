from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class WardrobeService:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, category: str = "clothing", color: str = "unknown", source: str = "hermes") -> dict:
        item_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO wardrobe_items (id, name, category, color, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                name.strip() or "未命名衣物",
                category.strip() or "clothing",
                color.strip() or "unknown",
                source,
                "active",
                _now(),
            ),
        )
        return self.get(item_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query(
                "SELECT * FROM wardrobe_items WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        return self.db.query("SELECT * FROM wardrobe_items ORDER BY created_at DESC LIMIT 100")

    def get(self, item_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM wardrobe_items WHERE id = ?", (item_id,))

    def update(
        self,
        item_id: str,
        name: str | None = None,
        category: str | None = None,
        color: str | None = None,
    ) -> dict:
        current = self.get(item_id)
        if not current:
            raise KeyError(f"Wardrobe item not found: {item_id}")
        self.db.execute(
            "UPDATE wardrobe_items SET name = ?, category = ?, color = ? WHERE id = ?",
            (
                name if name is not None else current["name"],
                category if category is not None else current["category"],
                color if color is not None else current["color"],
                item_id,
            ),
        )
        return self.get(item_id) or {}

    def set_status(self, item_id: str, status: str) -> dict:
        if status not in {"active", "archived", "deleted"}:
            raise ValueError(f"Unsupported wardrobe status: {status}")
        if not self.get(item_id):
            raise KeyError(f"Wardrobe item not found: {item_id}")
        self.db.execute("UPDATE wardrobe_items SET status = ? WHERE id = ?", (status, item_id))
        return self.get(item_id) or {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

