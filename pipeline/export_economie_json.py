"""Materialize the économie theme as JSON for the Astro site. First export
script for this theme -- same category + headline structure as
export_sante_json.py. Two indicators (pib_total, pib_par_habitant) use a
dedicated monetary sentence function; the other 8 (all "%") share one
generic rate function.

Categories ordered by logical sequence: production (how big is the
economy) -> commerce extérieur (how it trades and finances itself
externally) -> finances publiques (how the state finances itself) ->
niveau de vie (what it means for people) -- ending on the outcome, not
starting there.

Usage: uv run python -m pipeline.export_economie_json
Output: site/src/data/economie.json
"""

import json

import duckdb

from pipeline.sentences import sentence_economie_montant, sentence_economie_rate

OUT_PATH = "site/src/data/economie.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

MONTANT_INDICATORS = {"pib_total", "pib_par_habitant"}

CATEGORIES = [
    ("production", "Production", [
        "pib_total",
        "pib_par_habitant",
        "taux_croissance_pib",
    ]),
    ("commerce", "Commerce extérieur", [
        "exportations_pib",
        "importations_pib",
        "investissements_directs_etrangers",
        "dette_exterieure_rnb",
    ]),
    ("finances_publiques", "Finances publiques", [
        "recettes_publiques_pib",
    ]),
    ("niveau_de_vie", "Niveau de vie", [
        "taux_chomage",
        "taux_pauvrete",
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
    if indicator_id in MONTANT_INDICATORS:
        lead_text, lead_template_id = sentence_economie_montant(indicator_id, latest[0], latest[1])
    else:
        lead_text, lead_template_id = sentence_economie_rate(indicator_id, latest[0], latest[1])

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
        if ind["indicator_id"] == "pib_par_habitant"
    )

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_economie_json.py — ne pas éditer directement."
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
