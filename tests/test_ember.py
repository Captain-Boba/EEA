import contextlib
import copy
import calendar
import io
import json
import os
import sqlite3
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.cli import main
from electricity_atlas.config import EMBER_ISO3, SOURCE_NAME
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


class EmberImportAndAggregationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_iso2_to_iso3_mapping_includes_all_pilot_countries_and_uk(self):
        self.assertEqual(EMBER_ISO3, {
            "DE": "DEU", "FR": "FRA", "ES": "ESP", "IT": "ITA", "PL": "POL",
            "UK": "GBR", "NO": "NOR", "SE": "SWE", "DK": "DNK", "NL": "NLD",
        })
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

    def test_sources_are_strictly_separated(self):
        timestamp = "2025-01-01T00:00:00+01:00"
        self.connection.execute(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES ('DE','Deutschland','',?,?,?,?,?,60,'generation_total',100,'MW','observed')""",
            (timestamp, timestamp, SOURCE_NAME, "public_power", "PT1H"),
        )
        self.connection.execute(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES ('DE','2025-01-01','2025-12-31','yearly','ember',
                       'electricity-generation/yearly','Solar','generation_solar',50,'TWh','observed')"""
        )
        energy_charts = aggregate_country(self.connection, "DE", 2025)
        ember = aggregate_country(self.connection, "DE", 2025, source="ember")
        self.assertAlmostEqual(energy_charts["generation_twh"], 0.0001)
        self.assertEqual(ember["generation_twh"], 50.0)
        self.assertIsNone(ember["price_avg_eur_mwh"])
        self.assertIsNone(ember["import_twh"])

    def test_combined_view_prefers_energy_charts_generation_and_fills_ember_gaps(self):
        timestamp = "2025-01-01T00:00:00+01:00"
        self.connection.execute(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES ('DE','Deutschland','',?,?,?,?,?,60,'generation_total',100,'MW','observed')""",
            (timestamp, timestamp, SOURCE_NAME, "public_power", "PT1H"),
        )
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [
                ("DE", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "electricity-generation/yearly", "Solar", "generation_solar", 50, "TWh", "observed"),
                ("DE", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "electricity-demand/yearly", "", "consumption", 500, "TWh", "observed"),
                ("DE", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "carbon-intensity/yearly", "", "carbon_intensity", 200, "gCO2/kWh", "observed"),
            ],
        )

        combined = aggregate_country(self.connection, "DE", 2025, source="combined")

        self.assertAlmostEqual(combined["generation_twh"], 0.0001)
        self.assertEqual(combined["renewable_twh"], 0.0)
        self.assertEqual(combined["consumption_twh"], 500.0)
        self.assertEqual(combined["carbon_intensity_gco2eq_kwh"], 200.0)
        self.assertEqual(combined["generation_source"], "energy-charts")
        self.assertEqual(combined["sources_used"], ["energy-charts", "ember"])
        self.assertEqual(combined["value_sources"]["generation_twh"], "Energy-Charts.info")
        self.assertEqual(combined["value_sources"]["consumption_twh"], "Ember, CC BY 4.0")

    def test_combined_view_uses_ember_generation_without_losing_energy_charts_trade(self):
        timestamp = "2025-01-01T00:00:00+01:00"
        rows = []
        for metric, value in (("import_total", 200), ("export_total", 50)):
            rows.append((
                "UK", "Vereinigtes Königreich", "", timestamp, timestamp, SOURCE_NAME,
                "cbpf", "PT1H", 60, metric, value, "MW", "observed",
            ))
        self.connection.executemany(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [
                ("UK", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "electricity-generation/yearly", "Solar", "generation_solar", 50, "TWh", "observed"),
                ("UK", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "electricity-demand/yearly", "", "consumption", 60, "TWh", "observed"),
                ("UK", "2025-01-01", "2025-12-31", "yearly", "ember",
                 "carbon-intensity/yearly", "", "carbon_intensity", 150, "gCO2/kWh", "observed"),
            ],
        )

        combined = aggregate_country(self.connection, "UK", 2025, source="combined")

        self.assertEqual(combined["generation_twh"], 50.0)
        self.assertEqual(combined["generation_source"], "ember")
        self.assertAlmostEqual(combined["import_twh"], 0.0002)
        self.assertAlmostEqual(combined["export_twh"], 0.00005)
        self.assertAlmostEqual(combined["net_import_twh"], 0.00015)
        self.assertEqual(combined["value_sources"]["generation_twh"], "Ember, CC BY 4.0")
        self.assertEqual(combined["value_sources"]["import_twh"], "Energy-Charts.info")

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


class EmberCliTests(unittest.TestCase):
    def test_missing_key_aborts_before_database_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "must-not-exist.sqlite3"
            previous = Path.cwd()
            stderr = io.StringIO()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(stderr):
                    exit_code = main(["--db", str(db_path), "import", "--source", "ember", "--year", "2025"])
            finally:
                os.chdir(previous)
        self.assertNotEqual(exit_code, 0)
        self.assertFalse(db_path.exists())
        self.assertIn("Ember import aborted", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
