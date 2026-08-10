import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from electricity_atlas.cli import main
from electricity_atlas.config import COUNTRIES, SOURCE_NAME
from electricity_atlas.db import connect, initialize
from electricity_atlas.importer import Importer, Period


def public_power_payload(start_date: str, value: float = 10.0, malformed_second: bool = False):
    timestamp = f"{start_date}T00:00:00+01:00"
    series_ids = [
        "solar",
        "wind_onshore",
        "wind_offshore",
        "hydro_run_of_river",
        "biomass",
        "fossil_gas",
        "fossil_hard_coal",
        "fossil_brown_coal_lignite",
        "load",
        "renewable_share_of_generation",
    ]
    values = {series_id: value for series_id in series_ids}
    values["load"] = value * 10
    values["renewable_share_of_generation"] = 50.0
    data = [{"timestamp": timestamp, "values": values}]
    if malformed_second:
        data.append({"timestamp": "not-a-timestamp", "values": values})
    return {
        "endpoint": "public_power",
        "country": "de",
        "timezone": "Europe/Berlin",
        "resolution": "PT1H",
        "interval_minutes": 60,
        "unit": "MW",
        "license": "fixture",
        "available_from": timestamp,
        "available_until": timestamp,
        "series": [{"id": series_id} for series_id in series_ids],
        "data": data,
    }


def cbpf_payload(start_date: str):
    timestamp = f"{start_date}T00:00:00+01:00"
    return {
        "resolution": "PT1H",
        "interval_minutes": 60,
        "unit": "GW",
        "license": "fixture",
        "available_from": timestamp,
        "available_until": timestamp,
        "series": [{"id": "france"}, {"id": "sum"}],
        "data": [{"timestamp": timestamp, "values": {"france": 1.0, "sum": 1.0}}],
    }


def price_payload(start_date: str):
    timestamp = f"{start_date}T00:00:00+01:00"
    return {
        "resolution": "PT1H",
        "interval_minutes": 60,
        "unit": "EUR/MWh",
        "license": "fixture",
        "available_from": timestamp,
        "available_until": timestamp,
        "series": {"id": "day_ahead_price"},
        "data": [{"timestamp": timestamp, "values": {"day_ahead_price": 50.0}}],
    }


class ImportSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        self.connection = connect(self.db_path)
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()
        self.tempdir.cleanup()

    def add_observation(self, month: int, value: float, day: int = 1):
        timestamp = f"2025-{month:02d}-{day:02d}T00:00:00+01:00"
        self.connection.execute(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES ('DE','Deutschland','',?,?,?,?, 'PT1H',60,'generation_total',?,'MW','observed')""",
            (timestamp, timestamp, SOURCE_NAME, "public_power", value),
        )

    @staticmethod
    def dispatch_payload(endpoint, target_name, target, start_date="", end_date="", extra=None, refresh=False):
        if endpoint == "public_power":
            return public_power_payload(start_date, 20.0)
        if endpoint == "cbpf":
            return cbpf_payload(start_date)
        if endpoint == "price":
            return price_payload(start_date)
        raise AssertionError(f"Unexpected endpoint in fixture: {endpoint}")

    def test_january_july_import_preserves_all_other_months(self):
        for month in range(1, 13):
            self.add_observation(month, float(month))
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)
        with patch.object(importer.client, "get", side_effect=self.dispatch_payload):
            result = importer.import_country("DE", 2025, [1, 7])

        self.assertEqual(result["errors"], 0)
        values = {
            int(row["month"]): row["value"]
            for row in self.connection.execute(
                """SELECT CAST(substr(timestamp,6,2) AS INTEGER) AS month, value
                   FROM observation
                   WHERE country_code='DE' AND source_endpoint='public_power'
                     AND metric='generation_total'"""
            )
        }
        self.assertEqual(set(values), set(range(1, 13)))
        self.assertNotEqual(values[1], 1.0)
        self.assertNotEqual(values[7], 7.0)
        for month in set(range(1, 13)) - {1, 7}:
            self.assertEqual(values[month], float(month))
        self.assertEqual(result["skipped"][0]["endpoint"], "installed_power")

    def test_failed_refresh_preserves_old_observations(self):
        self.add_observation(1, 123.0)
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)

        def dispatch(endpoint, *args, **kwargs):
            if endpoint == "public_power":
                raise RuntimeError("simulated download failure")
            return self.dispatch_payload(endpoint, *args, **kwargs)

        with patch.object(importer.client, "get", side_effect=dispatch):
            result = importer.import_country("DE", 2025, [1])
        value = self.connection.execute(
            """SELECT value FROM observation
               WHERE country_code='DE' AND source_endpoint='public_power' AND metric='generation_total'"""
        ).fetchone()[0]
        self.assertEqual(value, 123.0)
        self.assertEqual(result["errors"], 1)
        self.assertGreater(result["failures"][0]["preserved_rows"], 0)

    def test_failure_after_cache_commit_does_not_lose_old_data(self):
        self.add_observation(1, 321.0)
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)

        def cache_then_malformed(*args, **kwargs):
            payload = public_power_payload("2025-01-01", 30.0, malformed_second=True)
            self.connection.execute(
                """INSERT INTO api_cache
                   (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
                   VALUES ('public_power','de','2025-01-01','2025-01-31','fixture','now',200,'hash',?)""",
                (json.dumps(payload),),
            )
            self.connection.commit()
            return payload

        with patch.object(importer.client, "get", side_effect=cache_then_malformed):
            with self.assertRaises(ValueError):
                importer._import_period("public_power", COUNTRIES["DE"], Period("2025-01-01", "2025-01-31"))
        rows = list(
            self.connection.execute(
                """SELECT timestamp,value FROM observation
                   WHERE country_code='DE' AND source_endpoint='public_power' AND metric='generation_total'"""
            )
        )
        self.assertEqual([(row["timestamp"], row["value"]) for row in rows], [("2025-01-01T00:00:00+01:00", 321.0)])
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM api_cache").fetchone()[0], 1)

    def test_validation_failure_preserves_old_data(self):
        self.add_observation(1, 222.0)
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)
        invalid = public_power_payload("2025-01-01")
        invalid["data"] = []
        with patch.object(importer.client, "get", return_value=invalid):
            with self.assertRaises(ValueError):
                importer._import_period("public_power", COUNTRIES["DE"], Period("2025-01-01", "2025-01-31"))
        value = self.connection.execute(
            """SELECT value FROM observation
               WHERE country_code='DE' AND source_endpoint='public_power' AND metric='generation_total'"""
        ).fetchone()[0]
        self.assertEqual(value, 222.0)

    def test_january_refresh_rejects_valid_february_record_without_writes(self):
        self.add_observation(1, 444.0)
        self.connection.commit()

        def dispatch(endpoint, target_name, target, start_date="", end_date="", extra=None, refresh=False):
            if endpoint == "public_power":
                payload = public_power_payload("2025-01-01", 60.0)
                payload["data"].append(public_power_payload("2025-02-01", 70.0)["data"][0])
                return payload
            return self.dispatch_payload(endpoint, target_name, target, start_date, end_date, extra, refresh)

        output = io.StringIO()
        with patch("electricity_atlas.importer.EnergyChartsClient.get", side_effect=dispatch):
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--db", str(self.db_path), "import", "--year", "2025",
                    "--months", "1", "--countries", "DE", "--refresh",
                ])

        rows = self.connection.execute(
            """SELECT timestamp,value FROM observation
               WHERE country_code='DE' AND source_endpoint='public_power'
               ORDER BY timestamp"""
        ).fetchall()
        self.assertNotEqual(exit_code, 0)
        self.assertIn("outside requested period 2025-01-01..2025-01-31", output.getvalue())
        self.assertEqual([(row["timestamp"], row["value"]) for row in rows], [
            ("2025-01-01T00:00:00+01:00", 444.0),
        ])

    def test_successful_refresh_fully_replaces_target_without_duplicates(self):
        self.add_observation(1, 1.0, 1)
        self.add_observation(1, 2.0, 2)
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)
        with patch.object(importer.client, "get", return_value=public_power_payload("2025-01-01", 40.0)):
            importer._import_period("public_power", COUNTRIES["DE"], Period("2025-01-01", "2025-01-31"))
        total_rows = self.connection.execute(
            """SELECT COUNT(*) FROM observation
               WHERE country_code='DE' AND source_endpoint='public_power' AND metric='generation_total'"""
        ).fetchone()[0]
        distinct_rows = self.connection.execute(
            """SELECT COUNT(DISTINCT timestamp_utc) FROM observation
               WHERE country_code='DE' AND source_endpoint='public_power' AND metric='generation_total'"""
        ).fetchone()[0]
        self.assertEqual(total_rows, 1)
        self.assertEqual(distinct_rows, 1)

    def test_quality_issues_outside_target_period_are_preserved(self):
        self.connection.execute(
            """INSERT INTO quality_issue
               (country_code,endpoint,period_start,period_end,issue_type,severity,details)
               VALUES ('DE','public_power','2025-01-01','2025-12-31','old_issue','warning','keep outside')"""
        )
        self.connection.commit()
        importer = Importer(self.connection, refresh=True)
        with patch.object(importer.client, "get", return_value=public_power_payload("2025-01-01", 50.0)):
            importer._import_period("public_power", COUNTRIES["DE"], Period("2025-01-01", "2025-01-31"))
        old_issues = self.connection.execute(
            """SELECT period_start,period_end FROM quality_issue
               WHERE country_code='DE' AND endpoint='public_power' AND issue_type='old_issue'"""
        ).fetchall()
        self.assertEqual([(row["period_start"], row["period_end"]) for row in old_issues], [("2025-02-01", "2025-12-31")])

    def test_cli_returns_nonzero_for_partial_failure(self):
        success = {"errors": 0, "successes": [{"endpoint": "public_power"}], "failures": []}
        failure = {
            "errors": 1,
            "successes": [{"endpoint": "cbpf"}],
            "failures": [{"endpoint": "public_power", "error": "failed", "preserved_rows": 12}],
        }
        output = io.StringIO()
        with patch("electricity_atlas.cli.Importer.import_country", side_effect=[success, failure]):
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--db", str(self.db_path), "import", "--year", "2025",
                    "--months", "1", "--countries", "DE", "FR",
                ])
        self.assertNotEqual(exit_code, 0)
        self.assertIn('"preserved_rows": 12', output.getvalue())


if __name__ == "__main__":
    unittest.main()
