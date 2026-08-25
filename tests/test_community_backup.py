import hashlib
import tempfile
import unittest
from pathlib import Path

from electricity_atlas.community import CommunityStore, browser_hash
from electricity_atlas.community_backup import backup_community_database
from electricity_atlas.db import database
from electricity_atlas.wallpaper_catalog import wallpaper_catalog


class CommunityBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "community.sqlite3"
        self.atlas = self.root / "atlas.sqlite3"
        self.output = self.root / "backups" / "community-backup.sqlite3"
        self.store = CommunityStore(self.source)
        self.store.initialize()
        with database(self.atlas) as connection:
            connection.execute(
                """INSERT INTO period_observation (
                    country_code, period_start, period_end, granularity, source, source_endpoint,
                    source_series, metric, value, unit, quality_status
                ) VALUES ('DE', '2025-01-01', '2025-01-31', 'monthly', 'ember', 'fixture', '', 'generation_twh', 1, 'TWh', 'observed')"""
            )
        self.wallpaper_id = wallpaper_catalog()[0]["id"]
        self.store.cast_vote(self.wallpaper_id, browser_hash("first-browser"), "up")
        self.store.cast_vote(self.wallpaper_id, browser_hash("second-browser"), "up")
        self.store.cast_vote(self.wallpaper_id, browser_hash("third-browser"), "down")

    def tearDown(self):
        self.temporary.cleanup()

    def test_backup_is_a_complete_independent_sqlite_copy_and_preserves_source(self):
        source_before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        atlas_before = hashlib.sha256(self.atlas.read_bytes()).hexdigest()
        result = backup_community_database(self.source, self.output)
        self.assertEqual(result, self.output)
        self.assertTrue(self.output.is_file())
        copied_state = next(
            state for state in CommunityStore(self.output).list_votes(browser_hash("first-browser"))
            if state["wallpaper_id"] == self.wallpaper_id
        )
        self.assertEqual((copied_state["upvotes"], copied_state["downvotes"], copied_state["score"], copied_state["rank"]), (2, 1, 1, 1))
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), source_before)
        self.assertEqual(hashlib.sha256(self.atlas.read_bytes()).hexdigest(), atlas_before)

    def test_backup_refuses_existing_target_unless_forced_and_never_uses_source_as_target(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b"existing backup")
        before = self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            backup_community_database(self.source, self.output)
        self.assertEqual(self.output.read_bytes(), before)
        backup_community_database(self.source, self.output, force=True)
        self.assertTrue(CommunityStore(self.output).healthcheck())
        with self.assertRaisesRegex(ValueError, "differ"):
            backup_community_database(self.source, self.source, force=True)


if __name__ == "__main__":
    unittest.main()
