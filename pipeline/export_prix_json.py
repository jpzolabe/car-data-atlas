"""Materialize the prix theme as JSON for the Astro site. Same CSV -> DuckDB
-> JSON handoff as export_population_json.py.

Widened 2026-09-12 from the global index alone to also include the published
inflation rate and 3 named COICOP sub-categories, all from the same already-
downloaded file (pipeline/fetch_ihpc.py) -- see docs/decisions.md. The global
index stays the page's headline/hero chart (top-level "series"/"lead_sentence",
unchanged shape); inflation and the categories are additive sections below it,
per docs/plan.md Sec2.3's headline-figure-then-breakdown rule.

Usage: uv run python -m pipeline.export_prix_json
Output: site/src/data/prix.json
"""

import json

import duckdb

from pipeline.sentences import (
    sentence_inflation,
    sentence_prix,
    sentence_prix_categorie,
    sentence_prix_denree,
)

OUT_PATH = "site/src/data/prix.json"

CATEGORY_INDICATORS = ["prix_ihpc_alimentation", "prix_ihpc_sante", "prix_ihpc_transports"]

# Market-level indicators (geographic_floor = "marche") -- entity-scoped,
# unlike the country-level IHPC series above.
MARKET_ENTITY_ID = "cf-m-bangui-v1"
DENREE_INDICATORS = [
    "prix_manioc_kg", "prix_riz_kg", "prix_mais_kg", "prix_boeuf_kg", "prix_huile_palme_l",
]


def fetch_series(con, indicator_id: str) -> list[tuple]:
    return con.execute("""
        select period, value, quality_flag
        from observations
        where indicator_id = ?
        order by period
    """, [indicator_id]).fetchall()


def fetch_market_series(con, indicator_id: str, entity_id: str) -> list[tuple]:
    return con.execute("""
        select period, value, quality_flag
        from observations
        where indicator_id = ? and entity_id = ?
        order by period
    """, [indicator_id, entity_id]).fetchall()


def fetch_national_breakdown(con) -> list[dict]:
    """Phase 4 step 3: the latest price per market and per commodity,
    grouped by préfecture -- every market with recent WFP data, not just
    Bangui. One row per market per commodity; the caller picks the latest
    period per (market, commodity) pair since coverage varies market to
    market."""
    placeholders = ",".join(["?"] * len(DENREE_INDICATORS))
    rows = con.execute(f"""
        select p.name_fr as prefecture_name, e.name_fr as market_name,
               o.indicator_id, o.period, o.value
        from observations o
        join entities e on o.entity_id = e.entity_id
        join entities p on e.parent_id = p.entity_id
        where o.indicator_id in ({placeholders}) and e.level = 'marche'
        order by o.period
    """, DENREE_INDICATORS).fetchall()

    latest_by_market_indicator: dict[tuple[str, str, str], tuple[str, float]] = {}
    for prefecture_name, market_name, indicator_id, period, value in rows:
        latest_by_market_indicator[(prefecture_name, market_name, indicator_id)] = (period, value)

    prefectures: dict[str, dict[str, dict]] = {}
    for key, latest in latest_by_market_indicator.items():
        prefecture_name, market_name, indicator_id = key
        period, value = latest
        pref = prefectures.setdefault(prefecture_name, {})
        market = pref.setdefault(market_name, {})
        market[indicator_id] = {"period": period, "value": value}

    result = []
    for prefecture_name in sorted(prefectures):
        markets = [
            {"name_fr": market_name, "prices": prices}
            for market_name, prices in sorted(prefectures[prefecture_name].items())
        ]
        result.append({"name_fr": prefecture_name, "markets": markets})
    return result


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
        create view entities as select * from read_csv_auto('data/entities.csv');
    """)

    names = dict(con.execute("select indicator_id, name_fr from indicators").fetchall())
    units = dict(con.execute("select indicator_id, unit from indicators").fetchall())
    definitions = dict(con.execute("select indicator_id, definition_fr from indicators").fetchall())

    rows = fetch_series(con, "prix_ihpc_global")

    source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'icasees-ihpc-dashboard'
    """).fetchone()
    source_dict = {
        "producer": source[0], "dataset_name": source[1],
        "url": source[2], "retrieved_at": source[3],
    }

    latest = rows[-1]  # (period, value, quality_flag)
    lead_text, lead_template_id = sentence_prix(
        period=latest[0], value=latest[1], reconciled=latest[2] == "estime"
    )

    inflation_rows = fetch_series(con, "taux_inflation")
    inflation_latest = inflation_rows[-1]
    inflation_lead, inflation_template_id = sentence_inflation(
        inflation_latest[0], inflation_latest[1]
    )
    inflation = {
        "definition_fr": definitions["taux_inflation"],
        "latest": {"period": inflation_latest[0], "value": inflation_latest[1]},
        "series": [{"period": r[0], "value": r[1]} for r in inflation_rows],
        "lead_sentence": inflation_lead,
        "lead_sentence_template_id": inflation_template_id,
    }

    categories = []
    for indicator_id in CATEGORY_INDICATORS:
        cat_rows = fetch_series(con, indicator_id)
        cat_latest = cat_rows[-1]
        cat_lead, cat_template_id = sentence_prix_categorie(
            indicator_id, cat_latest[0], cat_latest[1], cat_latest[2] == "estime"
        )
        categories.append({
            "indicator_id": indicator_id,
            "name_fr": names[indicator_id],
            "definition_fr": definitions[indicator_id],
            "latest": {"period": cat_latest[0], "value": cat_latest[1]},
            "series": [{"period": r[0], "value": r[1]} for r in cat_rows],
            "lead_sentence": cat_lead,
            "lead_sentence_template_id": cat_template_id,
        })

    wfp_source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'wfp-food-prices-hdx'
    """).fetchone()
    market_name = con.execute("""
        select name_fr from entities where entity_id = ?
    """, [MARKET_ENTITY_ID]).fetchone()[0]

    denrees = []
    for indicator_id in DENREE_INDICATORS:
        d_rows = fetch_market_series(con, indicator_id, MARKET_ENTITY_ID)
        d_latest = d_rows[-1]
        d_lead, d_template_id = sentence_prix_denree(indicator_id, d_latest[0], d_latest[1])
        denrees.append({
            "indicator_id": indicator_id,
            "name_fr": names[indicator_id],
            "definition_fr": definitions[indicator_id],
            "unit": units[indicator_id],
            "latest": {"period": d_latest[0], "value": d_latest[1]},
            "series": [{"period": r[0], "value": r[1]} for r in d_rows],
            "lead_sentence": d_lead,
            "lead_sentence_template_id": d_template_id,
        })

    breakdown = fetch_national_breakdown(con)

    market = {
        "entity_name": market_name,
        "source": {
            "producer": wfp_source[0], "dataset_name": wfp_source[1],
            "url": wfp_source[2], "retrieved_at": wfp_source[3],
        },
        "denrees": denrees,
        "breakdown": breakdown,
        "breakdown_labels": {i: names[i] for i in DENREE_INDICATORS},
    }

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_prix_json.py - ne pas éditer directement."
        ),
        "source": source_dict,
        "definition_fr": definitions["prix_ihpc_global"],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "series": [
            {"period": r[0], "value": r[1], "reconciled": r[2] == "estime"}
            for r in rows
        ],
        "inflation": inflation,
        "categories": categories,
        "market": market,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_markets = sum(len(p["markets"]) for p in breakdown)
    print(
        f"Wrote {len(rows)} months (global) + inflation + "
        f"{len(categories)} categories + {len(denrees)} market denrées + "
        f"breakdown ({total_markets} markets across {len(breakdown)} préfectures) "
        f"to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
