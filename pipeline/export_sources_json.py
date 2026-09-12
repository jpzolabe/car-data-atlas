"""Materialize data/sources.csv as JSON for the /sources page. Same CSV -> JSON
handoff pattern as the other export scripts - see docs/decisions.md.

Usage: uv run python -m pipeline.export_sources_json
Output: site/src/data/sources.json
"""

import json

import duckdb

OUT_PATH = "site/src/data/sources.json"


def main():
    con = duckdb.connect()
    con.execute("create view sources as select * from read_csv_auto('data/sources.csv');")

    rows = con.execute("""
        select source_id, producer, dataset_name, url, licence, licence_notes,
               geography_vintage, update_cadence, retrieved_at::varchar,
               authority_rank, access_notes
        from sources
        order by producer
    """).fetchall()
    cols = ["source_id", "producer", "dataset_name", "url", "licence", "licence_notes",
            "geography_vintage", "update_cadence", "retrieved_at",
            "authority_rank", "access_notes"]

    data = {
        "generated_note": (
            "Généré depuis data/sources.csv via "
            "pipeline/export_sources_json.py - ne pas éditer directement."
        ),
        "sources": [dict(zip(cols, r, strict=True)) for r in rows],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} sources to {OUT_PATH}")


if __name__ == "__main__":
    main()
