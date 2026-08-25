from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


def backup_community_database(source: Path | str, output: Path | str, *, force: bool = False) -> Path:
    source_path = Path(source)
    output_path = Path(output)
    if not source_path.is_file():
        raise ValueError("community database does not exist or is not a regular file")
    if source_path.resolve() == output_path.resolve():
        raise ValueError("community backup output must differ from the source database")
    if output_path.exists() and not force:
        raise FileExistsError("community backup output already exists; use --force to replace it")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".sqlite3", prefix=".community-backup-", dir=output_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        source_connection = sqlite3.connect(f"file:{source_path.resolve().as_posix()}?mode=ro", uri=True)
        try:
            try:
                source_connection.execute("SELECT 1 FROM wallpaper_vote LIMIT 1").fetchone()
            except sqlite3.Error as exc:
                raise ValueError("community database does not have the expected vote schema") from exc
            destination_connection = sqlite3.connect(temporary_path)
            try:
                source_connection.backup(destination_connection)
                destination_connection.commit()
            finally:
                destination_connection.close()
        finally:
            source_connection.close()
        if output_path.exists() and not force:
            raise FileExistsError("community backup output already exists; use --force to replace it")
        os.replace(temporary_path, output_path)
        temporary_path = None
        return output_path
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
