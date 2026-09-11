"""Materialize taux_achevement_primaire as JSON for the Astro site. Combines
two patterns already used elsewhere rather than inventing a third: the
national multi-source disclosure block from export_population_json.py (here,
survey vs. modelled, instead of census vs. modelled) and the dense line-chart
series from export_electricity_json.py (here, the modelled series, since the
survey series only has 4 points for CAF).

Usage: uv run python -m pipeline.export_education_json
Output: site/src/data/education.json
"""

import json

import duckdb

from pipeline.sentences import sentence_education

OUT_PATH = "site/src/data/education.json"


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
    """)

    national_rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.source_id, s.url
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = 'cf-pays-centrafrique-v1'
          and o.indicator_id = 'taux_achevement_primaire'
        order by o.period desc
    """).fetchall()

    survey_rows = [r for r in national_rows if r[5] == "unesco-uis-cr1-survey"]
    modelled_rows = [r for r in national_rows if r[5] == "unesco-uis-cr1-modelled"]

    headline = survey_rows[0]  # most recent survey year, per authority ranking
    same_year_modelled = next(r for r in modelled_rows if r[0] == headline[0])
    spread_pct = abs(headline[1] - same_year_modelled[1]) / same_year_modelled[1] * 100

    # The disclosure table compares like with like: the 4 real survey years
    # against the modelled series in those same years, not all 45 modelled
    # years (which belong on the chart, not in a "here's what disagrees"
    # table) — the modelled series is denser by construction, not by having
    # more genuine sources.
    survey_periods = {r[0] for r in survey_rows}
    comparable_modelled = [r for r in modelled_rows if r[0] in survey_periods]

    national = {
        "headline": {
            "value": headline[1], "period": headline[0], "quality_flag": headline[2],
            "producer": headline[3], "dataset_name": headline[4],
        },
        "spread_pct": round(spread_pct, 1),
        "spread_vs_period": same_year_modelled[0],
        "all_sources": [
            {
                "value": r[1], "period": r[0], "quality_flag": r[2],
                "producer": r[3], "dataset_name": r[4], "url": r[6],
            }
            for r in sorted(survey_rows + comparable_modelled, key=lambda r: r[0], reverse=True)
        ],
    }

    survey_source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'unesco-uis-cr1-survey'
    """).fetchone()
    modelled_source = con.execute("""
        select producer, dataset_name, url, retrieved_at::varchar
        from sources where source_id = 'unesco-uis-cr1-modelled'
    """).fetchone()

    lead_text, lead_template_id = sentence_education(headline[0], headline[1], headline[2])

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_education_json.py — ne pas éditer directement."
        ),
        "source": {
            "producer": modelled_source[0], "dataset_name": modelled_source[1],
            "url": modelled_source[2], "retrieved_at": modelled_source[3],
        },
        "source_survey": {
            "producer": survey_source[0], "dataset_name": survey_source[1],
            "url": survey_source[2], "retrieved_at": survey_source[3],
        },
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "national": national,
        "series": sorted(
            [{"period": r[0], "value": r[1]} for r in modelled_rows],
            key=lambda d: d["period"],
        ),
        "survey_points": sorted(
            [{"period": r[0], "value": r[1]} for r in survey_rows],
            key=lambda d: d["period"],
        ),
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        f"Wrote {len(modelled_rows)} modelled years + "
        f"{len(survey_rows)} survey points to {OUT_PATH}"
    )


if __name__ == "__main__":
    main()
