"""Materialize the santé theme as JSON for the Astro site. First export
script for this theme (previously nonexistent); same CSV -> DuckDB -> JSON
handoff as export_education_json.py, and the same category + headline
structure (docs/plan.md Sec2.3), since santé has 10 indicators across
natural groups just like éducation does. No multi-source disclosure
otherwise; every other indicator has exactly one source so far, so every
other block is the plain latest-value-plus-series shape.

Categories ordered by logical sequence per the headline-then-breakdown rule
(docs/decisions.md): what resources exist (système de santé) -> what
prevention happens (vaccination) -> what the outcomes are (mortalité et
espérance de vie) -> disease-specific burden (maladies).

Usage: uv run python -m pipeline.export_sante_json
Output: site/src/data/sante.json
"""

import json

import duckdb

from pipeline.sentences import (
    sentence_sante_effectif,
    sentence_sante_etablissements,
    sentence_sante_rate,
)

OUT_PATH = "site/src/data/sante.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

# Real absolute headcounts (2 from WHO GHO, 1 computed) alongside the
# existing density/% indicators; see docs/decisions.md for why these
# needed a second API (World Bank WDI only has densities).
EFFECTIF_INDICATORS = {"nombre_medecins", "nombre_personnel_infirmier", "nombre_lits_hopital"}

CATEGORIES = [
    ("systeme", "Système de santé", [
        "nombre_etablissements_sante",
        "depenses_sante_pib",
        "densite_medecins",
        "nombre_medecins",
        "densite_lits_hopital",
        "nombre_lits_hopital",
        "nombre_personnel_infirmier",
    ]),
    ("vaccination", "Vaccination", [
        "taux_vaccination_rougeole",
        "taux_vaccination_dtc",
    ]),
    ("maternelle_infantile", "Santé maternelle et infantile", [
        "soins_prenatals_4visites",
        "accouchement_assiste",
        "allaitement_exclusif",
        "retard_croissance_enfants",
        "emaciation_enfants",
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
    if indicator_id in EFFECTIF_INDICATORS:
        lead_text, lead_template_id = sentence_sante_effectif(indicator_id, latest[0], latest[1])
    else:
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


def build_etablissements_region_breakdown(con) -> list[dict]:
    """The Master List's own Admin1 column resolves to this project's 7
    régions (see pipeline/fetch_etablissements_sante.py's
    REGION_ADMIN1_ALIASES) - a real, if partial, subnational floor for this
    indicator, Master List only (healthsites.io has no equivalent régional
    field to compare against, so no second-source disclosure at this
    level).
    """
    rows = con.execute("""
        select e.name_fr, o.value
        from observations o
        join entities e on o.entity_id = e.entity_id
        where e.level = 'region' and o.indicator_id = 'nombre_etablissements_sante'
          and o.source_id = 'maina-master-facility-list-2019'
        order by o.value desc
    """).fetchall()
    return [{"region_name": r[0], "value": r[1]} for r in rows]


def build_etablissements_disclosure(con) -> dict:
    """nombre_etablissements_sante: the first health-facility count on the
    site, and a real disagreement between two independent sources: a
    static 2019 government-registry compilation (555) and a live,
    crowd-mapped OpenStreetMap extract (425). Same population.astro-style
    disclosure shape as économie's taux_croissance_pib. See
    docs/decisions.md.
    """
    rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.source_id, s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = 'nombre_etablissements_sante'
        order by o.period desc
    """, [COUNTRY_ID]).fetchall()

    headline = next(r for r in rows if r[5] == "maina-master-facility-list-2019")
    other = next(r for r in rows if r[5] == "hotosm-healthsites-caf")
    spread_pct = abs(headline[1] - other[1]) / other[1] * 100

    lead_text, lead_template_id = sentence_sante_etablissements(
        headline[0], headline[1], "un registre gouvernemental compilé en 2019"
    )

    return {
        "indicator_id": "nombre_etablissements_sante",
        "unit": "établissements",
        "latest": {"period": headline[0], "value": headline[1]},
        "series": [{"period": r[0], "value": r[1]} for r in sorted(rows, key=lambda r: r[0])],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "source": {
            "producer": headline[3], "dataset_name": headline[4],
            "url": headline[6], "retrieved_at": headline[7],
        },
        "national": {
            "headline": {
                "value": headline[1], "period": headline[0], "quality_flag": headline[2],
                "producer": headline[3], "dataset_name": headline[4],
            },
            "spread_pct": round(spread_pct, 1),
            "spread_vs_period": other[0],
            "all_sources": [
                {
                    "value": r[1], "period": r[0], "quality_flag": r[2] or "osm",
                    "producer": r[3], "dataset_name": r[4], "url": r[6],
                }
                for r in rows
            ],
        },
        "region_breakdown": build_etablissements_region_breakdown(con),
    }


def main():
    con = duckdb.connect()
    con.execute("""
        create view observations as select * from read_csv_auto('data/observations.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
        create view entities as select * from read_csv_auto('data/entities.csv');
    """)

    names = dict(con.execute("select indicator_id, name_fr from indicators").fetchall())
    units = dict(con.execute("select indicator_id, unit from indicators").fetchall())
    definitions = dict(con.execute("select indicator_id, definition_fr from indicators").fetchall())

    categories = []
    for key, label, indicator_ids in CATEGORIES:
        indicator_blocks = []
        for indicator_id in indicator_ids:
            if indicator_id == "nombre_etablissements_sante":
                block = build_etablissements_disclosure(con)
            else:
                block = build_indicator(con, indicator_id)
                block["unit"] = units[indicator_id]
            block["name_fr"] = names[indicator_id]
            block["definition_fr"] = definitions[indicator_id]
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
            "pipeline/export_sante_json.py - ne pas éditer directement."
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
