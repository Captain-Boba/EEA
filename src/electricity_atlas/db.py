from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


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

CREATE TABLE IF NOT EXISTS import_period (
    endpoint TEXT NOT NULL,
    target TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    available_from TEXT,
    available_until TEXT,
    resolution TEXT,
    interval_minutes INTEGER,
    unit TEXT,
    license TEXT,
    PRIMARY KEY(endpoint, target, start_date, end_date)
);

CREATE TABLE IF NOT EXISTS observation (
    country_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    bidding_zone TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    source_endpoint TEXT NOT NULL,
    source_resolution TEXT NOT NULL,
    interval_minutes INTEGER,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'observed',
    PRIMARY KEY(country_code, bidding_zone, timestamp_utc, metric, source_endpoint)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS observation_period_idx
ON observation(country_code, timestamp, metric);

CREATE TABLE IF NOT EXISTS bilateral_flow (
    country_code TEXT NOT NULL,
    counterparty TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    source_resolution TEXT NOT NULL,
    interval_minutes INTEGER NOT NULL,
    flow_mw REAL NOT NULL,
    PRIMARY KEY(country_code, counterparty, timestamp_utc, source)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS installed_capacity (
    country_code TEXT NOT NULL,
    country_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    source_resolution TEXT NOT NULL,
    category TEXT NOT NULL,
    value_mw REAL NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'observed',
    PRIMARY KEY(country_code, timestamp, category, source)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS quality_issue (
    id INTEGER PRIMARY KEY,
    country_code TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT NOT NULL,
    UNIQUE(country_code, endpoint, period_start, period_end, issue_type, details)
);

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
