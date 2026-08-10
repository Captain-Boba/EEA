import sqlite3
import unittest

from electricity_atlas.aggregation import aggregate_country
from electricity_atlas.config import SOURCE_NAME
from electricity_atlas.db import initialize
from electricity_atlas.monthly_migration import migrate_legacy_intervals


class MonthlyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_legacy_intervals_are_aggregated_then_removed(self):
        rows = []
        for hour, generation, price in ((0, 100.0, -10.0), (1, 300.0, 50.0)):
            timestamp = f"2025-01-01T{hour:02d}:00:00+01:00"
            rows.append((
                "DE", "Deutschland", "", timestamp, timestamp, SOURCE_NAME,
                "public_power", "PT1H", 60, "generation_total", generation, "MW", "observed",
            ))
            rows.append((
                "DE", "Deutschland", "DE-LU", timestamp, timestamp, SOURCE_NAME,
                "price", "PT1H", 60, "day_ahead_price", price, "EUR/MWh", "observed",
            ))
        self.connection.executemany(
            """INSERT INTO observation
               (country_code,country_name,bidding_zone,timestamp,timestamp_utc,source,source_endpoint,
                source_resolution,interval_minutes,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.connection.execute(
            """INSERT INTO bilateral_flow
               (country_code,counterparty,timestamp,timestamp_utc,source,source_resolution,interval_minutes,flow_mw)
               VALUES ('DE','FR','2025-01-01T00:00:00+01:00','2024-12-31T23:00:00+00:00',?,'PT1H',60,10)""",
            (SOURCE_NAME,),
        )

        result = migrate_legacy_intervals(self.connection)

        self.assertEqual(result["legacy_observations_removed"], 4)
        self.assertEqual(result["legacy_flows_removed"], 1)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM observation").fetchone()[0], 0)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM bilateral_flow").fetchone()[0], 0)
        generation = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source_endpoint='public_power' AND metric='generation_total'"""
        ).fetchone()[0]
        price = self.connection.execute(
            """SELECT value FROM period_observation
               WHERE source_endpoint='price' AND metric='day_ahead_price'"""
        ).fetchone()[0]
        self.assertAlmostEqual(generation, 0.0004)
        self.assertEqual(price, 20.0)
        self.assertEqual(aggregate_country(self.connection, "DE", 2025, 1)["generation_twh"], 0.0004)


if __name__ == "__main__":
    unittest.main()
