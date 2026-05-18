from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.skills import SkillRegistry


class SkillRuntime:
    def __init__(self, db: Database, registry: SkillRegistry):
        self.db = db
        self.registry = registry

    def run(self, skill_id: str, text: str) -> dict:
        output = self.registry.run(skill_id, text)
        status = "ok" if output.get("title") != "Skill 未注册" else "not_found"
        run_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO skill_runs (id, skill_id, input_text, output_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                skill_id,
                text,
                json.dumps(output, ensure_ascii=False),
                status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return {"run_id": run_id, "skill_id": skill_id, "status": status, "output": output}

    def list_runs(self, skill_id: str | None = None) -> list[dict]:
        if skill_id:
            rows = self.db.query(
                "SELECT * FROM skill_runs WHERE skill_id = ? ORDER BY created_at DESC LIMIT 100",
                (skill_id,),
            )
        else:
            rows = self.db.query("SELECT * FROM skill_runs ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["output"] = json.loads(row.pop("output_json"))
        return rows

