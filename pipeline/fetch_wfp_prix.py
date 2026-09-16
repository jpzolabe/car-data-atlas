"""Fetch, snapshot, and transform WFP's Central African Republic food price
series from HDX -- the first source at market-level geography (a point, not
an administrative area), per CLAUDE.md's own named example (prix_manioc_kg).

Widened 2026-09-12 (Phase 4, step 1: "wire the crosswalk into the
observation pipeline") from Bangui-only to every market with real, recent
data: 34 of the file's 41 markets have monthly `priceflag=actual` data for
all or most of the 5 staple commodities through 2025-2026, spread across
16 of the 20 préfectures -- checked live before widening, not assumed from
Bangui's own coverage. Each market becomes its own `marche`-level entity,
parented to the préfecture entity its `admin1` column names (verified to
match `data/entities.csv`'s préfecture names exactly, no fuzzy matching
needed). This is what lets /prix/ show a real "by préfecture" breakdown --
see docs/decisions.md.

Bangui keeps its full 2004-present history (already fetched, already the
page's detailed time series). Every other market is capped to 2025-01
onward: fetching each market's full history too would add roughly 14,000
rows to observations.csv for a breakdown table that only needs "what's the
price now, and a short recent trend," not two decades per market -- a
deliberate scope choice, not a data quality shortcut. Each market entity's
`valid_from` still uses that market's true first-observed date in the full
file, not the truncated fetch window, so the entity record doesn't imply
the market is newer than it is.

Idempotent by design: the source republishes its full historical series
each time, not incremental deltas, so re-running this fully replaces every
row from this source_id in observations.csv, and skips creating an entity
that already exists -- running it twice in a row produces the same files,
not duplicates.

Usage: uv run python -m pipeline.fetch_wfp_prix
"""

import csv
import datetime
import unicodedata
from pathlib import Path

import httpx

SOURCE_ID = "wfp-food-prices-hdx"
COUNTRY_ID = "cf-pays-centrafrique-v1"
FILE_URL = (
    "https://data.humdata.org/dataset/e9f27b34-f511-498c-a7f8-fe8d2321f7ba/"
    "resource/cb558a54-357a-4bcd-9edd-30caf65b1bd7/download/wfp_food_prices_caf.csv"
)

# WFP commodity name (as it appears in the "commodity" column, Retail rows
# only) -> (indicator_id, unit). "Cassava (cossette)" (dried cassava chips)
# was picked over the plain "Cassava" row, which stops in 2021.
COMMODITIES = {
    "Cassava (cossette)": ("prix_manioc_kg", "FCFA/kg"),
    "Rice": ("prix_riz_kg", "FCFA/kg"),
    "Maize": ("prix_mais_kg", "FCFA/kg"),
    "Meat (beef)": ("prix_boeuf_kg", "FCFA/kg"),
    "Oil (palm)": ("prix_huile_palme_l", "FCFA/L"),
}

BANGUI_MARKET = "Bangui"
OTHER_MARKETS_CUTOFF = "2025-01"  # YYYY-MM; Bangui alone keeps full history


def slugify(name: str) -> str:
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.lower().replace("'", "").replace(" ", "-")


def market_entity_id(market: str) -> str:
    return f"cf-m-{slugify(market)}-v1"


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


def load_prefecture_entity_ids() -> dict[str, str]:
    with open("data/entities.csv", encoding="utf-8") as f:
        return {
            row["name_fr"]: row["entity_id"]
            for row in csv.DictReader(f)
            if row["level"] == "prefecture"
        }


def scan_markets(csv_path: Path) -> dict[str, dict]:
    """One pass over the full file: for every market, its préfecture
    (admin1), coordinates, WFP market_id, and true first-observed date
    (independent of any date cutoff applied later when extracting rows)."""
    markets: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            m = row["market"]
            info = markets.setdefault(m, {
                "prefecture": row["admin1"], "lat": row["latitude"],
                "lon": row["longitude"], "market_id": row["market_id"],
                "first_date": row["date"],
            })
            if row["date"] < info["first_date"]:
                info["first_date"] = row["date"]
    return markets


def ensure_market_entities(markets: dict[str, dict], prefecture_ids: dict[str, str]) -> int:
    with open("data/entities.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_ids = {row["entity_id"] for row in reader}

    new_rows = []
    for market, info in markets.items():
        if market == BANGUI_MARKET:
            continue  # cf-m-bangui-v1 already exists, added when this theme started
        entity_id = market_entity_id(market)
        if entity_id in existing_ids:
            continue
        parent_id = prefecture_ids.get(info["prefecture"])
        if parent_id is None:
            print(
                f"  WARNING: no préfecture entity for '{info['prefecture']}' "
                f"({market}) - skipped"
            )
            continue
        new_rows.append({
            "entity_id": entity_id, "name_fr": f"Marché de {market}",
            "slug": f"{slugify(market)}-marche", "level": "marche",
            "parent_id": parent_id, "valid_from": info["first_date"],
            "valid_to": "", "superseded_by": "",
            "notes": (
                f"Coordonnées {info['lat']}° N / {info['lon']}° E ; "
                f"market_id={info['market_id']} dans le fichier du PAM (WFP) "
                f"« Central African Republic - Markets » sur HDX. valid_from "
                f"est la date de la première observation de prix disponible "
                f"dans la source pour ce marché, pas une date de création. "
                f"Voir cf-m-bangui-v1 pour le détail de la méthodologie."
            ),
        })

    if new_rows:
        with open("data/entities.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writerows(new_rows)
    return len(new_rows)


def extract_rows(csv_path: Path, retrieved_at: str) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["pricetype"] != "Retail" or row["priceflag"] != "actual":
                continue
            if row["commodity"] not in COMMODITIES:
                continue
            market = row["market"]
            period = row["date"][:7]  # "2026-07-15" -> "2026-07"
            if market != BANGUI_MARKET and period < OTHER_MARKETS_CUTOFF:
                continue
            indicator_id, unit = COMMODITIES[row["commodity"]]
            rows.append({
                "entity_id": market_entity_id(market), "indicator_id": indicator_id,
                "period": period, "value": round(float(row["price"]), 2),
                "unit": unit, "source_id": SOURCE_ID,
                "retrieved_at": retrieved_at, "quality_flag": "",
                "notes": (
                    f"Prix de détail relevé au marché de {market}, en francs "
                    f"CFA ({row['currency']})."
                ),
            })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    csv_path, today = fetch_snapshot()
    markets = scan_markets(csv_path)
    prefecture_ids = load_prefecture_entity_ids()
    added = ensure_market_entities(markets, prefecture_ids)
    print(f"Fetched snapshot to {csv_path}")
    print(f"Added {added} new market entities ({len(markets)} markets in file total)")

    rows = extract_rows(csv_path, today)
    replace_in_observations(rows)

    by_indicator: dict[str, int] = {}
    by_market: set[str] = set()
    for row in rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
        by_market.add(row["entity_id"])
    print(f"Replaced {len(by_indicator)} indicators across {len(by_market)} markets, "
          f"{len(rows)} observations total:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
