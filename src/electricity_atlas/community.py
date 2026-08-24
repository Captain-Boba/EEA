from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from .wallpaper_catalog import wallpaper_catalog, wallpaper_ids


COMMUNITY_SCHEMA = """
CREATE TABLE IF NOT EXISTS wallpaper_vote (
    wallpaper_id TEXT NOT NULL,
    browser_hash TEXT NOT NULL,
    vote INTEGER NOT NULL CHECK(vote IN (-1, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (wallpaper_id, browser_hash)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS wallpaper_vote_wallpaper_idx ON wallpaper_vote(wallpaper_id);
"""


def browser_hash(browser_id: str) -> str:
    return hashlib.sha256(browser_id.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CommunityStore:
    """Short-lived, write-safe connections for public wallpaper votes only."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(COMMUNITY_SCHEMA)
            connection.commit()

    @staticmethod
    def _states(connection: sqlite3.Connection, own_hash: str | None) -> list[dict[str, int | str | None | bool]]:
        aggregates = {
            row["wallpaper_id"]: (int(row["upvotes"]), int(row["downvotes"]))
            for row in connection.execute(
                """SELECT wallpaper_id,
                          SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) AS upvotes,
                          SUM(CASE WHEN vote = -1 THEN 1 ELSE 0 END) AS downvotes
                   FROM wallpaper_vote GROUP BY wallpaper_id"""
            )
        }
        own_votes = {}
        if own_hash:
            own_votes = {
                row["wallpaper_id"]: int(row["vote"])
                for row in connection.execute(
                    "SELECT wallpaper_id, vote FROM wallpaper_vote WHERE browser_hash = ?", (own_hash,)
                )
            }
        states = []
        for wallpaper in wallpaper_catalog():
            upvotes, downvotes = aggregates.get(wallpaper["id"], (0, 0))
            states.append({
                "wallpaper_id": wallpaper["id"],
                "upvotes": upvotes,
                "downvotes": downvotes,
                "score": upvotes - downvotes,
                "own_vote": own_votes.get(wallpaper["id"]),
            })
        ranked = sorted(states, key=lambda state: (-int(state["score"]), str(state["wallpaper_id"])))
        score_counts = Counter(int(state["score"]) for state in ranked)
        for index, state in enumerate(ranked, start=1):
            score = int(state["score"])
            state["rank"] = next(position for position, candidate in enumerate(ranked, start=1) if candidate["score"] == score)
            state["rank_shared"] = score_counts[score] > 1
        return states

    def list_votes(self, own_hash: str | None = None) -> list[dict[str, int | str | None | bool]]:
        with self._connection() as connection:
            return self._states(connection, own_hash)

    def cast_vote(self, wallpaper_id: str, own_hash: str, action: str) -> dict[str, int | str | None | bool]:
        if wallpaper_id not in wallpaper_ids():
            raise ValueError("unknown wallpaper_id")
        if action not in {"up", "down", "clear"}:
            raise ValueError("vote must be 'up', 'down', or 'clear'")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if action == "clear":
                    connection.execute(
                        "DELETE FROM wallpaper_vote WHERE wallpaper_id = ? AND browser_hash = ?",
                        (wallpaper_id, own_hash),
                    )
                else:
                    value = 1 if action == "up" else -1
                    now = _now()
                    connection.execute(
                        """INSERT INTO wallpaper_vote (wallpaper_id, browser_hash, vote, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(wallpaper_id, browser_hash) DO UPDATE SET
                             vote = excluded.vote, updated_at = excluded.updated_at""",
                        (wallpaper_id, own_hash, value, now, now),
                    )
                states = self._states(connection, own_hash)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return next(state for state in states if state["wallpaper_id"] == wallpaper_id)
