from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .config import DEFAULT_DB


DEFAULT_COMMUNITY_DB = Path("data/community.sqlite3")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@dataclass(frozen=True)
class ServerRuntimeConfig:
    atlas_db: Path
    community_db: Path
    host: str
    port: int
    public_origin: str | None
    require_existing_db: bool


def environment_truthy(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"", "0", "false", "no", "off"}:
        return False
    if normalized in {"1", "true", "yes", "on"}:
        return True
    raise ValueError("EEA_REQUIRE_EXISTING_DB must be true or false")


def parse_port(value: int | str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("EEA_PORT must be an integer between 1 and 65535") from exc
    if not 1 <= port <= 65535:
        raise ValueError("EEA_PORT must be between 1 and 65535")
    return port


def parse_public_origin(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    origin = value.strip()
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("EEA_PUBLIC_ORIGIN must be an absolute http or https origin without a path")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("EEA_PUBLIC_ORIGIN contains an invalid port") from exc
    return f"{parsed.scheme}://{parsed.netloc}"


def _configured_path(explicit: Path | None, environment_name: str, default: Path) -> Path:
    if explicit is not None:
        return Path(explicit)
    configured = os.environ.get(environment_name)
    return Path(configured) if configured else default


def resolve_community_db(explicit: Path | None = None) -> Path:
    return _configured_path(explicit, "EEA_COMMUNITY_DB", DEFAULT_COMMUNITY_DB)


def resolve_server_config(
    *,
    atlas_db: Path | None = None,
    community_db: Path | None = None,
    host: str | None = None,
    port: int | str | None = None,
    public_origin: str | None = None,
    require_existing_db: bool = False,
) -> ServerRuntimeConfig:
    resolved_host = host if host is not None else os.environ.get("EEA_HOST", DEFAULT_HOST)
    if not resolved_host or not resolved_host.strip():
        raise ValueError("EEA_HOST must not be empty")
    configured_port: int | str = port if port is not None else os.environ.get("EEA_PORT", DEFAULT_PORT)
    configured_origin = public_origin if public_origin is not None else os.environ.get("EEA_PUBLIC_ORIGIN")
    return ServerRuntimeConfig(
        atlas_db=_configured_path(atlas_db, "EEA_ATLAS_DB", DEFAULT_DB),
        community_db=resolve_community_db(community_db),
        host=resolved_host.strip(),
        port=parse_port(configured_port),
        public_origin=parse_public_origin(configured_origin),
        require_existing_db=require_existing_db or environment_truthy(os.environ.get("EEA_REQUIRE_EXISTING_DB")),
    )


def validate_existing_atlas_database(path: Path | str) -> None:
    database_path = Path(path)
    if not database_path.is_file():
        raise ValueError("required Atlas database does not exist or is not a regular file")
    try:
        resolved = database_path.resolve()
        connection = sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
        try:
            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise ValueError("required Atlas database cannot be opened") from exc
    if not {"period_observation", "api_cache", "source_cache"}.issubset(tables):
        raise ValueError("required Atlas database does not have the expected Atlas schema")
