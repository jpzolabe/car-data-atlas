"""Fetch health indicators for CAR from the World Bank API. First fetch
script for the santé theme (previously nonexistent) -- same idempotent
full-replace, one-HTTP-call-per-code pattern as fetch_infrastructures.py and
fetch_population_indicators.py.

All 10 codes below were confirmed to return real, non-empty CAF data before
being added -- most through 2023-2024, genuinely current. One real
exception, not smoothed over: SH.MED.BEDS.ZS (hospital beds) only has 6
points, the most recent from 2011 -- flagged in data/sources.csv and on the
page rather than hidden.

Usage: uv run python -m pipeline.fetch_sante
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"

# World Bank code -> (indicator_id, source_id, unit, notes)
INDICATORS = {
    "SP.DYN.LE00.IN": (
        "esperance_vie", "world-bank-life-expectancy", "ans",
        "Estimation Banque mondiale / UN Population Division.",
    ),
    "SH.DYN.MORT": (
        "taux_mortalite_moins_5ans", "world-bank-child-mortality",
        "pour 1 000 naissances vivantes",
        "Estimation UN IGME, compilée par la Banque mondiale.",
    ),
    "SP.DYN.IMRT.IN": (
        "taux_mortalite_infantile", "world-bank-child-mortality",
        "pour 1 000 naissances vivantes",
        "Estimation UN IGME, compilée par la Banque mondiale.",
    ),
    "SH.STA.MMRT": (
        "taux_mortalite_maternelle", "world-bank-maternal-mortality",
        "pour 100 000 naissances vivantes",
        "Estimation du groupe interagences OMS/UNICEF/UNFPA/Banque mondiale/UNPD.",
    ),
    "SH.IMM.MEAS": (
        "taux_vaccination_rougeole", "world-bank-immunization", "%",
        "Estimation conjointe OMS/UNICEF de la couverture vaccinale.",
    ),
    "SH.IMM.IDPT": (
        "taux_vaccination_dtc", "world-bank-immunization", "%",
        "Estimation conjointe OMS/UNICEF de la couverture vaccinale.",
    ),
    "SH.MED.PHYS.ZS": (
        "densite_medecins", "world-bank-health-workforce",
        "pour 1 000 habitants",
        "Estimation OMS Global Health Workforce Statistics, compilée par la Banque mondiale.",
    ),
    "SH.MED.BEDS.ZS": (
        "densite_lits_hopital", "world-bank-health-workforce",
        "pour 1 000 habitants",
        "Estimation OMS Global Health Workforce Statistics -- réellement ancienne "
        "(dernier point 2011), voir data/sources.csv.",
    ),
    "SH.XPD.CHEX.GD.ZS": (
        "depenses_sante_pib", "world-bank-health-expenditure", "% du PIB",
        "Estimation OMS Global Health Expenditure Database, compilée par la Banque mondiale.",
    ),
    "SH.HIV.INCD.ZS": (
        "incidence_vih", "world-bank-hiv-incidence",
        "pour 1 000 personnes non infectées 15-49 ans",
        "Estimation ONUSIDA, compilée par la Banque mondiale.",
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
    print(f"Added {len(new_rows)} health observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
