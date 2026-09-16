"""Fetch electricity access (World Bank EG.ELC.ACCS.ZS) for CAR. Idempotent
full-replace, same pattern as fetch_ihpc.py - safe to re-run on a schedule.

This is a real cross-check, not just new breadth: World Bank's 2019 value
(14.3%) exactly matches CLAUDE.md's own domain fact ("MICS 2018-19 gives
14.3% nationally"), and the series extends to 2024 (18.2%) - genuinely
fresher than what the brief assumed was stale.

Usage: uv run python -m pipeline.fetch_electricity_access
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "world-bank-electricity-access"
URL = "https://api.worldbank.org/v2/country/CAF/indicator/EG.ELC.ACCS.ZS?format=json&per_page=20&mrnev=15"


def fetch_rows(retrieved_at: str) -> list[dict]:
    resp = httpx.get(URL, timeout=30.0, headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    _, records = resp.json()
    rows = []
    for r in records:
        if r["value"] is None:
            continue
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "acces_electricite",
            "period": r["date"], "value": r["value"], "unit": "%",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "estime",
            "notes": "Estimation SDG 7.1.1 Electrification Dataset (ESMAP/Banque mondiale).",
        })
    return rows


def main():
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = fetch_rows(today)
    if not new_rows:
        raise SystemExit("No acces_electricite rows returned by the World Bank API - "
                          "aborting rather than writing an empty replace.")

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} acces_electricite observations, "
          f"{new_rows[0]['period']}-{new_rows[-1]['period']}.")


if __name__ == "__main__":
    main()
