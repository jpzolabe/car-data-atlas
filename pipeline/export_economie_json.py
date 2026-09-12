"""Materialize the économie theme as JSON for the Astro site. First export
script for this theme -- same category + headline structure as
export_sante_json.py. pib_total/pib_par_habitant and the 3 new absolute-$
indicators added 2026-09-12 (real World Bank counterparts to indicators
already on the page, not derived) use a dedicated monetary sentence
function; the other 8 (all "%") share one generic rate function.

Categories ordered by logical sequence: production (how big is the
economy) -> commerce extérieur (how it trades and finances itself
externally) -> finances publiques (how the state finances itself) ->
niveau de vie (what it means for people) -- ending on the outcome, not
starting there.

Prix and Agriculture are deliberately NOT indicators of this theme, even
though économie.astro shows a brief summary card for each with a link to
their own full page -- that's presentation (economie.astro imports
prix.json/agriculture.json directly for the cards), not data ownership.
Keeps each theme's JSON containing only the indicators that are actually
économie's own. See docs/decisions.md.

Usage: uv run python -m pipeline.export_economie_json
Output: site/src/data/economie.json
"""

import json

import duckdb

from pipeline.sentences import (
    sentence_economie_croissance_admin,
    sentence_economie_montant,
    sentence_economie_rate,
)

OUT_PATH = "site/src/data/economie.json"
COUNTRY_ID = "cf-pays-centrafrique-v1"

MONTANT_INDICATORS = {
    "pib_total", "pib_par_habitant", "pib_total_fcfa", "pib_par_habitant_fcfa",
    "exportations_montant", "importations_montant", "dette_exterieure_montant",
}

# taux_croissance_pib is built separately (build_croissance_disclosure) since
# it now has two disagreeing sources for 2020-2021 -- World Bank's annual
# modelled series (kept as the chart's "series") and ICASEES's own rebased
# comptes nationaux (higher authority per méthode.astro's ranking, shown as
# the headline with a disclosure of both). See docs/decisions.md.
CATEGORIES = [
    ("production", "Production", [
        "pib_total",
        "pib_par_habitant",
        "pib_total_fcfa",
        "pib_par_habitant_fcfa",
    ]),
    ("commerce", "Commerce extérieur", [
        "exportations_pib",
        "exportations_montant",
        "importations_pib",
        "importations_montant",
        "investissements_directs_etrangers",
        "dette_exterieure_rnb",
        "dette_exterieure_montant",
    ]),
    ("finances_publiques", "Finances publiques", [
        "recettes_publiques_pib",
    ]),
    ("niveau_de_vie", "Niveau de vie", [
        "taux_chomage",
        "taux_pauvrete",
    ]),
]


def build_indicator(con, indicator_id: str, source_id: str | None = None) -> dict:
    rows = con.execute("""
        select o.period, o.value, s.producer, s.dataset_name, s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = ?
              and (? is null or o.source_id = ?)
        order by o.period
    """, [COUNTRY_ID, indicator_id, source_id, source_id]).fetchall()

    latest = rows[-1]
    if indicator_id in MONTANT_INDICATORS:
        lead_text, lead_template_id = sentence_economie_montant(indicator_id, latest[0], latest[1])
    else:
        lead_text, lead_template_id = sentence_economie_rate(indicator_id, latest[0], latest[1])

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


def build_croissance_disclosure(con) -> dict:
    """taux_croissance_pib: World Bank's full annual series stays the chart
    ("series"), but the headline and a "N sources" disclosure use ICASEES's
    own rebased comptes nationaux for 2020-2021 where it exists -- higher
    authority per méthode.astro's ranking (donnée administrative nationale >
    estimation modélisée internationale), and a real, substantial
    disagreement (about 3.4% vs about 1%) worth surfacing rather than
    picking one silently.
    """
    wb_block = build_indicator(con, "taux_croissance_pib", source_id="world-bank-gdp")

    admin_rows = con.execute("""
        select o.period, o.value, o.quality_flag, s.producer, s.dataset_name,
               s.url, s.retrieved_at::varchar
        from observations o
        join sources s on o.source_id = s.source_id
        where o.entity_id = ? and o.indicator_id = 'taux_croissance_pib'
              and o.source_id = 'icasees-comptes-nationaux'
        order by o.period desc
    """, [COUNTRY_ID]).fetchall()

    headline_row = admin_rows[0]  # most recent ICASEES year (2021)
    same_year_wb = next(r for r in wb_block["series"] if r["period"] == headline_row[0])
    spread_pct = abs(headline_row[1] - same_year_wb["value"]) / abs(same_year_wb["value"]) * 100

    all_sources = [
        {
            "value": r[1], "period": r[0], "quality_flag": r[2],
            "producer": r[3], "dataset_name": r[4], "url": r[5],
        }
        for r in admin_rows
    ] + [
        {
            "value": v["value"], "period": v["period"], "quality_flag": "estime",
            "producer": wb_block["source"]["producer"],
            "dataset_name": wb_block["source"]["dataset_name"],
            "url": wb_block["source"]["url"],
        }
        for v in wb_block["series"]
        if v["period"] in {r[0] for r in admin_rows}
    ]

    lead_text, lead_template_id = sentence_economie_croissance_admin(
        headline_row[0], headline_row[1]
    )

    return {
        "indicator_id": "taux_croissance_pib",
        "latest": {"period": headline_row[0], "value": headline_row[1]},
        "series": wb_block["series"],
        "lead_sentence": lead_text,
        "lead_sentence_template_id": lead_template_id,
        "source": wb_block["source"],
        "national": {
            "headline": {
                "value": headline_row[1], "period": headline_row[0],
                "quality_flag": headline_row[2],
                "producer": headline_row[3], "dataset_name": headline_row[4],
            },
            "spread_pct": round(spread_pct, 1),
            "spread_vs_period": headline_row[0],
            "all_sources": all_sources,
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
    definitions = dict(con.execute("select indicator_id, definition_fr from indicators").fetchall())

    categories = []
    for key, label, indicator_ids in CATEGORIES:
        indicator_blocks = []
        for indicator_id in indicator_ids:
            block = build_indicator(con, indicator_id)
            block["name_fr"] = names[indicator_id]
            block["definition_fr"] = definitions[indicator_id]
            indicator_blocks.append(block)
        if key == "production":
            croissance_block = build_croissance_disclosure(con)
            croissance_block["name_fr"] = names["taux_croissance_pib"]
            croissance_block["definition_fr"] = definitions["taux_croissance_pib"]
            indicator_blocks.append(croissance_block)
        categories.append({"key": key, "label_fr": label, "indicators": indicator_blocks})

    headline_indicator = next(
        ind
        for cat in categories
        for ind in cat["indicators"]
        if ind["indicator_id"] == "pib_par_habitant"
    )

    data = {
        "generated_note": (
            "Généré depuis data/observations.csv via "
            "pipeline/export_economie_json.py - ne pas éditer directement."
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
