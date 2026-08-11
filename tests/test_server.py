import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from electricity_atlas.server import create_server


class ServerSmokeTests(unittest.TestCase):
    def test_missing_database_is_initialized_before_read_only_summary_api(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "test.sqlite3"
            self.assertFalse(db_path.exists())
            server = create_server(db_path, "127.0.0.1", 0)
            self.assertTrue(db_path.is_file())
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/", timeout=5) as response:
                    html = response.read().decode("utf-8")
                with urlopen(base + "/assets/europe.svg", timeout=5) as response:
                    map_svg = response.read().decode("utf-8")
                with urlopen(base + "/api/countries", timeout=5) as response:
                    countries = json.load(response)
                with urlopen(base + "/api/summary?year=2025&month=7", timeout=5) as response:
                    summary = json.load(response)
                with urlopen(base + "/api/summary?year=2025&month=7&source=ember", timeout=5) as response:
                    ember_summary = json.load(response)
                with urlopen(base + "/api/metrics", timeout=5) as response:
                    metrics = json.load(response)
                with urlopen(base + "/api/storage", timeout=5) as response:
                    storage = json.load(response)
                self.assertIn("European Electricity Atlas", html)
                self.assertIn("Datenquellen und Herkunft", html)
                self.assertIn('id="atlas-map-section"', html)
                self.assertNotIn("Energy-Charts", html)
                self.assertIn('id="year" type="number" min="2015"', html)
                self.assertIn("Natural Earth 1:50m Admin 0 Countries 5.1.1", map_svg)
                self.assertEqual(len(countries), 31)
                self.assertEqual({country["code"] for country in countries}, {row["country_code"] for row in summary})
                self.assertEqual(len(summary), 31)
                self.assertEqual(
                    {row["country_code"] for row in summary},
                    {"AT", "BE", "BG", "CH", "CZ", "DE", "DK", "ES", "EE", "FI", "FR", "UK", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "ME", "MK", "NL", "NO", "PL", "PT", "RO", "RS", "SK", "SI", "SE"},
                )
                self.assertEqual(summary[0]["period"], "2025-07")
                self.assertTrue(all(row["source"] == "ember" for row in summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in summary))
                self.assertEqual(len(ember_summary), 31)
                self.assertTrue(all(row["source"] == "ember" for row in ember_summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in ember_summary))
                self.assertIn("net_import_share_pct", {metric["id"] for metric in metrics})
                self.assertEqual(storage["snapshot_date"], None)
                self.assertEqual(storage["source"], "jrc")
                self.assertIn("JRC", storage["source_label"])
                self.assertEqual(storage["countries"], [])
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/api/summary?year=2025&source=combined", timeout=5)
                self.assertEqual(error.exception.code, 400)
                error.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
