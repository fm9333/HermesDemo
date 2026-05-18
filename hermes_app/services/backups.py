from __future__ import annotations

import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from hermes_app.core.config import BASE_DIR, get_settings
from hermes_app.core.database import Database


class BackupService:
    def __init__(self, db: Database, root: str | Path | None = None):
        self.db = db
        self.root = Path(root or _default_backup_root()).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, note: str = "manual") -> dict:
        backup_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
        backup_path = self.root / f"{backup_id}.zip"
        manifest = {
            "id": backup_id,
            "app": "Hermes",
            "kind": "sqlite-backup",
            "note": note.strip() or "manual",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_path": str(self.db.path),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot = Path(temp_dir) / "hermes.db"
            self.db.backup_to(snapshot)
            with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot, "hermes.db")
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        return self._inspect(backup_path)

    def list(self) -> list[dict]:
        backups = []
        for path in self.root.glob("*.zip"):
            try:
                backups.append(self._inspect(path))
            except (KeyError, json.JSONDecodeError, zipfile.BadZipFile):
                continue
        return sorted(backups, key=lambda item: item["created_at"], reverse=True)

    def restore(self, backup_id: str) -> dict:
        backup_path = self._path_for(backup_id)
        backup = self._inspect(backup_path)
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(backup_path) as archive:
                archive.extract("hermes.db", temp_dir)
            self.db.restore_from(Path(temp_dir) / "hermes.db")
        return {"status": "restored", "backup": backup}

    def _path_for(self, backup_id: str) -> Path:
        if "/" in backup_id or "\\" in backup_id or ".." in backup_id:
            raise KeyError(f"Backup not found: {backup_id}")
        path = self.root / f"{backup_id}.zip"
        if not path.exists():
            raise KeyError(f"Backup not found: {backup_id}")
        return path

    def _inspect(self, path: Path) -> dict:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        return {
            **manifest,
            "filename": path.name,
            "size": path.stat().st_size,
            "path": str(path),
        }


def _default_backup_root() -> Path:
    explicit = os.getenv("HERMES_BACKUP_DIR")
    settings = get_settings()
    db_path = Path(settings.database_path)
    if explicit:
        return Path(explicit)
    if db_path != Path(":memory:"):
        return db_path.parent / "backups"
    return BASE_DIR / "data" / "backups"
