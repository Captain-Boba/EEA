from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import COUNTRIES


WORK_DIRECTORY_NAME = ".refresh-work"
DEFAULT_REPORT_NAME = "REFRESH.generated.json"
SQLITE_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")


class RefreshLifecycleError(RuntimeError):
    """A controlled full-refresh failure with the production database protected."""


class RefreshLockError(RefreshLifecycleError):
    """The production database cannot be safely replaced while it is in use."""


class RefreshPathError(RefreshLifecycleError):
    """A refresh path escaped its dedicated per-run working directory."""


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_atlas_database(path: Path | str) -> dict[str, Any]:
    database_path = Path(path).resolve()
    connection = sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RefreshLifecycleError(f"SQLite integrity check failed: {integrity}")
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        required_tables = {"api_cache", "source_cache", "period_observation"}
        missing_tables = sorted(required_tables - tables)
        if missing_tables:
            raise RefreshLifecycleError(
                f"Atlas candidate is missing required tables: {', '.join(missing_tables)}"
            )
        countries = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT country_code FROM period_observation"
            )
        }
        expected_countries = set(COUNTRIES)
        if countries != expected_countries:
            missing = sorted(expected_countries - countries)
            unexpected = sorted(countries - expected_countries)
            raise RefreshLifecycleError(
                f"Atlas country set mismatch; missing={missing}, unexpected={unexpected}"
            )
        primary_key = (
            "country_code,period_start,period_end,granularity,source,"
            "source_endpoint,source_series,metric"
        )
        duplicate_groups = connection.execute(
            f"SELECT COUNT(*) FROM ("
            f"SELECT {primary_key}, COUNT(*) AS row_count FROM period_observation "
            f"GROUP BY {primary_key} HAVING row_count > 1)"
        ).fetchone()[0]
        null_required_rows = connection.execute(
            """SELECT COUNT(*) FROM period_observation
               WHERE country_code IS NULL OR period_start IS NULL OR period_end IS NULL
                  OR granularity IS NULL OR source IS NULL OR source_endpoint IS NULL
                  OR source_series IS NULL OR metric IS NULL OR value IS NULL
                  OR unit IS NULL OR quality_status IS NULL"""
        ).fetchone()[0]
        if duplicate_groups or null_required_rows:
            raise RefreshLifecycleError(
                "Atlas candidate contains duplicate keys or null required values: "
                f"duplicates={duplicate_groups}, null_required={null_required_rows}"
            )
        row_count = connection.execute(
            "SELECT COUNT(*) FROM period_observation"
        ).fetchone()[0]
        source_count = connection.execute(
            "SELECT COUNT(DISTINCT source) FROM period_observation"
        ).fetchone()[0]
        return {
            "integrity": integrity,
            "rows": row_count,
            "countries": len(countries),
            "sources": source_count,
            "duplicate_groups": duplicate_groups,
            "null_required_rows": null_required_rows,
        }
    finally:
        connection.close()


def _safe_run_id(run_id: str | None) -> str:
    if run_id is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        return f"{timestamp}-{uuid.uuid4().hex[:8]}"
    if not RUN_ID_PATTERN.fullmatch(run_id) or run_id in {".", ".."}:
        raise RefreshPathError(f"Unsafe refresh run id: {run_id!r}")
    return run_id


def _require_inside(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RefreshPathError(
            f"Refresh path escapes the run directory: {resolved_path}"
        ) from exc
    if resolved_path == resolved_root:
        raise RefreshPathError("A refresh file path cannot be the run directory itself")
    return resolved_path


def _windows_exclusive_open_check(path: Path) -> None:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    delete_access = 0x00010000
    open_existing = 3
    file_attribute_normal = 0x00000080
    handle = create_file(
        str(path),
        delete_access,
        0,
        None,
        open_existing,
        file_attribute_normal,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        error = ctypes.get_last_error()
        raise RefreshLockError(
            f"Database replacement preflight failed for {path}: "
            f"Windows file lock or access error {error}"
        )
    close_handle(handle)


def assert_database_replaceable(path: Path | str) -> None:
    database_path = Path(path).resolve()
    if not database_path.is_file():
        raise RefreshLifecycleError(f"Atlas database does not exist: {database_path}")
    probe_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".refresh-preflight-",
            dir=database_path.parent,
            delete=False,
        ) as probe:
            probe_path = Path(probe.name)
        probe_path.unlink()
        probe_path = None
    except OSError as exc:
        raise RefreshLockError(
            f"Atlas directory is not safely writable for replacement: {database_path.parent}"
        ) from exc
    finally:
        if probe_path is not None and probe_path.exists():
            probe_path.unlink()

    paths = [database_path]
    paths.extend(
        sidecar
        for suffix in SQLITE_SIDECAR_SUFFIXES
        if (sidecar := Path(f"{database_path}{suffix}")).exists()
    )
    if os.name == "nt":
        for candidate in paths:
            _windows_exclusive_open_check(candidate)
    else:
        for candidate in paths:
            descriptor = os.open(candidate, os.O_RDONLY)
            os.close(descriptor)


def _sqlite_backup(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RefreshPathError(f"Refresh backup target already exists: {destination}")
    source_connection = sqlite3.connect(
        f"file:{source.resolve().as_posix()}?mode=ro", uri=True
    )
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.execute("PRAGMA query_only = ON")
        source_connection.backup(destination_connection)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()


def _checkpoint_candidate(candidate: Path) -> None:
    connection = sqlite3.connect(candidate)
    try:
        busy, remaining, _checkpointed = connection.execute(
            "PRAGMA wal_checkpoint(TRUNCATE)"
        ).fetchone()
        if busy or remaining:
            raise RefreshLifecycleError(
                "Candidate WAL could not be fully checkpointed; "
                "a refresh connection may still be open"
            )
    finally:
        connection.close()


def _sidecar_paths(database_path: Path) -> list[Path]:
    return [Path(f"{database_path}{suffix}") for suffix in SQLITE_SIDECAR_SUFFIXES]


def _remove_production_sidecars(database_path: Path) -> list[dict[str, Any]]:
    removed: list[dict[str, Any]] = []
    for sidecar in _sidecar_paths(database_path):
        if sidecar.exists():
            removed.append({"path": str(sidecar), "size": sidecar.stat().st_size})
            sidecar.unlink()
    return removed


def _remove_new_empty_sidecars(
    database_path: Path,
    initial_sidecars: dict[str, dict[str, Any]],
) -> None:
    try:
        assert_database_replaceable(database_path)
    except RefreshLockError:
        return
    for sidecar in _sidecar_paths(database_path):
        initial = initial_sidecars[str(sidecar)]
        if initial["exists"] or not sidecar.exists():
            continue
        if sidecar.name.endswith("-shm") or sidecar.stat().st_size == 0:
            sidecar.unlink()


def _cleanup_run_directory(
    run_directory: Path,
    work_root: Path,
    database_files: list[Path],
) -> None:
    known_files: set[Path] = set()
    for database_file in database_files:
        known_files.add(_require_inside(database_file, run_directory))
        known_files.update(
            _require_inside(sidecar, run_directory)
            for sidecar in _sidecar_paths(database_file)
        )
    remaining = list(run_directory.iterdir()) if run_directory.exists() else []
    unexpected = [
        path
        for path in remaining
        if _require_inside(path, run_directory) not in known_files
    ]
    if unexpected:
        raise RefreshPathError(
            "Refusing broad cleanup because unexpected refresh artifacts remain: "
            + ", ".join(str(path) for path in unexpected)
        )
    rollback = database_files[0].resolve(strict=False)
    deletion_order = sorted(
        known_files,
        key=lambda path: (
            path == rollback,
            path.name == rollback.name,
            not path.name.endswith(SQLITE_SIDECAR_SUFFIXES),
            path.name,
        ),
    )
    for path in deletion_order:
        if path.exists():
            if not path.is_file():
                raise RefreshPathError(f"Unexpected non-file refresh artifact: {path}")
            path.unlink()
    remaining = list(run_directory.iterdir()) if run_directory.exists() else []
    if remaining:
        raise RefreshPathError(
            "Refusing broad cleanup because unexpected refresh artifacts remain: "
            + ", ".join(str(path) for path in remaining)
        )
    if run_directory.exists():
        run_directory.rmdir()
    if work_root.exists() and not any(work_root.iterdir()):
        work_root.rmdir()


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix=".refresh-report-",
            dir=path.parent,
            delete=False,
        ) as output:
            temporary = Path(output.name)
            json.dump(payload, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def run_refresh_lifecycle(
    database_path: Path | str,
    refresh_action: Callable[[Path], dict[str, Any] | None],
    *,
    validate_action: Callable[[Path], dict[str, Any]] = validate_atlas_database,
    report_path: Path | str | None = None,
    community_path: Path | str | None = None,
    run_id: str | None = None,
    replace_file: Callable[[Path, Path], None] = os.replace,
) -> dict[str, Any]:
    database_file = Path(database_path).resolve()
    data_directory = database_file.parent
    work_root = (data_directory / WORK_DIRECTORY_NAME).resolve(strict=False)
    if work_root.parent != data_directory:
        raise RefreshPathError(f"Unsafe refresh root: {work_root}")
    selected_run_id = _safe_run_id(run_id)
    run_directory = (work_root / selected_run_id).resolve(strict=False)
    if run_directory.parent != work_root:
        raise RefreshPathError(f"Unsafe refresh run directory: {run_directory}")
    rollback = _require_inside(run_directory / "rollback.sqlite3", run_directory)
    candidate = _require_inside(run_directory / "candidate.sqlite3", run_directory)
    restore = _require_inside(run_directory / "restore.sqlite3", run_directory)
    report_file = (
        Path(report_path).resolve()
        if report_path is not None
        else (data_directory / "reports" / DEFAULT_REPORT_NAME).resolve()
    )
    community_file = (
        Path(community_path).resolve()
        if community_path is not None
        else (data_directory / "community.sqlite3").resolve()
    )
    protected_paths = {database_file, community_file}
    if report_file in protected_paths:
        raise RefreshPathError("Refresh report path collides with a protected database")
    if database_file == community_file:
        raise RefreshPathError("Atlas and community databases must be different files")

    started_at = datetime.now(UTC).isoformat()
    phase = "preflight"
    original_hash = file_sha256(database_file) if database_file.exists() else None
    initial_sidecars = {
        str(sidecar): {
            "exists": sidecar.exists(),
            "size": sidecar.stat().st_size if sidecar.exists() else None,
        }
        for sidecar in _sidecar_paths(database_file)
    }
    community_before = file_sha256(community_file) if community_file.exists() else None
    candidate_hash: str | None = None
    rollback_hash: str | None = None
    refresh_result: dict[str, Any] | None = None
    candidate_validation: dict[str, Any] | None = None
    published_validation: dict[str, Any] | None = None
    exchange_started = False
    removed_sidecars: list[dict[str, Any]] = []
    restored = False
    cleanup_complete = False

    try:
        assert_database_replaceable(database_file)
        phase = "prepare-work-directory"
        run_directory.mkdir(parents=True, exist_ok=False)
        if run_directory.stat().st_dev != database_file.stat().st_dev:
            raise RefreshPathError("Refresh work directory is not on the Atlas database volume")

        phase = "backup"
        _sqlite_backup(database_file, rollback)
        rollback_hash = file_sha256(rollback)
        shutil.copy2(rollback, candidate)

        phase = "refresh"
        refresh_result = refresh_action(candidate) or {}

        phase = "checkpoint-candidate"
        _checkpoint_candidate(candidate)

        phase = "validate-candidate"
        candidate_validation = validate_action(candidate)
        candidate_hash = file_sha256(candidate)

        phase = "publish-preflight"
        assert_database_replaceable(database_file)
        exchange_started = True
        removed_sidecars = _remove_production_sidecars(database_file)

        phase = "publish"
        replace_file(candidate, database_file)

        phase = "validate-published"
        published_validation = validate_action(database_file)
        published_hash = file_sha256(database_file)
        if published_hash != candidate_hash:
            raise RefreshLifecycleError(
                "Published database hash does not match the validated candidate"
            )

        phase = "cleanup-published-sidecars"
        assert_database_replaceable(database_file)
        _remove_production_sidecars(database_file)

        phase = "cleanup"
        _cleanup_run_directory(
            run_directory,
            work_root,
            [rollback, candidate, restore],
        )
        cleanup_complete = True
        community_after = file_sha256(community_file) if community_file.exists() else None
        result = {
            "status": "success",
            "phase": "complete",
            "run_id": selected_run_id,
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "database": str(database_file),
            "previous_sha256": original_hash,
            "candidate_sha256": candidate_hash,
            "published_sha256": published_hash,
            "rollback_sha256": rollback_hash,
            "refresh": refresh_result,
            "candidate_validation": candidate_validation,
            "published_validation": published_validation,
            "community": {
                "path": str(community_file),
                "before_sha256": community_before,
                "after_sha256": community_after,
                "unchanged": community_before == community_after,
            },
            "cleanup_complete": cleanup_complete,
            "work_directory_retained": False,
        }
        _write_report(report_file, result)
        return result
    except Exception as exc:
        failure_phase = phase
        restore_error: str | None = None
        if exchange_started and rollback.exists():
            try:
                current_hash = file_sha256(database_file) if database_file.exists() else None
                removed_committed_sidecar = any(
                    item["size"] > 0
                    and item["path"].endswith(("-wal", "-journal"))
                    for item in removed_sidecars
                )
                if current_hash != original_hash or removed_committed_sidecar:
                    shutil.copy2(rollback, restore)
                    if database_file.exists():
                        assert_database_replaceable(database_file)
                        _remove_production_sidecars(database_file)
                    replace_file(restore, database_file)
                    validate_action(database_file)
                    assert_database_replaceable(database_file)
                    _remove_production_sidecars(database_file)
                    restored = True
            except Exception as restore_exc:
                restore_error = f"{type(restore_exc).__name__}: {restore_exc}"

        if restore_error is None and run_directory.exists():
            try:
                _cleanup_run_directory(
                    run_directory,
                    work_root,
                    [rollback, candidate, restore],
                )
                cleanup_complete = True
            except Exception as cleanup_exc:
                restore_error = f"cleanup: {type(cleanup_exc).__name__}: {cleanup_exc}"

        if not exchange_started:
            _remove_new_empty_sidecars(database_file, initial_sidecars)

        community_after = file_sha256(community_file) if community_file.exists() else None
        failure = {
            "status": "failed",
            "phase": failure_phase,
            "run_id": selected_run_id,
            "started_at": started_at,
            "completed_at": datetime.now(UTC).isoformat(),
            "database": str(database_file),
            "previous_sha256": original_hash,
            "current_sha256": file_sha256(database_file) if database_file.exists() else None,
            "candidate_sha256": candidate_hash,
            "rollback_sha256": rollback_hash,
            "error_type": type(exc).__name__,
            "error": str(exc)[:2000],
            "restored": restored,
            "restore_or_cleanup_error": restore_error,
            "community": {
                "path": str(community_file),
                "before_sha256": community_before,
                "after_sha256": community_after,
                "unchanged": community_before == community_after,
            },
            "cleanup_complete": cleanup_complete,
            "work_directory_retained": run_directory.exists(),
        }
        try:
            _write_report(report_file, failure)
        except Exception:
            pass
        message = (
            f"Refresh failed during {failure_phase}: {type(exc).__name__}: {exc}. "
            f"Report: {report_file}"
        )
        if restore_error is not None:
            message += f". Restore/cleanup issue: {restore_error}"
        error_type = RefreshLockError if isinstance(exc, RefreshLockError) else RefreshLifecycleError
        raise error_type(message) from exc
