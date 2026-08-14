import unittest
from datetime import date

from electricity_atlas.config import COUNTRIES, EMBER_SOURCE_NAME, EUROSTAT_SOURCE_NAME
from electricity_atlas.db import connect, initialize
from electricity_atlas.timeseries import build_timeseries


class TimeseriesTests(unittest.TestCase):
    def setUp(self):
        self.connection = connect(":memory:")
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def insert(
        self,
        code,
        start,
        end,
        granularity,
        metric,
        value,
        unit="TWh",
        source=EMBER_SOURCE_NAME,
        series="",
    ):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                code,
                start,
                end,
                granularity,
                source,
                "fixture",
                series,
                metric,
                value,
                unit,
                "observed",
            ),
        )
        self.connection.commit()

    def test_accepts_ten_unique_countries_and_rejects_eleven(self):
        codes = list(COUNTRIES)[:10]
        result = build_timeseries(
            self.connection,
            "generation_twh",
            codes,
            "2025-01",
            "2025-01",
            today=date(2026, 8, 13),
        )
        self.assertEqual([row["country_code"] for row in result["countries"]], codes)
        with self.assertRaisesRegex(ValueError, "1 to 10"):
            build_timeseries(
                self.connection,
                "generation_twh",
                list(COUNTRIES)[:11],
                "2025-01",
                "2025-01",
                today=date(2026, 8, 13),
            )

    def test_rejects_duplicate_unknown_and_empty_countries(self):
        for codes, message in ((["DE", "de"], "duplicate"), (["ZZ"], "unknown"), ([], "1 to 10")):
            with self.subTest(codes=codes), self.assertRaisesRegex(ValueError, message):
                build_timeseries(
                    self.connection,
                    "generation_twh",
                    codes,
                    "2025-01",
                    "2025-01",
                    today=date(2026, 8, 13),
                )

    def test_rejects_unknown_snapshot_metric_and_invalid_ranges(self):
        cases = (
            ("unknown", "2025-01", "2025-01", "known Atlas metric"),
            ("battery_power_gw", "2025-01", "2025-01", "snapshot-only"),
            ("generation_twh", "2025-03", "2025-02", "after end"),
            ("generation_twh", "2014-12", "2015-01", "between 2015-01"),
            ("generation_twh", "2026-09", "2026-09", "between 2015-01"),
            ("population", "2025-01", "2025-01", "YYYY"),
        )
        for metric, start, end, message in cases:
            with self.subTest(metric=metric, start=start), self.assertRaisesRegex(ValueError, message):
                build_timeseries(
                    self.connection,
                    metric,
                    ["DE"],
                    start,
                    end,
                    today=date(2026, 8, 13),
                )

    def test_monthly_series_is_chronological_and_preserves_gap(self):
        self.insert("DE", "2025-01-01", "2025-01-31", "monthly", "generation_total", 30)
        self.insert("DE", "2025-03-01", "2025-03-31", "monthly", "generation_total", 33)
        result = build_timeseries(
            self.connection,
            "generation_twh",
            ["DE"],
            "2025-01",
            "2025-03",
            today=date(2026, 8, 13),
        )
        self.assertEqual(result["granularity"], "monthly")
        points = result["countries"][0]["values"]
        self.assertEqual([point["period"] for point in points], ["2025-01", "2025-02", "2025-03"])
        self.assertEqual([point["value"] for point in points], [30.0, None, 33.0])
        self.assertEqual(points[1]["data_status"], "missing")

    def test_yearly_metric_uses_years(self):
        self.insert(
            "DE",
            "2020-01-01",
            "2020-12-31",
            "yearly",
            "population",
            83_000_000,
            unit="people",
            source=EUROSTAT_SOURCE_NAME,
        )
        result = build_timeseries(
            self.connection,
            "population",
            ["DE"],
            "2019",
            "2020",
            today=date(2026, 8, 13),
        )
        self.assertEqual(result["granularity"], "yearly")
        self.assertEqual(
            [point["value"] for point in result["countries"][0]["values"]],
            [None, 83_000_000.0],
        )

    def test_atlas_average_uses_all_countries_excludes_missing_and_includes_zero(self):
        self.insert("DE", "2025-01-01", "2025-01-31", "monthly", "generation_total", 30)
        self.insert("FR", "2025-01-01", "2025-01-31", "monthly", "generation_total", 20)
        self.insert("AT", "2025-01-01", "2025-01-31", "monthly", "generation_total", 0)
        result = build_timeseries(
            self.connection,
            "generation_twh",
            ["DE"],
            "2025-01",
            "2025-01",
            today=date(2026, 8, 13),
        )
        self.assertEqual(result["countries"][0]["values"][0]["value"], 30.0)
        self.assertAlmostEqual(result["atlas_average"]["values"][0]["value"], 50 / 3)
        self.assertNotIn("coverage", result["atlas_average"])

    def test_current_period_is_marked_provisional(self):
        result = build_timeseries(
            self.connection,
            "generation_twh",
            ["DE"],
            "2026-08",
            "2026-08",
            today=date(2026, 8, 13),
        )
        self.assertEqual(
            result["countries"][0]["values"][0]["period_status"],
            "provisional_current_month",
        )

    def test_monthly_baseline_uses_matching_months_in_selected_start_year(self):
        self.insert("DE", "2023-07-01", "2023-07-31", "monthly", "generation_total", 10)
        self.insert("DE", "2023-08-01", "2023-08-31", "monthly", "generation_total", 20)
        result = build_timeseries(
            self.connection,
            "generation_twh",
            ["DE"],
            "2023-07",
            "2026-08",
            today=date(2026, 8, 13),
        )
        self.assertEqual(
            result["comparison_baseline"],
            {"year": 2023, "method": "same_calendar_month"},
        )
        baseline_values = {
            point["period"]: point["value"]
            for point in result["countries"][0]["baseline_values"]
        }
        self.assertEqual(len(baseline_values), 12)
        self.assertEqual(baseline_values["2023-07"], 10.0)
        self.assertEqual(baseline_values["2023-08"], 20.0)

    def test_yearly_baseline_is_the_selected_start_year(self):
        self.insert(
            "DE",
            "2020-01-01",
            "2020-12-31",
            "yearly",
            "population",
            80_000_000,
            unit="people",
            source=EUROSTAT_SOURCE_NAME,
        )
        result = build_timeseries(
            self.connection,
            "population",
            ["DE"],
            "2020",
            "2021",
            today=date(2026, 8, 13),
        )
        self.assertEqual(result["comparison_baseline"], {"year": 2020, "method": "annual"})
        self.assertEqual(result["countries"][0]["baseline_values"][0]["period"], "2020")
        self.assertEqual(result["countries"][0]["baseline_values"][0]["value"], 80_000_000.0)


if __name__ == "__main__":
    unittest.main()
