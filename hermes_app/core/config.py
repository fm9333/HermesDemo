from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Hermes"
    app_version: str = "0.1.0"
    database_path: Path | str = os.getenv("HERMES_DB", str(BASE_DIR / "data" / "hermes.db"))
    debug: bool = os.getenv("HERMES_DEBUG", "false").lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

