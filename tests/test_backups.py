from hermes_app.core.database import Database
from hermes_app.services.backups import BackupService


def test_backup_service_creates_lists_and_restores_sqlite_snapshot(tmp_path):
    db = Database(tmp_path / "hermes.db")
    db.init()
    db.execute(
        """
        INSERT INTO memory_items
            (id, memory_type, key, value, sensitivity, status, source, confidence, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "memory-1",
            "preference",
            "topic",
            "local backup",
            "normal",
            "active",
            "test",
            0.9,
            "2026-05-18T00:00:00+00:00",
            None,
        ),
    )
    service = BackupService(db, root=tmp_path / "backups")

    backup = service.create("before-delete")
    db.execute("DELETE FROM memory_items WHERE id = ?", ("memory-1",))
    restored = service.restore(backup["id"])

    assert backup["note"] == "before-delete"
    assert backup["filename"].endswith(".zip")
    assert service.list()[0]["id"] == backup["id"]
    assert restored["status"] == "restored"
    assert db.query_one("SELECT * FROM memory_items WHERE id = ?", ("memory-1",))["value"] == "local backup"


def test_backup_restore_rejects_unknown_id(tmp_path):
    db = Database(tmp_path / "hermes.db")
    db.init()
    service = BackupService(db, root=tmp_path / "backups")

    try:
        service.restore("../bad")
    except KeyError as exc:
        assert "Backup not found" in str(exc)
    else:
        raise AssertionError("restore should reject unsafe backup ids")
