from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from electricity_atlas.battery_dashboard import BatteryDashboardClient, BATTERY_DASHBOARD_URL
from electricity_atlas.config import BATTERY_CHARTS_ENERGY_ENDPOINT, BATTERY_CHARTS_POWER_ENDPOINT
from electricity_atlas.db import initialize
from electricity_atlas.full_refresh import _optional_candidate_source
from electricity_atlas.refresh_safety import observation_coverage, require_preserved_coverage
from electricity_atlas.storage_online import BatteryChartsImporter, SourceDownload, StorageOnlineError


def csv_download(endpoint, end="2026-08-10", values="3,2,1"):
    text = "Date,Large-Scale Storage,Industrial Storage,Home Storage\n"
    text += f"2026-07-31 00:00:00,{values}\n{end} 00:00:00,{values}\n"
    return SourceDownload("battery_charts", endpoint, BATTERY_DASHBOARD_URL, "2026-09-23T00:00:00+00:00",
                          200, "text/csv", None, None, hashlib.sha256(text.encode()).hexdigest(), text)


class BatteryCsvTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        initialize(self.db)
        self.addCleanup(self.db.close)
        self.importer = BatteryChartsImporter(self.db, today=date(2026, 9, 23))

    def pair(self, end="2026-08-10"):
        return csv_download(BATTERY_CHARTS_ENERGY_ENDPOINT, end), csv_download(BATTERY_CHARTS_POWER_ENDPOINT, end, "1.5,1,0.5")

    def test_public_csv_units_quality_and_raw_provenance(self):
        result = self.importer.import_downloads(*self.pair())
        self.assertEqual(result["import_mode"], "public_dashboard_csv")
        rows = self.db.execute("SELECT metric,value,quality_status FROM period_observation WHERE source_series='national_registry_total' AND period_end='2026-08-10'").fetchall()
        self.assertEqual({r["metric"]: r["value"] for r in rows},
                         {"battery_energy_gwh": 6, "battery_power_gw": 3, "battery_duration_hours": 2})
        self.assertEqual({r["quality_status"] for r in rows}, {"provisional_current_month", "derived_provisional"})
        cached = self.db.execute("SELECT request_url,content_type,payload_text FROM source_cache").fetchall()
        self.assertEqual(len(cached), 2)
        for row in cached:
            self.assertEqual(row["request_url"], BATTERY_DASHBOARD_URL)
            self.assertEqual(row["content_type"], "text/csv")
            self.assertTrue(row["payload_text"].startswith("Date,"))

    def test_provisional_month_can_advance_and_close_without_disabling_coverage(self):
        self.importer.import_downloads(*self.pair())
        for end in ("2026-08-22", "2026-08-31"):
            before = observation_coverage(self.db)
            result = _optional_candidate_source(self.db, "battery_charts", lambda: self.importer.import_downloads(*self.pair(end)))
            self.assertEqual(result["status"], "refreshed")
            require_preserved_coverage(self.db, before)
        for end in ("2026-08-30", "2026-09-22"):
            # Backdating and dropping August in favour of September are rejected.
            result = _optional_candidate_source(self.db, "battery_charts", lambda: self.importer.import_downloads(*self.pair(end)))
            self.assertEqual(result["status"], "failed_optional")
            self.assertEqual(self.db.execute("SELECT MAX(period_end) FROM period_observation").fetchone()[0], "2026-08-31")
        for raw in self.db.execute("SELECT payload_text FROM source_cache"):
            self.assertIn("2026-08-31", raw[0])
        advanced = tuple(replace(item, payload_text=item.payload_text + "2026-09-22 00:00:00,4,2,1\n")
                         for item in self.pair("2026-08-31"))
        result = _optional_candidate_source(self.db, "battery_charts", lambda: self.importer.import_downloads(*advanced))
        self.assertEqual(result["status"], "refreshed")
        self.assertEqual(result["result"]["latest_date"], "2026-09-22")

    def test_csv_corruption_mismatch_or_partial_export_preserves_observations_and_cache(self):
        self.importer.import_downloads(*self.pair())
        original = list(self.db.iterdump())
        energy, power = self.pair("2026-08-31")
        invalid = [energy.payload_text.replace("Home Storage", "Unknown"),
                   energy.payload_text.replace(",3,2,1", ",nan,2,1"),
                   energy.payload_text.replace(",3,2,1", ",-1,2,1"),
                   energy.payload_text.replace(",3,2,1", ",,2,1"),
                   energy.payload_text.replace(",3,2,1", ",3,2,1,9"),
                   energy.payload_text.replace("2026-08-31", "2027-08-31"),
                   "<html>Access denied</html>",
                   "\n".join(energy.payload_text.splitlines()[:2])]
        for payload in invalid:
            with self.subTest(payload=payload):
                result = _optional_candidate_source(self.db, "battery_charts", lambda: self.importer.import_downloads(replace(energy, payload_text=payload), power))
                self.assertEqual(result["status"], "failed_optional")
                self.assertEqual(list(self.db.iterdump()), original)
        result = _optional_candidate_source(self.db, "battery_charts", lambda: self.importer.import_downloads(energy, self.pair()[1]))
        self.assertEqual(result["status"], "failed_optional")
        self.assertEqual(list(self.db.iterdump()), original)


class BrowserDownloadTests(unittest.TestCase):
    def test_access_denial_or_timeout_closes_browser_without_retry(self):
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        for failure in (403, 429, "timeout"):
            with self.subTest(failure=failure), patch("playwright.sync_api.sync_playwright") as playwright:
                browser = playwright.return_value.__enter__.return_value.chromium.launch.return_value
                page = browser.new_page.return_value
                page.goto.return_value.status = 200 if failure == "timeout" else failure
                if failure == "timeout":
                    page.wait_for_function.side_effect = PlaywrightTimeoutError("untrusted request URL")
                with self.assertRaises(StorageOnlineError) as caught:
                    BatteryDashboardClient().fetch_pair()
                self.assertNotIn("untrusted request URL", str(caught.exception))
                page.goto.assert_called_once()
                page.expect_download.assert_not_called()
                browser.close.assert_called_once_with()

    def test_buttons_download_both_files_and_close_browser_on_success_or_failure(self):
        for fail_second in (False, True):
            with self.subTest(fail_second=fail_second), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "download.csv"
                path.write_text(csv_download(BATTERY_CHARTS_ENERGY_ENDPOINT).payload_text, encoding="utf-8")
                with patch("playwright.sync_api.sync_playwright") as playwright:
                    browser = playwright.return_value.__enter__.return_value.chromium.launch.return_value
                    page = browser.new_page.return_value
                    page.goto.return_value.status = 200
                    pending = []
                    for chart in ("bessCumulativeEnergyChart", "bessCumulativePowerChart"):
                        item = MagicMock()
                        download = item.__enter__.return_value.value
                        download.suggested_filename = chart + ".csv"
                        download.path.return_value = str(path)
                        pending.append(item)
                    if fail_second:
                        pending[1].__enter__.return_value.value.suggested_filename = "unexpected.zip"
                    page.expect_download.side_effect = pending
                    if fail_second:
                        with self.assertRaises(StorageOnlineError):
                            BatteryDashboardClient().fetch_pair()
                    else:
                        pair = BatteryDashboardClient().fetch_pair()
                        self.assertEqual([d.endpoint for d in pair], [BATTERY_CHARTS_ENERGY_ENDPOINT, BATTERY_CHARTS_POWER_ENDPOINT])
                        self.assertTrue(all(d.request_url == BATTERY_DASHBOARD_URL for d in pair))
                    browser.close.assert_called_once_with()
                    page.goto.assert_called_once()
                    self.assertEqual(page.wait_for_function.call_count, 2)


if __name__ == "__main__":
    unittest.main()
