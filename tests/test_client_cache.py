import json
import sqlite3
import unittest
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


if __name__ == "__main__":
    unittest.main()
