"""Materialize the agriculture theme as JSON for the Astro site. Last of the
three brand-new theme export scripts this pass -- same category + headline
structure as export_sante_json.py / export_economie_json.py.

Categories ordered by logical sequence: terres et ressources (what land
exists to farm) -> production (what's grown on it) -> emploi et
alimentation (what it means for people -- jobs and nutrition outcomes).

Usage: uv run python -m pipeline.export_agriculture_json
Output: site/src/data/agriculture.json
"""

import json

import duckdb

from pipeline.sentences import sentence_agriculture_rate

OUT_PATH = "site/src/data/agriculture.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

CATEGORIES = [
    ("terres", "Terres et ressources", [
        "terres_agricoles",
        "terres_arables",
        "couverture_forestiere",
    ]),
    ("production", "Production", [
        "valeur_ajoutee_agriculture_pib",
        "indice_production_alimentaire",
        "rendement_cereales",
        "consommation_engrais",
    ]),
    ("emploi_alimentation", "Emploi et alimentation", [
        "emploi_agricole",
        "taux_sous_alimentation",
    ]),
]


def build_indicator(con, indicator_id: str) -> dict:
    rows = con.execute("""
        select o.period, o.value, s.producer, s.dataset_name, s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = ?
        order by o.period
    """, [COUNTRY_ID, indicator_id]).fetchall()

    latest = rows[-1]
    lead_text, lead_template_id = sentence_agriculture_rate(indicator_id, latest[0], latest[1])

    return {
        "indicator_id": indicator_id,
        "latest": {"period": latest[0], "value": latest[1]},
        "series": [{"period": r[0], "value": r[1]} for r in rows],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "source": {
            "producer": latest[2], "dataset_name": latest[3],
            "url": latest[4], "retrieved_at": latest[5],
        },
    }


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
    """)

    names = dict(con.execute("select indicator_id, name_fr from indicators").fetchall())

    categories = []
    for key, label, indicator_ids in CATEGORIES:
        indicator_blocks = []
        for indicator_id in indicator_ids:
            block = build_indicator(con, indicator_id)
            block["name_fr"] = names[indicator_id]
            indicator_blocks.append(block)
        categories.append({"key": key, "label_fr": label, "indicators": indicator_blocks})

    headline_indicator = next(
        ind
        for cat in categories
        for ind in cat["indicators"]
        if ind["indicator_id"] == "emploi_agricole"
    )

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_agriculture_json.py — ne pas éditer directement."
        ),
        "headline": headline_indicator,
        "categories": categories,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(c["indicators"]) for c in categories)
    print(f"Wrote {total} indicators across {len(categories)} categories to {OUT_PATH}")


if __name__ == "__main__":
    main()
