"""Add the national IHPC (consumer price index) global-indicator observations from
ICASEES's own published dashboard file. See docs/verification-debt.md for the base-
year reconciliation note this source carries.

Source: raw/icasees-ihpc/2026-09-11/ihpc_mensuel_national_2015_2026.xlsx, sheet
"Données", row IND1 ("INDICE GLOBAL"). Monthly, 2015M1-2026M4.

The file's own Notes_Methodologiques sheet documents a January 2020 base change and
a subsequent reconciliation of 2015-2019 values onto the post-2020 base, using an
official coefficient (4.12919) quoted from ICASEES's own bulletins and verified by
the note itself (continuity check at the Dec-2019/Jan-2020 boundary). Values before
2020-01 are marked quality_flag=estime here (reconciled/recalculated, not as
originally published — the original base-1981 values are preserved in the source
file's own "Archive_Base1981_Brute" sheet). Values from 2020-01 are as-published,
no flag.

Usage: uv run python -m pipeline.add_ihpc_observations
"""

import csv

import pandas as pd

SOURCE_ID = "icasees-ihpc-dashboard"
RETRIEVED_AT = "2026-09-11"
COUNTRY_ID = "cf-pays-centrafrique-v1"
RECONCILED_BEFORE = "2020-01"  # values before this are the recalculated ones


def month_col_to_period(col: str) -> str:
    # "2015M1" -> "2015-01", "2026M4" -> "2026-04"
    year, month = col.split("M")
    return f"{year}-{int(month):02d}"


def main():
    df = pd.read_excel(
        "raw/icasees-ihpc/2026-09-11/ihpc_mensuel_national_2015_2026.xlsx",
        sheet_name="Données", header=0,
    )
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
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
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

    with open("data/observations.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["entity_id", "indicator_id", "period", "value", "unit",
                        "source_id", "retrieved_at", "quality_flag", "notes"],
            lineterminator="\n",
        )
        writer.writerows(rows)

    print(f"Added {len(rows)} prix_ihpc_global observations "
          f"({sum(1 for r in rows if r['quality_flag'])} reconciled, "
          f"{sum(1 for r in rows if not r['quality_flag'])} as-published).")


if __name__ == "__main__":
    main()
