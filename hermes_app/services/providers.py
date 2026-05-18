from __future__ import annotations

import json
from datetime import datetime, timezone

from hermes_app.core.database import Database


class ProviderRegistry:
    defaults = [
        {
            "provider_id": "weather.open_meteo",
            "name": "Open-Meteo Weather",
            "provider_type": "weather",
            "status": "connected",
            "permissions": ["weather.lookup", "weather.cache"],
            "config": {"auth": "none"},
        },
        {
            "provider_id": "calendar.local",
            "name": "Local Calendar Placeholder",
            "provider_type": "calendar",
            "status": "disconnected",
            "permissions": ["calendar.read"],
            "config": {"auth": "pending"},
        },
        {
            "provider_id": "email.local",
            "name": "Local Email Placeholder",
            "provider_type": "email",
            "status": "disconnected",
            "permissions": ["email.read_metadata"],
            "config": {"auth": "pending"},
        },
        {
            "provider_id": "drive.local",
            "name": "Local Drive Placeholder",
            "provider_type": "drive",
            "status": "disconnected",
            "permissions": ["drive.read_metadata"],
            "config": {"auth": "pending"},
        },
    ]

    def __init__(self, db: Database):
        self.db = db

    def list(self) -> list[dict]:
        self.ensure_defaults()
        rows = self.db.query("SELECT * FROM providers ORDER BY provider_type, provider_id")
        return [self._deserialize(row) for row in rows]

    def get(self, provider_id: str) -> dict | None:
        self.ensure_defaults()
        row = self.db.query_one("SELECT * FROM providers WHERE provider_id = ?", (provider_id,))
        return self._deserialize(row) if row else None

    def connect(self, provider_id: str, config: dict | None = None) -> dict:
        provider = self.get(provider_id)
        if not provider:
            raise KeyError(f"Provider not found: {provider_id}")
        merged_config = {**provider["config"], **(config or {})}
        self._update(provider_id, "connected", merged_config)
        return self.get(provider_id) or {}

    def disconnect(self, provider_id: str) -> dict:
        if not self.get(provider_id):
            raise KeyError(f"Provider not found: {provider_id}")
        self._update(provider_id, "disconnected", None)
        return self.get(provider_id) or {}

    def ensure_defaults(self) -> None:
        for provider in self.defaults:
            if not self.db.query_one("SELECT provider_id FROM providers WHERE provider_id = ?", (provider["provider_id"],)):
                self.db.execute(
                    """
                    INSERT INTO providers
                        (provider_id, name, provider_type, status, permissions_json, config_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        provider["provider_id"],
                        provider["name"],
                        provider["provider_type"],
                        provider["status"],
                        json.dumps(provider["permissions"], ensure_ascii=False),
                        json.dumps(provider["config"], ensure_ascii=False),
                        _now(),
                    ),
                )

    def _update(self, provider_id: str, status: str, config: dict | None) -> None:
        if config is None:
            self.db.execute(
                "UPDATE providers SET status = ?, updated_at = ? WHERE provider_id = ?",
                (status, _now(), provider_id),
            )
            return
        self.db.execute(
            "UPDATE providers SET status = ?, config_json = ?, updated_at = ? WHERE provider_id = ?",
            (status, json.dumps(config, ensure_ascii=False), _now(), provider_id),
        )

    def _deserialize(self, row: dict) -> dict:
        row["permissions"] = json.loads(row.pop("permissions_json"))
        row["config"] = json.loads(row.pop("config_json"))
        return row


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
