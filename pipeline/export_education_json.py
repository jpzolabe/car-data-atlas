"""Materialize all education-theme indicators as JSON for the Astro site.

Widened from a single indicator (taux_achevement_primaire) to the full set
fetched by pipeline/fetch_education.py -- 14 indicators across 4 categories.
The 3 completion indicators keep the national multi-source disclosure block
(survey vs. modelled, a real disagreement); the other 11 have one source each
so far and get a plain latest-value-plus-series treatment. Same CSV -> DuckDB
-> JSON handoff as every other export script (docs/decisions.md) -- Astro
reads this file directly, never the raw CSVs.

Usage: uv run python -m pipeline.export_education_json
Output: site/src/data/education.json
"""

import json

import duckdb

from pipeline.sentences import sentence_completion, sentence_education_rate

OUT_PATH = "site/src/data/education.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

COMPLETION_INDICATORS = [
    "taux_achevement_primaire",
    "taux_achevement_secondaire_1er_cycle",
    "taux_achevement_secondaire_2nd_cycle",
]
SURVEY_SOURCE = "unesco-uis-completion-survey"
MODELLED_SOURCE = "unesco-uis-completion-modelled"

CATEGORIES = [
    ("achevement", "Achèvement scolaire", COMPLETION_INDICATORS),
    ("scolarisation", "Scolarisation", [
        "taux_scolarisation_net_primaire",
        "taux_scolarisation_brut_primaire",
        "taux_scolarisation_brut_secondaire_1er_cycle",
        "taux_scolarisation_brut_secondaire_2nd_cycle",
        "taux_scolarisation_brut_superieur",
    ]),
    ("retention", "Rétention et abandon", [
        "taux_redoublement_primaire",
        "taux_survie_primaire",
        "taux_non_scolarisation_primaire",
        "taux_non_scolarisation_secondaire_1er_cycle",
    ]),
    ("alphabetisation", "Alphabétisation", [
        "taux_alphabetisation_jeunes",
        "taux_alphabetisation_adultes",
    ]),
]


def build_completion_indicator(con, indicator_id: str) -> dict:
    rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.source_id, s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = ?
        order by o.period desc
    """, [COUNTRY_ID, indicator_id]).fetchall()

    survey_rows = [r for r in rows if r[5] == SURVEY_SOURCE]
    modelled_rows = [r for r in rows if r[5] == MODELLED_SOURCE]

    headline = survey_rows[0]
    same_year_modelled = next(r for r in modelled_rows if r[0] == headline[0])
    spread_pct = abs(headline[1] - same_year_modelled[1]) / same_year_modelled[1] * 100

    survey_periods = {r[0] for r in survey_rows}
    comparable_modelled = [r for r in modelled_rows if r[0] in survey_periods]

    lead_text, lead_template_id = sentence_completion(
        indicator_id, headline[0], headline[1], headline[2]
    )

    return {
        "indicator_id": indicator_id,
        "latest": {"period": headline[0], "value": headline[1], "quality_flag": headline[2]},
        "national": {
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
        },
        "series": sorted(
            [{"period": r[0], "value": r[1]} for r in modelled_rows],
            key=lambda d: d["period"],
        ),
        "survey_points": sorted(
            [{"period": r[0], "value": r[1]} for r in survey_rows],
            key=lambda d: d["period"],
        ),
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "source": {
            "producer": modelled_rows[0][3], "dataset_name": modelled_rows[0][4],
            "url": modelled_rows[0][6], "retrieved_at": modelled_rows[0][7],
        },
        "source_survey": {
            "producer": survey_rows[0][3], "dataset_name": survey_rows[0][4],
            "url": survey_rows[0][6], "retrieved_at": survey_rows[0][7],
        },
    }


def build_simple_indicator(con, indicator_id: str) -> dict:
    rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = ?
        order by o.period desc
    """, [COUNTRY_ID, indicator_id]).fetchall()

    latest = rows[0]
    lead_text, lead_template_id = sentence_education_rate(indicator_id, latest[0], latest[1])

    return {
        "indicator_id": indicator_id,
        "latest": {"period": latest[0], "value": latest[1], "quality_flag": latest[2]},
        "series": sorted(
            [{"period": r[0], "value": r[1]} for r in rows],
            key=lambda d: d["period"],
        ),
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "source": {
            "producer": latest[3], "dataset_name": latest[4],
            "url": latest[5], "retrieved_at": latest[6],
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
            if indicator_id in COMPLETION_INDICATORS:
                block = build_completion_indicator(con, indicator_id)
            else:
                block = build_simple_indicator(con, indicator_id)
            block["name_fr"] = names[indicator_id]
            indicator_blocks.append(block)
        categories.append({"key": key, "label_fr": label, "indicators": indicator_blocks})

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_education_json.py — ne pas éditer directement."
        ),
        "categories": categories,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(c["indicators"]) for c in categories)
    print(f"Wrote {total} indicators across {len(categories)} categories to {OUT_PATH}")


if __name__ == "__main__":
    main()
