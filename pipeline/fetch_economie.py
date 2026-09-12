"""Fetch economic indicators for CAR from the World Bank API. First fetch
script for the économie theme (previously nonexistent) -- same idempotent
full-replace, one-HTTP-call-per-code pattern as fetch_sante.py.

All 10 codes below were confirmed to return real, non-empty CAF data before
being added -- most through 2024-2025. Two exceptions, flagged rather than
smoothed over: SI.POV.DDAY (poverty) only has 3 points total (household
surveys are infrequent), and GC.REV.XGRT.GD.ZS (government revenue) stops
at 2021.

CLAUDE.md notes ICASEES has its own GDP rebasing (to a 2019 base) underway
-- these World Bank figures haven't been cross-checked against that once
published. See data/sources.csv and docs/verification-debt.md.

Usage: uv run python -m pipeline.fetch_economie
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"

# World Bank code -> (indicator_id, source_id, unit, notes)
INDICATORS = {
    "NY.GDP.MKTP.CD": (
        "pib_total", "world-bank-gdp", "US$",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "NY.GDP.PCAP.CD": (
        "pib_par_habitant", "world-bank-gdp", "US$",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "NY.GDP.MKTP.KD.ZG": (
        "taux_croissance_pib", "world-bank-gdp", "%",
        "Estimation Banque mondiale, comptes nationaux (PIB réel).",
    ),
    "SI.POV.DDAY": (
        "taux_pauvrete", "world-bank-poverty", "%",
        "Estimation basée sur enquête de ménages -- seulement 3 points disponibles pour la RCA.",
    ),
    "SL.UEM.TOTL.ZS": (
        "taux_chomage", "world-bank-unemployment", "%",
        "Estimation modélisée de l'Organisation internationale du travail (OIT).",
    ),
    "NE.EXP.GNFS.ZS": (
        "exportations_pib", "world-bank-trade", "%",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "NE.EXP.GNFS.CD": (
        "exportations_montant", "world-bank-trade", "US$",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "NE.IMP.GNFS.ZS": (
        "importations_pib", "world-bank-trade", "%",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "NE.IMP.GNFS.CD": (
        "importations_montant", "world-bank-trade", "US$",
        "Estimation Banque mondiale, comptes nationaux.",
    ),
    "DT.DOD.DECT.GN.ZS": (
        "dette_exterieure_rnb", "world-bank-external-debt", "%",
        "Estimation Banque mondiale, International Debt Statistics.",
    ),
    "DT.DOD.DECT.CD": (
        "dette_exterieure_montant", "world-bank-external-debt", "US$",
        "Estimation Banque mondiale, International Debt Statistics.",
    ),
    "BX.KLT.DINV.WD.GD.ZS": (
        "investissements_directs_etrangers", "world-bank-fdi", "%",
        "Estimation Banque mondiale, IMF Balance of Payments Statistics.",
    ),
    "GC.REV.XGRT.GD.ZS": (
        "recettes_publiques_pib", "world-bank-government-revenue", "%",
        "Estimation Banque mondiale, IMF Government Finance Statistics -- dernier point 2021.",
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
    print(f"Added {len(new_rows)} economic observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
