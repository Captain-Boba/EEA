from __future__ import annotations

import json
import os
import logging
import re
import subprocess
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .full_refresh import run_scheduled_refresh
from .refresh_lifecycle import file_sha256
from .refresh_safety import FileRefreshLock, RefreshBusyError, safe_error

logger = logging.getLogger(__name__)


MONTHLY_REPORT_NAME = "MONTHLY_REFRESH.generated.json"
LOCK_FILE_NAME = ".monthly-refresh.lock"
DEFAULT_DAY_UTC = 2
DEFAULT_HOUR_UTC = 3
DEFAULT_POLL_SECONDS = 24 * 60 * 60
DEFAULT_RETRY_SECONDS = 6 * 60 * 60
DEFAULT_LOCK_STALE_SECONDS = 12 * 60 * 60


class MonthlyRefreshConfigurationError(ValueError):
    """A monthly refresh setting is malformed or unsafe."""


MonthlyRefreshBusyError = RefreshBusyError


def utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_switch(value: str | None) -> bool:
    if value is None:
        return False
    if value == "0":
        return False
    if value == "1":
        return True
    raise MonthlyRefreshConfigurationError("EEA_MONTHLY_REFRESH must be exactly 0 or 1")


def _parse_int(
    environment: dict[str, str],
    name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = environment.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise MonthlyRefreshConfigurationError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise MonthlyRefreshConfigurationError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class MonthlyRefreshConfig:
    enabled: bool
    day_utc: int
    hour_utc: int
    poll_seconds: int
    retry_seconds: int
    lock_stale_seconds: int
    from_year: int
    battery_energy_file: Path | None
    battery_power_file: Path | None

    @classmethod
    def from_environment(cls, environment: dict[str, str] | None = None) -> "MonthlyRefreshConfig":
        env = dict(os.environ if environment is None else environment)
        return cls(
            enabled=_parse_switch(env.get("EEA_MONTHLY_REFRESH")),
            day_utc=_parse_int(env, "EEA_MONTHLY_REFRESH_DAY_UTC", DEFAULT_DAY_UTC, 1, 28),
            hour_utc=_parse_int(env, "EEA_MONTHLY_REFRESH_HOUR_UTC", DEFAULT_HOUR_UTC, 0, 23),
            poll_seconds=_parse_int(env, "EEA_MONTHLY_REFRESH_POLL_SECONDS", DEFAULT_POLL_SECONDS, 60, 7 * 24 * 60 * 60),
            retry_seconds=_parse_int(env, "EEA_MONTHLY_REFRESH_RETRY_SECONDS", DEFAULT_RETRY_SECONDS, 60, 7 * 24 * 60 * 60),
            lock_stale_seconds=_parse_int(env, "EEA_MONTHLY_REFRESH_LOCK_STALE_SECONDS", DEFAULT_LOCK_STALE_SECONDS, 300, 7 * 24 * 60 * 60),
            from_year=_parse_int(env, "EEA_MONTHLY_REFRESH_FROM_YEAR", 2015, 2015, 2100),
            battery_energy_file=Path(env["EEA_BATTERY_ENERGY_FILE"]).resolve() if env.get("EEA_BATTERY_ENERGY_FILE") else None,
            battery_power_file=Path(env["EEA_BATTERY_POWER_FILE"]).resolve() if env.get("EEA_BATTERY_POWER_FILE") else None,
        )


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", prefix=".monthly-report-",
            dir=path.parent, delete=False,
        ) as output:
            temporary = Path(output.name)
            json.dump(payload, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return None
    return payload if isinstance(payload, dict) else None


def monthly_refresh_status(database_path: Path | str) -> dict[str, Any]:
    """Read-only operational status; never start an import or open SQLite."""
    report_path = Path(database_path).resolve().parent / "reports" / MONTHLY_REPORT_NAME
    report = _read_json(report_path)
    if report is None:
        return {"status": "unreadable_report" if report_path.exists() else "not_run"}
    result = {key: report.get(key) for key in (
        "status", "target_month", "started_at", "completed_at", "publication",
        "next_attempt_at", "cleanup_complete", "published_sha256",
    )}
    sources = report.get("sources", {})
    if not isinstance(sources, dict):
        return {"status": "unreadable_report"}
    result["sources"] = {name: source.get("status") for name, source in sources.items()
                         if isinstance(source, dict)}
    return result


def monthly_refresh_health(database_path: Path | str) -> dict[str, Any]:
    """Strict public allowlist: no errors, paths, credentials or source payloads."""
    status = monthly_refresh_status(database_path)
    state = status.get("status")
    result = {"last_run_status": state if state in (
        "not_run", "unreadable_report", "running", "success", "failed"
    ) else "unreadable_report"}
    month = status.get("target_month")
    if isinstance(month, str) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        result["target_month"] = month
    for key in ("completed_at", "next_attempt_at"):
        try:
            timestamp = datetime.fromisoformat(str(status.get(key)))
            if timestamp.tzinfo is not None:
                result[key] = timestamp.astimezone(UTC).isoformat()
        except ValueError:
            pass
    return result


class PersistentRefreshLock(FileRefreshLock):
    def __init__(self, path: Path, stale_seconds: int, now=utc_now):
        # Keep the old constructor compatible; ownership no longer expires by age.
        super().__init__(path)


class MonthlyRefreshRunner:
    """One isolated planned refresh with a persistent lease and compact report."""

    def __init__(
        self,
        database_path: Path | str,
        community_path: Path | str,
        config: MonthlyRefreshConfig,
        *,
        report_path: Path | str | None = None,
        now: Callable[[], datetime] = utc_now,
        refresh: Callable[..., dict[str, Any]] = run_scheduled_refresh,
    ) -> None:
        self.database_path = Path(database_path).resolve()
        self.community_path = Path(community_path).resolve()
        self.config = config
        self.now = now
        self.refresh = refresh
        self.report_path = Path(report_path).resolve() if report_path else (
            self.database_path.parent / "reports" / MONTHLY_REPORT_NAME
        ).resolve()
        self.lifecycle_path = self.report_path.with_name("MONTHLY_LIFECYCLE.generated.json")
        protected = {self.database_path, self.community_path}
        for database_file in (self.database_path, self.community_path):
            protected.update(Path(f"{database_file}{suffix}") for suffix in ("-wal", "-shm", "-journal"))
        protected.update(self.database_path.parent / name for name in (LOCK_FILE_NAME, ".atlas-refresh.lock"))
        if self.database_path == self.community_path or self.report_path in protected or self.lifecycle_path in protected:
            raise MonthlyRefreshConfigurationError("Monthly report/database paths collide with protected files")
        if self.report_path == self.lifecycle_path:
            raise MonthlyRefreshConfigurationError("Monthly and lifecycle reports must be separate files")
        self.lock = PersistentRefreshLock(
            self.database_path.parent / LOCK_FILE_NAME,
            config.lock_stale_seconds,
            now=now,
        )

    def run(self, *, target_month: str | None = None) -> dict[str, Any]:
        started = self.now()
        month = target_month or started.strftime("%Y-%m")
        self.lock.acquire()
        lifecycle_path = self.lifecycle_path
        before_hash = None
        lifecycle_initialized = False
        lifecycle = {}
        try:
            previous = _read_json(self.report_path) or {}
            completed = _read_json(lifecycle_path) or {}
            if (previous.get("status") == "running" and previous.get("attempt_id")
                    and completed.get("run_id") == previous["attempt_id"]
                    and completed.get("status") == "success"):
                # Recover a crash between lifecycle publication and monthly report.
                previous = {**completed, "target_month": previous["target_month"],
                            "sources": completed.get("refresh", {}),
                            "publication": "published", "next_attempt_at": None}
                _atomic_json_write(self.report_path, previous)
            if previous.get("status") == "success" and previous.get("target_month") == month:
                return previous
            before_hash = file_sha256(self.database_path)
            attempt_id = uuid.uuid4().hex
            _atomic_json_write(self.report_path, {
                "status": "running", "target_month": month,
                "attempt_id": attempt_id,
                "started_at": started.isoformat(), "publication": "not_published",
            })
            # Do not mistake a previous run's lifecycle report for this attempt.
            _atomic_json_write(lifecycle_path, {"status": "running", "started_at": started.isoformat()})
            lifecycle_initialized = True
            logger.info("Monthly refresh started: %s", month)
            lifecycle = self.refresh(
                self.database_path,
                from_year=self.config.from_year,
                battery_energy_file=self.config.battery_energy_file,
                battery_power_file=self.config.battery_power_file,
                report_path=lifecycle_path,
                community_path=self.community_path,
                run_id=attempt_id,
            )
            result = {
                **lifecycle,
                "target_month": month,
                "sources": lifecycle.get("refresh", {}),
                "scheduler": {
                    "day_utc": self.config.day_utc,
                    "hour_utc": self.config.hour_utc,
                    "mode": "planned_production_refresh",
                },
                "publication": "published" if lifecycle.get("status") == "success" else "not_published",
                "next_attempt_at": None,
            }
            _atomic_json_write(self.report_path, result)
            logger.info("Monthly refresh finished: %s (%s)", month, result["publication"])
            return result
        except Exception as exc:
            lifecycle = lifecycle or (_read_json(lifecycle_path) if lifecycle_initialized else {}) or {}
            source_results = getattr(exc, "source_results", lifecycle.get("refresh", {}))
            # A report-write error after successful publication must not trigger
            # another import or falsely claim the production database was untouched.
            published = lifecycle.get("status") == "success"
            result = {
                **lifecycle,
                "target_month": month,
                "sources": source_results,
                "status": "success" if published else "failed",
                "started_at": lifecycle.get("started_at", started.isoformat()),
                "completed_at": self.now().isoformat(),
                "previous_sha256": lifecycle.get("previous_sha256", before_hash),
                "current_sha256": file_sha256(self.database_path),
                "publication": "published" if published else "not_published",
                "error_type": type(exc).__name__,
                "error": safe_error(exc),
                "next_attempt_at": None if published else (self.now() + timedelta(seconds=self.config.retry_seconds)).isoformat(),
            }
            _atomic_json_write(self.report_path, result)
            logger.error("Monthly refresh error: %s (%s)", month, type(exc).__name__)
            raise
        finally:
            self.lock.release()


class MonthlyRefreshScheduler:
    """Opt-in controller that launches each actual refresh in a child process."""

    def __init__(
        self,
        database_path: Path | str,
        community_path: Path | str,
        config: MonthlyRefreshConfig,
        *,
        report_path: Path | str | None = None,
        now: Callable[[], datetime] = utc_now,
        popen: Callable[..., Any] = subprocess.Popen,
    ) -> None:
        self.database_path = Path(database_path).resolve()
        self.community_path = Path(community_path).resolve()
        self.config = config
        self.report_path = Path(report_path).resolve() if report_path else (
            self.database_path.parent / "reports" / MONTHLY_REPORT_NAME
        ).resolve()
        self.now = now
        self.popen = popen
        self._process: Any | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._launch_not_before: datetime | None = None

    def _report(self) -> dict[str, Any] | None:
        return _read_json(self.report_path)

    def _is_due(self, current: datetime, report: dict[str, Any] | None) -> bool:
        target_month = current.strftime("%Y-%m")
        if report and report.get("status") == "success" and report.get("target_month") == target_month:
            return False
        if report and report.get("status") == "failed":
            retry_at = report.get("next_attempt_at")
            try:
                if retry_at and current < datetime.fromisoformat(str(retry_at)).astimezone(UTC):
                    return False
            except (TypeError, ValueError):
                pass
        return (current.day, current.hour) >= (self.config.day_utc, self.config.hour_utc)

    def _command(self) -> list[str]:
        command = [
            sys.executable, "-m", "electricity_atlas.cli", "--db", str(self.database_path),
            "monthly-refresh-run", "--community-db", str(self.community_path),
            "--refresh-report", str(self.report_path),
        ]
        return command

    def check(self, current: datetime | None = None) -> bool:
        if not self.config.enabled:
            return False
        if self._process is not None:
            if self._process.poll() is None:
                return False
            self._process = None
        moment = (current or self.now()).astimezone(UTC)
        if self._launch_not_before and moment < self._launch_not_before:
            return False
        if not self._is_due(moment, self._report()):
            return False
        self._launch_not_before = moment + timedelta(seconds=self.config.retry_seconds)
        self._process = self.popen(self._command(), start_new_session=True)
        return True

    def _wait_seconds(self) -> float:
        # Wake at the schedule/retry deadline, not only 24 hours after startup.
        current = self.now().astimezone(UTC)
        scheduled = current.replace(day=self.config.day_utc, hour=self.config.hour_utc,
                                    minute=0, second=0, microsecond=0)
        report = self._report() or {}
        if report.get("status") == "success" and report.get("target_month") == current.strftime("%Y-%m"):
            scheduled = (scheduled.replace(day=28) + timedelta(days=4)).replace(day=self.config.day_utc)
        retry = report.get("next_attempt_at")
        if retry:
            try:
                scheduled = max(scheduled, datetime.fromisoformat(str(retry)).astimezone(UTC))
            except (ValueError, TypeError):
                pass
        if self._launch_not_before:
            scheduled = max(scheduled, self._launch_not_before)
        if self._process is not None:
            return min(60, self.config.poll_seconds)
        return min(self.config.poll_seconds, max(1, (scheduled - current).total_seconds()))

    def start(self) -> None:
        if not self.config.enabled or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="eea-monthly-refresh", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.check()
            except Exception as exc:
                # The parent never overwrites a worker's report (or its success).
                logger.error("Monthly scheduler could not launch worker: %s", type(exc).__name__)
                self._launch_not_before = self.now() + timedelta(seconds=self.config.retry_seconds)
            self._stop.wait(self._wait_seconds())

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
