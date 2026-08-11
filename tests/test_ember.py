import contextlib
import copy
import calendar
import io
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.cli import main
from electricity_atlas.config import EMBER_ISO3
from electricity_atlas.db import initialize
from electricity_atlas.ember_client import EmberApiError, EmberClient, load_ember_api_key
from electricity_atlas.ember_importer import EmberImporter


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "ember"


def fixture(name):
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class FixtureEmberClient:
    FILES = {
        "electricity-generation/monthly": "generation_monthly.json",
        "electricity-generation/yearly": "generation_yearly.json",
        "electricity-demand/monthly": "demand_monthly.json",
        "electricity-demand/yearly": "demand_yearly.json",
        "carbon-intensity/monthly": "carbon_monthly.json",
        "carbon-intensity/yearly": "carbon_yearly.json",
    }

    def __init__(self):
        self.calls = []

    def get(self, endpoint, entity_code, start_date, end_date, extra=None, refresh=False):
        self.calls.append((endpoint, entity_code, start_date, end_date, extra, refresh))
        payload = copy.deepcopy(fixture(self.FILES[endpoint]))
        payload["data"] = [
            row for row in payload["data"] if start_date <= row["date"] <= end_date
        ]
        return payload


class FakeResponse:
    def __init__(self, payload):
        self.status = 200
        self.payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class EmberClientTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_environment_key_precedes_local_file_and_values_are_stripped(self):
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text("file-value\n", encoding="utf-8")
            self.assertEqual(load_ember_api_key(key_file, {"EMBER_API_KEY": "  environment-value  "}), "environment-value")
            self.assertEqual(load_ember_api_key(key_file, {}), "file-value")

    def test_key_is_redacted_from_cached_url_and_payload(self):
        secret = "".join(("sensitive", "-test-value"))
        payload = {
            "stats": {"query_parameters_used": {"api_key": secret}},
            "data": [],
            "message": f"request accepted for {secret}",
        }
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text(f" {secret}\n", encoding="utf-8")
            client = EmberClient(self.connection, key_file=key_file)
            captured_urls = []

            def respond(request, timeout):
                captured_urls.append(request.full_url)
                return FakeResponse(payload)

            with patch("electricity_atlas.ember_client.urlopen", side_effect=respond):
                result = client.get("carbon-intensity/yearly", "DEU", "2025", "2025")

        cached = self.connection.execute(
            "SELECT request_url,response_json FROM api_cache WHERE endpoint='ember/carbon-intensity/yearly'"
        ).fetchone()
        self.assertIn(secret, captured_urls[0])
        self.assertNotIn(secret, cached["request_url"])
        self.assertNotIn(secret, cached["response_json"])
        self.assertNotIn(secret, json.dumps(result))
        self.assertIn("api_key=REDACTED", cached["request_url"])

    def test_key_is_redacted_from_http_errors(self):
        secret = "".join(("sensitive", "-error-value"))
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text(secret, encoding="utf-8")
            client = EmberClient(self.connection, key_file=key_file)
            error = HTTPError("https://example.invalid", 403, "Forbidden", {}, BytesIO(f"denied {secret}".encode()))
            with patch("electricity_atlas.ember_client.urlopen", side_effect=error):
                with self.assertRaises(EmberApiError) as caught:
                    client.get("electricity-demand/yearly", "DEU", "2025", "2025", refresh=True)
            error.close()
        self.assertNotIn(secret, str(caught.exception))

    def test_options_endpoint_is_available(self):
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text("test-only-value", encoding="utf-8")
            client = EmberClient(self.connection, key_file=key_file)
            requested = []

            def respond(request, timeout):
                requested.append(request.full_url)
                return FakeResponse({"data": ["DEU", "GBR"]})

            with patch("electricity_atlas.ember_client.urlopen", side_effect=respond):
                result = client.options("electricity-generation", "monthly", "entity_code")
        self.assertEqual(result["data"], ["DEU", "GBR"])
        self.assertIn("/options/electricity-generation/monthly/entity_code?", requested[0])

    def test_covering_history_cache_is_sliced_without_network_request(self):
        cached_payload = {
            "data": [
                {"entity_code": "DEU", "date": "2015-01", "series": "Solar"},
                {"entity_code": "DEU", "date": "2026-07", "series": "Solar"},
            ]
        }
        self.connection.execute(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                "ember/electricity-generation/monthly", "DEU", "2015-01", "2026-09",
                "https://example.invalid?api_key=REDACTED", "2026-08-10T00:00:00+00:00",
                200, "test", json.dumps(cached_payload),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text("test-only-value", encoding="utf-8")
            client = EmberClient(self.connection, key_file=key_file)
            with patch("electricity_atlas.ember_client.urlopen") as urlopen_mock:
                result = client.get(
                    "electricity-generation/monthly", "DEU", "2015-01", "2026-01"
                )

        urlopen_mock.assert_not_called()
        self.assertEqual([row["date"] for row in result["data"]], ["2015-01"])

    def test_legacy_generation_cache_is_reused_only_for_explicit_non_aggregate_request(self):
        cached_payload = {"data": [
            {"entity_code": "DEU", "date": "2025-01", "series": "Solar", "is_aggregate_series": False}
        ]}
        self.connection.execute(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                "ember/electricity-generation/monthly", "DEU", "2025-01", "2026-01",
                "https://example.invalid?api_key=REDACTED", "2026-08-10T00:00:00+00:00",
                200, "test", json.dumps(cached_payload),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            key_file = Path(directory) / "EMBER_API_KEY.txt"
            key_file.write_text("test-only-value", encoding="utf-8")
            client = EmberClient(self.connection, key_file=key_file)
            with patch("electricity_atlas.ember_client.urlopen") as urlopen_mock:
                result = client.get(
                    "electricity-generation/monthly", "DEU", "2025-01", "2026-01",
                    extra={"is_aggregate_series": "false"},
                )

        urlopen_mock.assert_not_called()
        self.assertEqual(result, cached_payload)


class EmberImportAndAggregationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_iso2_to_iso3_mapping_includes_all_atlas_countries_and_uk(self):
        self.assertEqual(len(EMBER_ISO3), 31)
        self.assertEqual(EMBER_ISO3["UK"], "GBR")
        self.assertNotIn("AL", EMBER_ISO3)
        self.assertNotIn("RU", EMBER_ISO3)
        self.assertNotIn("TR", EMBER_ISO3)
        client = FixtureEmberClient()
        client.get = lambda endpoint, entity_code, start_date, end_date, extra=None, refresh=False: (
            client.calls.append((endpoint, entity_code, start_date, end_date, extra, refresh)) or {"data": []}
        )
        result = EmberImporter(self.connection, client=client).import_country("UK", 2025, [1])
        self.assertEqual(result["errors"], 0)
        self.assertEqual({call[1] for call in client.calls}, {"GBR"})

    def test_monthly_and_yearly_values_units_and_series_mapping(self):
        client = FixtureEmberClient()
        result = EmberImporter(self.connection, client=client).import_country("DE", 2025)
        self.assertEqual(result["errors"], 0)
        monthly_generation_call = next(call for call in client.calls if call[0] == "electricity-generation/monthly")
        self.assertEqual(monthly_generation_call[2:4], ("2025-01", "2026-01"))
        monthly = aggregate_country(self.connection, "DE", 2025, 1, source="ember")
        yearly = aggregate_country(self.connection, "DE", 2025, source="ember")
        self.assertEqual(monthly["generation_twh"], 65.0)
        self.assertEqual(monthly["consumption_twh"], 70.0)
        self.assertEqual(monthly["renewable_twh"], 21.0)
        self.assertEqual(monthly["carbon_intensity_gco2eq_kwh"], 250.0)
        self.assertEqual(yearly["generation_twh"], 650.0)
        self.assertEqual(yearly["consumption_twh"], 700.0)
        self.assertEqual(yearly["carbon_intensity_gco2eq_kwh"], 240.0)
        wind = self.connection.execute(
            """SELECT metric,unit FROM period_observation
               WHERE source='ember' AND source_series='Wind' AND granularity='monthly' AND metric='generation_wind'"""
        ).fetchone()
        share = self.connection.execute(
            """SELECT unit FROM period_observation
               WHERE source='ember' AND source_series='Wind' AND granularity='monthly'
                 AND metric='share_of_generation_pct'"""
        ).fetchone()
        self.assertEqual((wind["metric"], wind["unit"]), ("generation_wind", "TWh"))
        self.assertEqual(share["unit"], "%")

    def test_aggregate_series_supply_totals_and_net_import_share_without_double_counting(self):
        class AggregateClient:
            def get(self, endpoint, entity_code, start_date, end_date, extra=None, refresh=False):
                if endpoint == "electricity-generation/monthly":
                    if extra == {"is_aggregate_series": "true"}:
                        series = [
                            ("Total generation", 100.0), ("Renewables", 60.0),
                            ("Fossil", 30.0), ("Demand", 95.0), ("Net imports", 5.0),
                        ]
                        return {"data": [
                            {"entity_code": "DEU", "date": "2025-01", "series": name,
                             "is_aggregate_series": True, "generation_twh": value}
                            for name, value in series
                        ]}
                    return {"data": [
                        {"entity_code": "DEU", "date": "2025-01", "series": name,
                         "is_aggregate_series": False, "generation_twh": value}
                        for name, value in (("Solar", 10.0), ("Wind", 20.0), ("Nuclear", 10.0))
                    ]}
                if endpoint == "electricity-demand/monthly":
                    return {"data": [{"entity_code": "DEU", "date": "2025-01", "demand_twh": 95.0}]}
                if endpoint == "carbon-intensity/monthly":
                    return {"data": [{"entity_code": "DEU", "date": "2025-01", "emissions_intensity_gco2_per_kwh": 200.0}]}
                return {"data": []}

        result = EmberImporter(self.connection, client=AggregateClient()).import_country("DE", 2025, [1])
        self.assertEqual(result["errors"], 0)
        summary = aggregate_country(self.connection, "DE", 2025, 1)
        self.assertEqual(summary["generation_twh"], 100.0)
        self.assertEqual(summary["renewable_twh"], 60.0)
        self.assertEqual(summary["fossil_twh"], 30.0)
        self.assertEqual(summary["nuclear_twh"], 10.0)
        self.assertEqual(summary["net_imports_twh"], 5.0)
        self.assertAlmostEqual(summary["net_import_share_pct"], 5 / 95 * 100)

    def test_history_range_separates_completed_history_from_current_year(self):
        client = FixtureEmberClient()
        result = EmberImporter(self.connection, client=client).import_range(
            "DE", 2015, today=date(2026, 8, 10)
        )

        self.assertEqual(result["errors"], 0)
        self.assertEqual(len(client.calls), 11)
        monthly_calls = [call for call in client.calls if call[0].endswith("/monthly")]
        yearly_calls = [call for call in client.calls if call[0].endswith("/yearly")]
        self.assertEqual(
            {call[2:4] for call in monthly_calls},
            {("2015-01", "2026-01"), ("2026-01", "2026-09")},
        )
        self.assertEqual({call[2:4] for call in yearly_calls}, {("2015", "2025")})
        self.assertEqual(
            {call[0] for call in yearly_calls},
            {"electricity-generation/yearly", "carbon-intensity/yearly"},
        )
        generation_calls = [call for call in client.calls if call[0].startswith("electricity-generation/")]
        self.assertEqual(
            {call[4]["is_aggregate_series"] for call in generation_calls},
            {"true", "false"},
        )

    def test_history_range_rejects_years_outside_atlas_window(self):
        importer = EmberImporter(self.connection, client=FixtureEmberClient())
        with self.assertRaises(ValueError):
            importer.import_range("DE", 2014, today=date(2026, 8, 10))
        with self.assertRaises(ValueError):
            importer.import_range("DE", 2015, 2027, today=date(2026, 8, 10))

    def test_empty_supported_country_period_is_coverage_not_import_error(self):
        client = FixtureEmberClient()
        client.get = lambda *args, **kwargs: {"data": []}
        result = EmberImporter(self.connection, client=client).import_country("ME", 2025, [1])
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["rows"], 0)
        aggregate = aggregate_country(self.connection, "ME", 2025, 1, source="ember")
        self.assertEqual(aggregate["data_status"], "missing")

    def test_albania_is_not_an_atlas_country(self):
        with self.assertRaisesRegex(ValueError, "Unsupported Ember country"):
            EmberImporter(self.connection, client=FixtureEmberClient()).import_country("AL", 2025, [1])
        with self.assertRaisesRegex(ValueError, "Unsupported pilot country"):
            aggregate_country(self.connection, "AL", 2025, 1, source="ember")

    def test_invalid_response_preserves_existing_period_atomically(self):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-01-31','monthly','ember',
                       'electricity-generation/monthly','Solar','generation_solar',99,'TWh','observed')"""
        )
        self.connection.commit()

        class InvalidClient:
            def get(self, endpoint, entity_code, start_date, end_date, extra=None, refresh=False):
                if endpoint == "electricity-generation/monthly":
                    payload = fixture("generation_monthly.json")
                    payload["data"].append({
                        "entity": "Germany", "entity_code": "DEU", "date": "2025-02",
                        "series": "Solar", "is_aggregate_series": False,
                        "generation_twh": 1.0, "share_of_generation_pct": 1.0,
                    })
                    return payload
                return {"data": []}

        result = EmberImporter(self.connection, refresh=True, client=InvalidClient()).import_country("DE", 2025, [1])
        old = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source='ember' AND country_code='DE' AND metric='generation_solar'"""
        ).fetchall()
        february = self.connection.execute(
            "SELECT COUNT(*) FROM period_observation WHERE source='ember' AND period_start='2025-02-01'"
        ).fetchone()[0]
        self.assertEqual(result["errors"], 1)
        self.assertEqual([row["value"] for row in old], [99.0])
        self.assertEqual(february, 0)

    def test_non_ember_rows_are_ignored_and_other_sources_are_rejected(self):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                 source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-01-31','monthly','legacy','legacy','',
                       'generation_total',999,'TWh','observed')"""
        )
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-01-31','monthly','ember',
                       'electricity-generation/monthly','Solar','generation_solar',50,'TWh','observed')"""
        )
        ember = aggregate_country(self.connection, "DE", 2025, 1)
        self.assertEqual(ember["generation_twh"], 50.0)
        self.assertIsNone(ember["price_avg_eur_mwh"])
        with self.assertRaisesRegex(ValueError, "source must be 'ember'"):
            aggregate_country(self.connection, "DE", 2025, 1, source="legacy")

    def test_missing_values_remain_none_instead_of_invented_zeroes(self):
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-12-31','yearly','ember',
                       'electricity-demand/yearly','','consumption',500,'TWh','observed')"""
        )
        result = aggregate_country(self.connection, "DE", 2025, source="ember")
        self.assertEqual(result["consumption_twh"], 500.0)
        self.assertIsNone(result["generation_twh"])
        self.assertIsNone(result["renewable_twh"])
        self.assertIsNone(result["solar_twh"])
        self.assertIsNone(result["carbon_intensity_gco2eq_kwh"])
        self.assertEqual(result["data_status"], "partial")

    def test_yearly_demand_can_be_derived_only_from_twelve_monthly_values(self):
        rows = []
        for month in range(1, 13):
            last_day = calendar.monthrange(2025, month)[1]
            rows.append((
                "DE", f"2025-{month:02d}-01", f"2025-{month:02d}-{last_day:02d}",
                "monthly", "ember", "electricity-demand/monthly", "", "consumption",
                float(month), "TWh", "observed",
            ))
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        result = aggregate_country(self.connection, "DE", 2025, source="ember")
        self.assertEqual(result["consumption_twh"], 78.0)
        self.assertEqual(result["quality_issues"][0]["issue_type"], "yearly_demand_derived_from_monthly")

    def test_current_year_is_aggregated_ytd_from_available_months(self):
        year = date.today().year
        rows = []
        for month, generation, demand, carbon in ((1, 10.0, 20.0, 100.0), (2, 30.0, 40.0, 200.0)):
            last_day = calendar.monthrange(year, month)[1]
            start = f"{year}-{month:02d}-01"
            end = f"{year}-{month:02d}-{last_day:02d}"
            rows.extend(
                [
                    ("DE", start, end, "monthly", "ember", "electricity-generation/monthly", "Solar", "generation_solar", generation, "TWh", "observed"),
                    ("DE", start, end, "monthly", "ember", "electricity-demand/monthly", "", "consumption", demand, "TWh", "observed"),
                    ("DE", start, end, "monthly", "ember", "carbon-intensity/monthly", "", "carbon_intensity", carbon, "gCO2/kWh", "observed"),
                ]
            )
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )

        result = aggregate_country(self.connection, "DE", year, source="ember")

        self.assertEqual(result["period_status"], "ytd")
        self.assertEqual(result["generation_twh"], 40.0)
        self.assertEqual(result["consumption_twh"], 60.0)
        self.assertEqual(result["carbon_intensity_gco2eq_kwh"], 175.0)
        self.assertEqual(result["data_status"], "partial")
        self.assertEqual(result["quality_issues"][0]["issue_type"], "current_year_derived_from_monthly")


class EmberCliTests(unittest.TestCase):
    def test_history_range_cli_dispatches_to_ember_range_import(self):
        result = {"errors": 0, "rows": 1, "successes": [], "failures": []}
        with patch("electricity_atlas.cli.load_ember_api_key"), patch(
            "electricity_atlas.cli.database"
        ), patch(
            "electricity_atlas.cli.EmberImporter.import_range", return_value=result
        ) as import_range, patch("sys.stdout", new=io.StringIO()):
            exit_code = main([
                "import", "--from-year", "2015", "--countries", "DE"
            ])

        self.assertEqual(exit_code, 0)
        import_range.assert_called_once_with("DE", 2015, None)

    def test_missing_key_aborts_before_database_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "must-not-exist.sqlite3"
            previous = Path.cwd()
            stderr = io.StringIO()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(stderr):
                    exit_code = main(["--db", str(db_path), "import", "--year", "2025"])
            finally:
                os.chdir(previous)
        self.assertNotEqual(exit_code, 0)
        self.assertFalse(db_path.exists())
        self.assertIn("Ember import aborted", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
