"""Fetch ICASEES's 2025 population projection at sous-préfecture level -
Phase 4's real unlock for the site's finest geographic floor
(docs/plan.md's build order calls sous-préfecture the current floor
everywhere; population_totale had only reached préfecture until now).

Found via HDX's cod-ps-caf dataset ("Central African Republic -
Subnational Population Statistics"), which turned out to carry a much
newer resource than AGENTS.md's domain-facts note assumed ("built on the
2003 census projected to 2015... not yet fetched") - the dataset's own
metadata lists projections through 2025, produced directly by ICASEES for
the annual HNRP (Humanitarian Needs and Response Plan) cycle, not a
third-party projection. This file's Admin2_Pcode column is checked live
(not assumed) against every sous-préfecture pcode already in
data/aliases.csv (from the COD-AB v02 build): all 85 match exactly, no
fuzzy name matching needed - the safest possible join.

Two other COD-PS resources in the same dataset (Admin2/Admin3 CSVs dated
2015) were deliberately NOT used: their own descriptions say they don't
match COD-AB's unit counts (73 vs. 72, 177 vs. 175), meaning they're
built on the older 16-préfecture geography this project's crosswalk
already moved past - a real second crosswalk problem, not worth taking on
just to get an older, lower-resolution number than this file already
gives.

Writes population_totale at both sous_prefecture level (straight from the
file) and prefecture level (summed from the file's own sous-préfecture
rows, grouped by Admin1_Pcode) - the first préfecture-level population
figure newer than the existing 2021 estimate.

Usage: uv run python -m pipeline.fetch_icasees_population_projection
"""

import csv
import datetime
from pathlib import Path

import httpx
import openpyxl

INDICATOR_ID = "population_totale"
SOURCE_ID = "icasees-projection-population-2025"
FILE_URL = (
    "https://data.humdata.org/dataset/d3600c4b-d93d-4ed0-b7b1-359a060b916a/"
    "resource/d2ecb660-f273-433b-9020-e67509cf98db/download/"
    "ocha-car-projection-population-2025-icasees.xlsx"
)


def fetch_snapshot() -> tuple[Path, str]:
    today = datetime.date.today().isoformat()
    out_dir = Path(f"raw/icasees-projection-population-2025/{today}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ocha-car-projection-population-2025-icasees.xlsx"

    resp = httpx.get(FILE_URL, follow_redirects=True, timeout=30.0,
                      headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path, today


def load_pcode_entity_ids(level_prefix: str) -> dict[str, str]:
    with open("data/aliases.csv", encoding="utf-8") as f:
        return {
            row["alias"].strip(): row["entity_id"]
            for row in csv.DictReader(f)
            if row["alias_type"] == "pcode" and row["entity_id"].startswith(level_prefix)
        }


def extract_rows(xlsx_path: Path, retrieved_at: str) -> list[dict]:
    sp_by_pcode = load_pcode_entity_ids("cf-sp-")
    pref_by_pcode = load_pcode_entity_ids("cf-p-")

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["Population_HNRP 2026"]
    data_rows = list(ws.iter_rows(values_only=True))[1:]

    rows = []
    pref_totals: dict[str, float] = {}
    for r in data_rows:
        admin1_pcode, admin2_pcode, value = r[1], r[3], r[5]
        sp_entity_id = sp_by_pcode.get(admin2_pcode.strip())
        if sp_entity_id is None:
            raise ValueError(
                f"Admin2_Pcode {admin2_pcode!r} has no matching sous_prefecture entity"
            )
        rows.append({
            "entity_id": sp_entity_id, "indicator_id": INDICATOR_ID,
            "period": "2025", "value": round(value), "unit": "habitants",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "estime",
            "notes": (
                "Projection ICASEES 2025 pour le cycle humanitaire HNRP, "
                "au niveau sous-préfecture - premier chiffre à ce niveau "
                "pour cet indicateur."
            ),
        })
        pref_totals[admin1_pcode.strip()] = pref_totals.get(admin1_pcode.strip(), 0) + value

    for admin1_pcode, total in pref_totals.items():
        pref_entity_id = pref_by_pcode.get(admin1_pcode)
        if pref_entity_id is None:
            raise ValueError(f"Admin1_Pcode {admin1_pcode!r} has no matching prefecture entity")
        rows.append({
            "entity_id": pref_entity_id, "indicator_id": INDICATOR_ID,
            "period": "2025", "value": round(total), "unit": "habitants",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "estime",
            "notes": (
                "Somme des projections ICASEES 2025 par sous-préfecture "
                "(cycle HNRP) pour cette préfecture - plus récent que "
                "l'estimation 2021 déjà utilisée, mais une projection, "
                "pas un recensement."
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
    xlsx_path, today = fetch_snapshot()
    rows = extract_rows(xlsx_path, today)
    replace_in_observations(rows)
    sp_count = sum(1 for r in rows if r["entity_id"].startswith("cf-sp-"))
    pref_count = sum(1 for r in rows if r["entity_id"].startswith("cf-p-"))
    print(f"Wrote {sp_count} sous-préfecture rows and {pref_count} préfecture rows (2025)")


if __name__ == "__main__":
    main()
