import hashlib
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import MagicMock, patch

from electricity_atlas.db import database, read_database
from electricity_atlas.full_refresh import ScheduledRefreshCriticalError, run_scheduled_refresh
from electricity_atlas.monthly_refresh import (
    LOCK_FILE_NAME,
    MONTHLY_REPORT_NAME,
    MonthlyRefreshBusyError,
    MonthlyRefreshConfig,
    MonthlyRefreshConfigurationError,
    MonthlyRefreshRunner,
    MonthlyRefreshScheduler,
    PersistentRefreshLock,
)
from electricity_atlas.refresh_lifecycle import RefreshLifecycleError, run_refresh_lifecycle
from electricity_atlas.server import create_server


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeProcess:
    def __init__(self, return_code=None):
        self.return_code = return_code

    def poll(self):
        return self.return_code


class MonthlyRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.atlas = self.data / "atlas.sqlite3"
        self.community = self.data / "community.sqlite3"
        with database(self.atlas) as connection:
            connection.execute("CREATE TABLE refresh_fixture(value INTEGER NOT NULL)")
            connection.execute("INSERT INTO refresh_fixture VALUES (1)")
            connection.commit()
        with database(self.community) as connection:
            connection.execute("CREATE TABLE community_fixture(value INTEGER NOT NULL)")
            connection.execute("INSERT INTO community_fixture VALUES (7)")
            connection.commit()
        self.config = MonthlyRefreshConfig(
            enabled=True,
            day_utc=2,
            hour_utc=3,
            poll_seconds=60,
            retry_seconds=600,
            lock_stale_seconds=300,
            from_year=2015,
            battery_energy_file=None,
            battery_power_file=None,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_scheduler_is_disabled_by_default_and_rejects_invalid_environment(self):
        self.assertFalse(MonthlyRefreshConfig.from_environment({}).enabled)
        with self.assertRaises(MonthlyRefreshConfigurationError):
            MonthlyRefreshConfig.from_environment({"EEA_MONTHLY_REFRESH": "yes"})
        with self.assertRaises(MonthlyRefreshConfigurationError):
            MonthlyRefreshConfig.from_environment({"EEA_MONTHLY_REFRESH": "1", "EEA_MONTHLY_REFRESH_DAY_UTC": "31"})

    def test_due_month_starts_once_and_a_successful_report_blocks_a_second_run(self):
        now = datetime(2026, 9, 2, 3, tzinfo=UTC)
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        calls = []

        def popen(command, **kwargs):
            calls.append((command, kwargs))
            report.parent.mkdir(exist_ok=True)
            report.write_text(json.dumps({"status": "success", "target_month": "2026-09"}), encoding="utf-8")
            return FakeProcess(0)

        scheduler = MonthlyRefreshScheduler(self.atlas, self.community, self.config, now=lambda: now, popen=popen)
        self.assertTrue(scheduler.check(now))
        self.assertFalse(scheduler.check(now))
        self.assertEqual(len(calls), 1)
        self.assertIn("monthly-refresh-run", calls[0][0])
        self.assertTrue(calls[0][1]["start_new_session"])

    def test_missed_month_is_caught_up_and_failed_month_retries_after_backoff(self):
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir(exist_ok=True)
        report.write_text(json.dumps({"status": "success", "target_month": "2026-08"}), encoding="utf-8")
        calls = []
        scheduler = MonthlyRefreshScheduler(
            self.atlas, self.community, self.config,
            now=lambda: datetime(2026, 9, 1, 1, tzinfo=UTC),
            popen=lambda *args, **kwargs: calls.append(args) or FakeProcess(None),
        )
        self.assertTrue(scheduler.check())
        scheduler._process = None
        report.write_text(json.dumps({
            "status": "failed", "target_month": "2026-09",
            "next_attempt_at": "2026-09-01T05:00:00+00:00",
        }), encoding="utf-8")
        self.assertFalse(scheduler.check(datetime(2026, 9, 1, 4, tzinfo=UTC)))
        self.assertTrue(scheduler.check(datetime(2026, 9, 2, 3, tzinfo=UTC)))
        self.assertEqual(len(calls), 2)

    def test_persistent_lock_rejects_parallel_owner_and_recovers_an_orphan_without_killing_processes(self):
        now = datetime(2026, 9, 2, 3, tzinfo=UTC)
        first = PersistentRefreshLock(self.data / LOCK_FILE_NAME, 300, now=lambda: now)
        first.acquire()
        second = PersistentRefreshLock(self.data / LOCK_FILE_NAME, 300, now=lambda: now)
        with self.assertRaises(MonthlyRefreshBusyError):
            second.acquire()
        first.release()
        (self.data / LOCK_FILE_NAME).write_text(json.dumps({
            "token": "orphan", "pid": 99999999, "hostname": first.hostname,
            "started_at": (now - timedelta(hours=1)).isoformat(),
        }), encoding="utf-8")
        recovered = PersistentRefreshLock(self.data / LOCK_FILE_NAME, 300, now=lambda: now)
        recovered.acquire()
        self.assertTrue((self.data / LOCK_FILE_NAME).exists())
        recovered.release()
        self.assertFalse((self.data / LOCK_FILE_NAME).exists())

    def test_runner_preserves_community_and_old_atlas_on_critical_failure_then_allows_later_retry(self):
        community_wal = Path(f"{self.community}-wal")
        community_shm = Path(f"{self.community}-shm")
        community_wal.write_bytes(b"community wal sentinel")
        community_shm.write_bytes(b"community shm sentinel")
        before = {path: digest(path) for path in (self.atlas, self.community, community_wal, community_shm)}
        clock = datetime(2026, 9, 2, 3, tzinfo=UTC)

        def fail_refresh(*_args, **_kwargs):
            raise ScheduledRefreshCriticalError(
                {"ember": {"status": "failed_critical", "error": "critical fixture failure"}},
                RefreshLifecycleError("critical Ember fixture failure"),
            )

        failed = MonthlyRefreshRunner(
            self.atlas, self.community, self.config, now=lambda: clock, refresh=fail_refresh,
        )
        with self.assertRaises(ScheduledRefreshCriticalError):
            failed.run()
        self.assertEqual(digest(self.atlas), before[self.atlas])
        self.assertEqual(digest(self.community), before[self.community])
        self.assertEqual(digest(community_wal), before[community_wal])
        self.assertEqual(digest(community_shm), before[community_shm])
        report = json.loads((self.data / "reports" / MONTHLY_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["sources"]["ember"]["status"], "failed_critical")
        self.assertEqual(report["publication"], "not_published")
        self.assertEqual(report["next_attempt_at"], "2026-09-02T03:10:00+00:00")

        def successful_refresh(database_path, **kwargs):
            self.assertEqual(database_path, self.atlas)
            self.assertEqual(kwargs["community_path"], self.community)
            return {"status": "success", "refresh": {"ember": {"status": "refreshed"}}}

        retried = MonthlyRefreshRunner(
            self.atlas, self.community, self.config, now=lambda: clock, refresh=successful_refresh,
        ).run()
        self.assertEqual(retried["status"], "success")
        self.assertEqual(retried["sources"]["ember"]["status"], "refreshed")

    def test_cli_worker_uses_the_planned_runner_without_enabling_the_background_scheduler(self):
        from electricity_atlas.cli import main

        expected = {"status": "success", "published_sha256": "fixture"}
        with patch("electricity_atlas.cli.MonthlyRefreshRunner") as runner, patch.dict(
            os.environ, {"EEA_MONTHLY_REFRESH": "0"}, clear=False
        ):
            runner.return_value.run.return_value = expected
            self.assertEqual(main([
                "--db", str(self.atlas), "monthly-refresh-run",
                "--community-db", str(self.community),
            ]), 0)
        runner.assert_called_once()
        runner.return_value.run.assert_called_once_with()

    @unittest.skipIf(os.name == "nt", "Windows replaces an open SQLite file by design only after requests end")
    def test_linux_read_connection_can_finish_while_lifecycle_publishes_candidate(self):
        def validate(path):
            with sqlite3.connect(path) as connection:
                return {"value": connection.execute("SELECT value FROM refresh_fixture").fetchone()[0]}

        reader = sqlite3.connect(f"file:{self.atlas.resolve().as_posix()}?mode=ro", uri=True)
        try:
            self.assertEqual(reader.execute("SELECT value FROM refresh_fixture").fetchone()[0], 1)

            def update(candidate):
                with sqlite3.connect(candidate) as connection:
                    connection.execute("UPDATE refresh_fixture SET value=2")
                return {"sources": {"fixture": "refreshed"}}

            result = run_refresh_lifecycle(self.atlas, update, validate_action=validate, community_path=self.community)
            self.assertEqual(result["status"], "success")
            self.assertEqual(reader.execute("SELECT value FROM refresh_fixture").fetchone()[0], 1)
        finally:
            reader.close()
        with read_database(self.atlas) as fresh:
            self.assertEqual(fresh.execute("SELECT value FROM refresh_fixture").fetchone()[0], 2)

    @unittest.skipIf(os.name == "nt", "Windows denies SQLite replacement while the local threaded server owns a recent handle")
    def test_http_server_stays_reachable_before_and_after_a_fixture_candidate_exchange(self):
        server = create_server(self.atlas, port=0, community_path=self.community)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/api/health", timeout=5) as response:
                self.assertEqual(json.load(response)["status"], "ok")

            def validate(path):
                with sqlite3.connect(path) as connection:
                    return {"value": connection.execute("SELECT value FROM refresh_fixture").fetchone()[0]}

            def update(candidate):
                with sqlite3.connect(candidate) as connection:
                    connection.execute("UPDATE refresh_fixture SET value=2")
                return {"fixture": {"status": "refreshed"}}

            result = run_refresh_lifecycle(
                self.atlas, update, validate_action=validate, community_path=self.community,
            )
            self.assertEqual(result["status"], "success")
            with urlopen(base + "/api/health", timeout=5) as response:
                self.assertEqual(json.load(response)["status"], "ok")
            with urlopen(base + "/api/countries", timeout=5) as response:
                self.assertEqual(len(json.load(response)), 31)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


class ScheduledRefreshSourcePolicyTests(unittest.TestCase):
    def test_core_sources_are_strict_battery_without_files_is_preserved_and_jrc_storage_is_not_called(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.sqlite3"
            events = []

            def lifecycle(_database, action, **_kwargs):
                return {"status": "success", "refresh": action(candidate)}

            ember = MagicMock()
            ember.import_range.side_effect = lambda code, *_args: events.append(f"ember:{code}") or {"successes": [code], "errors": 0}
            price = MagicMock()
            price.import_prices.side_effect = lambda: events.append("prices") or {"rows": 1}
            core = MagicMock()
            core.import_years.side_effect = lambda *_args: events.append("core") or {"rows": 1}
            supplement = MagicMock()
            supplement.import_years.side_effect = lambda *_args: events.append("supplement") or {"rows": 1}
            hydro = MagicMock()
            hydro.import_release.side_effect = lambda: events.append("hydro") or {"rows": 1}
            ghg = MagicMock()
            ghg.import_url.side_effect = lambda: events.append("ghg") or {"rows": 1}
            with patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle), patch(
                "electricity_atlas.full_refresh.load_ember_api_key"
            ), patch("electricity_atlas.full_refresh.EmberImporter", return_value=ember), patch(
                "electricity_atlas.full_refresh.WholesalePriceImporter", return_value=price
            ), patch("electricity_atlas.full_refresh.EurostatImporter", return_value=core), patch(
                "electricity_atlas.full_refresh.EurostatSupplementImporter", return_value=supplement
            ), patch("electricity_atlas.full_refresh.JrcHydroImporter", return_value=hydro), patch(
                "electricity_atlas.full_refresh.EeaGhgImporter", return_value=ghg), patch(
                "electricity_atlas.full_refresh.BatteryChartsImporter"
            ) as battery, patch("electricity_atlas.full_refresh.OnlineStorageUpdater") as storage:
                result = run_scheduled_refresh(root / "atlas.sqlite3", to_year=2026)
            self.assertEqual(result["status"], "success")
            policy = result["refresh"]
            self.assertEqual(policy["battery_charts"]["status"], "preserved_controlled_input")
            self.assertEqual(policy["jrc_storage"]["status"], "preserved")
            battery.assert_not_called()
            storage.assert_not_called()
            self.assertEqual(events[0:3], ["ember:AT", "ember:BE", "ember:BG"])
            self.assertEqual(events[-5:], ["prices", "core", "supplement", "hydro", "ghg"])
            self.assertIn("ghg", events)

    def test_optional_source_error_is_reported_and_critical_source_error_aborts_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.sqlite3"

            def lifecycle(_database, action, **_kwargs):
                return action(candidate)

            ember = MagicMock()
            ember.import_range.return_value = {"successes": ["ok"], "errors": 0}
            with patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle), patch(
                "electricity_atlas.full_refresh.load_ember_api_key"
            ), patch("electricity_atlas.full_refresh.EmberImporter", return_value=ember), patch(
                "electricity_atlas.full_refresh.WholesalePriceImporter"
            ) as prices, patch("electricity_atlas.full_refresh.EurostatImporter") as core, patch(
                "electricity_atlas.full_refresh.EurostatSupplementImporter"
            ) as supplement, patch("electricity_atlas.full_refresh.JrcHydroImporter") as hydro, patch(
                "electricity_atlas.full_refresh.EeaGhgImporter") as ghg:
                prices.return_value.import_prices.return_value = {"rows": 1}
                core.return_value.import_years.return_value = {"rows": 1}
                supplement.return_value.import_years.return_value = {"rows": 1}
                hydro.return_value.import_release.side_effect = RuntimeError("temporary hydro fixture failure")
                ghg.return_value.import_url.return_value = {"rows": 1}
                result = run_scheduled_refresh(root / "atlas.sqlite3", to_year=2026)
            self.assertEqual(result["jrc_hydro"]["status"], "failed_optional")

            with patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle), patch(
                "electricity_atlas.full_refresh.load_ember_api_key"
            ), patch("electricity_atlas.full_refresh.EmberImporter", return_value=ember), patch(
                "electricity_atlas.full_refresh.WholesalePriceImporter"
            ) as prices:
                prices.return_value.import_prices.side_effect = RuntimeError("price fixture failure")
                with self.assertRaisesRegex(RuntimeError, "price fixture failure"):
                    run_scheduled_refresh(root / "atlas.sqlite3", to_year=2026)


if __name__ == "__main__":
    unittest.main()
