from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[2] / "web" / "wallpapers.json"


@lru_cache(maxsize=1)
def wallpaper_catalog() -> tuple[dict[str, Any], ...]:
    """Load and validate the sole machine-readable Europa Overload catalog."""
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Wallpaper catalog is unavailable") from exc
    if not isinstance(payload, list) or len(payload) != 250:
        raise RuntimeError("Wallpaper catalog must contain exactly 250 entries")
    required = {"id", "title", "subject", "country", "file", "width", "height", "author", "license"}
    ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for wallpaper in payload:
        if not isinstance(wallpaper, dict) or set(wallpaper) != required:
            raise RuntimeError("Wallpaper catalog has an invalid entry")
        wallpaper_id = wallpaper["id"]
        if not isinstance(wallpaper_id, str) or not wallpaper_id.startswith("commons-") or wallpaper_id in ids:
            raise RuntimeError("Wallpaper catalog has invalid stable IDs")
        ids.add(wallpaper_id)
        validated.append(wallpaper)
    return tuple(validated)


@lru_cache(maxsize=1)
def wallpaper_ids() -> frozenset[str]:
    return frozenset(wallpaper["id"] for wallpaper in wallpaper_catalog())
