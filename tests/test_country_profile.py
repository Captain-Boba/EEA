import unittest

from electricity_atlas.config import COUNTRIES, EMBER_SOURCE_NAME, EUROSTAT_SOURCE_NAME, JRC_SOURCE_NAME
from electricity_atlas.country_profile import build_country_profile
from electricity_atlas.db import connect, initialize


class CountryProfileTests(unittest.TestCase):
    def setUp(self):
        self.connection = connect(":memory:")
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def insert(self, code, start, end, granularity, source, metric, value, unit, series="", quality="observed"):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (code, start, end, granularity, source, "fixture", series, metric, value, unit, quality),
        )
        self.connection.commit()

    @staticmethod
    def metrics(profile):
        return {
            metric["id"]: metric
            for section in profile["sections"]
            for metric in section["metrics"]
        }

    def test_profile_is_catalog_driven_and_keeps_missing_values_null(self):
        profile = build_country_profile(self.connection, "DE", 2025)
        metrics = self.metrics(profile)
        self.assertEqual(profile["country"], {"code": "DE", "name": "Deutschland"})
        self.assertEqual(len(metrics), 82)
        self.assertIsNone(metrics["generation_twh"]["value"])
        self.assertEqual(metrics["generation_twh"]["data_status"], "missing")
        self.assertEqual(metrics["generation_twh"]["temporal_basis"], "yearly")
        self.assertIn("source", metrics["generation_twh"])
        self.assertIn("quality_status", metrics["generation_twh"])

    def test_month_profile_separates_monthly_yearly_and_snapshot_data(self):
        self.insert("DE", "2025-07-01", "2025-07-31", "monthly", EMBER_SOURCE_NAME, "generation_total", 42, "TWh")
        self.insert("DE", "2025-01-01", "2025-12-31", "yearly", EMBER_SOURCE_NAME, "generation_total", 500, "TWh")
        self.insert("DE", "2025-01-01", "2025-12-31", "yearly", EUROSTAT_SOURCE_NAME, "population", 84_000_000, "people")
        self.insert("DE", "2026-08-01", "2026-08-12", "snapshot", JRC_SOURCE_NAME, "pumped_storage_energy_gwh", 3, "GWh", "operational:pumped_storage")
        profile = build_country_profile(self.connection, "DE", 2025, 7)
        metrics = self.metrics(profile)
        self.assertEqual(metrics["generation_twh"]["value"], 42)
        self.assertEqual(metrics["generation_twh"]["temporal_basis"], "monthly")
        self.assertEqual(metrics["population"]["temporal_basis"], "yearly")
        self.assertEqual(metrics["population"]["actual_period"], "2025")
        self.assertEqual(metrics["pumped_storage_energy_gwh"]["temporal_basis"], "snapshot")
        self.assertEqual(metrics["pumped_storage_energy_gwh"]["actual_period"], "2026-08-12")

    def test_capacity_uses_actual_previous_reporting_year_without_backfill(self):
        self.insert("DE", "2024-01-01", "2024-12-31", "yearly", EUROSTAT_SOURCE_NAME, "capacity_total_gw", 266.344, "GW")
        self.insert("DE", "2024-01-01", "2024-12-31", "yearly", EUROSTAT_SOURCE_NAME, "capacity_solar_gw", 91.204, "GW")
        profile = build_country_profile(self.connection, "DE", 2025)
        metrics = self.metrics(profile)
        self.assertEqual(metrics["capacity_total_gw"]["value"], 266.344)
        self.assertEqual(metrics["capacity_total_gw"]["actual_period"], "2024")
        self.assertEqual(metrics["capacity_solar_gw"]["unit"], "GW")

    def test_every_atlas_country_is_retrievable_and_input_is_validated(self):
        for code in COUNTRIES:
            with self.subTest(code=code):
                self.assertEqual(build_country_profile(self.connection, code, 2025)["country"]["code"], code)
        for country, year, month, message in (("ZZ", 2025, None, "known Atlas"), ("DE", 2014, None, "between"), ("DE", 2025, 13, "month")):
            with self.subTest(country=country, year=year, month=month), self.assertRaisesRegex(ValueError, message):
                build_country_profile(self.connection, country, year, month)
