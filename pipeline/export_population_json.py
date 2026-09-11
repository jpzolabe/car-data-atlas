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

    # National-level multi-source disclosure — docs/plan.md §2.5. Two genuinely
    # independent sources disagree on the same country: RGPH-4 (census,
    # provisional) vs World Bank WDI (modelled estimate). Per CLAUDE.md's
    # authority ranking, census outranks modelled estimate regardless of
    # publication recency — the census row is hardcoded as the default/headline
    # here rather than computed generically, since authority_rank in
    # sources.csv is free text, not a sortable field, and there are only two
    # sources to choose between so far.
    national_rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.source_id, s.url
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = 'cf-pays-centrafrique-v1' and o.indicator_id = 'population_totale'
        order by o.period desc
    """).fetchall()

    headline = next(r for r in national_rows if r[5] == "icasees-rgph4-provisional")
    others = [r for r in national_rows if r[5] != "icasees-rgph4-provisional"]
    most_recent_other = others[0]  # already ordered by period desc
    spread_pct = abs(headline[1] - most_recent_other[1]) / most_recent_other[1] * 100

    national = {
        "headline": {
            "value": headline[1], "period": headline[0], "quality_flag": headline[2],
            "producer": headline[3], "dataset_name": headline[4],
        },
        "spread_pct": round(spread_pct, 1),
        "spread_vs_period": most_recent_other[0],
        "all_sources": [
            {
                "value": r[1], "period": r[0], "quality_flag": r[2],
                "producer": r[3], "dataset_name": r[4], "url": r[6],
            }
            for r in national_rows
        ],
    }

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
        "national": national,
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
