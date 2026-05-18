from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

from hermes_app.core.config import Settings
from hermes_app.services.settings import SettingsService


class UpdateService:
    def __init__(self, settings: Settings, app_settings: SettingsService):
        self.settings = settings
        self.app_settings = app_settings

    def status(self) -> dict:
        return {
            "current_version": self.settings.app_version,
            "enabled": self.app_settings.get("auto_update_enabled")["value"],
            "channel": self.app_settings.get("update_channel")["value"],
            "manifest_url": self.app_settings.get("update_manifest_url")["value"],
        }

    def check(self, manifest_url: str | None = None) -> dict:
        status = self.status()
        url = (manifest_url or status["manifest_url"]).strip()
        if not url:
            return {"status": "not_configured", **status}

        manifest = self._fetch_manifest(url)
        manifest_channel = manifest.get("channel", "stable")
        if manifest_channel not in {status["channel"], "all"}:
            return {"status": "channel_mismatch", "manifest": manifest, **status}

        latest_version = str(manifest.get("version", "0"))
        has_update = _is_newer(latest_version, status["current_version"])
        return {
            "status": "update_available" if has_update else "up_to_date",
            "manifest": manifest,
            "latest_version": latest_version,
            **status,
        }

    def _fetch_manifest(self, url: str) -> dict:
        if url.startswith("file://"):
            return json.loads(Path(url.removeprefix("file://")).read_text(encoding="utf-8"))
        if "://" not in url:
            return json.loads(Path(url).read_text(encoding="utf-8"))
        request = Request(url, headers={"User-Agent": "HermesDesktop/0.1 update checker"})
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))


def _is_newer(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for part in value.split("."):
        digits = "".join(char for char in part if char.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)
