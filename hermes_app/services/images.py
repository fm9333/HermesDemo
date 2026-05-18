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

    def recognize_clothing(self, image_id: str) -> dict:
        image_record = self.get(image_id)
        if not image_record:
            raise KeyError(f"Image not found: {image_id}")
        file_record = self.file_service.get(image_record["file_id"])
        if not file_record:
            raise KeyError(f"File not found for image: {image_id}")

        with Image.open(file_record["storage_path"]) as image:
            rgb_image = image.convert("RGB").resize((1, 1))
            red, green, blue = rgb_image.getpixel((0, 0))

        color = _color_name(red, green, blue)
        category = _category_from_filename(image_record["filename"])
        name = f"{color}{_category_label(category)}"
        return {
            "image_id": image_id,
            "file_id": image_record["file_id"],
            "name": name,
            "category": category,
            "color": color,
            "confidence": 0.58,
            "method": "local_pixel_and_filename_heuristic",
            "wardrobe_payload": {"name": name, "category": category, "color": color},
        }


def _category_from_filename(filename: str) -> str:
    lower = filename.lower()
    if any(word in lower for word in ("coat", "jacket", "outerwear", "外套", "夹克")):
        return "outerwear"
    if any(word in lower for word in ("shirt", "衬衫", "tshirt", "t-shirt")):
        return "shirt"
    if any(word in lower for word in ("shoe", "sneaker", "鞋")):
        return "shoes"
    return "clothing"


def _category_label(category: str) -> str:
    return {
        "outerwear": "外套",
        "shirt": "上衣",
        "shoes": "鞋",
        "clothing": "衣物",
    }.get(category, "衣物")


def _color_name(red: int, green: int, blue: int) -> str:
    if max(red, green, blue) < 45:
        return "黑色"
    if min(red, green, blue) > 220:
        return "白色"
    if abs(red - green) < 18 and abs(green - blue) < 18:
        return "灰色"
    if red >= green and red >= blue:
        return "红色"
    if green >= red and green >= blue:
        return "绿色"
    return "蓝色"
