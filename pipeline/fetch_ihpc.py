"""Fetch, snapshot, and transform the national IHPC series - the reusable,
idempotent version of what add_ihpc_observations.py did as a one-off. This is
what .github/workflows/fetch-ihpc.yml runs on a schedule.

Idempotent by design: ICASEES republishes the *entire* historical series each
time (not incremental deltas), so re-running this fully replaces every
indicator in INDICATOR_CODES in observations.csv rather than appending -
running it twice in a row produces the same file, not duplicates.

Widened 2026-09-12 from the global index (IND1) alone to include 3 named
COICOP sub-categories and the published "Inflation" row (IND14) -- the same
downloaded file already had these, per prix.astro's own gap-note. IND14 is
published as-is (rule zero: use real data even when a naive recomputation
from IND1 doesn't reconcile with it) -- see docs/verification-debt.md for
that discrepancy, deliberately not resolved by guessing at a methodology.

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

# Row code in the file's "Données" sheet -> (indicator_id, unit). All 4 new
# codes were checked for real, non-empty values before being added (IND11
# "Enseignement" was also checked and skipped -- only 76/136 months
# populated and not one of the 3 categories prix.astro's gap-note named).
INDICATOR_CODES = {
    "IND1": ("prix_ihpc_global", "indice"),
    "IND2": ("prix_ihpc_alimentation", "indice"),
    "IND7": ("prix_ihpc_sante", "indice"),
    "IND8": ("prix_ihpc_transports", "indice"),
    "IND14": ("taux_inflation", "%"),
}


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


def index_notes(reconciled: bool) -> str:
    return (
        "Valeur reconciliée sur la base 2019 via le coefficient officiel "
        "4,12919 (publié dans les avertissements des bulletins IHPC) - "
        "valeur brute d'origine (base 1981) conservée dans le fichier "
        "source, feuille Archive_Base1981_Brute."
        if reconciled else
        "Valeur telle que publiée (base 2019)."
    )


def inflation_notes() -> str:
    # Deliberately not claiming the same base-rebasing coefficient applies
    # here -- that methodology note in the source file is specific to the
    # index rows (IND1-13), not stated for this rate. A naive month-over-
    # month or year-over-year recomputation from IND1 doesn't reproduce this
    # column either -- published as-is, not silently reinterpreted. See
    # docs/verification-debt.md.
    return (
        "Taux publié tel quel par la source dans la même feuille que "
        "l'indice ; une recomputation glissement mensuel ou annuel à partir "
        "de l'indice global (IND1) ne reproduit pas cette colonne, "
        "méthodologie exacte non confirmée -- voir docs/verification-debt.md."
    )


def extract_rows(xlsx_path: Path, retrieved_at: str) -> list[dict]:
    df = pd.read_excel(xlsx_path, sheet_name="Données", header=0)
    month_cols = [c for c in df.columns if isinstance(c, str) and "M" in c and c[:2] == "20"]

    rows = []
    for code, (indicator_id, unit) in INDICATOR_CODES.items():
        code_row = df[df.iloc[:, 0] == code].iloc[0]
        for col in month_cols:
            period = month_col_to_period(col)
            value = code_row[col]
            if pd.isna(value):
                continue
            reconciled = period < RECONCILED_BEFORE
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": period, "value": round(float(value), 2), "unit": unit,
                "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
                "quality_flag": "estime" if reconciled else "",
                "notes": inflation_notes() if code == "IND14" else index_notes(reconciled),
            })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    replaced_indicators = {v[0] for v in INDICATOR_CODES.values()}
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
    xlsx_path, today = fetch_snapshot()
    rows = extract_rows(xlsx_path, today)
    replace_in_observations(rows)
    print(f"Fetched snapshot to {xlsx_path}")
    by_indicator: dict[str, int] = {}
    for row in rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Replaced {len(by_indicator)} indicators, {len(rows)} observations total:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
