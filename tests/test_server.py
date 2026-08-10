import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from electricity_atlas.db import database
from electricity_atlas.server import AtlasHandler


class ServerSmokeTests(unittest.TestCase):
    def test_static_ui_and_summary_api(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "test.sqlite3"
            with database(db_path):
                pass
            handler = type("TestHandler", (AtlasHandler,), {"db_path": db_path})
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/", timeout=5) as response:
                    html = response.read().decode("utf-8")
                with urlopen(base + "/api/summary?year=2025&month=7", timeout=5) as response:
                    summary = json.load(response)
                self.assertIn("European Electricity Atlas", html)
                self.assertEqual(len(summary), 10)
                self.assertEqual(summary[0]["period"], "2025-07")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

