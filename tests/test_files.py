from io import BytesIO

from docx import Document
from pypdf import PdfWriter

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


def test_file_service_reads_text_upload(tmp_path):
    db = Database(tmp_path / "files.db")
    db.init()
    service = FileService(db, root=tmp_path / "store")

    item = service.save_upload("meeting.md", "text/markdown", "结论：继续推进".encode("utf-8"))

    assert service.read_text(item["id"]) == "结论：继续推进"


def test_file_service_extracts_docx_upload(tmp_path):
    db = Database(tmp_path / "files.db")
    db.init()
    service = FileService(db, root=tmp_path / "store")

    buffer = BytesIO()
    document = Document()
    document.add_paragraph("结论：DOCX 可以解析")
    document.save(buffer)
    item = service.save_upload(
        "meeting.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        buffer.getvalue(),
    )

    assert "DOCX 可以解析" in service.extract_text(item["id"])


def test_file_service_accepts_pdf_upload(tmp_path):
    db = Database(tmp_path / "files.db")
    db.init()
    service = FileService(db, root=tmp_path / "store")

    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    item = service.save_upload("blank.pdf", "application/pdf", buffer.getvalue())

    assert service.extract_text(item["id"]) == ""
