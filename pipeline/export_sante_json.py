"""Materialize the santé theme as JSON for the Astro site. First export
script for this theme (previously nonexistent) -- same CSV -> DuckDB -> JSON
handoff as export_education_json.py, and the same category + headline
structure (docs/plan.md Sec2.3), since santé has 10 indicators across
natural groups just like éducation does. No multi-source disclosure yet --
every indicator has exactly one source so far, so every block is the plain
latest-value-plus-series shape.

Categories ordered by logical sequence per the headline-then-breakdown rule
(docs/decisions.md): what resources exist (système de santé) -> what
prevention happens (vaccination) -> what the outcomes are (mortalité et
espérance de vie) -> disease-specific burden (maladies).

Usage: uv run python -m pipeline.export_sante_json
Output: site/src/data/sante.json
"""

import json

import duckdb

from pipeline.sentences import sentence_sante_rate

OUT_PATH = "site/src/data/sante.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

CATEGORIES = [
    ("systeme", "Système de santé", [
        "depenses_sante_pib",
        "densite_medecins",
        "densite_lits_hopital",
    ]),
    ("vaccination", "Vaccination", [
        "taux_vaccination_rougeole",
        "taux_vaccination_dtc",
    ]),
    ("mortalite", "Mortalité et espérance de vie", [
        "esperance_vie",
        "taux_mortalite_moins_5ans",
        "taux_mortalite_infantile",
        "taux_mortalite_maternelle",
    ]),
    ("maladies", "Maladies", [
        "incidence_vih",
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
    lead_text, lead_template_id = sentence_sante_rate(indicator_id, latest[0], latest[1])

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
        if ind["indicator_id"] == "esperance_vie"
    )

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_sante_json.py — ne pas éditer directement."
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
