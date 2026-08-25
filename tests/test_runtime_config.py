import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from electricity_atlas.config import DEFAULT_DB
from electricity_atlas.db import database
from electricity_atlas.runtime import parse_public_origin, resolve_server_config
from electricity_atlas.server import create_server


class RuntimeConfigTests(unittest.TestCase):
    def test_explicit_server_values_override_environment_and_environment_overrides_defaults(self):
        with patch.dict(os.environ, {
            "EEA_ATLAS_DB": "environment-atlas.sqlite3",
            "EEA_COMMUNITY_DB": "environment-community.sqlite3",
            "EEA_HOST": "0.0.0.0",
            "EEA_PORT": "9010",
            "EEA_PUBLIC_ORIGIN": "https://atlas.example",
        }, clear=False):
            from_environment = resolve_server_config()
            explicit = resolve_server_config(
                atlas_db=Path("explicit-atlas.sqlite3"),
                community_db=Path("explicit-community.sqlite3"),
                host="127.0.0.1",
                port="8123",
                public_origin="http://localhost:8123",
            )
        self.assertEqual(from_environment.atlas_db, Path("environment-atlas.sqlite3"))
        self.assertEqual(from_environment.community_db, Path("environment-community.sqlite3"))
        self.assertEqual((from_environment.host, from_environment.port), ("0.0.0.0", 9010))
        self.assertEqual(from_environment.public_origin, "https://atlas.example")
        self.assertEqual(explicit.atlas_db, Path("explicit-atlas.sqlite3"))
        self.assertEqual(explicit.community_db, Path("explicit-community.sqlite3"))
        self.assertEqual((explicit.host, explicit.port), ("127.0.0.1", 8123))
        self.assertEqual(explicit.public_origin, "http://localhost:8123")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_server_config().atlas_db, DEFAULT_DB)

    def test_invalid_port_and_public_origin_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "EEA_PORT"):
            resolve_server_config(port="0")
        with self.assertRaisesRegex(ValueError, "EEA_PORT"):
            resolve_server_config(port="not-a-number")
        for value in ("atlas.example", "https://atlas.example/path", "https://atlas.example/?a=1", "ftp://atlas.example"):
            with self.assertRaisesRegex(ValueError, "EEA_PUBLIC_ORIGIN"):
                parse_public_origin(value)

    def test_cli_explicit_values_are_forwarded_ahead_of_environment(self):
        with patch.dict(os.environ, {
            "EEA_ATLAS_DB": "environment-atlas.sqlite3",
            "EEA_COMMUNITY_DB": "environment-community.sqlite3",
            "EEA_HOST": "0.0.0.0",
            "EEA_PORT": "9010",
        }, clear=False), patch("electricity_atlas.cli.serve") as mocked_serve:
            from electricity_atlas.cli import main

            result = main([
                "--db", "explicit-atlas.sqlite3", "serve", "--community-db", "explicit-community.sqlite3",
                "--host", "127.0.0.1", "--port", "8123", "--public-origin", "https://atlas.example",
                "--require-existing-db",
            ])
        self.assertEqual(result, 0)
        mocked_serve.assert_called_once_with(
            Path("explicit-atlas.sqlite3"), "127.0.0.1", 8123,
            community_path=Path("explicit-community.sqlite3"), public_origin="https://atlas.example",
            require_existing_db=True,
        )

    def test_strict_mode_does_not_create_missing_database_and_accepts_expected_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.sqlite3"
            with self.assertRaisesRegex(ValueError, "required Atlas database"):
                create_server(missing, port=0, require_existing_db=True)
            self.assertFalse(missing.exists())
            with database(missing):
                pass
            server = create_server(missing, port=0, require_existing_db=True)
            server.server_close()

    def test_normal_development_start_still_initializes_a_missing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "development.sqlite3"
            server = create_server(missing, port=0)
            try:
                self.assertTrue(missing.is_file())
            finally:
                server.server_close()


if __name__ == "__main__":
    unittest.main()
