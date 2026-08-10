import sqlite3
import unittest

from electricity_atlas.aggregation import (
    aggregate_country,
    installed_capacity_summary,
    net_import_balance,
    renewable_share,
    weighted_mean,
    weighted_median,
)
from electricity_atlas.config import SOURCE_NAME
from electricity_atlas.db import initialize
from electricity_atlas.coverage import coverage_rows
from electricity_atlas.importer import Importer, Period


class AggregationFunctionTests(unittest.TestCase):
    def test_renewable_share(self):
        self.assertEqual(renewable_share(25, 100), 25)
        self.assertIsNone(renewable_share(0, 0))

    def test_price_weighting_across_mixed_intervals(self):
        pairs = [(100, 60), (0, 15), (0, 15), (0, 15), (0, 15)]
        self.assertEqual(weighted_mean(pairs), 50)
        self.assertEqual(weighted_median(pairs), 50)

    def test_import_export_balance(self):
        self.assertEqual(net_import_balance(12, 20), -8)


class DatabaseAggregationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def add_period(self, metric, value, endpoint="public_power", zone="", unit="TWh"):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-01-31','monthly',?,?,?,?,?,?,'observed')""",
            (SOURCE_NAME, endpoint, zone, metric, value, unit),
        )

    def add_capacity(self, category, value, timestamp="2025-01-01T00:00:00+01:00", code="DE"):
        name = "Deutschland" if code == "DE" else "United Kingdom"
        self.connection.execute(
            """INSERT INTO installed_capacity
               (country_code,country_name,timestamp,source,source_resolution,category,value_mw,quality_status)
               VALUES (?,?,?,?,?,?,?,'observed_end_of_period')""",
            (code, name, timestamp, SOURCE_NAME, "P1Y", category, value),
        )

    def test_time_aggregation_and_trade(self):
        for metric, value in {
            "generation_total": 0.001, "generation_solar": 0.0002, "generation_wind_onshore": 0.0003,
            "generation_wind_offshore": 0, "generation_hydro": 0, "generation_biomass": 0,
            "generation_nuclear": 0.0001, "generation_gas": 0.0004, "generation_coal": 0,
            "generation_lignite": 0, "generation_oil": 0, "generation_other": 0,
            "consumption": 0.0009, "import_total": 0.00005, "export_total": 0.00015, "net_import": -0.0001,
        }.items():
            self.add_period(metric, value, endpoint="cbpf" if metric in {"import_total", "export_total", "net_import"} else "public_power")
        for metric, value, unit in (
            ("day_ahead_price", -10, "EUR/MWh"),
            ("day_ahead_price_median", -10, "EUR/MWh"),
            ("day_ahead_price_min", -10, "EUR/MWh"),
            ("day_ahead_price_max", -10, "EUR/MWh"),
            ("negative_price_intervals", 1, "count"),
            ("negative_price_hours", 1, "hours"),
            ("price_weight_hours", 1, "hours"),
        ):
            self.add_period(metric, value, endpoint="price", zone="DE-LU", unit=unit)
        result = aggregate_country(self.connection, "DE", 2025, 1)
        self.assertAlmostEqual(result["generation_twh"], 0.001)
        self.assertAlmostEqual(result["renewable_twh"], 0.0005)
        self.assertEqual(result["renewable_share_pct"], 50)
        self.assertAlmostEqual(result["net_import_twh"], -0.0001)
        self.assertEqual(result["negative_price_intervals"], 1)
        self.assertEqual(result["negative_price_hours"], 1)

    def test_missing_interval_is_recorded(self):
        importer = Importer(self.connection)
        payload = {
            "interval_minutes": 15,
            "data": [
                {"timestamp": "2025-01-01T00:00:00+01:00"},
                {"timestamp": "2025-01-01T00:15:00+01:00"},
                {"timestamp": "2025-01-01T00:45:00+01:00"},
            ],
        }
        from electricity_atlas.config import COUNTRIES
        importer._check_intervals("public_power", COUNTRIES["DE"], Period("2025-01-01", "2025-01-01"), payload)
        issue = self.connection.execute("SELECT * FROM quality_issue").fetchone()
        self.assertEqual(issue["issue_type"], "missing_intervals")
        self.assertEqual(issue["details"], "1")

    def test_incomplete_source_does_not_emit_precise_generation_total(self):
        self.add_period("generation_total", 0.001)
        self.connection.execute(
            """INSERT INTO quality_issue
               (country_code,endpoint,period_start,period_end,issue_type,severity,details)
               VALUES ('DE','public_power','2025-01-01','2025-01-31','missing_expected_series','error','[\"solar\"]')"""
        )
        result = aggregate_country(self.connection, "DE", 2025, 1)
        self.assertIsNone(result["generation_twh"])
        self.assertEqual(result["data_status"], "partial")

    def test_installed_capacity_uses_solar_ac_when_dc_is_absent(self):
        self.add_capacity("fossil_gas", 100)
        self.add_capacity("solar_ac", 50)
        result = installed_capacity_summary(self.connection, "DE", "2026-01-01", 2025)
        self.assertEqual(result["value_mw"], 150)

    def test_installed_capacity_uses_solar_dc_when_ac_is_absent(self):
        self.add_capacity("fossil_gas", 100)
        self.add_capacity("solar_dc", 60)
        result = installed_capacity_summary(self.connection, "DE", "2026-01-01", 2025)
        self.assertEqual(result["value_mw"], 160)

    def test_installed_capacity_prefers_solar_dc_without_double_counting(self):
        self.add_capacity("fossil_gas", 100)
        self.add_capacity("solar_ac", 50)
        self.add_capacity("solar_dc", 60)
        result = installed_capacity_summary(self.connection, "DE", "2026-01-01", 2025)
        self.assertEqual(result["value_mw"], 160)

    def test_stale_installed_capacity_snapshot_is_visible(self):
        self.add_capacity("fossil_gas", 100, timestamp="2020-01-01T00:00:00+00:00", code="UK")
        result = aggregate_country(self.connection, "UK", 2025)
        uk_coverage = next(row for row in coverage_rows(self.connection, 2025) if row["country_code"] == "UK")
        self.assertEqual(result["installed_capacity_snapshot_year"], 2020)
        self.assertEqual(result["installed_capacity_status"], "stale")
        self.assertEqual(result["data_status"], "partial")
        self.assertEqual(uk_coverage["installed_capacity"], "partial")

    def test_current_installed_capacity_snapshot_remains_full(self):
        self.add_capacity("fossil_gas", 100, timestamp="2025-01-01T00:00:00+01:00")
        result = aggregate_country(self.connection, "DE", 2025)
        de_coverage = next(row for row in coverage_rows(self.connection, 2025) if row["country_code"] == "DE")
        self.assertEqual(result["installed_capacity_snapshot"], "2025-01-01T00:00:00+01:00")
        self.assertEqual(result["installed_capacity_status"], "current")
        self.assertEqual(de_coverage["installed_capacity"], "full")


if __name__ == "__main__":
    unittest.main()
