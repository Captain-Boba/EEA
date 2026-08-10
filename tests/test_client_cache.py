import json
import sqlite3
import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

from electricity_atlas.client import EnergyChartsClient
from electricity_atlas.db import initialize


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        initialize(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_cached_period_avoids_network(self):
        payload = {"data": [{"timestamp": "2025-01-01T00:00:00+01:00", "values": {}}]}
        self.connection.execute(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES ('public_power','de','2025-01-01','2025-01-31','x','now',200,'hash',?)""",
            (json.dumps(payload),),
        )
        client = EnergyChartsClient(self.connection)
        with patch("electricity_atlas.client.urlopen") as mocked:
            result = client.get("public_power", "country", "de", "2025-01-01", "2025-01-31")
        self.assertEqual(result, payload)
        mocked.assert_not_called()

    def test_covering_annual_cache_is_sliced_for_month(self):
        payload = {
            "data": [
                {"timestamp": "2025-01-15T00:00:00+01:00", "values": {"x": 1}},
                {"timestamp": "2025-02-15T00:00:00+01:00", "values": {"x": 2}},
            ],
            "available_from": "2025-01-15T00:00:00+01:00",
            "available_until": "2025-02-15T00:00:00+01:00",
        }
        self.connection.execute(
            """INSERT INTO api_cache
               (endpoint,target,start_date,end_date,request_url,fetched_at,status_code,sha256,response_json)
               VALUES ('public_power','de','2025-01-01','2025-12-31','x','now',200,'hash',?)""",
            (json.dumps(payload),),
        )
        client = EnergyChartsClient(self.connection)
        with patch("electricity_atlas.client.urlopen") as mocked:
            result = client.get("public_power", "country", "de", "2025-01-01", "2025-01-31")
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["values"]["x"], 1)
        mocked.assert_not_called()

    def test_no_content_is_cached_as_regular_coverage_gap(self):
        client = EnergyChartsClient(self.connection)
        error = HTTPError(
            "https://example.invalid", 404, "Not Found", {}, BytesIO(b"no content available")
        )
        with patch("electricity_atlas.client.urlopen", side_effect=error) as mocked:
            first = client.get("price", "bzn", "DE-LU", "2015-01-01", "2015-12-31")
        error.close()
        with patch("electricity_atlas.client.urlopen") as second_mock:
            second = client.get("price", "bzn", "DE-LU", "2015-01-01", "2015-12-31")

        self.assertEqual(first["coverage_status"], "not_available")
        self.assertEqual(second, first)
        self.assertEqual(mocked.call_count, 1)
        second_mock.assert_not_called()
        cached = self.connection.execute(
            "SELECT status_code FROM api_cache WHERE endpoint='price' AND target='DE-LU'"
        ).fetchone()
        self.assertEqual(cached["status_code"], 404)


if __name__ == "__main__":
    unittest.main()
