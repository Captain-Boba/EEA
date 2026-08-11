import sqlite3
import unittest

from electricity_atlas.db import initialize, migrate_atlas_catalog


class AtlasCatalogMigrationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)
        for table in ("observation", "bilateral_flow", "installed_capacity", "quality_issue", "import_period"):
            self.connection.execute(f'CREATE TABLE "{table}" (id INTEGER)')

    def tearDown(self):
        self.connection.close()

    def test_migration_preserves_supported_sources_and_removes_albania_and_legacy(self):
        rows = [
            ("DE", "2025-01-01", "2025-01-31", "monthly", "ember", "generation", "Solar", "generation_solar", 1.0, "TWh", "observed"),
            ("DE", "2025-01-01", "2025-12-31", "yearly", "eurostat", "population", "", "population", 83_000_000.0, "people", "observed"),
            ("DE", "2025-01-01", "2025-01-01", "snapshot", "jrc", "storage", "", "storage_power_gw", 10.0, "GW", "observed"),
            ("AL", "2025-01-01", "2025-01-31", "monthly", "ember", "generation", "Solar", "generation_solar", 0.5, "TWh", "observed"),
            ("DE", "2025-01-01", "2025-01-31", "monthly", "legacy", "generation", "Solar", "generation_solar", 2.0, "TWh", "observed"),
        ]
        self.connection.executemany(
            """INSERT INTO period_observation
               (country_code,period_start,period_end,granularity,source,source_endpoint,
                source_series,metric,value,unit,quality_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        self.connection.executemany(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [
                ("ember/generation", "DEU", "2025-01", "2025-12", "redacted", "now", 200, "a", "{}"),
                ("ember/generation", "ALB", "2025-01", "2025-12", "redacted", "now", 200, "c", "{}"),
                ("legacy/generation", "DE", "2025-01", "2025-12", "legacy", "now", 200, "b", "{}"),
            ],
        )

        result = migrate_atlas_catalog(self.connection)

        self.assertEqual(result["period_rows_removed"], 2)
        self.assertEqual(result["api_cache_rows_removed"], 2)
        self.assertEqual(
            {row[0] for row in self.connection.execute("SELECT DISTINCT source FROM period_observation")},
            {"ember", "eurostat", "jrc"},
        )
        self.assertEqual(
            self.connection.execute("SELECT endpoint FROM api_cache").fetchone()[0],
            "ember/generation",
        )
        tables = {
            row[0]
            for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertTrue(set(result["tables_dropped"]).isdisjoint(tables))


if __name__ == "__main__":
    unittest.main()
