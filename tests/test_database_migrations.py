import sqlite3

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


def test_database_init_migrates_legacy_tables_before_creating_indexes(tmp_path):
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE idea_cards (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE wardrobe_items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                color TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE prd_drafts (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            INSERT INTO idea_cards (id, title, body, tags_json, created_at)
            VALUES ('idea-legacy', 'Legacy idea', 'body', '[]', '2026-05-18T00:00:00+00:00');
            """
        )
        conn.commit()
    finally:
        conn.close()

    db = Database(path)
    db.init()

    idea = db.query_one("SELECT * FROM idea_cards WHERE id = ?", ("idea-legacy",))
    indexes = {item["name"] for item in db.list_indexes()}
    assert idea["status"] == "active"
    assert idea["direction"] == ""
    assert "idx_idea_cards_status_created" in indexes
    assert "idx_prd_drafts_status_created" in indexes
