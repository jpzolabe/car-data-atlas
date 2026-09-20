"""Fetch additional infrastructure indicators for CAR from the World Bank
API. Same idempotent full-replace pattern as fetch_electricity_access.py,
generalized to loop over several indicator codes in one script rather than
one script per indicator (each is a separate HTTP call -- unlike the UIS
API used for education, the World Bank API doesn't accept a comma-separated
indicator list in one request).

Part of a deliberate pass to widen infrastructures beyond its single
indicator (acces_electricite) -- AGENTS.md itself calls this "the weakest
theme." All 4 codes below were confirmed to return real, non-empty, recent
(up to 2024) CAF data before being added -- genuinely fresher than most of
education's indicators.

Usage: uv run python -m pipeline.fetch_infrastructures
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"

# World Bank code -> (indicator_id, source_id, notes)
INDICATORS = {
    "IT.NET.USER.ZS": (
        "taux_utilisation_internet", "world-bank-internet-users",
        "Estimation ITU (Union internationale des télécommunications), "
        "compilée par la Banque mondiale.",
    ),
    "IT.CEL.SETS.P2": (
        "abonnements_mobiles", "world-bank-mobile-subscriptions",
        "Estimation ITU, compilée par la Banque mondiale. Peut dépasser "
        "100 (abonnements multiples par personne).",
    ),
    "SH.H2O.BASW.ZS": (
        "acces_eau_potable_base", "world-bank-water-access",
        "Estimation WHO/UNICEF Joint Monitoring Programme (JMP), compilée par la Banque mondiale.",
    ),
    "SH.STA.BASS.ZS": (
        "acces_assainissement_base", "world-bank-sanitation-access",
        "Estimation WHO/UNICEF Joint Monitoring Programme (JMP), compilée par la Banque mondiale.",
    ),
}


def fetch_indicator(code: str, retrieved_at: str) -> list[dict]:
    indicator_id, source_id, notes = INDICATORS[code]
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
            "period": r["date"], "value": r["value"], "unit": "%",
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
    if not new_rows:
        raise SystemExit('No rows returned by the World Bank API - aborting rather '
                          'than deleting existing rows with nothing to replace them.')

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    # Filtered by source_id, not indicator_id - see docs/decisions.md for
    # the original version of this bug, found in fetch_economie.py.
    replaced_sources = {v[1] for v in INDICATORS.values()}
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["source_id"] in replaced_sources)
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
        f"Added {len(new_rows)} infrastructure observations across "
        f"{len(by_indicator)} indicators:"
    )
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
