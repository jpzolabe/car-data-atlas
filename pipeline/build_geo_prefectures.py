"""Materialize per-entity GeoJSON files from the already-fetched COD-AB v02
snapshot (raw/cod-ab-caf/2026-09-05/caf_admin_boundaries.geojson.zip), the
same file data/entities.csv itself was built from. No new fetch - this is
processing, not sourcing.

Follows geo/README.md's planned convention: geo/raw/{entity_id}.geojson
(full precision, as fetched) and geo/simplified/{entity_id}.geojson
(simplified for rendering, kept under the 50 KB per-map performance
budget). One deviation from that README, noted here rather than silently
diverging: it names mapshaper as the simplification tool; this uses
shapely instead (already an approved pipeline dependency, unlike
mapshaper, which would need a new one - see AGENTS.md's "ask before
adding any dependency"). Same Douglas-Peucker algorithm either way.

Uses the "_em" (edge-matched) geometries, not the plain admin0/admin1
files - AGENTS.md's own source notes name COD-EM as "for cartography"
specifically (shared borders between adjacent préfectures line up
exactly, no gaps or overlaps), and it turns out to already be bundled in
the same zip as COD-AB, not a separate fetch as AGENTS.md's research
table assumed when written.

Joins every admin1_em feature to this project's préfecture entities via
adm1_pcode, checked live against data/aliases.csv rather than assumed:
all 20 match exactly, no fuzzy matching needed - the geometry is the same
COD-AB v02 vintage entities.csv itself was built from, so this is
expected, not a coincidence.

Usage: uv run python -m pipeline.build_geo_prefectures
"""

import csv
import json
import zipfile
from pathlib import Path

from shapely.geometry import mapping, shape

ZIP_PATH = "raw/cod-ab-caf/2026-09-05/caf_admin_boundaries.geojson.zip"
COUNTRY_ENTITY_ID = "cf-pays-centrafrique-v1"
SIMPLIFY_TOLERANCE = 0.02  # degrees - roughly 2 km at this latitude

RAW_DIR = Path("geo/raw")
SIMPLIFIED_DIR = Path("geo/simplified")


def load_prefecture_pcode_map() -> dict[str, str]:
    with open("data/aliases.csv", encoding="utf-8") as f:
        return {
            row["alias"]: row["entity_id"]
            for row in csv.DictReader(f)
            if row["alias_type"] == "pcode" and row["entity_id"].startswith("cf-p-")
        }


def write_feature(path: Path, entity_id: str, name_fr: str, geometry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"entity_id": entity_id, "name_fr": name_fr},
            "geometry": geometry,
        }],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(feature_collection, f, ensure_ascii=False)


def main():
    pcode_to_entity = load_prefecture_pcode_map()

    with zipfile.ZipFile(ZIP_PATH) as z:
        adm0 = json.loads(z.read("caf_admin0_em.geojson"))
        adm1 = json.loads(z.read("caf_admin1_em.geojson"))

    written = 0

    country_feature = adm0["features"][0]
    country_geom = country_feature["geometry"]
    write_feature(
        RAW_DIR / f"{COUNTRY_ENTITY_ID}.geojson",
        COUNTRY_ENTITY_ID, "République centrafricaine", country_geom,
    )
    country_simplified = shape(country_geom).simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
    if not country_simplified.is_valid:
        raise ValueError("Simplified country geometry is invalid")
    write_feature(
        SIMPLIFIED_DIR / f"{COUNTRY_ENTITY_ID}.geojson",
        COUNTRY_ENTITY_ID, "République centrafricaine", mapping(country_simplified),
    )
    written += 1

    for feature in adm1["features"]:
        pcode = feature["properties"]["adm1_pcode"]
        entity_id = pcode_to_entity.get(pcode)
        if entity_id is None:
            raise ValueError(f"adm1_pcode {pcode!r} has no matching préfecture entity")
        name_fr = feature["properties"]["adm1_name"]
        geom = feature["geometry"]

        write_feature(RAW_DIR / f"{entity_id}.geojson", entity_id, name_fr, geom)

        simplified = shape(geom).simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
        if not simplified.is_valid:
            raise ValueError(f"Simplified geometry for {entity_id} is invalid")
        write_feature(
            SIMPLIFIED_DIR / f"{entity_id}.geojson", entity_id, name_fr, mapping(simplified),
        )
        written += 1

    print(f"Wrote {written} entities' raw + simplified GeoJSON to {RAW_DIR} and {SIMPLIFIED_DIR}")


if __name__ == "__main__":
    main()
