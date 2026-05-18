from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from uuid import uuid4

from hermes_app.core.database import Database


class LocalSecretCodec:
    def __init__(self, db: Database):
        source = os.getenv("HERMES_SECRET_KEY") or f"hermes-local-v1|{db.path}|{platform.node()}"
        self._key = hashlib.sha256(source.encode("utf-8")).digest()

    def encode(self, value: str) -> str:
        if not value:
            return ""
        data = value.encode("utf-8")
        encoded = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(data))
        return "v1." + base64.urlsafe_b64encode(encoded).decode("ascii")

    def decode(self, value: str) -> str:
        if not value:
            return ""
        if not value.startswith("v1."):
            return ""
        try:
            data = base64.urlsafe_b64decode(value[3:].encode("ascii"))
        except ValueError:
            return ""
        decoded = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(data))
        try:
            return decoded.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    def preview(self, value: str) -> str:
        secret = self.decode(value)
        if not secret:
            return ""
        if len(secret) <= 8:
            return "*" * len(secret)
        return f"{secret[:4]}...{secret[-4:]}"


class LLMProviderService:
    provider_types = {"openai_compatible", "openai", "local_openai_compatible"}
    protocols = {"chat_completions"}
    statuses = {"connected", "disabled"}

    def __init__(self, db: Database):
        self.db = db
        self.codec = LocalSecretCodec(db)

    def list(self) -> list[dict]:
        rows = self.db.query(
            """
            SELECT * FROM llm_providers
            ORDER BY is_default DESC, updated_at DESC, provider_id
            """
        )
        return [self._deserialize(row) for row in rows]

    def list_calls(self, limit: int = 80) -> list[dict]:
        rows = self.db.query("SELECT * FROM llm_calls ORDER BY created_at DESC LIMIT ?", (limit,))
        for row in rows:
            row["request"] = json.loads(row.pop("request_json"))
            row["response"] = json.loads(row.pop("response_json"))
        return rows

    def get(self, provider_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM llm_providers WHERE provider_id = ?", (provider_id,))
        return self._deserialize(row) if row else None

    def get_runtime(self, provider_id: str | None = None) -> dict | None:
        if provider_id:
            row = self.db.query_one("SELECT * FROM llm_providers WHERE provider_id = ?", (provider_id,))
        else:
            row = self.db.query_one(
                """
                SELECT * FROM llm_providers
                WHERE is_default = 1 AND status = 'connected'
                ORDER BY updated_at DESC LIMIT 1
                """
            )
        if not row or row["status"] != "connected":
            return None
        provider = dict(row)
        provider["api_key"] = self.codec.decode(provider.pop("api_key_secret", ""))
        provider["is_default"] = bool(provider["is_default"])
        provider["allow_file_context"] = bool(provider["allow_file_context"])
        return provider

    def create(self, payload: dict) -> dict:
        provider_id = self._clean_id(payload.get("provider_id") or f"llm.{uuid4()}")
        if self.get(provider_id):
            raise ValueError(f"Provider already exists: {provider_id}")
        values = self._normalize_payload(payload, partial=False)
        is_default = bool(payload.get("is_default")) or not self._has_default()
        if is_default:
            self._clear_default()
        now = _now()
        self.db.execute(
            """
            INSERT INTO llm_providers
                (provider_id, name, provider_type, protocol, base_url, endpoint_path,
                 api_key_secret, model, temperature, timeout_seconds, max_output_tokens,
                 status, is_default, allow_file_context, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider_id,
                values["name"],
                values["provider_type"],
                values["protocol"],
                values["base_url"],
                values["endpoint_path"],
                self.codec.encode(values.get("api_key", "")),
                values["model"],
                values["temperature"],
                values["timeout_seconds"],
                values["max_output_tokens"],
                values["status"],
                int(is_default),
                int(values["allow_file_context"]),
                now,
                now,
            ),
        )
        return self.get(provider_id) or {}

    def update(self, provider_id: str, payload: dict) -> dict:
        existing = self.db.query_one("SELECT * FROM llm_providers WHERE provider_id = ?", (provider_id,))
        if not existing:
            raise KeyError(f"Provider not found: {provider_id}")
        values = {**dict(existing), **self._normalize_payload(payload, partial=True)}
        if "api_key" in payload:
            values["api_key_secret"] = self.codec.encode(payload.get("api_key") or "")
        if payload.get("is_default") is True:
            self._clear_default()
            values["is_default"] = 1
        self.db.execute(
            """
            UPDATE llm_providers
            SET name = ?, provider_type = ?, protocol = ?, base_url = ?, endpoint_path = ?,
                api_key_secret = ?, model = ?, temperature = ?, timeout_seconds = ?,
                max_output_tokens = ?, status = ?, is_default = ?, allow_file_context = ?,
                updated_at = ?
            WHERE provider_id = ?
            """,
            (
                values["name"],
                values["provider_type"],
                values["protocol"],
                values["base_url"],
                values["endpoint_path"],
                values["api_key_secret"],
                values["model"],
                values["temperature"],
                values["timeout_seconds"],
                values["max_output_tokens"],
                values["status"],
                int(values["is_default"]),
                int(values["allow_file_context"]),
                _now(),
                provider_id,
            ),
        )
        return self.get(provider_id) or {}

    def set_default(self, provider_id: str) -> dict:
        if not self.get(provider_id):
            raise KeyError(f"Provider not found: {provider_id}")
        self._clear_default()
        self.db.execute(
            "UPDATE llm_providers SET is_default = 1, status = 'connected', updated_at = ? WHERE provider_id = ?",
            (_now(), provider_id),
        )
        return self.get(provider_id) or {}

    def delete(self, provider_id: str) -> dict:
        provider = self.get(provider_id)
        if not provider:
            raise KeyError(f"Provider not found: {provider_id}")
        self.db.execute("DELETE FROM llm_providers WHERE provider_id = ?", (provider_id,))
        if provider["is_default"]:
            replacement = self.db.query_one("SELECT provider_id FROM llm_providers ORDER BY updated_at DESC LIMIT 1")
            if replacement:
                self.set_default(replacement["provider_id"])
        return {"deleted": True, "provider_id": provider_id}

    def record_call(
        self,
        provider_id: str,
        model: str,
        prompt_id: str,
        status: str,
        request: dict,
        response: dict,
        error: str = "",
        latency_ms: int = 0,
    ) -> dict:
        call_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO llm_calls
                (id, provider_id, model, prompt_id, status, request_json, response_json, error, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                provider_id,
                model,
                prompt_id,
                status,
                json.dumps(request, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                error,
                latency_ms,
                _now(),
            ),
        )
        return {
            "id": call_id,
            "provider_id": provider_id,
            "model": model,
            "prompt_id": prompt_id,
            "status": status,
            "error": error,
            "latency_ms": latency_ms,
        }

    def _normalize_payload(self, payload: dict, partial: bool) -> dict:
        values = {}
        defaults = {
            "name": "OpenAI Compatible",
            "provider_type": "openai_compatible",
            "protocol": "chat_completions",
            "base_url": "https://api.openai.com/v1",
            "endpoint_path": "/chat/completions",
            "api_key": "",
            "model": "",
            "temperature": 0.2,
            "timeout_seconds": 45.0,
            "max_output_tokens": 1200,
            "status": "connected",
            "allow_file_context": False,
        }
        for key, default in defaults.items():
            if key in payload:
                values[key] = payload[key]
            elif not partial:
                values[key] = default
        if not partial and not str(values.get("model", "")).strip():
            raise ValueError("model is required.")
        for key in ("name", "base_url", "endpoint_path", "model"):
            if key in values:
                values[key] = str(values[key]).strip()
        if "provider_type" in values and values["provider_type"] not in self.provider_types:
            raise ValueError("provider_type is invalid.")
        if "protocol" in values and values["protocol"] not in self.protocols:
            raise ValueError("protocol is invalid.")
        if "status" in values and values["status"] not in self.statuses:
            raise ValueError("status is invalid.")
        if "temperature" in values:
            values["temperature"] = float(values["temperature"])
            if not 0 <= values["temperature"] <= 2:
                raise ValueError("temperature must be between 0 and 2.")
        if "timeout_seconds" in values:
            values["timeout_seconds"] = float(values["timeout_seconds"])
            if values["timeout_seconds"] <= 0:
                raise ValueError("timeout_seconds must be positive.")
        if "max_output_tokens" in values:
            values["max_output_tokens"] = int(values["max_output_tokens"])
            if values["max_output_tokens"] < 0:
                raise ValueError("max_output_tokens must be >= 0.")
        if "allow_file_context" in values:
            values["allow_file_context"] = bool(values["allow_file_context"])
        return values

    def _deserialize(self, row: dict) -> dict:
        item = dict(row)
        secret = item.pop("api_key_secret", "")
        item["is_default"] = bool(item["is_default"])
        item["allow_file_context"] = bool(item["allow_file_context"])
        item["api_key_set"] = bool(secret)
        item["api_key_preview"] = self.codec.preview(secret)
        return item

    def _has_default(self) -> bool:
        return bool(self.db.query_one("SELECT provider_id FROM llm_providers WHERE is_default = 1"))

    def _clear_default(self) -> None:
        self.db.execute("UPDATE llm_providers SET is_default = 0")

    def _clean_id(self, value: str) -> str:
        provider_id = str(value).strip()
        if not provider_id or any(char.isspace() for char in provider_id):
            raise ValueError("provider_id cannot be empty or contain whitespace.")
        return provider_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
