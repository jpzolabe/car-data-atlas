"""Materialize a JSON artifact for the Astro site from the population_totale
observations, joined against entities (for région/préfecture names and hierarchy)
and sources (for the citation line). This is the CSV -> DuckDB -> JSON handoff
described in docs/decisions.md — Astro reads this file directly, it never parses
or joins the raw CSVs itself.

Usage: uv run python -m pipeline.export_population_json
Output: site/src/data/population.json
"""

import json

import duckdb

from pipeline.sentences import sentence_population

OUT_PATH = "site/src/data/population.json"


def main():
    con = duckdb.connect()
    con.execute("""
        create view entities as select * from read_csv_auto('data/entities.csv');
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
    """)

    rows = con.execute("""
        select
          p.name_fr as prefecture,
          r.name_fr as region,
          max(case when o.period = '2003' then o.value end) as pop_2003,
          max(case when o.period = '2021' then o.value end) as pop_2021,
          max(case when o.period = '2021' then o.quality_flag end) as pop_2021_flag,
          max(o.source_id) as source_id
        from entities p
        join entities r on p.parent_id = r.entity_id
        join observations o on o.entity_id = p.entity_id
                             and o.indicator_id = 'population_totale'
        where p.level = 'prefecture'
        group by p.name_fr, r.name_fr
        order by r.name_fr, p.name_fr
    """).fetchall()

    source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'citypopulation-de-caf'
    """).fetchone()

    # Lead sentence: the most populous préfecture, as a representative example —
    # not one sentence per row, matching docs/plan.md's "one generated sentence
    # per chart" pattern rather than per data point.
    lead_row = max(rows, key=lambda r: r[3])  # r[3] = pop_2021
    lead_text, lead_template_id = sentence_population(
        prefecture=lead_row[0], year="2021", value=lead_row[3], reconciled=True
    )

    data = {
        "generated_note": (
            "Généré à partir de data/observations.csv via "
            "pipeline/export_population_json.py — ne pas éditer directement."
        ),
        "source": {
            "producer": source[0], "dataset_name": source[1],
            "url": source[2], "retrieved_at": source[3],
        },
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "prefectures": [
            {
                "prefecture": r[0], "region": r[1],
                "pop_2003": r[2], "pop_2021": r[3],
                "pop_2021_flag": r[4],
            }
            for r in rows
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(rows)} préfectures to {OUT_PATH}")


if __name__ == "__main__":
    main()
