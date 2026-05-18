from __future__ import annotations

import os
import secrets
import socket
import threading
import time
import urllib.error
import urllib.request
import logging
from dataclasses import dataclass
from pathlib import Path

import uvicorn

from desktop.app_paths import DesktopPaths, ensure_desktop_paths
from desktop.logging_config import setup_desktop_logging


logger = logging.getLogger(__name__)


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


@dataclass
class DesktopServiceState:
    host: str
    port: int
    token: str
    base_url: str
    client_url: str
    database_path: Path
    app_root: Path


class DesktopServiceManager:
    def __init__(self, app_data_dir: str | Path | None = None, host: str = "127.0.0.1", port: int | None = None):
        self.paths: DesktopPaths = ensure_desktop_paths(app_data_dir)
        self.host = host
        self.port = port or find_free_port(host)
        self.token = secrets.token_urlsafe(32)
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None
        self._previous_env: dict[str, str | None] = {}
        self.log_file = setup_desktop_logging(self.paths.logs)

    @property
    def state(self) -> DesktopServiceState:
        base_url = f"http://{self.host}:{self.port}"
        return DesktopServiceState(
            host=self.host,
            port=self.port,
            token=self.token,
            base_url=base_url,
            client_url=f"{base_url}/?token={self.token}",
            database_path=self.paths.database_path,
            app_root=self.paths.root,
        )

    def start(self, timeout_seconds: float = 15.0) -> DesktopServiceState:
        if self.thread and self.thread.is_alive():
            return self.state

        logger.info("Starting Hermes local service on %s:%s", self.host, self.port)
        self._set_env("HERMES_DB", str(self.paths.database_path))
        self._set_env("HERMES_LOCAL_TOKEN", self.token)
        self._set_env("HERMES_DESKTOP_MODE", "true")

        from hermes_app.main import app

        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, name="HermesLocalService", daemon=True)
        self.thread.start()
        self._wait_until_ready(timeout_seconds)
        logger.info("Hermes local service is ready at %s", self.state.base_url)
        return self.state

    def stop(self, timeout_seconds: float = 10.0) -> None:
        logger.info("Stopping Hermes local service")
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout_seconds)
        self._restore_env()
        logger.info("Hermes local service stopped")

    def _wait_until_ready(self, timeout_seconds: float) -> None:
        deadline = time.monotonic() + timeout_seconds
        last_error: Exception | None = None
        health_url = f"http://{self.host}:{self.port}/api/health"
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(health_url, timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError) as exc:
                last_error = exc
            time.sleep(0.1)
        raise RuntimeError(f"Hermes local service did not start on {health_url}: {last_error}")

    def _set_env(self, key: str, value: str) -> None:
        if key not in self._previous_env:
            self._previous_env[key] = os.environ.get(key)
        os.environ[key] = value

    def _restore_env(self) -> None:
        for key, value in self._previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._previous_env.clear()
