import calendar
import hashlib
import io
import sqlite3
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.cli import main
from electricity_atlas.config import (
    ATLAS_COUNTRIES,
    EMBER_COUNTRIES,
    EMBER_PRICE_ENDPOINT,
)
from electricity_atlas.db import initialize
from electricity_atlas.ember_aggregation import _price_summary
from electricity_atlas.price_importer import (
    PriceDownload,
    PriceImportError,
    WholesalePriceImporter,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ember" / "wholesale_prices.csv"


def fixture_text() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


class FixturePriceClient:
    def __init__(self, payload: str):
        self.payload = payload

    def fetch(self) -> PriceDownload:
        return PriceDownload(
            request_url="https://example.test/monthly.csv",
            fetched_at="2026-08-10T12:00:00+00:00",
            status_code=200,
            content_type="text/csv;charset=utf-8",
            etag='"fixture-etag"',
            last_modified="Mon, 10 Aug 2026 09:09:02 GMT",
            sha256=hashlib.sha256(self.payload.encode("utf-8")).hexdigest(),
            payload_text=self.payload,
        )


class WholesalePriceImportTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def importer(self, payload: str | None = None, today: date = date(2026, 8, 10)):
        text = fixture_text() if payload is None else payload
        return WholesalePriceImporter(self.connection, FixturePriceClient(text), today=today)

    def test_complete_csv_import_keeps_raw_payload_and_maps_all_32_countries(self):
        payload = fixture_text()
        result = self.importer(payload).import_prices()

        self.assertEqual(result["countries"], 32)
        self.assertEqual(result["countries_with_values"], 32)
        self.assertEqual(len(ATLAS_COUNTRIES), 32)
        self.assertEqual(set(EMBER_COUNTRIES), set(ATLAS_COUNTRIES))
        rows = self.connection.execute(
            """SELECT COUNT(*) AS count,COUNT(DISTINCT country_code) AS countries
               FROM period_observation WHERE source_endpoint=?""",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()
        self.assertEqual((rows["count"], rows["countries"]), (43, 32))
        uk = self.connection.execute(
            "SELECT country_code FROM period_observation WHERE source_endpoint=? AND country_code='UK'",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()
        self.assertEqual(uk["country_code"], "UK")
        cache = self.connection.execute(
            "SELECT * FROM source_cache WHERE source='ember' AND endpoint=?",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()
        self.assertEqual(cache["payload_text"], payload)
        self.assertEqual(cache["etag"], '"fixture-etag"')
        self.assertEqual(cache["sha256"], hashlib.sha256(payload.encode("utf-8")).hexdigest())

    def test_damaged_header_duplicate_and_non_numeric_price_are_rejected(self):
        invalid_payloads = (
            fixture_text().replace("Price (EUR/MWhe)", "Price (EUR/MWh)", 1),
            fixture_text() + "Albania,ALB,2025-01-01,50.00\n",
            fixture_text().replace("Albania,ALB,2025-01-01,50.00", "Albania,ALB,2025-01-01,not-a-number"),
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload.splitlines()[0]):
                with self.assertRaises(PriceImportError):
                    self.importer(payload).import_prices()
                self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM source_cache").fetchone()[0], 0)
                self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM period_observation").fetchone()[0], 0)

    def test_negative_prices_are_valid(self):
        self.importer().import_prices()
        price = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source_endpoint=? AND country_code='FI' AND period_start='2025-01-01'""",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()[0]
        self.assertEqual(price, -5.0)

    def test_empty_price_cell_is_missing_coverage_not_zero(self):
        payload = fixture_text().replace(
            "North Macedonia,MKD,2025-01-01,70.00",
            "North Macedonia,MKD,2025-01-01,",
        )
        result = self.importer(payload).import_prices()
        self.assertEqual(result["countries"], 32)
        self.assertEqual(result["countries_with_values"], 31)
        stored = self.connection.execute(
            """SELECT COUNT(*) FROM period_observation
               WHERE source_endpoint=? AND country_code='MK'""",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()[0]
        self.assertEqual(stored, 0)

    def test_current_month_is_provisional(self):
        self.importer(today=date(2025, 1, 15)).import_prices()
        statuses = {
            row["quality_status"]
            for row in self.connection.execute(
                """SELECT quality_status FROM period_observation
                   WHERE source_endpoint=? AND period_start='2025-01-01'""",
                (EMBER_PRICE_ENDPOINT,),
            )
        }
        self.assertEqual(statuses, {"provisional_current_month"})

    def test_invalid_refresh_preserves_old_prices_and_cache_atomically(self):
        self.importer().import_prices()
        before_price = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source_endpoint=? AND country_code='AL'""",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()[0]
        before_hash = self.connection.execute("SELECT sha256 FROM source_cache").fetchone()[0]
        damaged = fixture_text().replace("Country,ISO3 Code", "Country,Broken", 1)

        with self.assertRaises(PriceImportError):
            self.importer(damaged).import_prices()

        after_price = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source_endpoint=? AND country_code='AL'""",
            (EMBER_PRICE_ENDPOINT,),
        ).fetchone()[0]
        after_hash = self.connection.execute("SELECT sha256 FROM source_cache").fetchone()[0]
        self.assertEqual((after_price, after_hash), (before_price, before_hash))

    def test_yearly_price_is_weighted_by_calendar_days_and_incomplete_history_stays_empty(self):
        self.importer().import_prices()
        germany = aggregate_country(self.connection, "DE", 2025, source="ember")
        expected = sum(
            month * calendar.monthrange(2025, month)[1] for month in range(1, 13)
        ) / 365
        self.assertAlmostEqual(germany["price_avg_eur_mwh"], expected)
        self.assertEqual(germany["price_coverage"], "complete")
        self.assertEqual(germany["price_months_complete"], 12)

        austria = aggregate_country(self.connection, "AT", 2025, source="ember")
        self.assertIsNone(austria["price_avg_eur_mwh"])
        self.assertEqual(austria["price_coverage"], "incomplete")
        self.assertEqual(austria["data_status"], "partial")

    def test_current_year_price_is_ytd_and_excludes_provisional_month(self):
        rows = []
        for month, value in ((1, 10.0), (2, 20.0), (3, 30.0), (4, 999.0)):
            last_day = calendar.monthrange(2025, month)[1]
            rows.append((
                "DE", f"2025-{month:02d}-01", f"2025-{month:02d}-{last_day:02d}",
                "monthly", "ember", EMBER_PRICE_ENDPOINT, "national_wholesale_price",
                "day_ahead_price", value, "EUR/MWh",
                "provisional_current_month" if month == 4 else "observed",
            ))
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        result = _price_summary(self.connection, "DE", 2025, None, today=date(2025, 4, 15))
        expected = (10 * 31 + 20 * 28 + 30 * 31) / (31 + 28 + 31)
        self.assertAlmostEqual(result["price_avg_eur_mwh"], expected)
        self.assertEqual(result["price_coverage"], "ytd")
        self.assertEqual(result["price_months_complete"], 3)

class PriceCliTests(unittest.TestCase):
    def test_import_prices_cli_uses_dedicated_importer(self):
        result = {"rows": 10, "countries": 32}
        with patch("electricity_atlas.cli.database"), patch(
            "electricity_atlas.cli.WholesalePriceImporter.import_prices", return_value=result
        ) as import_prices, patch("sys.stdout", new=io.StringIO()):
            exit_code = main(["import-prices"])
        self.assertEqual(exit_code, 0)
        import_prices.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
