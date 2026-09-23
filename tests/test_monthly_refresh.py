import hashlib
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from contextlib import ExitStack
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
    PUBLIC_REFRESH_SOURCES,
    monthly_refresh_health,
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
        self.assertFalse(scheduler.check())
        self.assertTrue(scheduler.check(datetime(2026, 9, 2, 3, tzinfo=UTC)))
        scheduler._process = None
        report.write_text(json.dumps({
            "status": "failed", "target_month": "2026-09",
            "next_attempt_at": "2026-09-02T05:00:00+00:00",
        }), encoding="utf-8")
        self.assertFalse(scheduler.check(datetime(2026, 9, 2, 4, tzinfo=UTC)))
        self.assertTrue(scheduler.check(datetime(2026, 9, 2, 5, tzinfo=UTC)))
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
            "token": "orphan", "pid": 99999999, "hostname": "old-container",
            "started_at": (now - timedelta(hours=1)).isoformat(),
        }), encoding="utf-8")
        recovered = PersistentRefreshLock(self.data / LOCK_FILE_NAME, 300, now=lambda: now)
        recovered.acquire()
        self.assertTrue((self.data / LOCK_FILE_NAME).exists())
        recovered.release()
        self.assertTrue((self.data / LOCK_FILE_NAME).exists())

    def test_schedule_waits_until_exact_deadline_and_retry_instead_of_next_daily_poll(self):
        from dataclasses import replace
        now = datetime(2026, 9, 2, 2, 59, tzinfo=UTC)
        scheduler = MonthlyRefreshScheduler(self.atlas, self.community,
            replace(self.config, poll_seconds=86400), now=lambda: now)
        self.assertEqual(scheduler._wait_seconds(), 60)
        now = datetime(2026, 9, 2, 3, tzinfo=UTC)
        scheduler.report_path.parent.mkdir(exist_ok=True)
        scheduler.report_path.write_text(json.dumps({"status": "failed", "target_month": "2026-09",
            "next_attempt_at": "2026-09-02T09:00:00+00:00"}), encoding="utf-8")
        self.assertEqual(scheduler._wait_seconds(), 21600)

    def test_dead_child_without_report_is_backed_off(self):
        now = datetime(2026, 9, 2, 3, tzinfo=UTC)
        scheduler = MonthlyRefreshScheduler(self.atlas, self.community, self.config,
            now=lambda: now, popen=lambda *a, **k: FakeProcess(1))
        self.assertTrue(scheduler.check())
        self.assertFalse(scheduler.check(now + timedelta(seconds=60)))
        self.assertTrue(scheduler.check(now + timedelta(seconds=600)))

    def test_worker_checks_month_again_under_lock(self):
        refresh = MagicMock(return_value={"status": "success", "refresh": {}})
        runner = MonthlyRefreshRunner(self.atlas, self.community, self.config,
            now=lambda: datetime(2026, 9, 2, 3, tzinfo=UTC), refresh=refresh)
        self.assertEqual(runner.run()["status"], "success")
        self.assertEqual(runner.run()["status"], "success")
        refresh.assert_called_once()

    def test_worker_recovers_published_lifecycle_without_reimporting(self):
        refresh = MagicMock()
        runner = MonthlyRefreshRunner(self.atlas, self.community, self.config,
            now=lambda: datetime(2026, 9, 2, 3, tzinfo=UTC), refresh=refresh)
        runner.report_path.parent.mkdir()
        runner.report_path.write_text(json.dumps({"status": "running", "attempt_id": "fixture-run",
            "target_month": "2026-09"}), encoding="utf-8")
        runner.lifecycle_path.write_text(json.dumps({"status": "success", "run_id": "fixture-run",
            "refresh": {"ember": {"status": "refreshed"}}}), encoding="utf-8")
        result = runner.run()
        self.assertEqual(result["publication"], "published")
        self.assertEqual(result["sources"]["ember"]["status"], "refreshed")
        refresh.assert_not_called()

    def test_old_lifecycle_success_is_not_reused_for_new_failure(self):
        runner = MonthlyRefreshRunner(self.atlas, self.community, self.config,
            now=lambda: datetime(2026, 9, 2, 3, tzinfo=UTC),
            refresh=MagicMock(side_effect=RuntimeError("fixture failure")))
        runner.report_path.parent.mkdir()
        runner.lifecycle_path.write_text(json.dumps({"status": "success", "run_id": "old-run",
            "previous_sha256": "wrong-old-hash"}), encoding="utf-8")
        with self.assertRaises(RuntimeError):
            runner.run()
        result = json.loads(runner.report_path.read_text(encoding="utf-8"))
        self.assertEqual(result["publication"], "not_published")
        self.assertEqual(result["previous_sha256"].lower(), digest(self.atlas))

    def test_read_only_status_does_not_create_database_or_expose_error_paths(self):
        from electricity_atlas.monthly_refresh import monthly_refresh_status, monthly_refresh_health
        missing = self.root / "does-not-exist" / "atlas.sqlite3"
        self.assertEqual(monthly_refresh_status(missing), {"status": "not_run"})
        self.assertFalse(missing.parent.exists())
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir()
        report.write_text(json.dumps({"status": "failed", "error": "secret/path",
            "database": "private/path", "sources": {"ember": {"status": "failed_critical", "error": "secret"}}}), encoding="utf-8")
        result = monthly_refresh_status(self.atlas)
        self.assertNotIn("error", result)
        self.assertNotIn("database", result)
        self.assertEqual(result["sources"], {"ember": "failed_critical"})
        health = monthly_refresh_health(self.atlas)
        self.assertEqual(health["last_run_status"], "failed")
        self.assertEqual(health["sources"]["ember"], "failed_critical")
        self.assertEqual(health["publication"], "unknown")
        self.assertNotIn("secret", json.dumps(health))
        report.write_text(json.dumps({"status": "private/path", "target_month": "secret",
            "completed_at": "secret", "sources": {}}), encoding="utf-8")
        self.assertEqual(monthly_refresh_health(self.atlas), {"last_run_status": "unreadable_report"})

    def test_public_source_status_is_allowlisted_and_retention_is_a_warning(self):
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir()
        sources = {name: {"status": "refreshed"} for name in PUBLIC_REFRESH_SOURCES}
        sources.update({"ember": {"status": "refreshed_with_retention"},
                        "jrc_storage": {"status": "failed_optional", "error": "private-secret"},
                        "cache_cleanup": {"status": "completed"},
                        "private-secret": {"status": "private-secret"}})
        report.write_text(json.dumps({"status": "success", "publication": "published", "sources": sources}), encoding="utf-8")
        health = monthly_refresh_health(self.atlas)
        self.assertEqual(health["source_warnings"], ["ember", "jrc_storage"])
        self.assertEqual(health["publication"], "published")
        self.assertEqual(set(health["sources"]), set(PUBLIC_REFRESH_SOURCES))
        self.assertNotIn("private-secret", json.dumps(health))

    def test_malformed_public_status_values_never_leak_or_crash(self):
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir()
        for bad in (None, [], {}, 42, "private-secret"):
            report.write_text(json.dumps({"status": "success", "publication": bad,
                "sources": {"ember": {"status": bad}}, "completed_at": bad}), encoding="utf-8")
            health = monthly_refresh_health(self.atlas)
            self.assertEqual(health["sources"]["ember"], "unknown")
            self.assertEqual(health["publication"], "unknown")
            self.assertNotIn("private-secret", json.dumps(health))
        report.write_text('{"status":"success","sources":[]}', encoding="utf-8")
        self.assertEqual(monthly_refresh_health(self.atlas), {"last_run_status": "unreadable_report"})

    def test_restart_and_december_rollover_do_not_repeat_successful_month(self):
        report = self.data / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir()
        report.write_text(json.dumps({"status": "success", "target_month": "2026-12"}), encoding="utf-8")
        launches = []
        for moment, due in ((datetime(2026, 12, 31, 23, tzinfo=UTC), False),
                            (datetime(2027, 1, 2, 2, 59, tzinfo=UTC), False),
                            (datetime(2027, 1, 2, 3, tzinfo=UTC), True)):
            scheduler = MonthlyRefreshScheduler(self.atlas, self.community, self.config,
                now=lambda: moment, popen=lambda *a, **k: launches.append(a) or FakeProcess())
            self.assertEqual(scheduler.check(), due)
        self.assertEqual(len(launches), 1)

    def test_success_report_cannot_delay_next_month_with_a_stale_retry_field(self):
        scheduler = MonthlyRefreshScheduler(self.atlas, self.community, self.config,
            now=lambda: datetime(2026, 10, 2, 2, 59, tzinfo=UTC))
        scheduler.report_path.parent.mkdir()
        scheduler.report_path.write_text(json.dumps({"status": "success", "target_month": "2026-09",
            "next_attempt_at": "2099-01-01T00:00:00+00:00"}), encoding="utf-8")
        self.assertEqual(scheduler._wait_seconds(), 60)

    def test_naive_invalid_and_overflow_retry_dates_do_not_depend_on_host_timezone(self):
        moment = datetime(2026, 9, 2, 3, tzinfo=UTC)
        scheduler = MonthlyRefreshScheduler(self.atlas, self.community, self.config, now=lambda: moment)
        scheduler.report_path.parent.mkdir()
        for retry in ("2099-01-01T00:00:00", "9999-12-31T23:00:00-12:00", {}, "bad"):
            report = {"status": "failed", "next_attempt_at": retry}
            scheduler.report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertTrue(scheduler._is_due(moment, report))
            self.assertEqual(scheduler._wait_seconds(), 1)

    def test_february_and_utc_boundary_schedule(self):
        from dataclasses import replace
        from datetime import timezone
        scheduler = MonthlyRefreshScheduler(self.atlas, self.community,
            replace(self.config, day_utc=28), popen=lambda *a, **k: FakeProcess())
        # Local February 28 is still February 27 in UTC.
        self.assertFalse(scheduler.check(datetime(2028, 2, 28, 3, tzinfo=timezone(timedelta(hours=4)))))
        self.assertTrue(scheduler.check(datetime(2028, 2, 28, 7, tzinfo=timezone(timedelta(hours=4)))))

    def test_invalid_worker_month_is_rejected_before_any_file_write(self):
        refresh = MagicMock()
        runner = MonthlyRefreshRunner(self.atlas, self.community, self.config, refresh=refresh)
        for month in ("", "2026-13", "secret/path", [], "2026-1"):
            with self.assertRaises(MonthlyRefreshConfigurationError):
                runner.run(target_month=month)
        refresh.assert_not_called()
        self.assertFalse(runner.report_path.parent.exists())

    def test_monthly_report_cannot_overwrite_database_or_sidecars(self):
        before = self.atlas.read_bytes()
        for path in (self.atlas, self.community, Path(f"{self.community}-wal"),
                     self.data / LOCK_FILE_NAME):
            with self.assertRaises(MonthlyRefreshConfigurationError):
                MonthlyRefreshRunner(self.atlas, self.community, self.config, report_path=path)
        self.assertEqual(self.atlas.read_bytes(), before)

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
    def test_explicit_local_battery_files_never_fall_back_to_browser(self):
        fixtures = Path(__file__).parent / "fixtures" / "storage"
        for power in (None, fixtures / "missing.json", fixtures / "battery_power.json"):
            with self.subTest(power=power), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                stack.enter_context(patch("electricity_atlas.full_refresh.run_refresh_lifecycle",
                                          side_effect=lambda _path, action, **_kw: action(root / "candidate.sqlite3")))
                stack.enter_context(patch("electricity_atlas.full_refresh.load_ember_api_key"))
                ember = stack.enter_context(patch("electricity_atlas.full_refresh.EmberImporter"))
                ember.return_value.import_range.return_value = {"successes": [], "errors": 0}
                for cls, method in (("WholesalePriceImporter", "import_prices"),
                                    ("EurostatImporter", "import_years"),
                                    ("EurostatSupplementImporter", "import_years"),
                                    ("JrcHydroImporter", "import_release"),
                                    ("EeaGhgImporter", "import_url")):
                    mock = stack.enter_context(patch(f"electricity_atlas.full_refresh.{cls}"))
                    getattr(mock.return_value, method).return_value = {"rows": 0}
                storage = stack.enter_context(patch("electricity_atlas.full_refresh.OnlineStorageUpdater"))
                storage.return_value.update.return_value = {"jrc": {"rows": 0}}
                browser = stack.enter_context(patch("electricity_atlas.full_refresh.BatteryDashboardClient"))
                result = run_scheduled_refresh(root / "atlas.sqlite3",
                                               battery_energy_file=fixtures / "battery_energy.json",
                                               battery_power_file=power)
                expected = "refreshed" if power is not None and power.is_file() else "preserved_controlled_input"
                self.assertEqual(result["battery_charts"]["status"], expected)
                browser.assert_not_called()

    def test_core_sources_are_strict_and_public_storage_exports_are_optional(self):
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
            ) as battery, patch("electricity_atlas.full_refresh.OnlineStorageUpdater") as storage, patch(
                "electricity_atlas.full_refresh.BatteryDashboardClient"
            ) as dashboard, patch("electricity_atlas.full_refresh.JrcDashboardClient") as jrc:
                dashboard.return_value.fetch_pair.return_value = ("energy", "power")
                battery.return_value.import_downloads.return_value = {"rows": 12}
                storage.return_value.update.return_value = {"jrc": {"rows": 3}}
                result = run_scheduled_refresh(root / "atlas.sqlite3", to_year=2026)
            self.assertEqual(result["status"], "success")
            policy = result["refresh"]
            self.assertEqual(policy["battery_charts"]["status"], "refreshed")
            self.assertEqual(policy["jrc_storage"]["status"], "refreshed")
            battery.return_value.import_downloads.assert_called_once_with("energy", "power")
            jrc.assert_called_once_with(headed=False)
            storage.return_value.update.assert_called_once_with()
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
                "electricity_atlas.full_refresh.EeaGhgImporter") as ghg, patch(
                "electricity_atlas.full_refresh.BatteryDashboardClient"
            ) as battery, patch("electricity_atlas.full_refresh.OnlineStorageUpdater") as storage:
                battery.return_value.fetch_pair.side_effect = RuntimeError("fixture browser unavailable")
                storage.return_value.update.side_effect = RuntimeError("fixture browser unavailable")
                prices.return_value.import_prices.return_value = {"rows": 1}
                core.return_value.import_years.return_value = {"rows": 1}
                supplement.return_value.import_years.return_value = {"rows": 1}
                hydro.return_value.import_release.side_effect = RuntimeError("temporary hydro fixture failure")
                ghg.return_value.import_url.return_value = {"rows": 1}
                result = run_scheduled_refresh(root / "atlas.sqlite3", to_year=2026)
            self.assertEqual(result["jrc_hydro"]["status"], "failed_optional")
            self.assertEqual(result["battery_charts"]["status"], "failed_optional")
            self.assertEqual(result["jrc_storage"]["status"], "failed_optional")

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
