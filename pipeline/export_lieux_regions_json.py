"""Materialize one JSON entry per région - the admin level between pays and
préfecture that had entities.csv rows and site-wide grouping (prefectures/
index.astro, each préfecture's region_name) but no page or URL of its own.
Added 2026-10-16 after an external UX review flagged this as the one tier
in the hierarchy that exists in the data but not on the site.

Région itself isn't an observed entity for most indicators - population is
a sum of its préfectures (same idea as a préfecture's pop_2025 being a sum
of its sous-préfectures), labelled as such rather than presented as a
directly published régional figure. Santé is the one indicator genuinely
observed at région level (nombre_etablissements_sante, see
pipeline/fetch_etablissements_sante.py) - this page is its canonical home;
préfecture pages still show their own région's figure too, since that
remains the finest depth available for santé at that préfecture.

Usage: uv run python -m pipeline.export_lieux_regions_json
Output: site/src/data/lieux_regions.json
"""

import json
import re

import duckdb

OUT_PATH = "site/src/data/lieux_regions.json"


def main():
    con = duckdb.connect()
    con.execute("""
        create view entities as select * from read_csv_auto('data/entities.csv');
        create view observations as select * from read_csv_auto('data/observations.csv');
    """)

    regions = con.execute("""
        select entity_id, name_fr, slug, notes
        from entities
        where level = 'region'
        order by name_fr
    """).fetchall()

    prefectures = con.execute("""
        select entity_id, name_fr, slug, parent_id
        from entities
        where level = 'prefecture'
    """).fetchall()

    pop_rows = con.execute("""
        select entity_id, period, value
        from observations
        where indicator_id = 'population_totale' and period in ('2021', '2025')
    """).fetchall()
    pop_by_entity: dict[str, dict[str, float]] = {}
    for entity_id, period, value in pop_rows:
        pop_by_entity.setdefault(entity_id, {})[period] = value

    national_2021 = pop_by_entity.get("cf-pays-centrafrique-v1", {}).get("2021")

    sante_rows = con.execute("""
        select entity_id, period, value
        from observations
        where indicator_id = 'nombre_etablissements_sante'
          and source_id = 'maina-master-facility-list-2019'
    """).fetchall()
    sante_by_region = {entity_id: {"period": period, "value": value} for entity_id, period, value in sante_rows}

    prefectures_by_region: dict[str, list[dict]] = {}
    for entity_id, name_fr, slug, parent_id in prefectures:
        pop = pop_by_entity.get(entity_id, {})
        prefectures_by_region.setdefault(parent_id, []).append({
            "entity_id": entity_id, "name_fr": name_fr, "slug": slug,
            "pop_2021": pop.get("2021"), "pop_2025": pop.get("2025"),
        })

    result = {}
    for entity_id, name_fr, slug, notes in regions:
        prefs = sorted(
            prefectures_by_region.get(entity_id, []),
            key=lambda p: (p["pop_2021"] is None, -(p["pop_2021"] or 0)),
        )
        chef_lieu_match = re.search(r"Chef-lieu régional\s*:\s*([^.]+)\.", notes)
        chef_lieu = chef_lieu_match.group(1).strip() if chef_lieu_match else None

        pop_2021_vals = [p["pop_2021"] for p in prefs]
        pop_2025_vals = [p["pop_2025"] for p in prefs]
        pop_2021_total = sum(pop_2021_vals) if all(v is not None for v in pop_2021_vals) and pop_2021_vals else None
        pop_2025_total = sum(pop_2025_vals) if all(v is not None for v in pop_2025_vals) and pop_2025_vals else None

        sante = sante_by_region.get(entity_id)

        result[slug] = {
            "entity_id": entity_id,
            "name_fr": name_fr,
            "slug": slug,
            "chef_lieu": chef_lieu,
            "notes": notes,
            "prefectures": prefs,
            "population": None if pop_2021_total is None else {
                "pop_2021_total": pop_2021_total,
                "pop_2025_total": pop_2025_total,
                "share_of_national_pct": (
                    round(pop_2021_total / national_2021 * 100, 1) if national_2021 else None
                ),
            },
            "sante": None if sante is None else {"period": sante["period"], "value": sante["value"]},
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(result)} régions to {OUT_PATH}")


if __name__ == "__main__":
    main()
