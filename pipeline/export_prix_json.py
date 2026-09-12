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

from pipeline.sentences import sentence_inflation, sentence_prix, sentence_prix_categorie

OUT_PATH = "site/src/data/prix.json"

CATEGORY_INDICATORS = ["prix_ihpc_alimentation", "prix_ihpc_sante", "prix_ihpc_transports"]


def fetch_series(con, indicator_id: str) -> list[tuple]:
    return con.execute("""
        select period, value, quality_flag
        from observations
        where indicator_id = ?
        order by period
    """, [indicator_id]).fetchall()


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
    """)

    names = dict(con.execute("select indicator_id, name_fr from indicators").fetchall())

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
            "latest": {"period": cat_latest[0], "value": cat_latest[1]},
            "series": [{"period": r[0], "value": r[1]} for r in cat_rows],
            "lead_sentence": cat_lead,
            "lead_sentence_template_id": cat_template_id,
        })

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_prix_json.py — ne pas éditer directement."
        ),
        "source": source_dict,
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "series": [
            {"period": r[0], "value": r[1], "reconciled": r[2] == "estime"}
            for r in rows
        ],
        "inflation": inflation,
        "categories": categories,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Wrote {len(rows)} months (global) + inflation + "
        f"{len(categories)} categories to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
