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

    def create_candidate(self, candidate: MemoryCandidate, source: str = "chat", reason: str = "") -> dict:
        now = datetime.now(timezone.utc).isoformat()
        candidate_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO memory_candidates
                (id, memory_type, key, value, sensitivity, status, source, reason, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                candidate.memory_type,
                candidate.key,
                candidate.value,
                candidate.sensitivity,
                "pending",
                source,
                reason or "Hermes 从用户输入中提取到一条可保存记忆。",
                candidate.confidence,
                now,
            ),
        )
        return self.get_candidate(candidate_id) or {}

    def list_candidates(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query(
                "SELECT * FROM memory_candidates WHERE status = ? ORDER BY created_at DESC LIMIT 80",
                (status,),
            )
        return self.db.query("SELECT * FROM memory_candidates ORDER BY created_at DESC LIMIT 80")

    def get_candidate(self, candidate_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM memory_candidates WHERE id = ?", (candidate_id,))

    def confirm_candidate(self, candidate_id: str) -> dict:
        row = self.get_candidate(candidate_id)
        if not row:
            raise KeyError(f"Memory candidate not found: {candidate_id}")
        if row["status"] == "confirmed":
            existing = self.db.query_one(
                """
                SELECT * FROM memory_items
                WHERE key = ? AND value = ? AND source = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (row["key"], row["value"], "memory_candidate"),
            )
            return existing or {}
        if row["status"] == "rejected":
            raise ValueError("Rejected memory candidate cannot be confirmed.")

        item = self.save(
            MemoryCandidate(
                memory_type=row["memory_type"],
                key=row["key"],
                value=row["value"],
                sensitivity=row["sensitivity"],
                confidence=row["confidence"],
            ),
            source="memory_candidate",
        )
        self.db.execute("UPDATE memory_candidates SET status = ? WHERE id = ?", ("confirmed", candidate_id))
        return item

    def reject_candidate(self, candidate_id: str) -> dict:
        row = self.get_candidate(candidate_id)
        if not row:
            raise KeyError(f"Memory candidate not found: {candidate_id}")
        if row["status"] == "pending":
            self.db.execute("UPDATE memory_candidates SET status = ? WHERE id = ?", ("rejected", candidate_id))
        return self.get_candidate(candidate_id) or {}

    def list(self) -> list[dict]:
        return self.db.query("SELECT * FROM memory_items ORDER BY created_at DESC LIMIT 80")

    def get(self, memory_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM memory_items WHERE id = ?", (memory_id,))

    def delete(self, memory_id: str) -> bool:
        cursor = self.db.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0
