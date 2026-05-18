from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DesktopPaths:
    root: Path
    config: Path
    data: Path
    files: Path
    logs: Path
    skills: Path
    evals: Path
    backups: Path

    @property
    def database_path(self) -> Path:
        return self.data / "hermes.db"


def default_app_data_dir() -> Path:
    explicit = os.getenv("HERMES_DESKTOP_HOME")
    if explicit:
        return Path(explicit).expanduser().resolve()

    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "Hermes"

    return Path.home() / ".hermes"


def ensure_desktop_paths(root: str | Path | None = None) -> DesktopPaths:
    base = Path(root).expanduser().resolve() if root else default_app_data_dir()
    paths = DesktopPaths(
        root=base,
        config=base / "config",
        data=base / "data",
        files=base / "files",
        logs=base / "logs",
        skills=base / "skills",
        evals=base / "evals",
        backups=base / "backups",
    )
    for path in (
        paths.root,
        paths.config,
        paths.data,
        paths.files / "uploads",
        paths.files / "generated",
        paths.files / "exports",
        paths.logs,
        paths.skills / "system",
        paths.skills / "personal",
        paths.skills / "draft",
        paths.evals,
        paths.backups,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return paths

