from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .full_refresh import run_scheduled_refresh
from .refresh_lifecycle import RefreshLifecycleError, file_sha256


MONTHLY_REPORT_NAME = "MONTHLY_REFRESH.generated.json"
LOCK_FILE_NAME = ".monthly-refresh.lock"
DEFAULT_DAY_UTC = 2
DEFAULT_HOUR_UTC = 3
DEFAULT_POLL_SECONDS = 24 * 60 * 60
DEFAULT_RETRY_SECONDS = 6 * 60 * 60
DEFAULT_LOCK_STALE_SECONDS = 12 * 60 * 60


class MonthlyRefreshConfigurationError(ValueError):
    """A monthly refresh setting is malformed or unsafe."""


class MonthlyRefreshBusyError(RuntimeError):
    """Another persisted monthly refresh lease is still active."""


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
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@dataclass
class PersistentRefreshLock:
    path: Path
    stale_seconds: int
    now: Callable[[], datetime] = utc_now
    hostname: str = socket.gethostname()
    token: str | None = None

    def _owner(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "pid": os.getpid(),
            "hostname": self.hostname,
            "started_at": self.now().isoformat(),
        }

    def _is_stale(self, owner: dict[str, Any]) -> bool:
        started_raw = owner.get("started_at")
        try:
            started = datetime.fromisoformat(str(started_raw))
            if started.tzinfo is None:
                return True
            expired = self.now() - started.astimezone(UTC) > timedelta(seconds=self.stale_seconds)
        except (TypeError, ValueError):
            return True
        if owner.get("hostname") == self.hostname:
            pid = owner.get("pid")
            if isinstance(pid, int) and pid > 0:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return True
                except PermissionError:
                    return False
                except OSError:
                    # Windows reports an invalid non-existent PID as a generic
                    # OSError.  Keep an unexpired lease in that ambiguous case.
                    return expired
                else:
                    return False
        return expired

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.token = uuid.uuid4().hex
        for attempt in range(2):
            try:
                descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                existing = _read_json(self.path) or {}
                if attempt == 0 and self._is_stale(existing):
                    # The lease has expired or its same-host owner vanished.  No
                    # process is terminated; a replacement token is simply allowed.
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                self.token = None
                raise MonthlyRefreshBusyError("A monthly refresh lease is already active")
            else:
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                        json.dump(self._owner(), output, ensure_ascii=False, allow_nan=False)
                        output.write("\n")
                except Exception:
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    raise
                return
        self.token = None
        raise MonthlyRefreshBusyError("A monthly refresh lease is already active")

    def release(self) -> None:
        if self.token is None:
            return
        owner = _read_json(self.path)
        if owner and owner.get("token") == self.token:
            self.path.unlink(missing_ok=True)
        self.token = None


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
        self.lock = PersistentRefreshLock(
            self.database_path.parent / LOCK_FILE_NAME,
            config.lock_stale_seconds,
            now=now,
        )

    def run(self, *, target_month: str | None = None) -> dict[str, Any]:
        started = self.now()
        month = target_month or started.strftime("%Y-%m")
        before_hash = file_sha256(self.database_path)
        self.lock.acquire()
        try:
            lifecycle = self.refresh(
                self.database_path,
                from_year=self.config.from_year,
                battery_energy_file=self.config.battery_energy_file,
                battery_power_file=self.config.battery_power_file,
                report_path=self.report_path,
                community_path=self.community_path,
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
            return result
        except Exception as exc:
            lifecycle = _read_json(self.report_path) or {}
            source_results = getattr(exc, "source_results", lifecycle.get("refresh", {}))
            result = {
                **lifecycle,
                "target_month": month,
                "sources": source_results,
                "status": "failed",
                "started_at": lifecycle.get("started_at", started.isoformat()),
                "completed_at": self.now().isoformat(),
                "previous_sha256": lifecycle.get("previous_sha256", before_hash),
                "current_sha256": file_sha256(self.database_path),
                "publication": "not_published",
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
                "next_attempt_at": (self.now() + timedelta(seconds=self.config.retry_seconds)).isoformat(),
            }
            _atomic_json_write(self.report_path, result)
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
        if report and isinstance(report.get("target_month"), str) and report["target_month"] < target_month:
            return True
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
        if not self._is_due(moment, self._report()):
            return False
        self._process = self.popen(self._command(), start_new_session=True)
        return True

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
                _atomic_json_write(self.report_path, {
                    "status": "failed",
                    "target_month": self.now().strftime("%Y-%m"),
                    "publication": "not_published",
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:1000],
                    "next_attempt_at": (self.now() + timedelta(seconds=self.config.retry_seconds)).isoformat(),
                })
            self._stop.wait(self.config.poll_seconds)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
