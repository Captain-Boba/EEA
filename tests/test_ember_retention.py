"""Offline synthetic source withdrawals; never read or refresh the live Atlas."""
import calendar
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack, closing
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from electricity_atlas.db import initialize
from electricity_atlas.ember_importer import EmberImporter
from electricity_atlas.ember_aggregation import aggregate_ember_country
from electricity_atlas.ember_retention import (
    monthly_ember_baseline, retain_monthly_source_gaps, RETAINED_SOURCE_GAP,
)
from electricity_atlas.refresh_safety import observation_coverage, require_preserved_coverage
from electricity_atlas.timeseries import build_timeseries
from electricity_atlas.country_profile import _metric_payload
from electricity_atlas.metrics import METRICS_BY_ID
from electricity_atlas.full_refresh import run_scheduled_refresh, ScheduledRefreshCriticalError
from electricity_atlas.refresh_lifecycle import run_refresh_lifecycle


class EmberRetentionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        initialize(self.db)
        self.addCleanup(self.db.close)

    def seed(self, country="HU", month="2017-01", series="Solar", metric="generation_solar"):
        year, number = map(int, month.split("-"))
        start = month + "-01"
        end = f"{month}-{calendar.monthrange(year, number)[1]}"
        rows = [("electricity-generation", series, metric, 2, "TWh"),
                ("electricity-generation", series, "share_of_generation_pct", 20, "%"),
                ("electricity-generation", "Gas", "generation_gas", 8, "TWh"),
                ("electricity-generation", "Gas", "share_of_generation_pct", 80, "%"),
                ("electricity-generation", "Total generation", "generation_total", 10, "TWh"),
                ("electricity-demand", "", "consumption", 12, "TWh"),
                ("carbon-intensity", "", "carbon_intensity", 100, "gCO2/kWh")]
        self.db.executemany("""INSERT INTO period_observation VALUES
            (?,?,?,'monthly','ember',?,?,?,?,?,'observed')""",
            [(country, start, end, endpoint + "/monthly", name, kind, value, unit)
             for endpoint, name, kind, value, unit in rows])
        self.db.commit()

    def withdraw(self, country="HU", month="2017-01", series="Solar"):
        self.db.execute("DELETE FROM period_observation WHERE country_code=? AND period_start=? AND source_series=?",
                        (country, month + "-01", series))
        self.db.execute("UPDATE period_observation SET value=value*2, quality_status='observed' "
                        "WHERE country_code=? AND period_start=?", (country, month + "-01"))

    def test_partial_loss_restores_whole_month_but_keeps_other_updates(self):
        self.seed()
        self.seed(month="2017-02")
        before = monthly_ember_baseline(self.db)
        coverage = observation_coverage(self.db)
        self.withdraw()
        self.db.execute("UPDATE period_observation SET value=99 WHERE period_start='2017-02-01'")
        self.seed(month="2017-03")
        report = retain_monthly_source_gaps(self.db, before)
        require_preserved_coverage(self.db, coverage)
        self.assertEqual(report["missing_observations"], 2)
        self.assertEqual(report["retained_observations"], 7)
        restored = monthly_ember_baseline(self.db)
        for key, row in before.items():
            if row["period_start"] == "2017-01-01":
                self.assertEqual(restored[key]["value"], row["value"])
                self.assertEqual(restored[key]["quality_status"], RETAINED_SOURCE_GAP)
        self.assertEqual(self.db.execute("SELECT value FROM period_observation WHERE period_start='2017-02-01'").fetchone()[0], 99)
        self.assertEqual(len(restored), 21)

    def test_real_importer_recovers_and_clears_retained_status(self):
        self.seed()
        before = monthly_ember_baseline(self.db)
        client = MagicMock()
        recovered_source = False
        def payload(endpoint, *_args, extra=None, **_kwargs):
            if endpoint.startswith("electricity-generation"):
                entries = [("Total generation", 20, None)] if extra["is_aggregate_series"] == "true" else [("Gas", 18, 90)]
                if recovered_source and extra["is_aggregate_series"] == "false":
                    entries.append(("Solar", 2, 10))
                return {"data": [{"entity_code": "HUN", "date": "2017-01", "series": series,
                                  "generation_twh": value, "share_of_generation_pct": share,
                                  "is_aggregate_series": series == "Total generation"}
                                 for series, value, share in entries]}
            field = "demand_twh" if endpoint.startswith("electricity-demand") else "emissions_intensity_gco2_per_kwh"
            return {"data": [{"entity_code": "HUN", "date": "2017-01", field: 24}]}
        client.get.side_effect = payload
        importer = EmberImporter(self.db, client=client, refresh=True)
        for endpoint in ("electricity-generation", "electricity-demand", "carbon-intensity"):
            importer._import_endpoint("HU", endpoint + "/monthly", "monthly", "2017-01", "2017-01")
        report = retain_monthly_source_gaps(self.db, before)
        self.assertEqual(report["missing_observations"], 2)
        # Complete subsequent source response replaces every retained row.
        retained = monthly_ember_baseline(self.db)
        recovered_source = True
        for endpoint in ("electricity-generation", "electricity-demand", "carbon-intensity"):
            importer._import_endpoint("HU", endpoint + "/monthly", "monthly", "2017-01", "2017-01")
        recovered = retain_monthly_source_gaps(self.db, retained)
        self.assertEqual(recovered["retained_periods"], [])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM period_observation WHERE quality_status=?", (RETAINED_SOURCE_GAP,)).fetchone()[0], 0)

    def test_repeated_withdrawal_is_idempotent_and_one_sided_share_loss_retains_pair(self):
        self.seed()
        for _ in range(2):
            before = monthly_ember_baseline(self.db)
            self.db.execute("DELETE FROM period_observation WHERE source_series='Solar' AND metric='share_of_generation_pct'")
            self.db.execute("UPDATE period_observation SET value=999 WHERE metric='generation_solar'")
            report = retain_monthly_source_gaps(self.db, before)
            self.assertEqual(report["missing_observations"], 1)
            self.assertEqual(self.db.execute("SELECT value FROM period_observation WHERE metric='generation_solar'").fetchone()[0], 2)

    def test_outages_and_non_component_losses_still_fail_without_restoration(self):
        for condition in ("1=1", "metric='generation_total'", "metric='consumption'",
                          "metric='carbon_intensity'", "source_series IN ('Solar','Gas')"):
            with self.subTest(condition=condition):
                self.db.execute("DELETE FROM period_observation")
                self.seed()
                before = monthly_ember_baseline(self.db)
                self.db.execute("DELETE FROM period_observation WHERE " + condition)
                count = self.db.execute("SELECT COUNT(*) FROM period_observation").fetchone()[0]
                with self.assertRaises(ValueError):
                    retain_monthly_source_gaps(self.db, before)
                self.assertEqual(self.db.execute("SELECT COUNT(*) FROM period_observation").fetchone()[0], count)

    def test_synthetic_regression_for_all_304_missing_keys(self):
        affected = []
        for country, first, last, series, metric in (
            ("FI", "2017-01", "2018-12", "Solar", "generation_solar"),
            ("HU", "2017-01", "2018-12", "Solar", "generation_solar"),
            ("PL", "2015-01", "2018-12", "Solar", "generation_solar"),
            ("SE", "2021-12", "2026-07", "Other renewables", "generation_other_renewables"),
        ):
            for year in range(int(first[:4]), int(last[:4]) + 1):
                for month in range(1, 13):
                    token = f"{year}-{month:02}"
                    if first <= token <= last:
                        self.seed(country, token, series, metric)
                        affected.append((country, token, series))
        before = monthly_ember_baseline(self.db)
        coverage = observation_coverage(self.db)
        for country, month, series in affected:
            self.withdraw(country, month, series)
        report = retain_monthly_source_gaps(self.db, before)
        self.assertEqual(report["missing_observations"], 304)
        self.assertEqual(len(report["retained_periods"]), 152)
        require_preserved_coverage(self.db, coverage)

    def test_api_marks_monthly_ytd_profile_timeseries_and_average_not_prices(self):
        token = f"{date.today().year}-01"
        self.seed(month=token)
        before = monthly_ember_baseline(self.db)
        self.withdraw(month=token)
        retain_monthly_source_gaps(self.db, before)
        for month in (1, None):
            row = aggregate_ember_country(self.db, "HU", date.today().year, month)
            self.assertIn("generation_twh", row["retained_source_metrics"])
            self.assertNotIn("price_avg_eur_mwh", row["retained_source_metrics"])
            self.assertEqual(row["retained_source_periods"], [token])
            self.assertEqual(row["generation_twh"], 10)
            self.assertEqual(row["solar_share_pct"], 20)
            profile = _metric_payload(METRICS_BY_ID["generation_twh"], row,
                                      requested_period=token, temporal_basis="monthly", actual_period=token)
            self.assertEqual(profile["quality_status"], RETAINED_SOURCE_GAP)
        result = build_timeseries(self.db, "generation_twh", ["HU"], token, token)
        self.assertEqual(result["countries"][0]["values"][0]["quality_status"], RETAINED_SOURCE_GAP)
        self.assertEqual(result["atlas_average"]["values"][0]["quality_status"], RETAINED_SOURCE_GAP)

    def test_closed_year_monthly_demand_fallback_marks_only_dependent_metrics(self):
        for month in range(1, 13):
            self.seed(month=f"2017-{month:02}")
        before = monthly_ember_baseline(self.db)
        self.withdraw()
        retain_monthly_source_gaps(self.db, before)
        row = aggregate_ember_country(self.db, "HU", 2017)
        self.assertIn("consumption_twh", row["retained_source_metrics"])
        self.assertNotIn("generation_twh", row["retained_source_metrics"])
        self.assertEqual(row["consumption_twh"], 144)

    def test_scheduled_lifecycle_publishes_retention_but_later_failure_publishes_nothing(self):
        self.seed()
        for fail_prices in (False, True):
            with self.subTest(fail_prices=fail_prices), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "atlas.sqlite3"
                with closing(sqlite3.connect(path)) as target:
                    self.db.backup(target)
                original = path.read_bytes()

                def importer(connection, **_kwargs):
                    stub = MagicMock()
                    def import_range(*_args):
                        connection.execute("DELETE FROM period_observation WHERE source_series='Solar'")
                        connection.execute("UPDATE period_observation SET value=value*2")
                        connection.commit()
                        return {"errors": 0, "successes": ["fixture"]}
                    stub.import_range.side_effect = import_range
                    return stub

                def lifecycle(database, action, **kwargs):
                    return run_refresh_lifecycle(database, action,
                                                 validate_action=lambda _: {"fixture": True}, **kwargs)

                with ExitStack() as stack:
                    stack.enter_context(patch("electricity_atlas.full_refresh.EMBER_COUNTRIES", ("HU",)))
                    stack.enter_context(patch("electricity_atlas.full_refresh.load_ember_api_key"))
                    stack.enter_context(patch("electricity_atlas.full_refresh.EmberImporter", side_effect=importer))
                    stack.enter_context(patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle))
                    for browser_source, method in (("BatteryDashboardClient", "fetch_pair"),
                                                    ("OnlineStorageUpdater", "update")):
                        mock = stack.enter_context(patch(f"electricity_atlas.full_refresh.{browser_source}"))
                        getattr(mock.return_value, method).side_effect = RuntimeError("offline fixture")
                    for cls, method in (("WholesalePriceImporter", "import_prices"),
                                        ("EurostatImporter", "import_years"),
                                        ("EurostatSupplementImporter", "import_years"),
                                        ("JrcHydroImporter", "import_release"), ("EeaGhgImporter", "import_url")):
                        mock = stack.enter_context(patch(f"electricity_atlas.full_refresh.{cls}"))
                        getattr(mock.return_value, method).return_value = {"rows": 0}
                        if fail_prices and cls == "WholesalePriceImporter":
                            mock.return_value.import_prices.side_effect = ValueError("fixture price failure")
                    if fail_prices:
                        with self.assertRaises(ScheduledRefreshCriticalError):
                            run_scheduled_refresh(path)
                        self.assertEqual(path.read_bytes(), original)
                    else:
                        result = run_scheduled_refresh(path)
                        self.assertEqual(result["status"], "success")
                        self.assertEqual(result["refresh"]["ember"]["status"], "refreshed_with_retention")
                        with closing(sqlite3.connect(path)) as published:
                            self.assertEqual(published.execute("SELECT COUNT(*) FROM period_observation WHERE quality_status=?",
                                                               (RETAINED_SOURCE_GAP,)).fetchone()[0], 7)
                self.assertFalse((Path(directory) / ".refresh-work").exists())


if __name__ == "__main__":
    unittest.main()
