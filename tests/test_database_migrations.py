from hermes_app.core.database import MIGRATIONS, Database


def test_database_init_records_migrations_idempotently(tmp_path):
    db = Database(tmp_path / "migrations.db")
    db.init()
    db.execute(
        """
        INSERT INTO memory_items
            (id, memory_type, key, value, sensitivity, status, source, confidence, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "memory-migration",
            "preference",
            "release",
            "preserve data",
            "normal",
            "active",
            "test",
            0.9,
            "2026-05-18T00:00:00+00:00",
            None,
        ),
    )

    db.init()

    migrations = db.list_migrations()
    assert [item["id"] for item in migrations] == [migration[0] for migration in MIGRATIONS]
    assert len({item["id"] for item in migrations}) == len(MIGRATIONS)
    assert db.query_one("SELECT * FROM memory_items WHERE id = ?", ("memory-migration",))["value"] == "preserve data"
