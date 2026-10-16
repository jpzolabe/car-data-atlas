"""Fetch UNHCR's forced-displacement statistics for CAR as a country of
origin (not country of asylum) - refugees and asylum-seekers who left the
country, internally displaced persons (PDI/IDPs) who didn't cross a
border, and the annual return flows for each. A real, re-queryable public
API, so this follows the fetch_*.py idempotent-replace pattern.

Country-of-origin only, deliberately: CAR also hosts some refugees from
neighbouring crises (Sudan notably), but the dominant, defining story for
this country is people displaced FROM it, not the smaller inbound flow -
kept to one clear story rather than two half-told ones. Revisit with a
coa=CAF (country of asylum) query later if that changes.

API docs: https://api.unhcr.org/docs/refugee-statistics.html
Usage: uv run python -m pipeline.fetch_unhcr_displacement
"""

import csv
import datetime

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "unhcr-population-api"
BASE_URL = "https://api.unhcr.org/population/v1/population/"
YEAR_FROM = 2012  # earliest year this API returns clean, gap-free data for CAF

# UNHCR API field -> (indicator_id, is_annual_flow). Stock fields (refugees,
# idps, asylum_seekers) are cumulative at year-end; flow fields (the two
# "returned_*") are annual counts, not cumulative - same distinction noted
# in data/sources.csv's access_notes for this source.
FIELDS = {
    "idps": "personnes_deplacees_internes",
    "refugees": "refugies_a_letranger",
    "asylum_seekers": "demandeurs_asile_a_letranger",
    "returned_idps": "personnes_deplacees_rentrees",
    "returned_refugees": "refugies_rentres",
}

NOTES = "Donnée administrative UNHCR, comptage opérationnel par pays d'origine."


def fetch_rows(retrieved_at: str) -> list[dict]:
    resp = httpx.get(
        BASE_URL,
        params={"coo": "CAF", "cf_type": "ISO", "yearFrom": YEAR_FROM,
                "yearTo": datetime.date.today().year, "limit": 30},
        timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    items = resp.json()["items"]

    rows = []
    for item in items:
        for field, indicator_id in FIELDS.items():
            value = item.get(field)
            if value in (None, "-"):
                continue
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": str(item["year"]), "value": int(value), "unit": "personnes",
                "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
                "quality_flag": "administratif", "notes": NOTES,
            })
    return rows


def main():
    today = datetime.date.today().isoformat()
    new_rows = fetch_rows(today)
    if not new_rows:
        raise SystemExit("No UNHCR displacement rows returned - aborting rather than "
                          "deleting existing rows with nothing to replace them.")

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    existing = [r for r in existing if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    by_indicator: dict[str, int] = {}
    for row in new_rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Added {len(new_rows)} UNHCR displacement observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
