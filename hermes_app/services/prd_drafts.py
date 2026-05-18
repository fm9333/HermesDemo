from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class PrdDraftService:
    def __init__(self, db: Database):
        self.db = db

    def create_from_idea(self, idea: dict) -> dict:
        existing = self.get_by_idea(idea["id"])
        if existing:
            return existing

        draft_id = str(uuid4())
        title = f"PRD 草案：{idea['title']}"
        body = self._compose_body(idea)
        self.db.execute(
            """
            INSERT INTO prd_drafts (id, idea_id, title, body, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (draft_id, idea["id"], title, body, "draft", _now()),
        )
        return self.get(draft_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query(
                "SELECT * FROM prd_drafts WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        return self.db.query("SELECT * FROM prd_drafts ORDER BY created_at DESC LIMIT 100")

    def get(self, draft_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM prd_drafts WHERE id = ?", (draft_id,))

    def get_by_idea(self, idea_id: str) -> dict | None:
        return self.db.query_one(
            "SELECT * FROM prd_drafts WHERE idea_id = ? ORDER BY created_at DESC LIMIT 1",
            (idea_id,),
        )

    def _compose_body(self, idea: dict) -> str:
        risks = "\n".join(f"- {item}" for item in idea.get("risks", [])) or "- 待补充"
        next_steps = "\n".join(f"- {item}" for item in idea.get("next_steps", [])) or "- 待补充"
        return "\n".join(
            [
                f"# {idea['title']}",
                "",
                "## 背景",
                idea.get("pain_point") or "待补充",
                "",
                "## 目标用户",
                idea.get("target_user") or "待补充",
                "",
                "## 核心假设",
                idea.get("core_assumption") or "待补充",
                "",
                "## MVP 范围",
                idea.get("mvp_plan") or "待补充",
                "",
                "## 反方挑战",
                idea.get("counter_challenge") or "待补充",
                "",
                "## 风险",
                risks,
                "",
                "## 下一步",
                next_steps,
            ]
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
