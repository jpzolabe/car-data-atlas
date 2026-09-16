"""Materialize one JSON entry per préfecture for Phase 4's first place
pages (docs/plan.md Sec2.4). Same CSV -> DuckDB -> JSON handoff as every
other export script; Astro reads this file directly.

Scope for this pass: population_totale (now reaching sous-préfecture,
see pipeline/fetch_icasees_population_projection.py) and the 5 WFP
market prices are the indicators confirmed to reach below préfecture
level; nombre_etablissements_sante reaches région level only (7 régions,
each covering several préfectures - see
pipeline/fetch_etablissements_sante.py), one level short of préfecture,
and is surfaced as such rather than folded into the same "available"
bucket as population/prix. Every other theme is included only as an
explicit "no data at this level" entry in each place's freshness list,
not silently omitted. Each préfecture page shows its own sous-préfectures'
2025 population figures directly (no separate page per sous-préfecture
yet - that's still a bigger, separate step, see docs/plan.md Sec2.4 item
4's second half). Locator maps are also still not part of this pass (item
3); they need new geo/mapshaper infrastructure.

Usage: uv run python -m pipeline.export_lieux_prefecture_json
Output: site/src/data/lieux_prefectures.json
"""

import json

import duckdb

OUT_PATH = "site/src/data/lieux_prefectures.json"

# Every theme on the site today; the per-place freshness list below marks
# which of these actually have préfecture-level data.
ALL_THEMES = [
    "Population", "Prix", "Infrastructures", "Éducation",
    "Santé", "Économie", "Agriculture",
]


def main():
    con = duckdb.connect()
    con.execute("""
        create view entities as select * from read_csv_auto('data/entities.csv');
        create view aliases as select * from read_csv_auto('data/aliases.csv');
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
    """)

    prefectures = con.execute("""
        select p.entity_id, p.name_fr, p.slug, p.valid_from::varchar, p.notes,
               r.entity_id as region_id, r.name_fr as region_name
        from entities p
        join entities r on p.parent_id = r.entity_id
        where p.level = 'prefecture'
        order by p.name_fr
    """).fetchall()

    pop_rows = con.execute("""
        select entity_id, period, value, quality_flag
        from observations
        where indicator_id = 'population_totale'
    """).fetchall()
    pop_by_entity: dict[str, dict[str, tuple]] = {}
    for entity_id, period, value, flag in pop_rows:
        pop_by_entity.setdefault(entity_id, {})[period] = (value, flag)

    national_2021 = pop_by_entity.get("cf-pays-centrafrique-v1", {}).get("2021", (None, None))[0]

    pop_2021_by_pref = {
        eid: vals["2021"][0]
        for eid, vals in pop_by_entity.items()
        if "2021" in vals and eid != "cf-pays-centrafrique-v1"
    }
    ranked = sorted(pop_2021_by_pref.items(), key=lambda kv: kv[1], reverse=True)
    rank_by_entity = {eid: i + 1 for i, (eid, _) in enumerate(ranked)}

    market_rows = con.execute("""
        select p.entity_id as prefecture_id, e.name_fr as market_name,
               o.indicator_id, o.period, o.value
        from observations o
        join entities e on o.entity_id = e.entity_id
        join entities p on e.parent_id = p.entity_id
        where e.level = 'marche'
        order by o.period
    """).fetchall()
    markets_by_prefecture: dict[str, dict[str, dict]] = {}
    for prefecture_id, market_name, indicator_id, period, value in market_rows:
        pref = markets_by_prefecture.setdefault(prefecture_id, {})
        market = pref.setdefault(market_name, {})
        # overwritten in period order -> ends up holding the latest value
        market[indicator_id] = {"period": period, "value": value}

    sp_rows = con.execute("""
        select p.entity_id as prefecture_id, sp.name_fr as sous_prefecture_name, o.value
        from observations o
        join entities sp on o.entity_id = sp.entity_id
        join entities p on sp.parent_id = p.entity_id
        where sp.level = 'sous_prefecture' and o.indicator_id = 'population_totale'
          and o.period = '2025'
        order by sp.name_fr
    """).fetchall()
    sous_prefectures_by_prefecture: dict[str, list[dict]] = {}
    for prefecture_id, sp_name, value in sp_rows:
        sous_prefectures_by_prefecture.setdefault(prefecture_id, []).append({
            "name_fr": sp_name, "pop_2025": value,
        })

    sante_region_rows = con.execute("""
        select entity_id, period, value
        from observations
        where indicator_id = 'nombre_etablissements_sante'
          and source_id = 'maina-master-facility-list-2019'
    """).fetchall()
    sante_by_region: dict[str, dict] = {
        entity_id: {"period": period, "value": value}
        for entity_id, period, value in sante_region_rows
        if entity_id != "cf-pays-centrafrique-v1"
    }

    alias_rows = con.execute("""
        select entity_id, source_id, alias, alias_type
        from aliases
        where alias_type = 'pcode'
    """).fetchall()
    aliases_by_entity: dict[str, list[dict]] = {}
    for entity_id, source_id, alias, _alias_type in alias_rows:
        aliases_by_entity.setdefault(entity_id, []).append({"source_id": source_id, "code": alias})

    siblings_by_region: dict[str, list[dict]] = {}
    for entity_id, name_fr, slug, _valid_from, _notes, region_id, _region_name in prefectures:
        siblings_by_region.setdefault(region_id, []).append({
            "entity_id": entity_id, "name_fr": name_fr, "slug": slug,
            "pop_2021": pop_2021_by_pref.get(entity_id),
        })

    result = {}
    for entity_id, name_fr, slug, valid_from, notes, region_id, region_name in prefectures:
        pop = pop_by_entity.get(entity_id, {})
        pop_2021, pop_2021_flag = pop.get("2021", (None, None))
        pop_2003, _ = pop.get("2003", (None, None))
        pop_2025, _ = pop.get("2025", (None, None))
        sous_prefectures = sorted(
            sous_prefectures_by_prefecture.get(entity_id, []), key=lambda s: s["name_fr"]
        )

        markets = [
            {"name_fr": m, "prices": prices}
            for m, prices in sorted(markets_by_prefecture.get(entity_id, {}).items())
        ]

        siblings = [
            s for s in siblings_by_region.get(region_id, []) if s["entity_id"] != entity_id
        ]

        sante_region = sante_by_region.get(region_id)

        freshness = []
        for theme in ALL_THEMES:
            if theme == "Population" and pop_2021 is not None:
                pop_period = "2025" if pop_2025 is not None else "2021"
                freshness.append({
                    "theme": theme, "period": pop_period, "available": True,
                    "level": "sous_prefecture" if sous_prefectures else "prefecture",
                })
            elif theme == "Prix" and markets:
                latest_period = max(
                    v["period"] for m in markets for v in m["prices"].values()
                )
                freshness.append({
                    "theme": theme, "period": latest_period, "available": True,
                    "level": "prefecture",
                })
            elif theme == "Santé" and sante_region is not None:
                freshness.append({
                    "theme": theme, "period": sante_region["period"], "available": True,
                    "level": "region",
                })
            else:
                freshness.append({
                    "theme": theme, "period": None, "available": False, "level": None,
                })

        result[slug] = {
            "entity_id": entity_id,
            "name_fr": name_fr,
            "slug": slug,
            "region_name": region_name,
            "valid_from": valid_from,
            "notes": notes,
            "aliases": aliases_by_entity.get(entity_id, []),
            "population": None if pop_2021 is None else {
                "pop_2003": pop_2003,
                "pop_2021": pop_2021,
                "pop_2021_flag": pop_2021_flag,
                "pop_2025": pop_2025,
                "rank_2021": rank_by_entity.get(entity_id),
                "total_prefectures": len(rank_by_entity),
                "national_2021": national_2021,
                "share_of_national_pct": (
                    round(pop_2021 / national_2021 * 100, 1) if national_2021 else None
                ),
            },
            "sous_prefectures": sous_prefectures,
            "markets": markets,
            "siblings": siblings,
            "sante_region": None if sante_region is None else {
                "region_name": region_name,
                "period": sante_region["period"],
                "value": sante_region["value"],
            },
            "freshness": freshness,
        }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with_population = sum(1 for v in result.values() if v["population"])
    with_markets = sum(1 for v in result.values() if v["markets"])
    with_sante_region = sum(1 for v in result.values() if v["sante_region"])
    with_sous_prefectures = sum(1 for v in result.values() if v["sous_prefectures"])
    print(
        f"Wrote {len(result)} préfectures to {OUT_PATH} "
        f"({with_population} with population data, {with_markets} with market prices, "
        f"{with_sante_region} with a régional santé figure, "
        f"{with_sous_prefectures} with sous-préfecture population)"
    )


if __name__ == "__main__":
    main()
