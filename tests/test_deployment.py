import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener, urlopen

from electricity_atlas.db import database
from electricity_atlas.server import create_server
from electricity_atlas.wallpaper_catalog import wallpaper_catalog


class DeploymentHttpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.atlas = root / "atlas.sqlite3"
        self.community = root / "community.sqlite3"
        with database(self.atlas):
            pass
        self.server = create_server(
            self.atlas,
            port=0,
            community_path=self.community,
            public_origin="https://atlas.example",
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.wallpaper_id = wallpaper_catalog()[0]["id"]

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.temporary.cleanup()

    def vote_request(self, *, origin=None, forwarded=None, forwarded_host=None, content_type="application/json"):
        headers = {"Content-Type": content_type}
        if origin is not None:
            headers["Origin"] = origin
        if forwarded is not None:
            headers["X-Forwarded-Proto"] = forwarded
        if forwarded_host is not None:
            headers["X-Forwarded-Host"] = forwarded_host
        return Request(
            self.base + "/api/wallpaper-votes",
            data=json.dumps({"wallpaper_id": self.wallpaper_id, "vote": "up"}).encode("utf-8"),
            headers=headers,
            method="POST",
        )

    def test_health_is_healthy_and_does_not_expose_database_paths(self):
        with urlopen(self.base + "/api/health", timeout=5) as response:
            payload = json.load(response)
        self.assertEqual(payload, {"status": "ok", "atlas_database": "ok", "community_database": "ok"})
        self.assertNotIn(str(self.atlas), json.dumps(payload))
        self.assertNotIn(str(self.community), json.dumps(payload))

    def test_health_returns_non_success_when_a_database_is_unavailable(self):
        self.community.unlink()
        with self.assertRaises(HTTPError) as unavailable:
            urlopen(self.base + "/api/health", timeout=5)
        self.assertEqual(unavailable.exception.code, 503)
        payload = json.load(unavailable.exception)
        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["community_database"], "unavailable")
        self.assertNotIn(str(self.community), json.dumps(payload))
        unavailable.exception.close()

    def test_public_origin_requires_the_exact_origin_and_https_cookie_is_secure(self):
        for origin in (None, "https://wrong.example"):
            with self.assertRaises(HTTPError) as rejected:
                build_opener().open(self.vote_request(origin=origin))
            self.assertEqual(rejected.exception.code, 400)
            rejected.exception.close()
        with build_opener().open(
            self.vote_request(origin="https://atlas.example", forwarded="http", forwarded_host="wrong.example")
        ) as response:
            cookie = response.headers["Set-Cookie"]
        self.assertIn("Secure", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_vote_posts_require_json_content_type(self):
        with self.assertRaises(HTTPError) as rejected:
            build_opener().open(self.vote_request(origin="https://atlas.example", content_type="text/plain"))
        self.assertEqual(rejected.exception.code, 400)
        rejected.exception.close()


if __name__ == "__main__":
    unittest.main()
