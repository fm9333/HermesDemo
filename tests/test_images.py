from io import BytesIO

from PIL import Image

from hermes_app.core.database import Database
from hermes_app.services.files import FileService
from hermes_app.services.images import ImageService


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 3), color=(255, 0, 0)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_image_service_saves_image_metadata(tmp_path):
    db = Database(tmp_path / "images.db")
    db.init()
    files = FileService(db, root=tmp_path / "store")
    service = ImageService(db, files)

    item = service.save_upload("coat.png", "image/png", _png_bytes())

    assert item["filename"] == "coat.png"
    assert item["width"] == 2
    assert item["height"] == 3
    assert item["status"] == "uploaded"

