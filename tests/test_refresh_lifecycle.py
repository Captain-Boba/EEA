import hashlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from electricity_atlas.cli import main
from electricity_atlas.config import EMBER_COUNTRIES
from electricity_atlas.full_refresh import run_full_refresh
from electricity_atlas.refresh_lifecycle import (
    RefreshLifecycleError,
    RefreshLockError,
    RefreshPathError,
    run_refresh_lifecycle,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simple_validation(path: Path) -> dict[str, object]:
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        value = connection.execute("SELECT value FROM refresh_fixture").fetchone()[0]
    finally:
        connection.close()
    if integrity != "ok":
        raise RuntimeError(integrity)
    return {"integrity": integrity, "value": value}


class RefreshLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.atlas = self.data / "atlas.sqlite3"
        connection = sqlite3.connect(self.atlas)
        connection.execute("CREATE TABLE refresh_fixture(value INTEGER NOT NULL)")
        connection.execute("INSERT INTO refresh_fixture VALUES (1)")
        connection.commit()
        connection.close()
        self.community = self.data / "community.sqlite3"
        community = sqlite3.connect(self.community)
        community.execute("CREATE TABLE wallpaper_vote(id INTEGER PRIMARY KEY, score INTEGER)")
        community.execute("INSERT INTO wallpaper_vote(score) VALUES (7)")
        community.commit()
        community.close()
        self.reports = self.data / "reports"
        self.reports.mkdir()
        self.existing_report = self.reports / "existing.txt"
        self.existing_report.write_text("keep me", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def update_candidate(candidate: Path) -> dict[str, int]:
        connection = sqlite3.connect(candidate)
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("UPDATE refresh_fixture SET value = value + 1")
        connection.commit()
        connection.close()
        return {"updated": 1}

    def test_success_cleans_candidates_backups_and_sidecars_and_preserves_protected_data(self):
        community_before = self.community.read_bytes()
        result = run_refresh_lifecycle(
            self.atlas,
            self.update_candidate,
            validate_action=simple_validation,
            run_id="success-one",
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["published_validation"]["value"], 2)
        self.assertFalse((self.data / ".refresh-work").exists())
        self.assertFalse(Path(f"{self.atlas}-wal").exists())
        self.assertFalse(Path(f"{self.atlas}-shm").exists())
        self.assertFalse(any("candidate" in path.name or "rollback" in path.name for path in self.data.iterdir()))
        self.assertEqual(self.community.read_bytes(), community_before)
        self.assertEqual(self.existing_report.read_text(encoding="utf-8"), "keep me")
        report = json.loads((self.reports / "REFRESH.generated.json").read_text(encoding="utf-8"))
        self.assertTrue(report["cleanup_complete"])
        self.assertTrue(report["community"]["unchanged"])

    def test_failed_import_keeps_atlas_byte_identical_and_cleans_work_directory(self):
        before = self.atlas.read_bytes()

        def fail(_candidate: Path):
            raise RuntimeError("controlled import failure")

        with self.assertRaisesRegex(RefreshLifecycleError, "controlled import failure"):
            run_refresh_lifecycle(
                self.atlas,
                fail,
                validate_action=simple_validation,
                run_id="failed-import",
            )
        self.assertEqual(self.atlas.read_bytes(), before)
        self.assertFalse((self.data / ".refresh-work").exists())
        self.assertFalse(Path(f"{self.atlas}-wal").exists())
        self.assertFalse(Path(f"{self.atlas}-shm").exists())
        report = json.loads((self.reports / "REFRESH.generated.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["phase"], "refresh")

    def test_replace_that_changes_target_then_fails_restores_previous_database(self):
        replacement_calls = 0

        def replace_then_fail_once(source: Path, target: Path):
            nonlocal replacement_calls
            replacement_calls += 1
            os.replace(source, target)
            if replacement_calls == 1:
                raise OSError("simulated exchange interruption")

        with self.assertRaisesRegex(RefreshLifecycleError, "exchange interruption"):
            run_refresh_lifecycle(
                self.atlas,
                self.update_candidate,
                validate_action=simple_validation,
                run_id="exchange-failure",
                replace_file=replace_then_fail_once,
            )
        self.assertEqual(simple_validation(self.atlas)["value"], 1)
        self.assertFalse((self.data / ".refresh-work").exists())
        report = json.loads((self.reports / "REFRESH.generated.json").read_text(encoding="utf-8"))
        self.assertTrue(report["restored"])
        self.assertTrue(report["cleanup_complete"])

    def test_two_successive_runs_do_not_leave_attempt_or_work_files(self):
        for run_id in ("first-run", "second-run"):
            run_refresh_lifecycle(
                self.atlas,
                self.update_candidate,
                validate_action=simple_validation,
                run_id=run_id,
            )
        self.assertEqual(simple_validation(self.atlas)["value"], 3)
        self.assertFalse((self.data / ".refresh-work").exists())
        leftovers = [
            path.name
            for path in self.data.iterdir()
            if "attempt" in path.name or "candidate" in path.name or "rollback" in path.name
        ]
        self.assertEqual(leftovers, [])

    def test_path_guard_rejects_run_ids_that_escape_the_work_root(self):
        outside = self.data / "outside.sqlite3"
        outside.write_bytes(b"protected")
        with self.assertRaises(RefreshPathError):
            run_refresh_lifecycle(
                self.atlas,
                self.update_candidate,
                validate_action=simple_validation,
                run_id="../outside",
            )
        self.assertEqual(outside.read_bytes(), b"protected")
        self.assertFalse((self.data / ".refresh-work").exists())

    @unittest.skipUnless(os.name == "nt", "Windows file-lock behavior")
    def test_open_sqlite_database_fails_preflight_before_refresh_action(self):
        action_called = False
        active = sqlite3.connect(self.atlas)
        active.execute("SELECT * FROM refresh_fixture").fetchall()

        def action(_candidate: Path):
            nonlocal action_called
            action_called = True

        try:
            with self.assertRaises(RefreshLockError):
                run_refresh_lifecycle(
                    self.atlas,
                    action,
                    validate_action=simple_validation,
                    run_id="locked-database",
                )
        finally:
            active.close()
        self.assertFalse(action_called)
        self.assertEqual(simple_validation(self.atlas)["value"], 1)
        self.assertFalse((self.data / ".refresh-work").exists())


class FullRefreshCliTests(unittest.TestCase):
    def test_refresh_all_cli_forwards_local_battery_files_and_lifecycle_options(self):
        expected = {"status": "success", "published_sha256": "abc"}
        with patch("electricity_atlas.cli.run_full_refresh", return_value=expected) as refresh, redirect_stdout(io.StringIO()):
            exit_code = main([
                "--db", "data/atlas.sqlite3", "refresh-all",
                "--from-year", "2015", "--to-year", "2026",
                "--battery-energy-file", "battery-energy.json",
                "--battery-power-file", "battery-power.json",
                "--refresh-report", "data/reports/refresh.json",
            ])
        self.assertEqual(exit_code, 0)
        refresh.assert_called_once_with(
            Path("data/atlas.sqlite3"),
            from_year=2015,
            to_year=2026,
            battery_energy_file=Path("battery-energy.json"),
            battery_power_file=Path("battery-power.json"),
            eea_file=None,
            report_path=Path("data/reports/refresh.json"),
        )

    def test_full_refresh_runs_all_sources_sequentially_inside_lifecycle_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "candidate.sqlite3"
            events = []

            def lifecycle(_database, action, **kwargs):
                return {"status": "success", "refresh": action(candidate), "kwargs": kwargs}

            def importer(name, result):
                mocked = MagicMock()
                method = {
                    "prices": "import_prices",
                    "eurostat_core": "import_years",
                    "eurostat_supplement": "import_years",
                    "jrc_hydro": "import_release",
                    "eea_ghg": "import_url",
                    "battery_charts": "import_files",
                }[name]
                getattr(mocked, method).side_effect = lambda *args: events.append(name) or result
                return mocked

            ember = MagicMock()
            ember.import_range.side_effect = lambda code, start, end: events.append(f"ember:{code}") or {
                "successes": [code], "errors": 0,
            }
            online_storage = MagicMock()
            online_storage.update.side_effect = lambda: events.append("jrc_storage") or {
                "jrc": {"rows": 150, "network_requests": 1, "download_requests": 4}
            }
            with patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle), patch(
                "electricity_atlas.full_refresh.load_ember_api_key",
                side_effect=lambda: events.append("ember_key"),
            ), patch("electricity_atlas.full_refresh.EmberImporter", return_value=ember), patch(
                "electricity_atlas.full_refresh.WholesalePriceImporter",
                return_value=importer("prices", {"rows": 3970}),
            ), patch(
                "electricity_atlas.full_refresh.EurostatImporter",
                return_value=importer("eurostat_core", {"rows": 1021}),
            ), patch(
                "electricity_atlas.full_refresh.EurostatSupplementImporter",
                return_value=importer("eurostat_supplement", {"rows": 4603}),
            ), patch(
                "electricity_atlas.full_refresh.JrcHydroImporter",
                return_value=importer("jrc_hydro", {"rows": 67}),
            ), patch(
                "electricity_atlas.full_refresh.EeaGhgImporter",
                return_value=importer("eea_ghg", {"rows": 270}),
            ), patch(
                "electricity_atlas.full_refresh.BatteryChartsImporter",
                return_value=importer("battery_charts", {"rows": 1680}),
            ), patch(
                "electricity_atlas.full_refresh.OnlineStorageUpdater",
                return_value=online_storage,
            ):
                result = run_full_refresh(
                    root / "atlas.sqlite3",
                    from_year=2015,
                    to_year=2026,
                    battery_energy_file=root / "energy.json",
                    battery_power_file=root / "power.json",
                )
            expected = ["ember_key"]
            expected.extend(f"ember:{code}" for code in EMBER_COUNTRIES)
            expected.extend([
                "prices", "eurostat_core", "eurostat_supplement", "jrc_hydro",
                "eea_ghg", "battery_charts", "jrc_storage",
            ])
            self.assertEqual(events, expected)
            self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()
