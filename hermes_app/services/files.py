from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from hermes_app.core.config import BASE_DIR, get_settings
from hermes_app.core.database import Database


class FileService:
    def __init__(self, db: Database, root: str | Path | None = None):
        self.db = db
        self.root = Path(root or _default_file_root()).expanduser().resolve()
        self.uploads = self.root / "uploads"
        self.uploads.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, content_type: str, data: bytes) -> dict:
        file_id = str(uuid4())
        safe_name = _safe_filename(filename)
        storage_path = self.uploads / f"{file_id}-{safe_name}"
        storage_path.write_bytes(data)
        self.db.execute(
            """
            INSERT INTO files (id, filename, content_type, size, storage_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id,
                safe_name,
                content_type or "application/octet-stream",
                len(data),
                str(storage_path),
                "uploaded",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return self.get(file_id) or {}

    def list(self) -> list[dict]:
        return self.db.query("SELECT * FROM files ORDER BY created_at DESC LIMIT 100")

    def get(self, file_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM files WHERE id = ?", (file_id,))


def _default_file_root() -> Path:
    explicit = os.getenv("HERMES_FILES_DIR")
    if explicit:
        return Path(explicit)
    db_path = Path(get_settings().database_path)
    if db_path != Path(":memory:"):
        return db_path.parent / "files"
    return BASE_DIR / "data" / "files"


def _safe_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    return re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]", "_", name) or "upload.bin"

