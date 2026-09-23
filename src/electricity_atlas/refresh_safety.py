"""Shared, offline safety checks for refresh workers."""
from __future__ import annotations

import errno
import json
import os
import re
import socket
from datetime import UTC, datetime
from pathlib import Path


class RefreshBusyError(RuntimeError):
    pass


class FileRefreshLock:
    """Kernel-owned lock; the stable file must never be unlinked while in use.

    Closing/crashing releases the lock. Timestamps and PIDs are diagnostic only,
    so PID reuse, container hostnames and partially written metadata are harmless.
    """

    def __init__(self, path: Path):
        self.path = path
        self._file = None

    def acquire(self) -> None:
        if self._file is not None:
            raise RefreshBusyError("Refresh lock already held by this owner")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        handle = os.fdopen(descriptor, "r+b", buffering=0)
        try:
            if os.name == "nt":
                import msvcrt
                # Windows permits locking beyond EOF, avoiding an init/write race.
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise RefreshBusyError("Another refresh worker holds the database lock") from exc
            raise
        self._file = handle
        try:
            payload = {"pid": os.getpid(), "hostname": socket.gethostname(),
                       "started_at": datetime.now(UTC).isoformat()}
            handle.write(b" " + json.dumps(payload).encode("utf-8"))
            handle.truncate()
        except Exception:
            self.release()
            raise

    def release(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_args):
        self.release()


def safe_error(error: object) -> str:
    text = str(error)
    for name, value in os.environ.items():
        if value and len(value) >= 4 and any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(value, "REDACTED")
    return re.sub(r"(?i)((?:api[_-]?key|token|password|secret)=)[^&\s]+", r"\1REDACTED", text)[:1000]


def observation_coverage(connection) -> dict[tuple, str]:
    """Identity coverage, not values: legitimate numerical revisions are allowed.

    Snapshot sources may advance their date but must retain every series and may
    not move backwards. Time series must retain every already published period.
    """
    coverage = {}
    for row in connection.execute("""
        SELECT country_code, source, source_endpoint, source_series, metric,
               granularity, period_start, period_end, unit FROM period_observation
    """):
        country, source, endpoint, series, metric, granularity, start, end, unit = row
        # Battery registry exports extend a provisional month's end date on
        # subsequent runs. Preserve month identity and require a non-decreasing
        # end date; no missing month/series or completed-month regression allowed.
        battery_month = (source == "battery_charts" and granularity == "monthly"
                         and start[:7] == end[:7] and start.endswith("-01"))
        key = (country, source, endpoint, series, metric, granularity, unit,
               "" if granularity == "snapshot" else start,
               "" if granularity == "snapshot" or battery_month else end)
        coverage[key] = max(end if battery_month else start, coverage.get(key, ""))
    return coverage


def require_preserved_coverage(connection, before: dict[tuple, str]) -> None:
    after = observation_coverage(connection)
    missing = [key for key, latest in before.items() if key not in after or after[key] < latest]
    if missing:
        raise ValueError(f"Refresh would remove or backdate {len(missing)} published observation keys")


def prune_superseded_ember_cache(connection, refreshed_since: str) -> int:
    """Only discard responses fully covered by a newer validated response.

    Exact targets include aggregate/options flags. Different targets, endpoints,
    partially overlapping ranges and caches not refreshed this run stay intact.
    SQLite reuses the freed pages; do not VACUUM the live production database.
    """
    cursor = connection.execute("""
        DELETE FROM api_cache AS old
        WHERE old.endpoint LIKE 'ember/%' AND EXISTS (
            SELECT 1 FROM api_cache AS new
            WHERE new.endpoint = old.endpoint AND new.target = old.target
              AND new.start_date <= old.start_date AND new.end_date >= old.end_date
              AND new.fetched_at > old.fetched_at AND new.fetched_at >= ?
              AND new.status_code = 200
        )
    """, (refreshed_since,))
    connection.commit()
    return cursor.rowcount
