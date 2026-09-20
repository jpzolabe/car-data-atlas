"""Materialize the infrastructures theme as JSON for the Astro site. Replaces
export_electricity_json.py (renamed, not just extended -- the theme is no
longer just electricity). Same CSV -> DuckDB -> JSON handoff as every other
export script.

Electricity stays the headline (AGENTS.md's own domain fact cites it, and its
2019 value exactly matches the MICS 2018-19 figure -- the clearest, most
independently-verified figure in this theme). Internet use, mobile
subscriptions, water and sanitation access are additive "Autres indicateurs"
cards below it, all from the World Bank API, all confirmed to have real,
fresh (up to 2024) CAF data before being added -- see docs/decisions.md.

Usage: uv run python -m pipeline.export_infrastructures_json
Output: site/src/data/infrastructures.json
"""

import json

import duckdb

from pipeline.sentences import sentence_electricity, sentence_infrastructure_rate

OUT_PATH = "site/src/data/infrastructures.json"

OTHER_INDICATORS = [
    "taux_utilisation_internet",
    "abonnements_mobiles",
    "acces_eau_potable_base",
    "acces_assainissement_base",
]


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
    """)

    names = dict(con.execute("select indicator_id, name_fr from indicators").fetchall())
    definitions = dict(con.execute("select indicator_id, definition_fr from indicators").fetchall())

    rows = con.execute("""
        select period, value
        from observations
        where indicator_id = 'acces_electricite'
        order by period
    """).fetchall()

    source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'world-bank-electricity-access'
    """).fetchone()

    latest_period, latest_value = rows[-1]
    prev_value = rows[-2][1] if len(rows) > 1 else None
    lead_text, lead_template_id = sentence_electricity(latest_period, latest_value, prev_value)

    others = []
    for indicator_id in OTHER_INDICATORS:
        other_rows = con.execute("""
            select o.period, o.value, s.producer, s.dataset_name, s.url, s.retrieved_at::varchar
            from observations o
            join sources s on o.source_id = s.source_id
            where o.indicator_id = ?
            order by o.period
        """, [indicator_id]).fetchall()
        latest = other_rows[-1]
        cat_lead, cat_template_id = sentence_infrastructure_rate(indicator_id, latest[0], latest[1])
        others.append({
            "indicator_id": indicator_id,
            "name_fr": names[indicator_id],
            "definition_fr": definitions[indicator_id],
            "latest": {"period": latest[0], "value": latest[1]},
            "series": [{"period": r[0], "value": r[1]} for r in other_rows],
            "lead_sentence": cat_lead,
            "lead_sentence_template_id": cat_template_id,
            "source": {
                "producer": latest[2], "dataset_name": latest[3],
                "url": latest[4], "retrieved_at": latest[5],
            },
        })

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_infrastructures_json.py - ne pas éditer directement."
        ),
        "source": {
            "producer": source[0], "dataset_name": source[1],
            "url": source[2], "retrieved_at": source[3],
        },
        "definition_fr": definitions["acces_electricite"],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "series": [{"period": p, "value": v} for p, v in rows],
        "other_indicators": others,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} years (électricité) + {len(others)} other indicators to {OUT_PATH}")


if __name__ == "__main__":
    main()
