import json
import zipfile

from hermes_app.core.database import Database
from hermes_app.services.exports import ExportService


def test_export_service_creates_json_zip_for_selected_tables(tmp_path):
    db = Database(tmp_path / "exports.db")
    db.init()
    db.execute(
        """
        INSERT INTO todo_items (id, title, source, source_id, status, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("todo-export", "Export data", "test", None, "open", "2026-05-18T00:00:00+00:00", None),
    )
    service = ExportService(db, root=tmp_path / "exports")

    export = service.create(tables=["todo_items", "schema_migrations"], note="unit-test")

    assert export["note"] == "unit-test"
    assert export["tables"] == ["todo_items", "schema_migrations"]
    assert service.list()[0]["id"] == export["id"]
    with zipfile.ZipFile(export["path"]) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        todos = json.loads(archive.read("tables/todo_items.json").decode("utf-8"))
    assert manifest["kind"] == "json-export"
    assert todos[0]["id"] == "todo-export"


def test_export_service_rejects_unknown_tables(tmp_path):
    db = Database(tmp_path / "exports.db")
    db.init()
    service = ExportService(db, root=tmp_path / "exports")

    try:
        service.create(tables=["sqlite_master"])
    except ValueError as exc:
        assert "Unsupported export tables" in str(exc)
    else:
        raise AssertionError("unknown export tables should be rejected")
