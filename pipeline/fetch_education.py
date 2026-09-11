"""Fetch primary-education completion rate for CAR from the UNESCO Institute
for Statistics (UIS) Data API. Idempotent full-replace, same pattern as
fetch_electricity_access.py.

Two indicators, on purpose, from the same API: CR.1 (survey-based, "both
sexes") and CR.MOD.1 (UIS's own modelled/interpolated series). This is a real
disagreement, not a manufactured one for the multi-source disclosure mechanism
(docs/plan.md Sec2.5) -- CR.1 only has 4 real observation years for CAF (2000,
2006, 2010, 2019) while CR.MOD.1 fills in every year 1981-2025, and the two
diverge by several points in the one year they overlap (2019: 27.0 vs 29.2).

The UIS API's own base URL and REST shape were not documented anywhere
findable this session (the old bulk-download endpoint at
download.uis.unesco.org/bdds/ 404s; the "unesco_reader" Python package's docs
don't spell out the URL either) -- confirmed instead by requesting
api.uis.unesco.org/api/public/data/indicators with no params and reading its
own 400 error body, which names the required query parameters.

Usage: uv run python -m pipeline.fetch_education
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
GEO_UNIT = "CAF"
BASE_URL = "https://api.uis.unesco.org/api/public/data/indicators"

INDICATORS = {
    "CR.1": {
        "source_id": "unesco-uis-cr1-survey",
        "quality_flag": "enquete",
        "notes": (
            "Donnée ponctuelle issue d'une enquête ou d'un recensement "
            "national, agrégée par l'UIS."
        ),
    },
    "CR.MOD.1": {
        "source_id": "unesco-uis-cr1-modelled",
        "quality_flag": "estime",
        "notes": "Estimation modélisée/interpolée par l'UIS pour combler les années sans enquête.",
    },
}


def fetch_rows(indicator: str, retrieved_at: str) -> list[dict]:
    resp = httpx.get(
        BASE_URL,
        params={"geoUnit": GEO_UNIT, "indicator": indicator},
        timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    meta = INDICATORS[indicator]
    rows = []
    for r in resp.json()["records"]:
        if r["value"] is None:
            continue
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "taux_achevement_primaire",
            "period": str(r["year"]), "value": r["value"], "unit": "%",
            "source_id": meta["source_id"], "retrieved_at": retrieved_at,
            "quality_flag": meta["quality_flag"], "notes": meta["notes"],
        })
    return rows


def main():
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = []
    for indicator in INDICATORS:
        new_rows.extend(fetch_rows(indicator, today))

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    source_ids = {meta["source_id"] for meta in INDICATORS.values()}
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["indicator_id"] == "taux_achevement_primaire"
                and r["source_id"] in source_ids)
    ]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} taux_achevement_primaire observations "
          f"({sum(1 for r in new_rows if r['source_id'] == 'unesco-uis-cr1-survey')} survey, "
          f"{sum(1 for r in new_rows if r['source_id'] == 'unesco-uis-cr1-modelled')} modelled).")


if __name__ == "__main__":
    main()
