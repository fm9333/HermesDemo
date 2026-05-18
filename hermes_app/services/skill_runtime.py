from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.skills import SkillRegistry

if TYPE_CHECKING:
    from hermes_app.services.llm_client import LLMClient


class SkillRuntime:
    llm_prompt_map = {
        "document.summarize": "skill.document.summarize",
        "work.todo_extract": "skill.work.todo_extract",
        "content.list_generate": "skill.content.list_generate",
    }

    def __init__(self, db: Database, registry: SkillRegistry, llm_client: "LLMClient | None" = None):
        self.db = db
        self.registry = registry
        self.llm_client = llm_client

    def run(self, skill_id: str, text: str) -> dict:
        output = self._run_with_llm(skill_id, text) or self.registry.run(skill_id, text)
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

    def _run_with_llm(self, skill_id: str, text: str) -> dict | None:
        if not self.llm_client or skill_id not in self.llm_prompt_map:
            return None
        result = self.llm_client.chat(
            text,
            prompt_id=self.llm_prompt_map[skill_id],
            context={"skill_id": skill_id, "output": "Return the requested JSON or structured content only."},
        )
        if result.get("status") != "ok" or not result.get("reply"):
            return None
        reply = result["reply"]
        try:
            parsed = json.loads(reply)
            if isinstance(parsed, dict):
                parsed.setdefault("title", f"{skill_id} LLM 输出")
                parsed["_llm"] = {
                    "provider_id": result.get("provider_id"),
                    "model": result.get("model"),
                    "call_id": result.get("call_id"),
                }
                return parsed
        except json.JSONDecodeError:
            pass
        return {
            "title": f"{skill_id} LLM 输出",
            "content": reply,
            "_llm": {
                "provider_id": result.get("provider_id"),
                "model": result.get("model"),
                "call_id": result.get("call_id"),
            },
        }
