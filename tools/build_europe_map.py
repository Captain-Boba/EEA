"""Build the local Europe SVG used by the web UI.

The script intentionally uses only the Python standard library. It consumes
Natural Earth 1:50m Admin 0 Countries GeoJSON, clips it to the European map
extent, simplifies the rings, and emits one SVG path per country feature.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, Sequence
from xml.sax.saxutils import quoteattr


SOURCE_VERSION = "5.1.1"
SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "v5.1.1/geojson/ne_50m_admin_0_countries.geojson"
)
SOURCE_SHA256 = "3e458fc036ad0a66411f2c1e6cac49c5d7bfb81cb1123bc513b22511a2b7fdeb"

# Geometry is clipped with a margin outside the visible extent so the
# artificial clip edges never appear as country borders in the SVG viewport.
CLIP_BOUNDS = (-30.0, 30.0, 55.0, 76.0)
MAP_BOUNDS = (-25.0, 34.0, 42.0, 72.0)
SIMPLIFY_TOLERANCE = 0.035
SVG_WIDTH = 960.0
SVG_PADDING = 8.0

ATLAS_ISO3 = frozenset({
    "AUT", "BEL", "BGR", "CHE", "CZE", "DEU", "DNK", "ESP", "EST", "FIN",
    "FRA", "GBR", "GRC", "HRV", "HUN", "IRL", "ITA", "LTU", "LUX", "LVA",
    "MNE", "MKD", "NLD", "NOR", "POL", "PRT", "ROU", "SRB", "SVK", "SVN",
    "SWE",
})

Point = tuple[float, float]


def _admin_code(properties: dict[str, object]) -> str:
    # ADM0_A3 is stable for France and Norway, whose ISO_A3 value is -99 in
    # Natural Earth because their map-unit geometry includes dependencies.
    return str(properties.get("ADM0_A3") or properties.get("ISO_A3") or "")


def _rings(geometry: dict[str, object]) -> Iterable[list[Point]]:
    coordinates = geometry.get("coordinates")
    if geometry.get("type") == "Polygon" and isinstance(coordinates, list):
        polygons = [coordinates]
    elif geometry.get("type") == "MultiPolygon" and isinstance(coordinates, list):
        polygons = coordinates
    else:
        return
    for polygon in polygons:
        for ring in polygon:
            yield [(float(point[0]), float(point[1])) for point in ring]


def _inside(point: Point, edge: str, value: float) -> bool:
    x, y = point
    return {
        "left": x >= value,
        "right": x <= value,
        "bottom": y >= value,
        "top": y <= value,
    }[edge]


def _intersection(start: Point, end: Point, edge: str, value: float) -> Point:
    x1, y1 = start
    x2, y2 = end
    if edge in {"left", "right"}:
        ratio = 0.0 if x2 == x1 else (value - x1) / (x2 - x1)
        return value, y1 + ratio * (y2 - y1)
    ratio = 0.0 if y2 == y1 else (value - y1) / (y2 - y1)
    return x1 + ratio * (x2 - x1), value


def _clip_edge(points: Sequence[Point], edge: str, value: float) -> list[Point]:
    if not points:
        return []
    output: list[Point] = []
    start = points[-1]
    for end in points:
        start_inside = _inside(start, edge, value)
        end_inside = _inside(end, edge, value)
        if end_inside:
            if not start_inside:
                output.append(_intersection(start, end, edge, value))
            output.append(end)
        elif start_inside:
            output.append(_intersection(start, end, edge, value))
        start = end
    return output


def clip_ring(points: Sequence[Point]) -> list[Point]:
    min_lon, min_lat, max_lon, max_lat = CLIP_BOUNDS
    clipped = list(points)
    for edge, value in (
        ("left", min_lon), ("right", max_lon), ("bottom", min_lat), ("top", max_lat)
    ):
        clipped = _clip_edge(clipped, edge, value)
    if len(clipped) < 3:
        return []
    if clipped[0] != clipped[-1]:
        clipped.append(clipped[0])
    return clipped


def _distance_to_segment(point: Point, start: Point, end: Point) -> float:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    ratio = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + ratio * dx), py - (y1 + ratio * dy))


def _simplify_open(points: Sequence[Point], tolerance: float) -> list[Point]:
    if len(points) <= 2:
        return list(points)
    start, end = points[0], points[-1]
    distances = [_distance_to_segment(point, start, end) for point in points[1:-1]]
    if not distances or max(distances) <= tolerance:
        return [start, end]
    index = distances.index(max(distances)) + 1
    return _simplify_open(points[: index + 1], tolerance)[:-1] + _simplify_open(points[index:], tolerance)


def simplify_ring(points: Sequence[Point]) -> list[Point]:
    if len(points) <= 8:
        return list(points)
    simplified = _simplify_open(points[:-1], SIMPLIFY_TOLERANCE)
    if len(simplified) < 3:
        return list(points)
    simplified.append(simplified[0])
    return simplified


def project(point: Point) -> Point:
    """Project geographic coordinates directly into the local SVG plane."""
    lon, lat = point
    return lon, -lat


def _path(rings: Sequence[Sequence[Point]], transform) -> str:
    commands: list[str] = []
    for ring in rings:
        projected = [transform(project(point)) for point in ring]
        if len(projected) < 4:
            continue
        commands.append(f"M{projected[0][0]:.1f},{projected[0][1]:.1f}")
        commands.extend(f"L{x:.1f},{y:.1f}" for x, y in projected[1:-1])
        commands.append("Z")
    return "".join(commands)


def build(source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    features: list[dict[str, object]] = []

    for feature in payload.get("features", []):
        geometry = feature.get("geometry") or {}
        source_rings = list(_rings(geometry))
        min_lon, min_lat, max_lon, max_lat = CLIP_BOUNDS
        was_clipped = any(
            not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat)
            for ring in source_rings for lon, lat in ring
        )
        clipped_rings = []
        for ring in source_rings:
            clipped = clip_ring(ring)
            if not clipped:
                continue
            simplified = simplify_ring(clipped)
            if len(simplified) >= 4:
                clipped_rings.append(simplified)
        if not clipped_rings:
            continue
        properties = feature.get("properties") or {}
        code = _admin_code(properties)
        features.append({
            "code": code,
            "name": str(properties.get("NAME_EN") or properties.get("NAME") or code),
            "ne_id": str(properties.get("NE_ID") or code),
            "rings": clipped_rings,
            "clipped": was_clipped,
            "label": (float(properties.get("LABEL_X")), float(properties.get("LABEL_Y")))
            if properties.get("LABEL_X") is not None and properties.get("LABEL_Y") is not None
            else None,
        })
    found = {str(feature["code"]) for feature in features} & ATLAS_ISO3
    if found != ATLAS_ISO3:
        missing = ", ".join(sorted(ATLAS_ISO3 - found))
        raise ValueError(f"Natural Earth source is missing Atlas geometries: {missing}")

    atlas_counts = {code: sum(feature["code"] == code for feature in features) for code in ATLAS_ISO3}
    duplicated = sorted(code for code, count in atlas_counts.items() if count != 1)
    if duplicated:
        raise ValueError(f"Atlas geometry codes must occur exactly once: {', '.join(duplicated)}")

    view_min_lon, view_min_lat, view_max_lon, view_max_lat = MAP_BOUNDS
    view_outline = []
    for index in range(101):
        ratio = index / 100
        lon = view_min_lon + (view_max_lon - view_min_lon) * ratio
        lat = view_min_lat + (view_max_lat - view_min_lat) * ratio
        view_outline.extend((
            project((lon, view_min_lat)), project((lon, view_max_lat)),
            project((view_min_lon, lat)), project((view_max_lon, lat)),
        ))
    min_x = min(point[0] for point in view_outline)
    max_x = max(point[0] for point in view_outline)
    min_y = min(point[1] for point in view_outline)
    max_y = max(point[1] for point in view_outline)
    scale = (SVG_WIDTH - 2 * SVG_PADDING) / (max_x - min_x)
    svg_height = (max_y - min_y) * scale + 2 * SVG_PADDING

    def transform(point: Point) -> Point:
        return (
            SVG_PADDING + (point[0] - min_x) * scale,
            SVG_PADDING + (point[1] - min_y) * scale,
        )

    paths = []
    for feature in sorted(features, key=lambda item: (item["code"] in ATLAS_ISO3, item["name"])):
        label = feature["label"]
        label_attributes = ""
        if label is not None and MAP_BOUNDS[0] <= label[0] <= MAP_BOUNDS[2] and MAP_BOUNDS[1] <= label[1] <= MAP_BOUNDS[3]:
            label_x, label_y = transform(project(label))
            label_attributes = f' data-label-x="{label_x:.1f}" data-label-y="{label_y:.1f}"'
        paths.append(
            "  <path class=\"map-country\""
            f" data-ne-id={quoteattr(str(feature['ne_id']))}"
            f" data-ne-code={quoteattr(str(feature['code']))}"
            f" data-ne-name={quoteattr(str(feature['name']))}"
            f" data-clipped=\"{'true' if feature['clipped'] else 'false'}\""
            f"{label_attributes} d={quoteattr(_path(feature['rings'], transform))}/>"
        )

    svg = "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH:.0f} {svg_height:.0f}" role="img" aria-labelledby="map-asset-title map-asset-desc">',
        "  <title id=\"map-asset-title\">Europäische Länderkarte</title>",
        "  <desc id=\"map-asset-desc\">Vereinfachte Ländergeometrien für den European Electricity Atlas.</desc>",
        f"  <metadata>Natural Earth 1:50m Admin 0 Countries {SOURCE_VERSION}; public domain; {SOURCE_URL}; visible extent {MAP_BOUNDS}; geometry clipped with margin {CLIP_BOUNDS}; simplified tolerance {SIMPLIFY_TOLERANCE} degrees.</metadata>",
        '  <g id="europe-countries" fill-rule="evenodd">',
        *paths,
        "  </g>",
        '  <g id="map-value-labels" aria-hidden="true"></g>',
        "</svg>",
        "",
    ])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8", newline="\n")
    print(f"Wrote {destination} with {len(features)} European/background features and {len(found)} Atlas countries")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    build(args.source, args.destination)


if __name__ == "__main__":
    main()
