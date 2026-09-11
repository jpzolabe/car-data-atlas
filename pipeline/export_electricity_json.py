"""Materialize acces_electricite as JSON for the Astro site. Same pattern as
export_prix_json.py.

Usage: uv run python -m pipeline.export_electricity_json
Output: site/src/data/electricite.json
"""

import json

import duckdb

from pipeline.sentences import sentence_electricity

OUT_PATH = "site/src/data/electricite.json"


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
    """)

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

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_electricity_json.py — ne pas éditer directement."
        ),
        "source": {
            "producer": source[0], "dataset_name": source[1],
            "url": source[2], "retrieved_at": source[3],
        },
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "series": [{"period": p, "value": v} for p, v in rows],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} years to {OUT_PATH}")


if __name__ == "__main__":
    main()
