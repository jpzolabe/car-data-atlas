"""Add balance-of-payments summary observations for RCA, hand-extracted from
BEAC's per-year "Balance des Paiements type" Excel files (one file per
exercice, downloaded individually - not a single reusable feed, so this
follows add_comptes_nationaux.py's pattern rather than fetch_*.py's).

Four summary rows per year, read directly from each file's "TYPE " sheet
(credit column minus debit column, in million FCFA, converted to FCFA here):

- bop_solde_transactions_courantes: "Solde du compte des transactions courantes"
- bop_solde_biens: "Solde du commerce de biens"
- bop_solde_services: "Solde du commerce de services"
- bop_besoin_financement_global: "Capacité (+)/Besoin (-) de financement du
  solde des transactions courantes et de capital"

Genuinely new to this project - nothing in observations.csv currently
represents the current-account structure, only trade-as-%-of-GDP
(world-bank-trade) and HS2-level export/import composition (oec-baci-trade-2024).

Every file's own title says "provisoire" (provisional) for its exercice,
including years several years old by now - BEAC appears not to revise the
filename/title once a final figure exists, so quality_flag is "provisoire"
for every row here, not just the most recent year.

Data-quality gap, not a licence issue (see docs/verification-debt.md): the
2021 and 2022 files (BDP_RCA_2021_16092025.xlsx, BDP_RCA_2022_16092025.xlsx)
are both corrupted ZIP containers on BEAC's own server - reproduced on a
fresh download (Content-Length matches the downloaded byte count exactly, so
not a truncated transfer), confirmed with `unzip -t` and Python's zipfile.
2020's file had the same corruption but was recoverable with `zip -FF`
(repair) + openpyxl's keep_links=False; 2021 and 2022 were not - repair
produced a zip missing xl/sharedStrings.xml (2021) or with an unrecoverable
deflate stream (2022). Left as a real gap (2 years missing out of 2018-2024)
rather than guessed at or interpolated - see rule zero.

Usage: uv run python -m pipeline.add_beac_balance_paiements
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "beac-balance-paiements-rca"
RETRIEVED_AT = "2026-10-16"

# (period, solde transactions courantes, solde biens, solde services,
# besoin de financement global) - all in million FCFA as published, 2021 and
# 2022 missing (source files corrupted, see module docstring).
ROWS = [
    ("2018", -143196, -235829, -86953, -57677),
    ("2019", -89185, -272036, -56819, -24168),
    ("2020", -92096, -213863, -36416, 71338),
    ("2023", -62409, -160164, -39722, -22676),
    ("2024", -143953, -210032, -38569, -48453),
]

NOTES = {
    "bop_solde_transactions_courantes": (
        "Solde du compte des transactions courantes (crédit moins débit), "
        "Balance des Paiements type de la RCA, feuille TYPE. Négatif = déficit."
    ),
    "bop_solde_biens": (
        "Solde du commerce de biens (crédit moins débit), Balance des "
        "Paiements type de la RCA, feuille TYPE. Négatif = déficit."
    ),
    "bop_solde_services": (
        "Solde du commerce de services (crédit moins débit), Balance des "
        "Paiements type de la RCA, feuille TYPE. Négatif = déficit."
    ),
    "bop_besoin_financement_global": (
        "Capacité (+)/Besoin (-) de financement du solde des transactions "
        "courantes et de capital, Balance des Paiements type de la RCA, "
        "feuille TYPE. Négatif = besoin de financement."
    ),
}


def build_rows() -> list[dict]:
    rows = []
    for period, courant, biens, services, financement in ROWS:
        for indicator_id, value in [
            ("bop_solde_transactions_courantes", courant),
            ("bop_solde_biens", biens),
            ("bop_solde_services", services),
            ("bop_besoin_financement_global", financement),
        ]:
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": period, "value": value * 1_000_000, "unit": "FCFA",
                "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
                "quality_flag": "provisoire", "notes": NOTES[indicator_id],
            })
    return rows


def main():
    new_rows = build_rows()

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

    print(f"Added {len(new_rows)} BEAC balance-of-payments observations "
          f"({len(ROWS)} years x 4 indicators, 2021/2022 missing - source "
          f"files corrupted, see docs/verification-debt.md).")


if __name__ == "__main__":
    main()
