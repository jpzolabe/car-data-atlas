"""Fetch education indicators for CAR from the UNESCO Institute for Statistics
(UIS) Data API. Idempotent full-replace, same pattern as
fetch_electricity_access.py.

Started as a single indicator (primary completion) and widened deliberately:
CLAUDE.md's own indicator-ID example (`taux_achevement_primaire`) was
illustrative, not a scope limit, and the same free API has real CAF data
across completion, enrollment, retention and literacy -- confirmed by
querying each candidate code against geoUnit=CAF before adding it here, not
assumed from the indicator catalogue's global metadata (which lists every
country combined and would overstate what actually exists for CAR).

Three families, three source_ids (see data/sources.csv):
- unesco-uis-completion-{survey,modelled}: CR.1/2/3 (survey, sparse) and
  CR.MOD.1/2/3 (UIS's own annual model) -- a real disagreement, used to
  exercise the multi-source disclosure mechanism (docs/plan.md Sec2.5).
- unesco-uis-education-administrative: enrollment ratios, repetition,
  survival, out-of-school -- single series each, no second source to
  disagree with yet.
- unesco-uis-literacy: youth/adult literacy.

The UIS API's own base URL and REST shape were not documented anywhere
findable this session (the old bulk-download endpoint at
download.uis.unesco.org/bdds/ 404s; the "unesco_reader" Python package's docs
don't spell out the URL either) -- confirmed instead by requesting
api.uis.unesco.org/api/public/data/indicators with no params and reading its
own 400 error body, which names the required query parameters. The API used
to accept a comma-separated list of indicator codes in one call - as of
2026-09-16 that now returns zero records with a "could not be found" hint
for any 2+-code request, confirmed by testing 1 through 21 codes directly
(1 works, 2 already fails) - an external API change, not something this
project's own request changed. Fetches one code per request now.

Usage: uv run python -m pipeline.fetch_education
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
GEO_UNIT = "CAF"
BASE_URL = "https://api.uis.unesco.org/api/public/data/indicators"

SURVEY_SOURCE = "unesco-uis-completion-survey"
MODELLED_SOURCE = "unesco-uis-completion-modelled"
ADMIN_SOURCE = "unesco-uis-education-administrative"
LITERACY_SOURCE = "unesco-uis-literacy"
OOS_MODELLED_SOURCE = "unesco-uis-outofschool-modelled"

# UIS code -> (indicator_id, source_id, quality_flag). Every code below was
# confirmed to return real, non-empty records for geoUnit=CAF before being
# added -- see docs/decisions.md for the discovery method. Every *.MOD.*
# family was explicitly checked for a modelled counterpart before a plain
# indicator was accepted as "this is genuinely all UIS has" -- found for
# completion and out-of-school (extends coverage to 2025), not found for
# enrollment ratios, repetition or survival (those really do stop at their
# last administrative year, 2011-2017).
INDICATORS = {
    "CR.1": ("taux_achevement_primaire", SURVEY_SOURCE, "enquete"),
    "CR.MOD.1": ("taux_achevement_primaire", MODELLED_SOURCE, "estime"),
    "CR.2": ("taux_achevement_secondaire_1er_cycle", SURVEY_SOURCE, "enquete"),
    "CR.MOD.2": ("taux_achevement_secondaire_1er_cycle", MODELLED_SOURCE, "estime"),
    "CR.3": ("taux_achevement_secondaire_2nd_cycle", SURVEY_SOURCE, "enquete"),
    "CR.MOD.3": ("taux_achevement_secondaire_2nd_cycle", MODELLED_SOURCE, "estime"),
    "GER.1": ("taux_scolarisation_brut_primaire", ADMIN_SOURCE, "administratif"),
    "NERT.1.CP": ("taux_scolarisation_net_primaire", ADMIN_SOURCE, "administratif"),
    "GER.2": ("taux_scolarisation_brut_secondaire_1er_cycle", ADMIN_SOURCE, "administratif"),
    "GER.3": ("taux_scolarisation_brut_secondaire_2nd_cycle", ADMIN_SOURCE, "administratif"),
    "GER.5T8": ("taux_scolarisation_brut_superieur", ADMIN_SOURCE, "administratif"),
    "REPR.1.CP": ("taux_redoublement_primaire", ADMIN_SOURCE, "administratif"),
    "SR.1.GLAST.CP": ("taux_survie_primaire", ADMIN_SOURCE, "administratif"),
    "ROFST.1.CP": ("taux_non_scolarisation_primaire", ADMIN_SOURCE, "administratif"),
    "ROFST.MOD.1": ("taux_non_scolarisation_primaire", OOS_MODELLED_SOURCE, "estime"),
    "ROFST.2.CP": ("taux_non_scolarisation_secondaire_1er_cycle", ADMIN_SOURCE, "administratif"),
    "ROFST.MOD.2": ("taux_non_scolarisation_secondaire_1er_cycle", OOS_MODELLED_SOURCE, "estime"),
    "ROFST.3.CP": ("taux_non_scolarisation_secondaire_2nd_cycle", ADMIN_SOURCE, "administratif"),
    "ROFST.MOD.3": ("taux_non_scolarisation_secondaire_2nd_cycle", OOS_MODELLED_SOURCE, "estime"),
    "LR.AG15T24": ("taux_alphabetisation_jeunes", LITERACY_SOURCE, "enquete"),
    "LR.AG15T99": ("taux_alphabetisation_adultes", LITERACY_SOURCE, "enquete"),
}

NOTES_BY_SOURCE = {
    SURVEY_SOURCE: (
        "Donnée ponctuelle issue d'une enquête ou d'un recensement "
        "national, agrégée par l'UIS."
    ),
    MODELLED_SOURCE: (
        "Estimation modélisée/interpolée par l'UIS pour combler les "
        "années sans enquête."
    ),
    OOS_MODELLED_SOURCE: (
        "Estimation modélisée/interpolée par l'UIS, distincte de la donnée "
        "administrative officielle du même indicateur."
    ),
    ADMIN_SOURCE: (
        "Donnée administrative nationale (annuaire scolaire) compilée "
        "par l'UIS -- méthodologie exacte par indicateur non confirmée "
        "point par point, voir docs/verification-debt.md."
    ),
    LITERACY_SOURCE: (
        "Donnée de recensement ou d'enquête compilée par l'UIS."
    ),
}


def fetch_all(retrieved_at: str) -> list[dict]:
    rows = []
    for code in INDICATORS:
        resp = httpx.get(
            BASE_URL,
            params={"geoUnit": GEO_UNIT, "indicator": code},
            timeout=30.0,
            headers={"User-Agent": "rca-donnees-project/0.1"},
        )
        resp.raise_for_status()
        for r in resp.json()["records"]:
            if r["value"] is None or r["indicatorId"] not in INDICATORS:
                continue
            indicator_id, source_id, quality_flag = INDICATORS[r["indicatorId"]]
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": str(r["year"]), "value": r["value"], "unit": "%",
                "source_id": source_id, "retrieved_at": retrieved_at,
                "quality_flag": quality_flag, "notes": NOTES_BY_SOURCE[source_id],
            })
    return rows


def main():
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = fetch_all(today)
    if not new_rows:
        raise SystemExit("No education rows returned by the UIS API - "
                          "aborting rather than deleting existing rows with nothing to replace them.")

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    # Filtered by source_id, not indicator_id - several indicator_ids here
    # (e.g. taux_achevement_primaire) are deliberately shared between a
    # survey source and a modelled source for the disclosure mechanism; an
    # indicator_id-only filter would risk one source's re-fetch deleting
    # the other's rows for the same indicator. See docs/decisions.md for
    # the original version of this bug, found in fetch_economie.py.
    education_sources = {v[1] for v in INDICATORS.values()}
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["source_id"] in education_sources)
    ]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    by_indicator: dict[str, int] = {}
    for row in new_rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Added {len(new_rows)} education observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
