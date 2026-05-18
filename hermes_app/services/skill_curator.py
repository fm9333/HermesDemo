from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class SkillCuratorService:
    def __init__(self, db: Database):
        self.db = db

    def run(self) -> dict:
        suggestions = self.suggest()
        status = "attention_needed" if suggestions else "ok"
        summary = self._summary(suggestions)
        run_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO skill_curator_runs (id, status, suggestions_json, summary, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, status, json.dumps(suggestions, ensure_ascii=False), summary, _now()),
        )
        return {
            "id": run_id,
            "status": status,
            "suggestions": suggestions,
            "summary": summary,
        }

    def suggest(self) -> list[dict]:
        skills = self._list_skills()
        patches = self._list_patches()
        suggestions: list[dict] = []
        suggestions.extend(self._duplicate_suggestions(skills))
        suggestions.extend(self._draft_suggestions(skills))
        suggestions.extend(self._failed_patch_suggestions(patches))
        suggestions.extend(self._churn_suggestions(skills))
        suggestions.extend(self._source_suggestions(skills))
        return sorted(suggestions, key=lambda item: (item["priority"], item["type"], item["title"]))

    def list_runs(self, limit: int = 50) -> list[dict]:
        rows = self.db.query("SELECT * FROM skill_curator_runs ORDER BY created_at DESC LIMIT ?", (limit,))
        for row in rows:
            row["suggestions"] = json.loads(row.pop("suggestions_json"))
        return rows

    def _duplicate_suggestions(self, skills: list[dict]) -> list[dict]:
        groups = defaultdict(list)
        for skill in skills:
            if skill["status"] != "archived":
                groups[_normalize(skill["title"])].append(skill)
        suggestions = []
        for title_key, group in groups.items():
            if title_key and len(group) > 1:
                suggestions.append(
                    {
                        "type": "duplicate_skill",
                        "priority": 20,
                        "severity": "medium",
                        "title": f"发现重复 Personal Skill：{group[0]['title']}",
                        "action": "review_merge_or_archive",
                        "skill_ids": [item["id"] for item in group],
                        "payload": {"count": len(group), "title_key": title_key},
                    }
                )
        return suggestions

    def _draft_suggestions(self, skills: list[dict]) -> list[dict]:
        suggestions = []
        for skill in skills:
            if skill["status"] == "draft" and skill["eval_status"] != "passed":
                suggestions.append(
                    {
                        "type": "unevaluated_draft",
                        "priority": 30,
                        "severity": "medium",
                        "title": f"草案尚未通过评测：{skill['title']}",
                        "action": "run_eval_before_activation",
                        "skill_ids": [skill["id"]],
                        "payload": {"eval_status": skill["eval_status"]},
                    }
                )
        return suggestions

    def _failed_patch_suggestions(self, patches: list[dict]) -> list[dict]:
        suggestions = []
        for patch in patches:
            if patch["status"] == "failed" or patch["eval_status"] == "failed":
                suggestions.append(
                    {
                        "type": "failed_patch",
                        "priority": 35,
                        "severity": "medium",
                        "title": f"技能补丁评测失败：{patch['reason'][:40]}",
                        "action": "revise_or_drop_patch",
                        "skill_ids": [patch["personal_skill_id"]],
                        "patch_id": patch["id"],
                        "payload": {"eval_report": patch["eval_report"]},
                    }
                )
        return suggestions

    def _churn_suggestions(self, skills: list[dict]) -> list[dict]:
        suggestions = []
        for skill in skills:
            if skill["status"] == "active" and skill["version"] >= 4:
                suggestions.append(
                    {
                        "type": "high_churn_skill",
                        "priority": 50,
                        "severity": "low",
                        "title": f"技能版本变更较频繁：{skill['title']}",
                        "action": "review_stability",
                        "skill_ids": [skill["id"]],
                        "payload": {"version": skill["version"]},
                    }
                )
        return suggestions

    def _source_suggestions(self, skills: list[dict]) -> list[dict]:
        suggestions = []
        for skill in skills:
            if skill["status"] == "active" and not skill.get("source_run_id"):
                suggestions.append(
                    {
                        "type": "weak_source_trace",
                        "priority": 60,
                        "severity": "low",
                        "title": f"技能缺少来源运行记录：{skill['title']}",
                        "action": "attach_source_or_review",
                        "skill_ids": [skill["id"]],
                        "payload": {"skill_id": skill["skill_id"]},
                    }
                )
        return suggestions

    def _list_skills(self) -> list[dict]:
        rows = self.db.query("SELECT * FROM personal_skills ORDER BY created_at DESC")
        for row in rows:
            row["output_contract"] = json.loads(row.pop("output_contract_json"))
            row["eval_report"] = json.loads(row.pop("eval_report_json"))
        return rows

    def _list_patches(self) -> list[dict]:
        rows = self.db.query("SELECT * FROM personal_skill_patches ORDER BY created_at DESC")
        for row in rows:
            row["proposed_output_contract"] = json.loads(row.pop("proposed_output_contract_json"))
            row["eval_report"] = json.loads(row.pop("eval_report_json"))
        return rows

    def _summary(self, suggestions: list[dict]) -> str:
        if not suggestions:
            return "Skill Curator 未发现需要处理的问题。"
        by_type = defaultdict(int)
        for suggestion in suggestions:
            by_type[suggestion["type"]] += 1
        parts = [f"{key}: {count}" for key, count in sorted(by_type.items())]
        return "；".join(parts)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    return "".join(char.lower() for char in value.strip() if not char.isspace())
