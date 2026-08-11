from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS api_cache (
    id INTEGER PRIMARY KEY,
    endpoint TEXT NOT NULL,
    target TEXT NOT NULL,
    start_date TEXT NOT NULL DEFAULT '',
    end_date TEXT NOT NULL DEFAULT '',
    request_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    response_json TEXT NOT NULL,
    UNIQUE(endpoint, target, start_date, end_date)
);

CREATE TABLE IF NOT EXISTS source_cache (
    source TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    request_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    content_type TEXT,
    etag TEXT,
    last_modified TEXT,
    sha256 TEXT NOT NULL,
    payload_text TEXT NOT NULL,
    PRIMARY KEY(source, endpoint)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS period_observation (
    country_code TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    granularity TEXT NOT NULL,
    source TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    source_series TEXT NOT NULL DEFAULT '',
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'observed',
    PRIMARY KEY (
        country_code, period_start, period_end, granularity,
        source, source_endpoint, source_series, metric
    )
) WITHOUT ROWID;
"""


OBSOLETE_TABLES = (
    "bilateral_flow",
    "import_period",
    "installed_capacity",
    "observation",
    "quality_issue",
)


def connect(path: Path | str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    connection.commit()


SUPPORTED_SOURCES = ("ember", "eurostat", "jrc")


def migrate_atlas_catalog(connection: sqlite3.Connection) -> dict[str, Any]:
    existing_tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    placeholders = ",".join("?" for _ in SUPPORTED_SOURCES)
    period_rows_removed = connection.execute(
        f"SELECT COUNT(*) FROM period_observation WHERE source NOT IN ({placeholders}) OR country_code='AL'",
        SUPPORTED_SOURCES,
    ).fetchone()[0]
    api_cache_rows_removed = connection.execute(
        "SELECT COUNT(*) FROM api_cache WHERE endpoint NOT LIKE 'ember/%' OR target='ALB' OR target LIKE 'ALB|%'"
    ).fetchone()[0]
    source_cache_rows_removed = connection.execute(
        f"SELECT COUNT(*) FROM source_cache WHERE source NOT IN ({placeholders})",
        SUPPORTED_SOURCES,
    ).fetchone()[0]
    dropped = [table for table in OBSOLETE_TABLES if table in existing_tables]

    connection.execute("SAVEPOINT atlas_catalog_migration")
    try:
        connection.execute(
            f"DELETE FROM period_observation WHERE source NOT IN ({placeholders}) OR country_code='AL'",
            SUPPORTED_SOURCES,
        )
        connection.execute(
            "DELETE FROM api_cache WHERE endpoint NOT LIKE 'ember/%' OR target='ALB' OR target LIKE 'ALB|%'"
        )
        connection.execute(
            f"DELETE FROM source_cache WHERE source NOT IN ({placeholders})",
            SUPPORTED_SOURCES,
        )
        for table in dropped:
            connection.execute(f'DROP TABLE "{table}"')
        connection.execute("RELEASE SAVEPOINT atlas_catalog_migration")
    except Exception:
        connection.execute("ROLLBACK TO SAVEPOINT atlas_catalog_migration")
        connection.execute("RELEASE SAVEPOINT atlas_catalog_migration")
        raise
    connection.commit()
    return {
        "period_rows_removed": period_rows_removed,
        "api_cache_rows_removed": api_cache_rows_removed,
        "source_cache_rows_removed": source_cache_rows_removed,
        "tables_dropped": dropped,
    }


def migrate_to_ember_only(connection: sqlite3.Connection) -> dict[str, Any]:
    """Backward-compatible alias for databases created before auxiliary sources."""
    return migrate_atlas_catalog(connection)


@contextmanager
def database(path: Path | str) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        initialize(connection)
        yield connection
    finally:
        connection.close()


@contextmanager
def read_database(path: Path | str) -> Iterator[sqlite3.Connection]:
    db_path = Path(path).resolve()
    connection = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def reset(path: Path | str) -> bool:
    db_path = Path(path)
    if not db_path.exists():
        return False
    db_path.unlink()
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            sidecar.unlink()
    return True
