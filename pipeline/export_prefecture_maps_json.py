"""Materialize ready-to-draw SVG path strings for the locator maps on each
préfecture place page, from the simplified GeoJSON in geo/simplified/
(pipeline/build_geo_prefectures.py). Astro pages get plain "M x,y L x,y Z"
path data and a shared viewBox - no GeoJSON parsing or projection math in
the page itself, matching every other page's build-time-only-computation
rule (CLAUDE.md: zero client JS on place pages).

Projection: a simple equirectangular fit, not a proper cartographic
projection - fine at this scale (a small locator map of one mid-sized
country, not a navigational map) and keeps this dependency-free
(pyproject.toml has no projection library, and this doesn't need one).
Longitude is scaled by cos(mean_latitude) so the map isn't visibly
stretched east-west; both axes then share one scale factor fit to a
700px-wide viewBox, computed from the country outline's own bounding box
so every préfecture's shape sits correctly relative to the whole country
and to every other préfecture.

Usage: uv run python -m pipeline.export_prefecture_maps_json
Output: site/src/data/prefecture_maps.json
"""

import json
import math
from pathlib import Path

OUT_PATH = "site/src/data/prefecture_maps.json"
SIMPLIFIED_DIR = Path("geo/simplified")
COUNTRY_ENTITY_ID = "cf-pays-centrafrique-v1"
TARGET_WIDTH = 700


def load_geojson(entity_id: str) -> dict:
    with open(SIMPLIFIED_DIR / f"{entity_id}.geojson", encoding="utf-8") as f:
        return json.load(f)["features"][0]


def geometry_bounds(geometry: dict) -> tuple[float, float, float, float]:
    lons, lats = [], []

    def collect(coords, depth):
        if depth == 0:
            lons.append(coords[0])
            lats.append(coords[1])
        else:
            for c in coords:
                collect(c, depth - 1)

    depth = {"Polygon": 2, "MultiPolygon": 3}[geometry["type"]]
    collect(geometry["coordinates"], depth)
    return min(lons), min(lats), max(lons), max(lats)


def make_projector(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    mean_lat_rad = math.radians((min_lat + max_lat) / 2)
    lon_scale = math.cos(mean_lat_rad)

    raw_width = (max_lon - min_lon) * lon_scale
    raw_height = max_lat - min_lat
    scale = TARGET_WIDTH / raw_width
    height = raw_height * scale

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - min_lon) * lon_scale * scale
        y = (max_lat - lat) * scale  # flip: SVG y grows downward
        return round(x, 1), round(y, 1)

    return project, TARGET_WIDTH, round(height, 1)


def polygon_to_path(coordinates: list, project) -> str:
    """coordinates: a Polygon's ring list (exterior + holes)."""
    parts = []
    for ring in coordinates:
        points = [project(lon, lat) for lon, lat in ring]
        d = f"M{points[0][0]},{points[0][1]} " + " ".join(
            f"L{x},{y}" for x, y in points[1:]
        ) + " Z"
        parts.append(d)
    return " ".join(parts)


def geometry_to_path(geometry: dict, project) -> str:
    if geometry["type"] == "Polygon":
        return polygon_to_path(geometry["coordinates"], project)
    return " ".join(polygon_to_path(poly, project) for poly in geometry["coordinates"])


def main():
    country_feature = load_geojson(COUNTRY_ENTITY_ID)
    min_lon, min_lat, max_lon, max_lat = geometry_bounds(country_feature["geometry"])
    project, width, height = make_projector(min_lon, min_lat, max_lon, max_lat)

    country_path = geometry_to_path(country_feature["geometry"], project)

    prefectures = {}
    for path in sorted(SIMPLIFIED_DIR.glob("cf-p-*.geojson")):
        with open(path, encoding="utf-8") as f:
            feature = json.load(f)["features"][0]
        entity_id = feature["properties"]["entity_id"]
        prefectures[entity_id] = {
            "name_fr": feature["properties"]["name_fr"],
            "path": geometry_to_path(feature["geometry"], project),
        }

    data = {
        "generated_note": (
            "Généré depuis geo/simplified/*.geojson via "
            "pipeline/export_prefecture_maps_json.py - ne pas éditer directement."
        ),
        "view_box": f"0 0 {width} {height}",
        "country_path": country_path,
        "prefectures": prefectures,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Wrote {len(prefectures)} préfecture paths to {OUT_PATH} (viewBox {width}x{height})")


if __name__ == "__main__":
    main()
