from contextlib import ExitStack
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from electricity_atlas.db import database
from electricity_atlas.ember_importer import EmberImporter
from electricity_atlas.full_refresh import _optional_candidate_source, run_scheduled_refresh, ScheduledRefreshCriticalError
from electricity_atlas.refresh_lifecycle import run_refresh_lifecycle, RefreshLockError
from electricity_atlas.refresh_safety import (
    FileRefreshLock, observation_coverage, require_preserved_coverage,
    prune_superseded_ember_cache, safe_error,
)


class RefreshSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "atlas.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def insert(self, connection, *, country="DE", source="ember", endpoint="electricity-demand/yearly",
               granularity="yearly", start="2025-01-01", end="2025-12-31"):
        connection.execute("""INSERT INTO period_observation
            (country_code,period_start,period_end,granularity,source,source_endpoint,source_series,metric,value,unit)
            VALUES (?,?,?,?,?,?,'','consumption',1,'TWh')""",
            (country, start, end, granularity, source, endpoint))
        connection.commit()

    def test_real_ember_empty_response_is_detected_after_replacement(self):
        with database(self.db) as connection:
            self.insert(connection)
            before = observation_coverage(connection)
            client = MagicMock()
            client.get.return_value = {"data": []}
            importer = EmberImporter(connection, client=client, refresh=True)
            self.assertEqual(importer._import_endpoint("DE", "electricity-demand/yearly", "yearly", "2025", "2025"), 0)
            with self.assertRaisesRegex(ValueError, "remove or backdate"):
                require_preserved_coverage(connection, before)

    def test_partial_optional_response_restores_rows_and_cache(self):
        with database(self.db) as connection:
            self.insert(connection, source="eea")
            self.insert(connection, source="eea", country="FR")
            def truncate():
                connection.execute("DELETE FROM period_observation WHERE country_code='FR'")
                connection.execute("UPDATE period_observation SET value=99")
                connection.execute("INSERT INTO source_cache VALUES ('eea','fixture','url','now',200,NULL,NULL,NULL,'hash','new')")
                return {"rows": 1}
            result = _optional_candidate_source(connection, "eea_ghg", truncate)
            self.assertEqual(result["status"], "failed_optional")
            self.assertEqual([r[0] for r in connection.execute("SELECT value FROM period_observation")], [1, 1])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM source_cache").fetchone()[0], 0)

    def test_revisions_and_new_snapshot_dates_are_allowed_but_backdating_is_not(self):
        with database(self.db) as connection:
            self.insert(connection, source="jrc", granularity="snapshot")
            before = observation_coverage(connection)
            connection.execute("UPDATE period_observation SET value=2, period_start='2026-01-01',period_end='2026-01-01'")
            require_preserved_coverage(connection, before)
            connection.execute("UPDATE period_observation SET period_start='2024-01-01'")
            with self.assertRaises(ValueError):
                require_preserved_coverage(connection, before)

    def test_cache_gc_only_removes_fully_superseded_same_target_responses(self):
        with database(self.db) as connection:
            def cache(target, start, end, fetched, endpoint="ember/demand", status=200):
                connection.execute("""INSERT INTO api_cache
                    (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
                    VALUES (?,?,?,?, 'url',?,?,'hash','{}')""", (endpoint,target,start,end,fetched,status))
            cache("DEU", "2026-01", "2026-06", "2026-07-01")
            cache("DEU", "2026-01", "2026-09", "2026-09-02")
            cache("DEU", "2025-01", "2026-05", "2026-07-01") # partial overlap
            cache("DEU|is_aggregate_series=true", "2026-01", "2026-06", "2026-07-01")
            cache("FRA", "2026-01", "2026-06", "2026-07-01")
            cache("FRA", "2026-01", "2026-09", "2026-09-02", status=500)
            cache("DEU", "2026-01", "2026-06", "2026-07-01", endpoint="other/demand")
            cache("ITA", "2026-01", "2026-06", "2026-07-01")
            cache("ITA", "2026-01", "2026-09", "2026-08-02") # not refreshed this run
            self.assertEqual(prune_superseded_ember_cache(connection, "2026-09-01"), 1)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM api_cache").fetchone()[0], 8)
            self.assertEqual(prune_superseded_ember_cache(connection, "2026-09-01"), 0)

    def test_kernel_lock_is_released_after_abrupt_child_exit(self):
        path = self.root / "lock"
        code = ("import os,sys; from pathlib import Path; "
                "from electricity_atlas.refresh_safety import FileRefreshLock; "
                "lock=FileRefreshLock(Path(sys.argv[1])); lock.acquire(); os._exit(0)")
        subprocess.run([sys.executable, "-c", code, str(path)], check=True, timeout=15)
        with FileRefreshLock(path):
            self.assertTrue(path.exists())

    def test_lifecycle_rejects_concurrent_manual_and_scheduled_workers(self):
        with FileRefreshLock(self.root / ".atlas-refresh.lock"):
            with self.assertRaises(RefreshLockError):
                run_refresh_lifecycle(self.db, MagicMock())

    def test_scheduled_critical_shrink_aborts_real_candidate_and_preserves_production(self):
        for failing_source in ("ember", "wholesale_prices", "eurostat"):
            with self.subTest(source=failing_source):
                with database(self.db) as connection:
                    connection.execute("DELETE FROM period_observation")
                    self.insert(connection, source=failing_source)
                    self.insert(connection, source=failing_source, country="FR")
                original = self.db.read_bytes()
                def factory(name):
                    def construct(connection, **kwargs):
                        importer = MagicMock()
                        def action(*args):
                            if name == failing_source:
                                connection.execute("DELETE FROM period_observation WHERE country_code='FR'")
                                connection.commit()
                            return {"rows": 1, "successes": ["ok"], "errors": 0}
                        importer.import_range.side_effect = action
                        importer.import_prices.side_effect = action
                        importer.import_years.side_effect = action
                        return importer
                    return construct
                def lifecycle(path, action, **kwargs):
                    return run_refresh_lifecycle(path, action, validate_action=lambda _: {"fixture": True}, **kwargs)
                with ExitStack() as stack:
                    stack.enter_context(patch("electricity_atlas.full_refresh.load_ember_api_key"))
                    stack.enter_context(patch("electricity_atlas.full_refresh.run_refresh_lifecycle", side_effect=lifecycle))
                    for cls, name in (("EmberImporter", "ember"), ("WholesalePriceImporter", "wholesale_prices"),
                                      ("EurostatImporter", "eurostat"), ("EurostatSupplementImporter", "supplement")):
                        stack.enter_context(patch(f"electricity_atlas.full_refresh.{cls}", side_effect=factory(name)))
                    with self.assertRaises(ScheduledRefreshCriticalError) as caught:
                        run_scheduled_refresh(self.db)
                self.assertEqual(self.db.read_bytes(), original)
                self.assertFalse((self.root / ".refresh-work").exists())
                failed_key = "eurostat_core" if failing_source == "eurostat" else failing_source
                self.assertEqual(caught.exception.source_results[failed_key]["status"], "failed_critical")

    def test_errors_redact_configured_credentials_and_query_secrets(self):
        with patch.dict(os.environ, {"EMBER_API_KEY": "fixture-private-key"}):
            error = safe_error("fixture-private-key https://example/?api_key=another-secret&x=1")
            self.assertNotIn("fixture-private-key", error)
            self.assertNotIn("another-secret", error)


if __name__ == "__main__":
    unittest.main()
