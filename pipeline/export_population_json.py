"""Materialize a JSON artifact for the Astro site from the population_totale
observations, joined against entities (for région/préfecture names and hierarchy)
and sources (for the citation line). This is the CSV -> DuckDB -> JSON handoff
described in docs/decisions.md - Astro reads this file directly, it never parses
or joins the raw CSVs itself.

Widened 2026-09-12 to also export 3 World Bank indicators (growth rate,
urban %, age dependency ratio) as additive "Autres indicateurs" cards,
following the same headline-then-breakdown pattern as prix/infrastructures;
population_totale's national multi-source disclosure stays the headline.

Widened again 2026-09-12: a 2025 ICASEES projection
(pipeline/fetch_icasees_population_projection.py) reaches sous-préfecture
level, this project's finest floor - the first indicator to get there.
Préfecture rows now carry a pop_2025 column (summed from the same file's
sous-préfecture rows) alongside the existing 2003/2021 columns, and a new
sous-préfecture breakdown groups all 85 by their parent préfecture.

Usage: uv run python -m pipeline.export_population_json
Output: site/src/data/population.json
"""

import json

import duckdb

from pipeline.sentences import sentence_population, sentence_population_rate

OUT_PATH = "site/src/data/population.json"

OTHER_INDICATORS = [
    "taux_croissance_population",
    "taux_urbanisation",
    "taux_dependance_demographique",
    "enregistrement_naissances",
    "mariage_precoce_filles",
]


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
          max(case when o.period = '2025' then o.value end) as pop_2025,
          max(o.source_id) as source_id
        from entities p
        join entities r on p.parent_id = r.entity_id
        join observations o on o.entity_id = p.entity_id
                             and o.indicator_id = 'population_totale'
        where p.level = 'prefecture'
        group by p.name_fr, r.name_fr
        order by r.name_fr, p.name_fr
    """).fetchall()

    sp_rows = con.execute("""
        select p.name_fr as prefecture, sp.name_fr as sous_prefecture, o.value
        from entities sp
        join entities p on sp.parent_id = p.entity_id
        join observations o on o.entity_id = sp.entity_id
                             and o.indicator_id = 'population_totale'
                             and o.period = '2025'
        where sp.level = 'sous_prefecture'
        order by p.name_fr, sp.name_fr
    """).fetchall()
    sous_prefectures_by_prefecture: dict[str, list[dict]] = {}
    for prefecture, sous_prefecture, value in sp_rows:
        sous_prefectures_by_prefecture.setdefault(prefecture, []).append({
            "name_fr": sous_prefecture, "pop_2025": value,
        })

    source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'citypopulation-de-caf'
    """).fetchone()

    # Répartition par sexe - same RGPH-4 observation the national headline
    # already cites (the split was sitting in that row's own notes field;
    # promoted to real indicators, see docs/decisions.md).
    hommes = con.execute("""
        select value from observations
        where entity_id = 'cf-pays-centrafrique-v1' and indicator_id = 'population_hommes'
    """).fetchone()[0]
    femmes = con.execute("""
        select value from observations
        where entity_id = 'cf-pays-centrafrique-v1' and indicator_id = 'population_femmes'
    """).fetchone()[0]
    sexe_total = hommes + femmes
    repartition_sexe = {
        "hommes": hommes, "femmes": femmes,
        "hommes_pct": round(hommes / sexe_total * 100, 1),
        "femmes_pct": round(femmes / sexe_total * 100, 1),
    }

    # National-level multi-source disclosure - docs/plan.md §2.5. Two genuinely
    # independent sources disagree on the same country: RGPH-4 (census,
    # provisional) vs World Bank WDI (modelled estimate). Per AGENTS.md's
    # authority ranking, census outranks modelled estimate regardless of
    # publication recency - the census row is hardcoded as the default/headline
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

    # Lead sentence: the most populous préfecture, as a representative example -
    # not one sentence per row, matching docs/plan.md's "one generated sentence
    # per chart" pattern rather than per data point.
    lead_row = max(rows, key=lambda r: r[3])  # r[3] = pop_2021
    lead_text, lead_template_id = sentence_population(
        prefecture=lead_row[0], year="2021", value=lead_row[3], reconciled=True
    )

    names = dict(con.execute(
        "select indicator_id, name_fr from read_csv_auto('data/indicators.csv')"
    ).fetchall())
    definitions = dict(con.execute(
        "select indicator_id, definition_fr from read_csv_auto('data/indicators.csv')"
    ).fetchall())

    others = []
    for indicator_id in OTHER_INDICATORS:
        other_rows = con.execute("""
            select o.period, o.value, s.producer, s.dataset_name, s.url, s.retrieved_at::varchar
            from observations o
            join sources s on o.source_id = s.source_id
            where o.entity_id = 'cf-pays-centrafrique-v1' and o.indicator_id = ?
            order by o.period
        """, [indicator_id]).fetchall()
        other_latest = other_rows[-1]
        other_lead, other_template_id = sentence_population_rate(
            indicator_id, other_latest[0], other_latest[1]
        )
        others.append({
            "indicator_id": indicator_id,
            "name_fr": names[indicator_id],
            "definition_fr": definitions[indicator_id],
            "latest": {"period": other_latest[0], "value": other_latest[1]},
            "series": [{"period": r[0], "value": r[1]} for r in other_rows],
            "lead_sentence": other_lead,
            "lead_sentence_template_id": other_template_id,
            "source": {
                "producer": other_latest[2], "dataset_name": other_latest[3],
                "url": other_latest[4], "retrieved_at": other_latest[5],
            },
        })

    data = {
        "generated_note": (
            "Généré à partir de data/observations.csv via "
            "pipeline/export_population_json.py - ne pas éditer directement."
        ),
        "source": {
            "producer": source[0], "dataset_name": source[1],
            "url": source[2], "retrieved_at": source[3],
        },
        "definition_fr": definitions["population_totale"],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "national": national,
        "repartition_sexe": repartition_sexe,
        "prefectures": [
            {
                "prefecture": r[0], "region": r[1],
                "pop_2003": r[2], "pop_2021": r[3],
                "pop_2021_flag": r[4], "pop_2025": r[5],
                "sous_prefectures": sous_prefectures_by_prefecture.get(r[0], []),
            }
            for r in rows
        ],
        "other_indicators": others,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Wrote {len(rows)} préfectures ({len(sp_rows)} sous-préfectures) "
        f"+ {len(others)} other indicators to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
