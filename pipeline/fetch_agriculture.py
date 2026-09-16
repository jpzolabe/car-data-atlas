"""Fetch agriculture indicators for CAR from the World Bank API. Last of the
three brand-new theme scripts this pass (santé, économie, agriculture) --
same idempotent full-replace, one-HTTP-call-per-code pattern.

All 9 codes below were confirmed to return real, non-empty CAF data before
being added -- the richest, most current dataset of the three new themes,
15 points each, mostly through 2022-2025, no genuinely stale indicator
(unlike santé's hospital-bed density or économie's poverty rate).

Usage: uv run python -m pipeline.fetch_agriculture
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"

# World Bank code -> (indicator_id, source_id, unit, notes)
INDICATORS = {
    "NV.AGR.TOTL.ZS": (
        "valeur_ajoutee_agriculture_pib", "world-bank-agriculture-value-added", "%",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "AG.LND.AGRI.ZS": (
        "terres_agricoles", "world-bank-land-use", "%",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.LND.AGRI.K2": (
        "superficie_agricole", "world-bank-land-use", "km²",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.LND.ARBL.ZS": (
        "terres_arables", "world-bank-land-use", "%",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.LND.FRST.ZS": (
        "couverture_forestiere", "world-bank-land-use", "%",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.PRD.FOOD.XD": (
        "indice_production_alimentaire", "world-bank-food-production", "indice",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.YLD.CREL.KG": (
        "rendement_cereales", "world-bank-cereal-yield", "kg/ha",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.PRD.CREL.MT": (
        "production_cereales", "world-bank-cereal-yield", "tonnes",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "AG.CON.FERT.ZS": (
        "consommation_engrais", "world-bank-fertilizer", "kg/ha",
        "Estimation FAO, compilée par la Banque mondiale. Valeur très faible, "
        "cohérente avec un usage d'engrais minimal en RCA.",
    ),
    "SN.ITK.DEFC.ZS": (
        "taux_sous_alimentation", "world-bank-undernourishment", "%",
        "Estimation FAO, compilée par la Banque mondiale.",
    ),
    "SL.AGR.EMPL.ZS": (
        "emploi_agricole", "world-bank-agricultural-employment", "%",
        "Estimation modélisée de l'Organisation internationale du travail (OIT).",
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
    print(f"Added {len(new_rows)} agriculture observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
