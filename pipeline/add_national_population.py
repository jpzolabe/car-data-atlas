"""Add national-level population_totale observations from two genuinely
independent sources, specifically to exercise the multi-source disclosure
mechanism (docs/plan.md §2.5) with a real conflict rather than a
manufactured one:

- ICASEES RGPH-4 provisional census (2025): 6,656,269 - the highest-authority
  source (national census) per AGENTS.md's ranking, but explicitly provisional.
  This value is NOT fetched here - no live endpoint was found for it this
  session (see docs/verification-debt.md) - it's entered as compiled in
  AGENTS.md, with that provenance chain stated plainly rather than presented
  as freshly verified.
- World Bank WDI (SP.POP.TOTL), fetched live via the public REST API: annual
  modelled estimates, lower authority per the ranking, but a real second
  number for the same country and an overlapping year (2025).

Usage: uv run python -m pipeline.add_national_population
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
WB_URL = "https://api.worldbank.org/v2/country/CAF/indicator/SP.POP.TOTL?format=json&per_page=10&mrnev=5"

RGPH4_ROW = {
    "entity_id": COUNTRY_ID, "indicator_id": "population_totale",
    "period": "2025", "value": 6656269, "unit": "habitants",
    "source_id": "icasees-rgph4-provisional", "retrieved_at": "2026-09-05",
    "quality_flag": "provisoire",
    "notes": (
        "3 312 532 hommes / 3 343 737 femmes ; densité 10,7/km². "
        "Marqué données non encore validées par ICASEES. Page primaire "
        "ICASEES non localisée à ce jour."
    ),
}


def fetch_world_bank_rows() -> list[dict]:
    resp = httpx.get(WB_URL, timeout=30.0, headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    _, records = resp.json()
    rows = []
    for r in records:
        if r["value"] is None:
            continue
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "population_totale",
            "period": r["date"], "value": r["value"], "unit": "habitants",
            "source_id": "world-bank-wdi-population", "retrieved_at": "2026-09-12",
            "quality_flag": "estime",
            "notes": "Estimation mi-année, midyear estimate (World Development Indicators).",
        })
    return rows


def main():
    new_rows = [RGPH4_ROW] + fetch_world_bank_rows()

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    # Idempotent: drop any prior rows for this entity+indicator from these two
    # sources before re-adding, so re-running doesn't duplicate.
    source_ids = {"icasees-rgph4-provisional", "world-bank-wdi-population"}
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["indicator_id"] == "population_totale"
                and r["source_id"] in source_ids)
    ]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} national population_totale observations "
          f"(1 RGPH-4 + {len(new_rows) - 1} World Bank years).")


if __name__ == "__main__":
    main()
