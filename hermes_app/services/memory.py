from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.schemas import MemoryCandidate


class MemoryService:
    def __init__(self, db: Database):
        self.db = db

    def extract_candidate(self, message: str) -> MemoryCandidate:
        value = message.strip()
        for marker in ("记住", "以后", "默认"):
            if marker in value:
                value = value.split(marker, 1)[-1].strip(" ，。:：")
                break

        sensitivity = "sensitive" if any(word in message for word in ("健康", "财务", "身份证", "位置")) else "normal"
        memory_type = "preference" if any(word in message for word in ("喜欢", "不喜欢", "默认", "以后")) else "profile"
        key = "user_preference" if memory_type == "preference" else "user_profile"

        return MemoryCandidate(
            memory_type=memory_type,
            key=key,
            value=value or message.strip(),
            sensitivity=sensitivity,
            confidence=0.76 if sensitivity == "normal" else 0.62,
        )

    def save(self, candidate: MemoryCandidate, source: str = "chat", status: str = "active") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        memory_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO memory_items
                (id, memory_type, key, value, sensitivity, status, source, confidence, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                candidate.memory_type,
                candidate.key,
                candidate.value,
                candidate.sensitivity,
                status,
                source,
                candidate.confidence,
                now,
                None,
            ),
        )
        return self.get(memory_id) or {}

    def list(self) -> list[dict]:
        return self.db.query("SELECT * FROM memory_items ORDER BY created_at DESC LIMIT 80")

    def get(self, memory_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM memory_items WHERE id = ?", (memory_id,))

    def delete(self, memory_id: str) -> bool:
        cursor = self.db.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0

