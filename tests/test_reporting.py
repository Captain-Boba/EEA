import contextlib
import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from electricity_atlas.cli import main
from electricity_atlas.db import database, read_database
from electricity_atlas.ember_importer import EmberImporter
from electricity_atlas.reporting import MANIFEST_NAME, REPORT_FILES, build_reports, write_reports


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "atlas.sqlite3"
        self.output = self.root / "reports"
        self.as_of = date(2026, 9, 23)
        with database(self.db):
            pass
        self.payload = {"data": [{"entity_code": "DEU", "date": "2025", "series": "Solar",
                                  "is_aggregate_series": False, "generation_twh": 0.0}]}
        self.cache(self.payload)
        with database(self.db) as connection:
            rows = EmberImporter(connection, client=object())._normalize_payload(
                "DE", "electricity-generation/yearly", "yearly", "2025", "2025", self.payload)
            for row in rows:
                connection.execute("INSERT INTO period_observation VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (row.country_code, row.period_start, row.period_end, row.granularity, "ember",
                     row.source_endpoint, row.source_series, row.metric, row.value, row.unit, "observed"))
            connection.commit()

    def tearDown(self):
        self.temp.cleanup()

    def cache(self, payload, *, start="2025", end="2025", fetched="2026-08-25T00:00:00+00:00"):
        raw = json.dumps(payload)
        with database(self.db) as connection:
            connection.execute("INSERT OR REPLACE INTO api_cache "
                "(endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json) "
                "VALUES (?,?,?,?,?,?,?,?,?)", ("ember/electricity-generation/yearly",
                "DEU|is_aggregate_series=false", start, end, "https://example.invalid?api_key=private-secret",
                fetched, 200, hashlib.sha256(raw.encode()).hexdigest(), raw))
            connection.commit()

    def report(self):
        with patch("electricity_atlas.ember_client.urlopen", side_effect=AssertionError("No network")), patch(
            "electricity_atlas.ember_client.load_ember_api_key", side_effect=AssertionError("No credentials")):
            return write_reports(self.db, self.output, 2025, as_of=self.as_of)

    def test_reproducible_bundle_preserves_database_and_null_versus_zero(self):
        before = self.db.read_bytes()
        report = self.report()
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["status"], "warnings")  # Intentionally incomplete fixture.
        self.assertEqual(report["ember_cache_checks"][0]["counts"], {"matched": 1})
        first = {path.name: path.read_bytes() for path in self.output.iterdir()}
        self.report()
        self.assertEqual(first, {path.name: path.read_bytes() for path in self.output.iterdir()})
        self.assertEqual(self.db.read_bytes(), before)
        manifest = json.loads(first[MANIFEST_NAME])
        self.assertEqual(set(manifest["files"]), set(REPORT_FILES))
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256(first[name]).hexdigest(), digest)
        summary = {row["country_code"]: row for row in json.loads(first["SUMMARY.generated.json"])}
        self.assertEqual(summary["DE"]["generation_twh"], 0.0)
        self.assertIsNone(summary["FR"]["generation_twh"])
        self.assertNotIn("private-secret", b"".join(first.values()).decode())

    def test_newest_missing_cache_value_is_not_masked_by_older_response(self):
        self.cache({"data": []}, start="2015", end="2025", fetched="2026-09-23T00:00:00+00:00")
        report = self.report()
        self.assertEqual(report["errors"], 1)
        self.assertEqual(report["ember_cache_checks"][0]["counts"], {"missing_in_latest_cache": 1})

    def test_retained_values_are_warnings_not_newly_verified(self):
        self.cache({"data": []})
        with database(self.db) as connection:
            connection.execute("UPDATE period_observation SET quality_status='retained_source_gap'")
            connection.commit()
        report = self.report()
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["ember_cache_checks"][0]["counts"], {"retained_source_gap": 1})

    def test_missing_cache_is_unverifiable_not_passed(self):
        with database(self.db) as connection:
            connection.execute("DELETE FROM api_cache")
            connection.commit()
        report = self.report()
        self.assertEqual(report["ember_cache_checks"][0]["counts"], {"unverifiable_no_cache": 1})
        self.assertEqual(report["status"], "warnings")

    def test_changed_value_is_an_error_and_cli_returns_nonzero(self):
        with database(self.db) as connection:
            connection.execute("UPDATE period_observation SET value=1")
            connection.commit()
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(["--db", str(self.db), "report", "--year", "2025", "--output", str(self.output),
                         "--as-of", self.as_of.isoformat()])
        self.assertEqual(code, 1)
        report = json.loads((self.output / "VALIDATION.generated.json").read_text())
        self.assertEqual(report["ember_cache_checks"][0]["counts"], {"value_mismatch": 1})

    def test_corrupt_or_malformed_cache_is_reported_without_raw_payload(self):
        for payload in ({"data": ["private-secret"]}, {"data": None}):
            self.cache(payload)
            report = self.report()
            self.assertEqual(report["ember_cache_checks"][0]["counts"], {"invalid_cache": 1})
            self.assertNotIn("private-secret", json.dumps(report))
        self.cache(self.payload)
        with database(self.db) as connection:
            connection.execute("UPDATE api_cache SET sha256='wrong'")
            connection.commit()
        self.assertEqual(self.report()["errors"], 1)

    def test_generation_legacy_cache_is_supported_only_when_nonaggregate(self):
        with database(self.db) as connection:
            connection.execute("UPDATE api_cache SET target='DEU'")
            connection.commit()
        self.assertEqual(self.report()["ember_cache_checks"][0]["counts"], {"matched": 1})

    def test_as_of_date_controls_ytd_and_price_aggregation(self):
        with database(self.db) as connection:
            connection.execute("INSERT INTO period_observation VALUES "
                "('DE','2025-01-01','2025-01-31','monthly','ember','electricity-generation/monthly',"
                "'Solar','generation_solar',2,'TWh','observed')")
            connection.commit()
        write_reports(self.db, self.output, 2025, as_of=date(2025, 9, 23))
        rows = json.loads((self.output / "SUMMARY.generated.json").read_text())
        row = next(row for row in rows if row["country_code"] == "DE")
        self.assertEqual(row["generation_twh"], 2)
        self.assertEqual(row["period_status"], "ytd")
        self.report()
        rows = json.loads((self.output / "SUMMARY.generated.json").read_text())
        row = next(row for row in rows if row["country_code"] == "DE")
        self.assertEqual(row["generation_twh"], 0)
        self.assertEqual(row["period_status"], "closed")

    def test_invalid_year_and_missing_database_do_not_replace_existing_reports(self):
        self.report()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        for year in (2014, 2027):
            with self.assertRaises(ValueError):
                write_reports(self.db, self.output, year, as_of=self.as_of)
        with self.assertRaises(sqlite3.OperationalError):
            write_reports(self.root / "missing.sqlite3", self.output, 2025, as_of=self.as_of)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})
        self.assertFalse((self.root / "missing.sqlite3").exists())

    def test_output_cannot_replace_input_database(self):
        renamed = self.root / "SUMMARY.generated.json"
        self.db.rename(renamed)
        before = renamed.read_bytes()
        with self.assertRaises(ValueError):
            write_reports(renamed, self.root, 2025, as_of=self.as_of)
        self.assertEqual(before, renamed.read_bytes())

    def test_staging_failure_preserves_previous_bundle_and_removes_temporary_files(self):
        self.report()
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        real_temp = tempfile.NamedTemporaryFile
        attempts = 0

        def fail_third(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 3:
                raise OSError("fixture disk full")
            return real_temp(*args, **kwargs)

        with patch("electricity_atlas.reporting.tempfile.NamedTemporaryFile", side_effect=fail_third):
            with self.assertRaises(OSError):
                self.report()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_wal_snapshot_stays_consistent_during_concurrent_commit(self):
        with database(self.db) as writer, read_database(self.db) as reader:
            reader.execute("BEGIN")
            first = build_reports(reader, 2025, as_of=self.as_of)
            writer.execute("UPDATE period_observation SET value=9")
            writer.commit()
            second = build_reports(reader, 2025, as_of=self.as_of)
            self.assertEqual(first, second)
        self.assertEqual(self.report()["errors"], 1)

    def test_failed_replacement_leaves_a_detectably_invalid_manifest(self):
        self.report()
        old_manifest = (self.output / MANIFEST_NAME).read_bytes()
        real_replace = __import__("os").replace
        attempts = 0

        def fail_second(source, target):
            nonlocal attempts
            attempts += 1
            if attempts == 2:
                raise OSError("fixture interrupted replacement")
            return real_replace(source, target)

        with patch("electricity_atlas.reporting.os.replace", side_effect=fail_second):
            with self.assertRaises(OSError):
                write_reports(self.db, self.output, 2025, as_of=date(2026, 10, 1))
        self.assertEqual((self.output / MANIFEST_NAME).read_bytes(), old_manifest)
        manifest = json.loads(old_manifest)
        self.assertNotEqual(hashlib.sha256((self.output / "COVERAGE.generated.md").read_bytes()).hexdigest(),
                            manifest["files"]["COVERAGE.generated.md"])
        self.assertFalse(list(self.output.glob(".atlas-report-*.tmp")))
        self.report()  # A rerun repairs the set without extra persistent copies.

    def test_checked_in_report_bundle_checksums_match_on_this_platform(self):
        root = Path(__file__).resolve().parents[1] / "data" / "reports"
        manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["files"]), set(REPORT_FILES))
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest, name)

    def test_monthly_cache_upper_bound_is_exclusive(self):
        with database(self.db) as connection:
            connection.execute("UPDATE period_observation SET period_start='2025-02-01',period_end='2025-02-28',"
                "granularity='monthly',source_endpoint='electricity-generation/monthly'")
            connection.execute("UPDATE api_cache SET endpoint='ember/electricity-generation/monthly',"
                "start_date='2025-01',end_date='2025-02'")
            connection.commit()
        self.assertEqual(self.report()["ember_cache_checks"][0]["counts"], {"unverifiable_no_cache": 1})

    def test_price_calendar_and_closed_year_require_complete_months(self):
        import calendar
        from electricity_atlas.aggregation import aggregate_country
        from electricity_atlas.config import EMBER_PRICE_ENDPOINT
        with database(self.db) as connection:
            for month in range(1, 13):
                connection.execute("INSERT INTO period_observation VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    ("DE", f"2025-{month:02d}-01", f"2025-{month:02d}-{calendar.monthrange(2025, month)[1]}",
                     "monthly", "ember", EMBER_PRICE_ENDPOINT, "", "day_ahead_price", float(month), "EUR/MWh",
                     "provisional_current_month" if month == 12 else "observed"))
            connection.commit()
            ytd = aggregate_country(connection, "DE", 2025, today=date(2025, 12, 31))
            closed = aggregate_country(connection, "DE", 2025, today=date(2026, 1, 1))
            self.assertEqual(ytd["price_coverage"], "ytd")
            self.assertIsNotNone(ytd["price_avg_eur_mwh"])
            self.assertEqual(closed["price_coverage"], "incomplete")
            self.assertIsNone(closed["price_avg_eur_mwh"])
            connection.execute("UPDATE period_observation SET quality_status='observed'")
            connection.commit()
            complete = aggregate_country(connection, "DE", 2025, today=date(2026, 1, 1))
            self.assertEqual(complete["price_coverage"], "complete")
            self.assertAlmostEqual(complete["price_avg_eur_mwh"],
                sum(month * calendar.monthrange(2025, month)[1] for month in range(1, 13)) / 365)


if __name__ == "__main__":
    unittest.main()
