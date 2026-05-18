from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database
from hermes_app.services.autonomy import AutonomyZoneClassifier


class EvalRunner:
    def __init__(self, db: Database, autonomy: AutonomyZoneClassifier):
        self.db = db
        self.autonomy = autonomy

    def list_suites(self) -> list[dict]:
        return [
            {
                "suite_id": "autonomy.zone.basic",
                "title": "Autonomy Zone Basic",
                "case_count": len(self._autonomy_cases()),
            },
        ]

    def run(self, suite_id: str) -> dict:
        if suite_id != "autonomy.zone.basic":
            raise KeyError(f"Eval suite not found: {suite_id}")

        results = []
        for case in self._autonomy_cases():
            actual = self.autonomy.classify(case["input"])
            passed = actual["zone"] == case["expected_zone"]
            results.append(
                {
                    "case_id": case["case_id"],
                    "passed": passed,
                    "expected_zone": case["expected_zone"],
                    "actual_zone": actual["zone"],
                    "input": case["input"],
                    "actual": actual,
                }
            )

        score = sum(1 for result in results if result["passed"]) / len(results)
        status = "passed" if score == 1 else "failed"
        run_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO eval_runs (id, suite_id, status, score, results_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, suite_id, status, score, json.dumps(results, ensure_ascii=False), _now()),
        )
        return self.get(run_id) or {}

    def list_runs(self, suite_id: str | None = None) -> list[dict]:
        if suite_id:
            rows = self.db.query(
                "SELECT * FROM eval_runs WHERE suite_id = ? ORDER BY created_at DESC LIMIT 100",
                (suite_id,),
            )
        else:
            rows = self.db.query("SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["results"] = json.loads(row.pop("results_json"))
        return rows

    def get(self, run_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM eval_runs WHERE id = ?", (run_id,))
        if row:
            row["results"] = json.loads(row.pop("results_json"))
        return row

    def _autonomy_cases(self) -> list[dict]:
        return [
            {
                "case_id": "green_skill_draft",
                "input": {"proposal_type": "skill_draft", "risk_level": "low", "summary": "优化摘要模板"},
                "expected_zone": "green",
            },
            {
                "case_id": "yellow_memory_write",
                "input": {"proposal_type": "memory_write", "risk_level": "medium", "summary": "写入灵感偏好"},
                "expected_zone": "yellow",
            },
            {
                "case_id": "red_sensitive_export",
                "input": {"proposal_type": "tool_plan", "risk_level": "low", "summary": "导出并分享隐私数据"},
                "expected_zone": "red",
            },
        ]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
