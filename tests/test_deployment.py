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
            headers = response.headers
        self.assertEqual(payload, {"status": "ok", "atlas_database": "ok", "community_database": "ok",
                                  "monthly_refresh": {"last_run_status": "not_run"}})
        self.assertNotIn(str(self.atlas), json.dumps(payload))
        self.assertNotIn(str(self.community), json.dumps(payload))
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(headers["Permissions-Policy"], "camera=(), geolocation=(), microphone=()")

    def test_static_pages_receive_security_headers(self):
        with urlopen(self.base + "/privacy.html", timeout=5) as response:
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_refresh_warning_or_failure_does_not_make_serving_databases_unhealthy(self):
        from electricity_atlas.monthly_refresh import MONTHLY_REPORT_NAME
        report = self.atlas.parent / "reports" / MONTHLY_REPORT_NAME
        report.parent.mkdir()
        for state, publication in (("success", "published"), ("failed", "not_published")):
            report.write_text(json.dumps({"status": state, "publication": publication,
                "sources": {"jrc_storage": {"status": "failed_optional", "error": "private-secret"}}}), encoding="utf-8")
            with urlopen(self.base + "/api/health", timeout=5) as response:
                self.assertEqual(response.status, 200)
                payload = json.load(response)
            self.assertEqual(payload["status"], "ok")
            self.assertIn("jrc_storage", payload["monthly_refresh"]["source_warnings"])
            self.assertEqual(payload["monthly_refresh"]["publication"], publication)
            self.assertNotIn("private-secret", json.dumps(payload))
            schemas = json.loads((Path(__file__).resolve().parents[1] / "web" / "openapi.json").read_text(encoding="utf-8"))["components"]["schemas"]
            self.assertTrue(set(payload) <= set(schemas["Health"]["properties"]))
            refresh_schema = schemas["MonthlyRefreshHealth"]["properties"]
            self.assertTrue(set(payload["monthly_refresh"]) <= set(refresh_schema))
            self.assertEqual(set(payload["monthly_refresh"]["sources"]), set(refresh_schema["sources"]["properties"]))
            self.assertTrue(set(payload["monthly_refresh"]["sources"].values()) <= set(schemas["RefreshSourceStatus"]["enum"]))

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
