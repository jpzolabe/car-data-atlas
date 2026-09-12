"""Fetch, snapshot, and transform WFP's Central African Republic food price
series from HDX -- the first source at market-level geography (a point, not
an administrative area), per CLAUDE.md's own named example (prix_manioc_kg).

Idempotent by design: the source republishes its full historical series each
time (2004 to present), not incremental deltas, so re-running this fully
replaces every indicator in COMMODITIES in observations.csv rather than
appending -- running it twice in a row produces the same file, not
duplicates.

Only the Bangui market, Retail pricetype, priceflag == "actual" (no
aggregated/estimated values) is used for now. HDX's file covers 41 markets
and 39 commodities in CAR; Bangui was picked as the one closest to a
"national" figure this dataset offers, and the 5 commodities below are the
only staples with monthly data continuing into 2026 rather than stopping
around 2018-2021 -- checked live, not assumed, before picking them. See
docs/decisions.md.

Usage: uv run python -m pipeline.fetch_wfp_prix
"""

import csv
import datetime
from pathlib import Path

import httpx

SOURCE_ID = "wfp-food-prices-hdx"
MARKET_ID = "cf-m-bangui-v1"
FILE_URL = (
    "https://data.humdata.org/dataset/e9f27b34-f511-498c-a7f8-fe8d2321f7ba/"
    "resource/cb558a54-357a-4bcd-9edd-30caf65b1bd7/download/wfp_food_prices_caf.csv"
)

# WFP commodity name (as it appears in the "commodity" column, Bangui/Retail
# rows only) -> (indicator_id, unit). "Cassava (cossette)" (dried cassava
# chips) was picked over the plain "Cassava" row, which stops in 2021.
COMMODITIES = {
    "Cassava (cossette)": ("prix_manioc_kg", "FCFA/kg"),
    "Rice": ("prix_riz_kg", "FCFA/kg"),
    "Maize": ("prix_mais_kg", "FCFA/kg"),
    "Meat (beef)": ("prix_boeuf_kg", "FCFA/kg"),
    "Oil (palm)": ("prix_huile_palme_l", "FCFA/L"),
}


def fetch_snapshot() -> tuple[Path, str]:
    today = datetime.date.today().isoformat()
    out_dir = Path(f"raw/wfp-food-prices/{today}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "wfp_food_prices_caf.csv"

    resp = httpx.get(
        FILE_URL, follow_redirects=True, timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path, today


def extract_rows(csv_path: Path, retrieved_at: str) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["market"] != "Bangui" or row["pricetype"] != "Retail":
                continue
            if row["commodity"] not in COMMODITIES:
                continue
            if row["priceflag"] != "actual":
                continue
            indicator_id, unit = COMMODITIES[row["commodity"]]
            period = row["date"][:7]  # "2026-07-15" -> "2026-07"
            rows.append({
                "entity_id": MARKET_ID, "indicator_id": indicator_id,
                "period": period, "value": round(float(row["price"]), 2),
                "unit": unit, "source_id": SOURCE_ID,
                "retrieved_at": retrieved_at, "quality_flag": "",
                "notes": (
                    f"Prix de détail relevé au marché de Bangui, en francs CFA "
                    f"({row['currency']})."
                ),
            })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    replaced_indicators = {v[0] for v in COMMODITIES.values()}
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["indicator_id"] not in replaced_indicators]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    csv_path, today = fetch_snapshot()
    rows = extract_rows(csv_path, today)
    replace_in_observations(rows)
    print(f"Fetched snapshot to {csv_path}")
    by_indicator: dict[str, int] = {}
    for row in rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Replaced {len(by_indicator)} indicators, {len(rows)} observations total:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
