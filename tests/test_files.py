from hermes_app.core.database import Database
from hermes_app.services.files import FileService


def test_file_service_saves_upload(tmp_path):
    db = Database(tmp_path / "files.db")
    db.init()
    service = FileService(db, root=tmp_path / "store")

    item = service.save_upload("会议 记录.txt", "text/plain", "hello".encode("utf-8"))

    assert item["filename"] == "会议_记录.txt"
    assert item["size"] == 5
    assert item["status"] == "uploaded"
    assert len(service.list()) == 1

