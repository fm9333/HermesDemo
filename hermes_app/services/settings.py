from __future__ import annotations

import json
from datetime import datetime, timezone

from hermes_app.core.database import Database


class SettingsService:
    defaults = {
        "autonomy_enabled": True,
        "yellow_zone_requires_confirmation": True,
        "red_zone_policy": "block",
        "eval_required_for_drafts": True,
        "notifications_enabled": True,
    }

    def __init__(self, db: Database):
        self.db = db

    def list(self) -> list[dict]:
        self.ensure_defaults()
        rows = self.db.query("SELECT * FROM app_settings ORDER BY key")
        return [self._deserialize(row) for row in rows]

    def get(self, key: str) -> dict | None:
        self.ensure_defaults()
        row = self.db.query_one("SELECT * FROM app_settings WHERE key = ?", (key,))
        return self._deserialize(row) if row else None

    def update(self, key: str, value) -> dict:
        if key not in self.defaults:
            raise KeyError(f"Unknown setting: {key}")
        self._validate(key, value)
        self.db.execute(
            """
            INSERT INTO app_settings (key, value_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = excluded.updated_at
            """,
            (key, json.dumps(value, ensure_ascii=False), _now()),
        )
        return self.get(key) or {}

    def ensure_defaults(self) -> None:
        for key, value in self.defaults.items():
            if not self.db.query_one("SELECT key FROM app_settings WHERE key = ?", (key,)):
                self.db.execute(
                    "INSERT INTO app_settings (key, value_json, updated_at) VALUES (?, ?, ?)",
                    (key, json.dumps(value, ensure_ascii=False), _now()),
                )

    def _validate(self, key: str, value) -> None:
        default = self.defaults[key]
        if isinstance(default, bool) and not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean.")
        if key == "red_zone_policy" and value not in {"block", "confirm_only"}:
            raise ValueError("red_zone_policy must be block or confirm_only.")

    def _deserialize(self, row: dict) -> dict:
        return {
            "key": row["key"],
            "value": json.loads(row["value_json"]),
            "updated_at": row["updated_at"],
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
