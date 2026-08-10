import json
import tempfile
import threading
import unittest
from pathlib import Path
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
                with urlopen(base + "/api/summary?year=2025&month=7", timeout=5) as response:
                    summary = json.load(response)
                with urlopen(base + "/api/summary?year=2025&month=7&source=ember", timeout=5) as response:
                    ember_summary = json.load(response)
                self.assertIn("European Electricity Atlas", html)
                self.assertIn("Datenquellen und Herkunft", html)
                self.assertEqual(len(summary), 10)
                self.assertEqual(summary[0]["period"], "2025-07")
                self.assertTrue(all(row["source"] == "combined" for row in summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in summary))
                self.assertEqual(len(ember_summary), 10)
                self.assertTrue(all(row["source"] == "ember" for row in ember_summary))
                self.assertTrue(all(row["data_status"] == "missing" for row in ember_summary))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
