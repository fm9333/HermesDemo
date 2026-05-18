from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class PersonalSkillService:
    valid_statuses = {"draft", "active", "archived"}
    valid_zones = {"green", "yellow", "red"}

    def __init__(self, db: Database):
        self.db = db

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            rows = self.db.query(
                "SELECT * FROM personal_skills WHERE status = ? ORDER BY created_at DESC LIMIT 100",
                (status,),
            )
        else:
            rows = self.db.query("SELECT * FROM personal_skills ORDER BY created_at DESC LIMIT 100")
        return [self._deserialize(row) for row in rows]

    def get(self, skill_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM personal_skills WHERE id = ?", (skill_id,))
        return self._deserialize(row) if row else None

    def create_draft(
        self,
        title: str,
        description: str,
        prompt_template: str,
        output_contract: dict,
        autonomy_zone: str = "green",
        source_run_id: str | None = None,
    ) -> dict:
        title = title.strip()
        prompt_template = prompt_template.strip()
        if not title:
            raise ValueError("title is required.")
        if not prompt_template:
            raise ValueError("prompt_template is required.")
        if autonomy_zone not in self.valid_zones:
            raise ValueError("autonomy_zone is invalid.")
        skill_id = str(uuid4())
        now = _now()
        public_skill_id = f"personal.{_slug(title)}.{skill_id[:8]}"
        eval_report = {
            "status": "not_run",
            "checks": [],
            "message": "Draft created. Run evaluation before activation.",
        }
        self.db.execute(
            """
            INSERT INTO personal_skills
                (id, skill_id, title, description, autonomy_zone, status, source_run_id,
                 prompt_template, output_contract_json, eval_status, eval_report_json,
                 version, created_at, updated_at, activated_at, archived_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill_id,
                public_skill_id,
                title,
                description.strip(),
                autonomy_zone,
                "draft",
                source_run_id,
                prompt_template,
                json.dumps(output_contract or {}, ensure_ascii=False),
                "not_run",
                json.dumps(eval_report, ensure_ascii=False),
                1,
                now,
                now,
                None,
                None,
            ),
        )
        self._record_version(skill_id, 1, "draft", prompt_template, output_contract or {}, eval_report)
        return self.get(skill_id) or {}

    def create_from_skill_run(self, run_id: str, title: str | None = None) -> dict:
        run = self.db.query_one("SELECT * FROM skill_runs WHERE id = ?", (run_id,))
        if not run:
            raise KeyError(f"Skill run not found: {run_id}")
        output = json.loads(run["output_json"])
        generated_title = title or f"{run['skill_id']} 个人技能草案"
        prompt = (
            "复用这次 Skill 输出中的成功结构，生成稳定、可评测、不可越权的 Personal Skill。\n\n"
            f"来源 Skill: {run['skill_id']}\n"
            f"输入样例: {run['input_text'][:800]}\n"
            f"输出样例: {json.dumps(output, ensure_ascii=False)[:1200]}"
        )
        contract = {
            "source_skill_id": run["skill_id"],
            "allowed_inputs": ["text"],
            "allowed_outputs": list(output.keys()) if isinstance(output, dict) else ["content"],
            "requires_eval_before_activation": True,
        }
        return self.create_draft(
            title=generated_title,
            description="由历史 Skill Run 沉淀的 Personal Skill 草案。",
            prompt_template=prompt,
            output_contract=contract,
            autonomy_zone="green",
            source_run_id=run_id,
        )

    def evaluate(self, skill_id: str) -> dict:
        skill = self.get(skill_id)
        if not skill:
            raise KeyError(f"Personal skill not found: {skill_id}")
        checks = [
            {
                "id": "prompt_present",
                "passed": bool(skill["prompt_template"].strip()),
                "message": "Prompt template is present.",
            },
            {
                "id": "output_contract_present",
                "passed": bool(skill["output_contract"]),
                "message": "Output contract is declared.",
            },
            {
                "id": "zone_not_red",
                "passed": skill["autonomy_zone"] != "red",
                "message": "Red Zone skills cannot be activated automatically.",
            },
            {
                "id": "source_traceable",
                "passed": bool(skill.get("source_run_id") or skill["description"]),
                "message": "Draft has a traceable source or rationale.",
            },
        ]
        passed = all(check["passed"] for check in checks)
        report = {"status": "passed" if passed else "failed", "checks": checks}
        self.db.execute(
            """
            UPDATE personal_skills
            SET eval_status = ?, eval_report_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (report["status"], json.dumps(report, ensure_ascii=False), _now(), skill_id),
        )
        return self.get(skill_id) or {}

    def activate(self, skill_id: str) -> dict:
        skill = self.get(skill_id)
        if not skill:
            raise KeyError(f"Personal skill not found: {skill_id}")
        if skill["eval_status"] != "passed":
            raise ValueError("Personal skill must pass evaluation before activation.")
        if skill["autonomy_zone"] == "red":
            raise ValueError("Red Zone personal skills cannot be activated.")
        now = _now()
        self.db.execute(
            """
            UPDATE personal_skills
            SET status = 'active', updated_at = ?, activated_at = ?
            WHERE id = ?
            """,
            (now, now, skill_id),
        )
        return self.get(skill_id) or {}

    def archive(self, skill_id: str) -> dict:
        if not self.get(skill_id):
            raise KeyError(f"Personal skill not found: {skill_id}")
        now = _now()
        self.db.execute(
            """
            UPDATE personal_skills
            SET status = 'archived', updated_at = ?, archived_at = ?
            WHERE id = ?
            """,
            (now, now, skill_id),
        )
        return self.get(skill_id) or {}

    def versions(self, skill_id: str) -> list[dict]:
        rows = self.db.query(
            """
            SELECT * FROM personal_skill_versions
            WHERE personal_skill_id = ?
            ORDER BY version DESC, created_at DESC
            """,
            (skill_id,),
        )
        for row in rows:
            row["output_contract"] = json.loads(row.pop("output_contract_json"))
            row["eval_report"] = json.loads(row.pop("eval_report_json"))
        return rows

    def _record_version(
        self,
        personal_skill_id: str,
        version: int,
        status: str,
        prompt_template: str,
        output_contract: dict,
        eval_report: dict,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO personal_skill_versions
                (id, personal_skill_id, version, status, prompt_template,
                 output_contract_json, eval_report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                personal_skill_id,
                version,
                status,
                prompt_template,
                json.dumps(output_contract, ensure_ascii=False),
                json.dumps(eval_report, ensure_ascii=False),
                _now(),
            ),
        )

    def _deserialize(self, row: dict) -> dict:
        row["output_contract"] = json.loads(row.pop("output_contract_json"))
        row["eval_report"] = json.loads(row.pop("eval_report_json"))
        return row


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isascii() and (char.isalnum() or char == "-"):
            allowed.append(char)
        elif char.isspace() or char in "_./":
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    return slug or "skill"
