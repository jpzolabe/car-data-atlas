"""Fetch additional population indicators for CAR from the World Bank API.
Same pattern as fetch_infrastructures.py -- one HTTP call per indicator code
(World Bank's API doesn't accept a comma-separated list the way UIS's does).

Part of the same completion pass as prix/infrastructures: population had
exactly one indicator (population_totale). All 3 codes below were confirmed
to return real, non-empty, genuinely current (through 2025) CAF data before
being added.

Usage: uv run python -m pipeline.fetch_population_indicators
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"

# World Bank code -> (indicator_id, source_id, unit, notes)
INDICATORS = {
    "SP.POP.GROW": (
        "taux_croissance_population", "world-bank-population-growth", "%",
        "Estimation Banque mondiale, dérivée des mêmes séries "
        "démographiques que population_totale.",
    ),
    "SP.URB.TOTL.IN.ZS": (
        "taux_urbanisation", "world-bank-urban-population", "%",
        "Estimation Banque mondiale, basée sur les définitions nationales "
        "de zone urbaine et les projections ONU-Habitat/DAES.",
    ),
    "SP.POP.DPND": (
        "taux_dependance_demographique", "world-bank-age-dependency", "%",
        "Population de moins de 15 ans et de 65 ans et plus, rapportée à "
        "la population de 15-64 ans. Peut dépasser 100 (plus de personnes "
        "à charge que d'actifs).",
    ),
}


def fetch_indicator(code: str, retrieved_at: str) -> list[dict]:
    indicator_id, source_id, unit, notes = INDICATORS[code]
    resp = httpx.get(
        BASE_URL.format(code=code), timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    _, records = resp.json()
    rows = []
    for r in records:
        if r["value"] is None:
            continue
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": r["date"], "value": r["value"], "unit": unit,
            "source_id": source_id, "retrieved_at": retrieved_at,
            "quality_flag": "estime", "notes": notes,
        })
    return rows


def main():
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = []
    for code in INDICATORS:
        new_rows.extend(fetch_indicator(code, today))

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    replaced_indicators = {v[0] for v in INDICATORS.values()}
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["indicator_id"] in replaced_indicators)
    ]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    by_indicator: dict[str, int] = {}
    for row in new_rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(
        f"Added {len(new_rows)} population observations across "
        f"{len(by_indicator)} indicators:"
    )
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
