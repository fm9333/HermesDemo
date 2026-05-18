from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from hermes_app.core.config import BASE_DIR


class RuntimeStateService:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or _default_runtime_root()).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "runtime-state.json"
        self._recovery = self._detect_recovery()

    @classmethod
    def from_database_path(cls, database_path: str | Path) -> "RuntimeStateService":
        path = Path(database_path)
        if str(database_path) == ":memory:":
            return cls()
        return cls(path.parent / "runtime")

    def start(self) -> dict:
        state = {
            "status": "running",
            "pid": os.getpid(),
            "started_at": _now(),
            "last_heartbeat": _now(),
            "clean_shutdown": False,
        }
        self._write(state)
        return self.status()

    def heartbeat(self) -> dict:
        state = self._read()
        state["last_heartbeat"] = _now()
        state["status"] = "running"
        self._write(state)
        return self.status()

    def mark_clean_shutdown(self) -> dict:
        state = self._read()
        state.update(
            {
                "status": "stopped",
                "clean_shutdown": True,
                "stopped_at": _now(),
            }
        )
        self._write(state)
        return self.status()

    def status(self) -> dict:
        return {
            "state": self._read(),
            "recovery": self._recovery,
            "state_path": str(self.state_path),
        }

    def _detect_recovery(self) -> dict:
        previous = self._read()
        if previous.get("status") == "running" and not previous.get("clean_shutdown", False):
            return {
                "status": "recovered",
                "reason": "previous_runtime_not_cleanly_stopped",
                "previous_pid": previous.get("pid"),
                "previous_started_at": previous.get("started_at"),
                "previous_last_heartbeat": previous.get("last_heartbeat"),
                "detected_at": _now(),
            }
        return {"status": "clean", "reason": "no_unclean_shutdown_detected", "detected_at": _now()}

    def _read(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"status": "unknown", "clean_shutdown": False}

    def _write(self, state: dict) -> None:
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_runtime_root() -> Path:
    explicit = os.getenv("HERMES_RUNTIME_DIR")
    if explicit:
        return Path(explicit)
    return BASE_DIR / "data" / "runtime"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
