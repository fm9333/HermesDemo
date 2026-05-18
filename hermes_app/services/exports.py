from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from hermes_app.core.config import BASE_DIR, get_settings
from hermes_app.core.database import Database


EXPORT_TABLES = (
    "memory_items",
    "memory_candidates",
    "reminders",
    "todo_items",
    "idea_cards",
    "prd_drafts",
    "weekly_reviews",
    "providers",
    "news_articles",
    "map_places",
    "app_settings",
    "schema_migrations",
)


class ExportService:
    def __init__(self, db: Database, root: str | Path | None = None):
        self.db = db
        self.root = Path(root or _default_export_root()).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, tables: list[str] | None = None, note: str = "manual") -> dict:
        selected_tables = self._validate_tables(tables or list(EXPORT_TABLES))
        export_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        export_path = self.root / f"{export_id}.zip"
        manifest = {
            "id": export_id,
            "app": "Hermes",
            "kind": "json-export",
            "note": note.strip() or "manual",
            "tables": selected_tables,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for table in selected_tables:
                rows = self.db.query(f"SELECT * FROM {table}")
                archive.writestr(
                    f"tables/{table}.json",
                    json.dumps(rows, ensure_ascii=False, indent=2),
                )
        return self._inspect(export_path)

    def list(self) -> list[dict]:
        exports = []
        for path in self.root.glob("*.zip"):
            try:
                exports.append(self._inspect(path))
            except (KeyError, json.JSONDecodeError, zipfile.BadZipFile):
                continue
        return sorted(exports, key=lambda item: item["created_at"], reverse=True)

    def _validate_tables(self, tables: list[str]) -> list[str]:
        unknown = [table for table in tables if table not in EXPORT_TABLES]
        if unknown:
            raise ValueError(f"Unsupported export tables: {', '.join(unknown)}")
        return list(dict.fromkeys(tables))

    def _inspect(self, path: Path) -> dict:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        return {
            **manifest,
            "filename": path.name,
            "size": path.stat().st_size,
            "path": str(path),
        }


def _default_export_root() -> Path:
    explicit = os.getenv("HERMES_EXPORT_DIR")
    settings = get_settings()
    db_path = Path(settings.database_path)
    if explicit:
        return Path(explicit)
    if db_path != Path(":memory:"):
        return db_path.parent / "exports"
    return BASE_DIR / "data" / "exports"
