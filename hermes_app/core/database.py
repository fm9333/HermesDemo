from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MIGRATIONS = (
    ("0001_core_schema", "Core memory, actions, settings, skills, files, and scenes schema"),
    ("0002_inspiration_workflows", "Idea cards, todos, PRD drafts, wardrobe, and feedback schema"),
    ("0003_proactive_integrations", "Providers, triggers, weekly reviews, news, and maps schema"),
    ("0004_release_backups", "Release readiness support for local backup and restore"),
    ("0005_performance_indexes", "Indexes for common status, source, and history queries"),
    ("0006_llm_provider_config", "OpenAI-compatible LLM provider configuration and prompt library support"),
)


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()

    def init(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                );

                CREATE TABLE IF NOT EXISTS memory_candidates (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pending_actions (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    executed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS execution_logs (
                    id TEXT PRIMARY KEY,
                    intent TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS providers (
                    provider_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    permissions_json TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS llm_providers (
                    provider_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    endpoint_path TEXT NOT NULL,
                    api_key_secret TEXT NOT NULL,
                    model TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    timeout_seconds REAL NOT NULL,
                    max_output_tokens INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_default INTEGER NOT NULL,
                    allow_file_context INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS llm_calls (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    error TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS eval_runs (
                    id TEXT PRIMARY KEY,
                    suite_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    results_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS growth_logs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    source_task TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    rolled_back_at TEXT
                );

                CREATE TABLE IF NOT EXISTS trigger_runs (
                    id TEXT PRIMARY KEY,
                    trigger_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weekly_reviews (
                    id TEXT PRIMARY KEY,
                    week_start TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    highlights_json TEXT NOT NULL,
                    next_actions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS news_articles (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS map_places (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    category TEXT NOT NULL,
                    place_type TEXT NOT NULL,
                    importance REAL NOT NULL,
                    address_json TEXT NOT NULL,
                    bounding_box_json TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    due_at_text TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS todo_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS prd_drafts (
                    id TEXT PRIMARY KEY,
                    idea_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(idea_id) REFERENCES idea_cards(id)
                );

                CREATE TABLE IF NOT EXISTS idea_cards (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    direction TEXT NOT NULL DEFAULT '',
                    target_user TEXT NOT NULL DEFAULT '',
                    pain_point TEXT NOT NULL DEFAULT '',
                    core_assumption TEXT NOT NULL DEFAULT '',
                    counter_challenge TEXT NOT NULL DEFAULT '',
                    analogy TEXT NOT NULL DEFAULT '',
                    mvp_plan TEXT NOT NULL DEFAULT '',
                    risks_json TEXT NOT NULL DEFAULT '[]',
                    next_steps_json TEXT NOT NULL DEFAULT '[]',
                    score REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS wardrobe_items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    color TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS weather_cache (
                    id TEXT PRIMARY KEY,
                    location TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS skill_runs (
                    id TEXT PRIMARY KEY,
                    skill_id TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    storage_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS images (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    content_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(file_id) REFERENCES files(id)
                );

                CREATE TABLE IF NOT EXISTS scenes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    context_signal TEXT NOT NULL,
                    user_state TEXT NOT NULL,
                    opportunity TEXT NOT NULL,
                    decision_policy TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    effect_score REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS scene_runs (
                    id TEXT PRIMARY KEY,
                    scene_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(scene_id) REFERENCES scenes(id)
                );

                CREATE TABLE IF NOT EXISTS scene_feedback (
                    id TEXT PRIMARY KEY,
                    scene_id TEXT NOT NULL,
                    run_id TEXT,
                    rating TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(scene_id) REFERENCES scenes(id),
                    FOREIGN KEY(run_id) REFERENCES scene_runs(id)
                );

                CREATE TABLE IF NOT EXISTS context_signals (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                );

                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    title TEXT NOT NULL,
                    opportunity_type TEXT NOT NULL,
                    priority REAL NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(signal_id) REFERENCES context_signals(id)
                );

                CREATE TABLE IF NOT EXISTS recommendations (
                    id TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
                );

                CREATE INDEX IF NOT EXISTS idx_pending_actions_status_created
                    ON pending_actions(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_memory_candidates_status_created
                    ON memory_candidates(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_reminders_status_created
                    ON reminders(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_todo_items_status_created
                    ON todo_items(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_idea_cards_status_created
                    ON idea_cards(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_prd_drafts_status_created
                    ON prd_drafts(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_context_signals_status_type_created
                    ON context_signals(status, signal_type, created_at);
                CREATE INDEX IF NOT EXISTS idx_opportunities_status_created
                    ON opportunities(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_recommendations_status_created
                    ON recommendations(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_news_articles_status_published
                    ON news_articles(status, published_at);
                CREATE INDEX IF NOT EXISTS idx_map_places_query_created
                    ON map_places(query, created_at);
                CREATE INDEX IF NOT EXISTS idx_llm_calls_provider_created
                    ON llm_calls(provider_id, created_at);
                """
            )
            self._ensure_column("wardrobe_items", "status", "TEXT NOT NULL DEFAULT 'active'")
            self._ensure_column("idea_cards", "direction", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "target_user", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "pain_point", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "core_assumption", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "counter_challenge", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "analogy", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "mvp_plan", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column("idea_cards", "risks_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column("idea_cards", "next_steps_json", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column("idea_cards", "score", "REAL NOT NULL DEFAULT 0")
            self._ensure_column("idea_cards", "status", "TEXT NOT NULL DEFAULT 'active'")
            for migration_id, description in MIGRATIONS:
                self._record_migration(migration_id, description)
            self._conn.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        if column not in {row["name"] for row in columns}:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _record_migration(self, migration_id: str, description: str) -> None:
        existing = self._conn.execute(
            "SELECT id FROM schema_migrations WHERE id = ?",
            (migration_id,),
        ).fetchone()
        if not existing:
            self._conn.execute(
                "INSERT INTO schema_migrations (id, description, applied_at) VALUES (?, ?, ?)",
                (migration_id, description, datetime.now(timezone.utc).isoformat()),
            )

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._conn.execute(sql, tuple(params))
            self._conn.commit()
            return cursor

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(sql, tuple(params)).fetchall()
            return [dict(row) for row in rows]

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(sql, tuple(params)).fetchone()
            return dict(row) if row else None

    def list_migrations(self) -> list[dict[str, Any]]:
        return self.query("SELECT * FROM schema_migrations ORDER BY id")

    def list_indexes(self) -> list[dict[str, Any]]:
        return self.query(
            """
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type = 'index' AND name NOT LIKE 'sqlite_autoindex%'
            ORDER BY name
            """
        )

    def backup_to(self, target: str | Path) -> None:
        target_path = Path(target)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            destination = sqlite3.connect(str(target_path))
            try:
                self._conn.backup(destination)
            finally:
                destination.close()

    def restore_from(self, source: str | Path) -> None:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(str(source_path))
        source_connection = sqlite3.connect(str(source_path))
        try:
            with self._lock:
                source_connection.backup(self._conn)
                self._conn.commit()
        finally:
            source_connection.close()
