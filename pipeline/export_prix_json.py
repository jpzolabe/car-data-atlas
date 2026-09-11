"""Materialize the prix_ihpc_global time series as JSON for the Astro site.
Same CSV -> DuckDB -> JSON handoff as export_population_json.py.

Usage: uv run python -m pipeline.export_prix_json
Output: site/src/data/prix.json
"""

import json

import duckdb

from pipeline.sentences import sentence_prix

OUT_PATH = "site/src/data/prix.json"


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
    """)

    rows = con.execute("""
        select period, value, quality_flag
        from observations
        where indicator_id = 'prix_ihpc_global'
        order by period
    """).fetchall()

    source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'icasees-ihpc-dashboard'
    """).fetchone()

    latest = rows[-1]  # (period, value, quality_flag)
    lead_text, lead_template_id = sentence_prix(
        period=latest[0], value=latest[1], reconciled=latest[2] == "estime"
    )

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_prix_json.py — ne pas éditer directement."
        ),
        "source": {
            "producer": source[0], "dataset_name": source[1],
            "url": source[2], "retrieved_at": source[3],
        },
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "series": [
            {"period": r[0], "value": r[1], "reconciled": r[2] == "estime"}
            for r in rows
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} months to {OUT_PATH}")


if __name__ == "__main__":
    main()
