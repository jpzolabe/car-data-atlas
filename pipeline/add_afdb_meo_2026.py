"""Add the AfDB's 2026/2027 real GDP growth projections for CAR, per
data/sources.csv's afdb-meo-january-2026 row. No live API - a periodic
PDF report, not a data feed - so this follows add_mfb_budget_2026.py's
pattern rather than fetch_*.py's.

Source: raw/afdb-meo/2026-10-16/meo26_complete_english.pdf, "Africa's
Macroeconomic Performance and Outlook, January 2026" (African Development
Bank Group). Table A2.1 "Real GDP growth (percent)", page 57, row
"Central African Rep." Text-extractable, read with pdfplumber, cross-read
against the page image before transcription.

Deliberately not transcribing the same table's 2024 (1.8%) and 2025
(2.2%, estimated) columns here - those years already have a World Bank
modelled-estimate figure in taux_croissance_pib (a genuine, if smaller,
disagreement between the two institutions that this script doesn't
introduce), and this project's quality_flag vocabulary doesn't yet
distinguish "past-year estimate" from "future-year projection" within
the same flag value - conflating a 2024 estimate and a 2026 projection
under one flag would blur that distinction. 2026 and 2027 are the only
periods with no other source at all.

Usage: uv run python -m pipeline.add_afdb_meo_2026
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "afdb-meo-january-2026"
RETRIEVED_AT = "2026-10-16"

NOTES = (
    "Projection de la Banque africaine de développement (pas une donnée "
    "déjà observée), Tableau A2.1 'Real GDP growth (percent)', page 57 de "
    "Africa's Macroeconomic Performance and Outlook, janvier 2026 (AfDB) ; "
    "diffère de l'estimation modélisée de la Banque mondiale pour les "
    "mêmes années, deux institutions distinctes."
)

ROWS = [
    ("2026", 2.8),
    ("2027", 3.2),
]


def build_rows() -> list[dict]:
    return [
        {
            "entity_id": COUNTRY_ID, "indicator_id": "taux_croissance_pib",
            "period": period, "value": value, "unit": "%",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "projection", "notes": NOTES,
        }
        for period, value in ROWS
    ]


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

    print(f"Added {len(new_rows)} AfDB GDP growth projection observations "
          f"({', '.join(p for p, _ in ROWS)}).")


if __name__ == "__main__":
    main()
