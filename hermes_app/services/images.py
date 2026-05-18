from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from hermes_app.core.database import Database
from hermes_app.services.files import FileService


class ImageService:
    def __init__(self, db: Database, file_service: FileService):
        self.db = db
        self.file_service = file_service

    def save_upload(self, filename: str, content_type: str, data: bytes) -> dict:
        if content_type and not content_type.startswith("image/"):
            raise ValueError("Only image uploads are accepted.")

        try:
            with Image.open(BytesIO(data)) as image:
                width, height = image.size
                detected_format = image.format.lower() if image.format else "image"
        except UnidentifiedImageError as exc:
            raise ValueError("Uploaded file is not a valid image.") from exc

        file_record = self.file_service.save_upload(filename, content_type or f"image/{detected_format}", data)
        image_id = str(uuid4())
        self.db.execute(
            """
            INSERT INTO images (id, file_id, filename, width, height, content_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                image_id,
                file_record["id"],
                file_record["filename"],
                width,
                height,
                content_type or f"image/{detected_format}",
                "uploaded",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return self.get(image_id) or {}

    def list(self) -> list[dict]:
        return self.db.query("SELECT * FROM images ORDER BY created_at DESC LIMIT 100")

    def get(self, image_id: str) -> dict | None:
        return self.db.query_one("SELECT * FROM images WHERE id = ?", (image_id,))

