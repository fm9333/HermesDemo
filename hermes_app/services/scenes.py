from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class SceneService:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        name: str,
        source: str = "user",
        context_signal: str = "manual",
        user_state: str = "unknown",
        opportunity: str = "recommendation",
        decision_policy: str = "confirm_before_interrupt",
        output_type: str = "recommendation",
        status: str = "active",
    ) -> dict:
        scene_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO scenes
                (id, name, source, context_signal, user_state, opportunity, decision_policy,
                 output_type, status, effect_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scene_id,
                name.strip() or "未命名场景",
                source,
                context_signal,
                user_state,
                opportunity,
                decision_policy,
                output_type,
                status,
                0.0,
                _now(),
            ),
        )
        return self.get(scene_id) or {}

    def list(self, status: str | None = None) -> list[dict]:
        if status:
            return self.db.query("SELECT * FROM scenes WHERE status = ? ORDER BY created_at DESC LIMIT 100", (status,))
        return self.db.query("SELECT * FROM scenes ORDER BY created_at DESC LIMIT 100")

    def get(self, scene_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM scenes WHERE id = ?", (scene_id,))

    def update(self, scene_id: str, **updates) -> dict:
        current = self.get(scene_id)
        if not current:
            raise KeyError(f"Scene not found: {scene_id}")
        allowed = {
            "name",
            "context_signal",
            "user_state",
            "opportunity",
            "decision_policy",
            "output_type",
            "status",
        }
        values = {key: value for key, value in updates.items() if key in allowed and value is not None}
        if values:
            assignments = ", ".join(f"{key} = ?" for key in values)
            self.db.execute(
                f"UPDATE scenes SET {assignments} WHERE id = ?",
                tuple(values.values()) + (scene_id,),
            )
        return self.get(scene_id) or {}

    def pause(self, scene_id: str) -> dict:
        return self.update(scene_id, status="paused")

    def run(self, scene_id: str) -> dict:
        scene = self.get(scene_id)
        if not scene:
            raise KeyError(f"Scene not found: {scene_id}")
        if scene["status"] != "active":
            output = {"type": "skipped", "reason": f"scene_status={scene['status']}"}
            status = "skipped"
        else:
            output = self._build_output(scene)
            status = "ok"
            self.db.execute(
                "UPDATE scenes SET effect_score = round(effect_score + ?, 3) WHERE id = ?",
                (0.1, scene_id),
            )

        run_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO scene_runs (id, scene_id, status, output_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, scene_id, status, json.dumps(output, ensure_ascii=False), _now()),
        )
        return {"run_id": run_id, "scene_id": scene_id, "status": status, "output": output}

    def list_runs(self, scene_id: str | None = None) -> list[dict]:
        if scene_id:
            rows = self.db.query(
                "SELECT * FROM scene_runs WHERE scene_id = ? ORDER BY created_at DESC LIMIT 100",
                (scene_id,),
            )
        else:
            rows = self.db.query("SELECT * FROM scene_runs ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["output"] = json.loads(row.pop("output_json"))
        return rows

    def record_feedback(
        self,
        scene_id: str,
        rating: str,
        reason: str = "",
        run_id: str | None = None,
        payload: dict | None = None,
    ) -> dict:
        if not self.get(scene_id):
            raise KeyError(f"Scene not found: {scene_id}")
        if run_id:
            run = self.db.query_one("SELECT * FROM scene_runs WHERE id = ?", (run_id,))
            if not run:
                raise KeyError(f"Scene run not found: {run_id}")
            if run["scene_id"] != scene_id:
                raise ValueError("Scene run does not belong to this scene.")

        normalized = (rating or "negative").strip().lower()
        if normalized not in {"positive", "helpful", "neutral", "negative", "misfire"}:
            raise ValueError("Unsupported scene feedback rating.")

        feedback_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO scene_feedback (id, scene_id, run_id, rating, reason, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                scene_id,
                run_id,
                normalized,
                (reason or "").strip(),
                json.dumps(payload or {}, ensure_ascii=False),
                _now(),
            ),
        )

        delta = self._feedback_delta(normalized)
        if delta:
            self.db.execute(
                "UPDATE scenes SET effect_score = round(max(effect_score + ?, 0), 3) WHERE id = ?",
                (delta, scene_id),
            )
        return self.get_feedback(feedback_id) or {}

    def list_feedback(self, scene_id: str | None = None) -> list[dict]:
        if scene_id:
            rows = self.db.query(
                "SELECT * FROM scene_feedback WHERE scene_id = ? ORDER BY created_at DESC LIMIT 100",
                (scene_id,),
            )
        else:
            rows = self.db.query("SELECT * FROM scene_feedback ORDER BY created_at DESC LIMIT 100")
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def get_feedback(self, feedback_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM scene_feedback WHERE id = ?", (feedback_id,))
        if row:
            row["payload"] = json.loads(row.pop("payload_json"))
        return row

    def _build_output(self, scene: dict) -> dict:
        return {
            "type": scene["output_type"],
            "title": scene["name"],
            "message": f"场景机会点：{scene['opportunity']}；策略：{scene['decision_policy']}",
            "requires_confirmation": scene["decision_policy"] != "silent",
        }

    def _feedback_delta(self, rating: str) -> float:
        if rating in {"positive", "helpful"}:
            return 0.2
        if rating == "misfire":
            return -0.3
        if rating == "negative":
            return -0.2
        return 0.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
