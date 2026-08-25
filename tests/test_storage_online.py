from __future__ import annotations

import json
import io
import sqlite3
import unittest
from contextlib import redirect_stdout
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from electricity_atlas.config import (
    BATTERY_CHARTS_ENERGY_ENDPOINT,
    BATTERY_CHARTS_POWER_ENDPOINT,
    JRC_STORAGE_API_ENDPOINT,
)
from electricity_atlas.cli import main
from electricity_atlas.db import initialize
from electricity_atlas.storage_online import (
    BatteryChartsClient,
    BatteryChartsImporter,
    JrcOnlineImporter,
    JrcStorageClient,
    OnlineStorageUpdater,
    SourceDownload,
    StorageOnlineError,
    latest_storage,
)
from electricity_atlas.storage_importer import JRC_DASHBOARD_EXPORTS


FIXTURES = Path(__file__).parent / "fixtures" / "storage"
NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


def connection() -> sqlite3.Connection:
    result = sqlite3.connect(":memory:")
    result.row_factory = sqlite3.Row
    initialize(result)
    return result


def download(source: str, endpoint: str, payload: str, status: int = 200) -> SourceDownload:
    return SourceDownload(
        source=source,
        endpoint=endpoint,
        request_url=f"https://example.invalid/{endpoint}?api_key=REDACTED",
        fetched_at=NOW.isoformat(),
        status_code=status,
        content_type="application/json",
        etag='"fixture"',
        last_modified="Wed, 12 Aug 2026 12:00:00 GMT",
        sha256="fixture-sha256",
        payload_text=payload,
    )


def fixture_downloads() -> tuple[SourceDownload, SourceDownload, SourceDownload]:
    energy = (FIXTURES / "battery_energy.json").read_text(encoding="utf-8")
    power = (FIXTURES / "battery_power.json").read_text(encoding="utf-8")
    jrc = (FIXTURES / "jrc_projects.json").read_text(encoding="utf-8")
    return (
        download("battery_charts", BATTERY_CHARTS_ENERGY_ENDPOINT, energy),
        download("battery_charts", BATTERY_CHARTS_POWER_ENDPOINT, power),
        download("jrc", JRC_STORAGE_API_ENDPOINT, jrc),
    )


class FakeResponse:
    def __init__(self, payload: str):
        self.payload = payload.encode("utf-8")
        self.status = 200
        self.headers = {"Content-Type": "application/json", "ETag": '"new"'}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class StorageImporterTests(unittest.TestCase):
    def setUp(self):
        self.connection = connection()
        self.energy, self.power, self.jrc = fixture_downloads()

    def tearDown(self):
        self.connection.close()

    def test_battery_segments_total_normalization_and_current_month_quality(self):
        result = BatteryChartsImporter(self.connection, date(2026, 8, 12)).import_downloads(
            self.energy, self.power
        )
        self.assertEqual(result["months"], 2)
        rows = self.connection.execute(
            "SELECT source_series,metric,value,quality_status FROM period_observation "
            "WHERE source='battery_charts' AND period_end='2026-08-12'"
        ).fetchall()
        values = {(row["source_series"], row["metric"]): row["value"] for row in rows}
        self.assertEqual(values[("national_registry_total", "battery_energy_gwh")], 12)
        self.assertEqual(values[("national_registry_total", "battery_power_gw")], 6)
        self.assertEqual(values[("national_registry_total", "battery_duration_hours")], 2)
        self.assertEqual(
            values[("national_registry_total", "battery_energy_gwh")],
            sum(values[(segment, "battery_energy_gwh")] for segment in ("home", "industrial", "grossspeicher")),
        )
        self.assertTrue(all("provisional" in row["quality_status"] for row in rows))

    def test_manual_battery_files_are_cached_without_network_credentials(self):
        result = BatteryChartsImporter(self.connection, date(2026, 8, 12)).import_files(
            FIXTURES / "battery_energy.json",
            FIXTURES / "battery_power.json",
        )
        self.assertEqual(result["import_mode"], "manual_json_files")
        cached = self.connection.execute(
            "SELECT request_url,sha256,payload_text FROM source_cache "
            "WHERE source='battery_charts' ORDER BY endpoint"
        ).fetchall()
        self.assertEqual(len(cached), 2)
        self.assertTrue(all(row["request_url"].startswith("manual-file:") for row in cached))
        self.assertTrue(all("api_key" not in row["request_url"] for row in cached))
        self.assertTrue(all(len(row["sha256"]) == 64 for row in cached))

    def test_jrc_filters_status_and_technology_and_preserves_missing_energy(self):
        result = JrcOnlineImporter(self.connection).import_download(self.jrc)
        self.assertEqual(result["countries_with_values"], 3)
        rows = self.connection.execute(
            "SELECT country_code,metric,value,quality_status FROM period_observation "
            "WHERE source='jrc' AND source_endpoint=?",
            (JRC_STORAGE_API_ENDPOINT,),
        ).fetchall()
        values = {(row["country_code"], row["metric"]): row for row in rows}
        self.assertEqual(values[("FR", "battery_power_gw")]["value"], 0.2)
        self.assertEqual(values[("FR", "battery_energy_gwh")]["value"], 0.4)
        self.assertEqual(values[("FR", "battery_duration_hours")]["value"], 2)
        self.assertIn("estimates", values[("FR", "battery_energy_gwh")]["quality_status"])
        self.assertEqual(values[("BE", "battery_power_gw")]["value"], 0.1)
        self.assertNotIn(("BE", "battery_energy_gwh"), values)
        self.assertEqual(values[("DE", "pumped_storage_power_gw")]["value"], 1)
        self.assertEqual(values[("DE", "pumped_storage_energy_gwh")]["value"], 8)
        self.assertNotIn(("DE", "battery_power_gw"), values)
        self.assertFalse(any(row["value"] == 0.999 for row in rows))

    def test_source_resolution_never_sums_jrc_into_german_battery_total(self):
        BatteryChartsImporter(self.connection).import_downloads(self.energy, self.power)
        JrcOnlineImporter(self.connection).import_download(self.jrc)
        rows = {row["country_code"]: row for row in latest_storage(self.connection)["countries"]}
        self.assertEqual(rows["DE"]["battery_power_gw"], 6)
        self.assertEqual(rows["DE"]["pumped_storage_power_gw"], 1)
        self.assertEqual(
            rows["DE"]["metric_provenance"]["battery_power_gw"]["coverage_type"],
            "national_registry_total",
        )
        self.assertEqual(rows["FR"]["battery_power_gw"], 0.2)
        self.assertEqual(
            rows["FR"]["metric_provenance"]["battery_power_gw"]["coverage_type"],
            "tracked_project_inventory",
        )

    def test_invalid_battery_json_preserves_existing_rows_and_cache(self):
        BatteryChartsImporter(self.connection).import_downloads(self.energy, self.power)
        before = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='battery_charts'"
        ).fetchone()
        invalid = download("battery_charts", BATTERY_CHARTS_POWER_ENDPOINT, "<html>blocked</html>")
        with self.assertRaises(StorageOnlineError):
            BatteryChartsImporter(self.connection).import_downloads(self.energy, invalid)
        after = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='battery_charts'"
        ).fetchone()
        self.assertEqual(tuple(before), tuple(after))
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM source_cache WHERE source='battery_charts'").fetchone()[0],
            2,
        )

    def test_invalid_jrc_schema_preserves_existing_rows(self):
        JrcOnlineImporter(self.connection).import_download(self.jrc)
        before = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='jrc'"
        ).fetchone()
        with self.assertRaises(StorageOnlineError):
            JrcOnlineImporter(self.connection).import_download(download("jrc", JRC_STORAGE_API_ENDPOINT, "{}"))
        after = self.connection.execute(
            "SELECT COUNT(*),SUM(value) FROM period_observation WHERE source='jrc'"
        ).fetchone()
        self.assertEqual(tuple(before), tuple(after))


class StorageClientTests(unittest.TestCase):
    def test_403_and_429_are_never_retried(self):
        for status in (403, 429):
            with self.subTest(status=status):
                calls = []

                def opener(request, timeout):
                    calls.append((request, timeout))
                    raise HTTPError(request.full_url, status, "blocked", {}, None)

                client = JrcStorageClient(opener=opener, sleeper=lambda _seconds: self.fail("unexpected retry"))
                with self.assertRaises(StorageOnlineError) as error:
                    client.fetch()
                self.assertEqual(len(calls), 1)
                self.assertIn(str(status), str(error.exception))

    def test_timeout_and_5xx_make_at_most_one_retry_after_ten_seconds(self):
        payload = (FIXTURES / "jrc_projects.json").read_text(encoding="utf-8")
        calls = []
        sleeps = []

        def timeout_then_success(request, timeout):
            calls.append((request, timeout))
            if len(calls) == 1:
                raise URLError(TimeoutError("timed out"))
            return FakeResponse(payload)

        result = JrcStorageClient(opener=timeout_then_success, sleeper=sleeps.append, now=lambda: NOW).fetch()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [10.0])

        calls.clear()
        sleeps.clear()

        def dns_failure(request, timeout):
            calls.append((request, timeout))
            raise URLError("name resolution failed")

        with self.assertRaises(StorageOnlineError):
            JrcStorageClient(opener=dns_failure, sleeper=sleeps.append).fetch()
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

        calls.clear()
        sleeps.clear()

        def always_500(request, timeout):
            calls.append((request, timeout))
            raise HTTPError(request.full_url, 500, "failure", {}, None)

        with self.assertRaises(StorageOnlineError):
            JrcStorageClient(opener=always_500, sleeper=sleeps.append).fetch()
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [10.0])

    def test_battery_online_access_is_disabled_before_any_request(self):
        requests = []

        def opener(request, timeout):
            requests.append(request.full_url)
            raise AssertionError("Battery-Charts network request")

        client = BatteryChartsClient("unused-local-key", opener=opener)
        with self.assertRaisesRegex(StorageOnlineError, "online access is disabled"):
            client.fetch_pair()
        self.assertEqual(requests, [])


class StorageUpdaterTests(unittest.TestCase):
    def setUp(self):
        self.connection = connection()
        self.energy, self.power, self.jrc = fixture_downloads()

    def tearDown(self):
        self.connection.close()

    def _cache(self, source: str, endpoint: str, payload: str):
        self.connection.execute(
            "INSERT INTO source_cache VALUES (?,?,?,?,?,?,?,?,?,?)",
            (source, endpoint, "https://example.invalid", NOW.isoformat(), 200, "application/json", None, None, "sha", payload),
        )

    def test_fresh_monthly_cache_prevents_all_network_calls(self):
        for endpoint in JRC_DASHBOARD_EXPORTS.values():
            self._cache("jrc", endpoint, "base64:fixture")

        class NeverJrc:
            def fetch_exports(self):
                raise AssertionError("JRC network call")

        result = OnlineStorageUpdater(
            self.connection,
            today=date(2026, 8, 20),
            jrc_client=NeverJrc(),
        ).update()
        self.assertEqual(result["jrc"]["network_requests"], 0)
        self.assertEqual(set(result), {"jrc"})

    def test_forced_refresh_is_limited_to_one_jrc_request(self):
        class FakeJrc:
            calls = 0

            def fetch_exports(self):
                self.calls += 1
                return SimpleNamespace(exports={}, snapshot_date="2026-08-25")

        jrc_client = FakeJrc()
        with patch("electricity_atlas.storage_online.JrcStorageImporter") as importer_mock:
            importer_mock.return_value.import_dashboard_categories.return_value = {"rows": 12}
            result = OnlineStorageUpdater(
                self.connection,
                refresh=True,
                today=date(2026, 8, 20),
                jrc_client=jrc_client,
            ).update()
        self.assertEqual(jrc_client.calls, 1)
        self.assertEqual(result["jrc"]["network_requests"], 1)
        self.assertEqual(result["jrc"]["download_requests"], 0)
        self.assertEqual(set(result), {"jrc"})

    def test_manual_import_never_persists_a_battery_key_field(self):
        BatteryChartsImporter(self.connection).import_files(
            FIXTURES / "battery_energy.json",
            FIXTURES / "battery_power.json",
        )
        dump = "\n".join(
            str(tuple(row)) for row in self.connection.execute("SELECT * FROM source_cache").fetchall()
        )
        self.assertNotIn("api_key", dump)
        self.assertIn("manual-file:", dump)


class StorageCliTests(unittest.TestCase):
    def test_update_storage_cli_dispatches_refresh_without_live_network(self):
        result = {"jrc": {"network_requests": 1}}
        fake_connection = object()
        with patch("electricity_atlas.cli.database") as database_mock, patch(
            "electricity_atlas.cli.OnlineStorageUpdater"
        ) as updater_mock, redirect_stdout(io.StringIO()):
            database_mock.return_value.__enter__.return_value = fake_connection
            updater_mock.return_value.update.return_value = result
            exit_code = main(["--db", "fixture.sqlite3", "update-storage", "--refresh"])
        self.assertEqual(exit_code, 0)
        updater_mock.assert_called_once_with(fake_connection, refresh=True)
        updater_mock.return_value.update.assert_called_once_with()

    def test_manual_battery_cli_dispatches_both_local_files(self):
        result = {"source": "battery_charts", "import_mode": "manual_json_files"}
        fake_connection = object()
        with patch("electricity_atlas.cli.database") as database_mock, patch(
            "electricity_atlas.cli.BatteryChartsImporter"
        ) as importer_mock, redirect_stdout(io.StringIO()):
            database_mock.return_value.__enter__.return_value = fake_connection
            importer_mock.return_value.import_files.return_value = result
            exit_code = main([
                "--db", "fixture.sqlite3", "import-battery-storage",
                "--energy-file", "energy.json", "--power-file", "power.json",
            ])
        self.assertEqual(exit_code, 0)
        importer_mock.assert_called_once_with(fake_connection)
        importer_mock.return_value.import_files.assert_called_once_with(
            Path("energy.json"), Path("power.json")
        )


if __name__ == "__main__":
    unittest.main()
