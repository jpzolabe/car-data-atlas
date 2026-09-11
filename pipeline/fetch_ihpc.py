"""Fetch, snapshot, and transform the national IHPC series — the reusable,
idempotent version of what add_ihpc_observations.py did as a one-off. This is
what .github/workflows/fetch-ihpc.yml runs on a schedule.

Idempotent by design: ICASEES republishes the *entire* historical series each
time (not incremental deltas), so re-running this fully replaces
prix_ihpc_global in observations.csv rather than appending — running it twice
in a row produces the same file, not duplicates.

See docs/verification-debt.md for the base-year reconciliation this source
carries, and pipeline/sentences.py for how these values reach the site.

Usage: uv run python -m pipeline.fetch_ihpc
"""

import csv
import datetime
from pathlib import Path

import httpx
import pandas as pd

SOURCE_ID = "icasees-ihpc-dashboard"
COUNTRY_ID = "cf-pays-centrafrique-v1"
RECONCILED_BEFORE = "2020-01"  # values before this are the source's own recalculated ones
FILE_URL = "https://www.icasees.org/edocman/ipc_ihpc/JD_ODP_IPC_Mensuel_National_RCA_ODP1.0.xlsx"


def month_col_to_period(col: str) -> str:
    # "2015M1" -> "2015-01", "2026M4" -> "2026-04"
    year, month = col.split("M")
    return f"{year}-{int(month):02d}"


def fetch_snapshot() -> Path:
    today = datetime.date.today().isoformat()
    out_dir = Path(f"raw/icasees-ihpc/{today}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ihpc_mensuel_national_2015_2026.xlsx"

    resp = httpx.get(FILE_URL, follow_redirects=True, timeout=30.0,
                      headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path, today


def extract_rows(xlsx_path: Path, retrieved_at: str) -> list[dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Données", header=0)
    global_row = df[df.iloc[:, 0] == "IND1"].iloc[0]
    month_cols = [c for c in df.columns if isinstance(c, str) and "M" in c and c[:2] == "20"]

    rows = []
    for col in month_cols:
        period = month_col_to_period(col)
        value = global_row[col]
        if pd.isna(value):
            continue
        reconciled = period < RECONCILED_BEFORE
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "prix_ihpc_global",
            "period": period, "value": round(float(value), 2), "unit": "indice",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "estime" if reconciled else "",
            "notes": (
                "Valeur reconciliée sur la base 2019 via le coefficient officiel "
                "4,12919 (publié dans les avertissements des bulletins IHPC) — "
                "valeur brute d'origine (base 1981) conservée dans le fichier "
                "source, feuille Archive_Base1981_Brute."
                if reconciled else
                "Valeur telle que publiée (base 2019)."
            ),
        })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["indicator_id"] != "prix_ihpc_global"]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    xlsx_path, today = fetch_snapshot()
    rows = extract_rows(xlsx_path, today)
    replace_in_observations(rows)
    print(f"Fetched snapshot to {xlsx_path}")
    print(f"Replaced prix_ihpc_global with {len(rows)} observations "
          f"({sum(1 for r in rows if r['quality_flag'])} reconciled, "
          f"{sum(1 for r in rows if not r['quality_flag'])} as-published), "
          f"latest period {rows[-1]['period']}.")


if __name__ == "__main__":
    main()
