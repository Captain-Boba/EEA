import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener

from electricity_atlas.community import CommunityStore, browser_hash
from electricity_atlas.server import VoteRateLimiter, create_server
from electricity_atlas.wallpaper_catalog import wallpaper_catalog


class CommunityStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "community.sqlite3"
        self.store = CommunityStore(self.path)
        self.store.initialize()
        self.first, self.second = [wallpaper["id"] for wallpaper in wallpaper_catalog()[:2]]
        self.alice = browser_hash("alice")
        self.bob = browser_hash("bob")

    def tearDown(self):
        self.temporary.cleanup()

    def state(self, wallpaper_id):
        return next(item for item in self.store.list_votes(self.alice) if item["wallpaper_id"] == wallpaper_id)

    def test_schema_first_vote_switch_clear_and_identical_request(self):
        self.assertTrue(self.path.exists())
        first = self.store.cast_vote(self.first, self.alice, "up")
        self.assertEqual((first["upvotes"], first["downvotes"], first["score"], first["own_vote"]), (1, 0, 1, 1))
        repeated = self.store.cast_vote(self.first, self.alice, "up")
        self.assertEqual((repeated["upvotes"], repeated["downvotes"], repeated["score"]), (1, 0, 1))
        switched = self.store.cast_vote(self.first, self.alice, "down")
        self.assertEqual((switched["upvotes"], switched["downvotes"], switched["score"], switched["own_vote"]), (0, 1, -1, -1))
        cleared = self.store.cast_vote(self.first, self.alice, "clear")
        self.assertEqual((cleared["upvotes"], cleared["downvotes"], cleared["score"], cleared["own_vote"]), (0, 0, 0, None))

    def test_two_browsers_scores_shared_ranks_and_all_catalog_images(self):
        for index in range(5):
            self.store.cast_vote(self.first, browser_hash(f"up-{index}"), "up")
        for index in range(15):
            self.store.cast_vote(self.second, browser_hash(f"down-{index}"), "down")
        states = self.store.list_votes(self.alice)
        self.assertEqual(len(states), 250)
        first = next(item for item in states if item["wallpaper_id"] == self.first)
        second = next(item for item in states if item["wallpaper_id"] == self.second)
        untouched = next(item for item in states if item["wallpaper_id"] not in {self.first, self.second})
        self.assertEqual(first["score"], 5)
        self.assertEqual(second["score"], -15)
        self.assertEqual(first["rank"], 1)
        self.assertTrue(untouched["rank_shared"])
        self.assertLess(untouched["rank"], second["rank"])

    def test_persistence_unknown_ids_and_atlas_is_not_part_of_community_store(self):
        self.store.cast_vote(self.first, self.alice, "up")
        reopened = CommunityStore(self.path)
        self.assertEqual(next(item for item in reopened.list_votes(self.alice) if item["wallpaper_id"] == self.first)["own_vote"], 1)
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.store.cast_vote("not-a-wallpaper", self.alice, "up")
        with self.assertRaisesRegex(ValueError, "vote must"):
            self.store.cast_vote(self.first, self.alice, "sideways")
        self.assertNotIn("atlas", self.path.name)

    def test_rate_limiter(self):
        limiter = VoteRateLimiter(limit=2, window_seconds=60)
        self.assertTrue(limiter.allow("browser", now=0))
        self.assertTrue(limiter.allow("browser", now=1))
        self.assertFalse(limiter.allow("browser", now=2))
        self.assertTrue(limiter.allow("browser", now=61))


class CommunityHttpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.atlas_path = self.root / "atlas.sqlite3"
        self.community_path = self.root / "community.sqlite3"
        self.previous = os.environ.get("EEA_COMMUNITY_DB")
        os.environ["EEA_COMMUNITY_DB"] = str(self.community_path)
        self.server = create_server(self.atlas_path, port=0)
        self.thread = __import__("threading").Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.wallpaper_id = wallpaper_catalog()[0]["id"]

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        if self.previous is None:
            os.environ.pop("EEA_COMMUNITY_DB", None)
        else:
            os.environ["EEA_COMMUNITY_DB"] = self.previous
        self.temporary.cleanup()

    def test_cookie_backed_api_rejects_invalid_input_and_preserves_atlas_database(self):
        original_atlas = hashlib.sha256(self.atlas_path.read_bytes()).hexdigest()
        opener = build_opener()
        request = Request(
            self.base + "/api/wallpaper-votes",
            data=(f'{{"wallpaper_id":"{self.wallpaper_id}","vote":"up"}}').encode(),
            headers={"Content-Type": "application/json", "Origin": self.base},
            method="POST",
        )
        with opener.open(request) as response:
            self.assertIn("HttpOnly", response.headers["Set-Cookie"])
            self.assertIn("SameSite=Lax", response.headers["Set-Cookie"])
        with self.assertRaises(HTTPError) as invalid:
            opener.open(Request(self.base + "/api/wallpaper-votes", data=b'{}', headers={"Content-Type": "application/json"}, method="POST"))
        self.assertEqual(invalid.exception.code, 400)
        self.assertEqual(hashlib.sha256(self.atlas_path.read_bytes()).hexdigest(), original_atlas)

    def test_http_unknown_wallpaper_and_rate_limit_are_rejected(self):
        self.server.RequestHandlerClass.vote_rate_limiter = VoteRateLimiter(limit=1, window_seconds=60)
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        with self.assertRaises(HTTPError) as unknown:
            opener.open(Request(
                self.base + "/api/wallpaper-votes", data=b'{"wallpaper_id":"unknown","vote":"up"}',
                headers={"Content-Type": "application/json", "Origin": self.base}, method="POST",
            ))
        self.assertEqual(unknown.exception.code, 400)
        valid = Request(
            self.base + "/api/wallpaper-votes", data=(f'{{"wallpaper_id":"{self.wallpaper_id}","vote":"up"}}').encode(),
            headers={"Content-Type": "application/json", "Origin": self.base}, method="POST",
        )
        with opener.open(valid) as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as limited:
            opener.open(valid)
        self.assertEqual(limited.exception.code, 429)
