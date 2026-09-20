"""Add the 2026 state budget observations hand-transcribed from the
Ministère des Finances et du Budget's "Note d'Information du Marché des
Titres Publics de la RCA" (January 2026), per data/sources.csv's
mfb-note-information-2026 row. No live API exists for this source - it is
a periodic PDF publication, not a data feed - so this follows
add_comptes_nationaux.py's pattern rather than fetch_*.py's.

The PDF (found via web search - finances.gouv.cf doesn't list it anywhere
but a direct link) is scanned/image-based, not text-extractable by
pdfplumber; values were read directly off the page images and typed here,
not parsed programmatically. Three figures, three tables:

- budget_ressources_totales: Tableau 2, page 22 (budget resources by
  source - 56.1% domestic revenue, 43.9% external resources).
- budget_depenses_totales: Tableau 4, page 23 (state expenditure by
  nature - 59.8% primary expenditure, 6.8% financial charges, 35.9%
  investment expenditure).
- budget_solde_global: Tableau 5, page 24 (budget balances - the
  document's own -1.2% of GDP figure and a separate primary balance of
  -30.24 billion FCFA are both in the notes below, not separate
  indicators here, since this project doesn't yet have a matching GDP
  denominator series in the same FCFA base to recompute the ratio from).

All three are the Loi de Finances 2026's voted forecast (adopted by the
Assemblée nationale 2025-12-10), not the year's actual execution - stated
as such in each observation's own notes.

Usage: uv run python -m pipeline.add_mfb_budget_2026
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "mfb-note-information-2026"
RETRIEVED_AT = "2026-09-13"

ROWS = [
    (
        "budget_ressources_totales", 368_430_000_000,
        "Loi de Finances 2026, adoptée le 10 décembre 2025. Chiffre "
        "prévisionnel voté (368,43 milliards FCFA), pas l'exécution "
        "réelle : 56,1% de recettes intérieures, 43,9% de ressources "
        "extérieures (Tableau 2, page 22).",
    ),
    (
        "budget_depenses_totales", 396_350_000_000,
        "Loi de Finances 2026, adoptée le 10 décembre 2025. Chiffre "
        "prévisionnel voté (396,35 milliards FCFA), pas l'exécution "
        "réelle : 59,8% dépenses primaires, 6,8% charges financières, "
        "35,9% dépenses d'investissement (Tableau 4, page 23).",
    ),
    (
        "budget_solde_global", -27_920_000_000,
        "Loi de Finances 2026, adoptée le 10 décembre 2025. Déficit "
        "prévisionnel voté (-27,92 milliards FCFA, soit -1,2% du PIB "
        "selon le même document) ; solde primaire de -30,24 milliards "
        "FCFA (Tableau 5, page 24).",
    ),
]


def build_rows() -> list[dict]:
    rows = []
    for indicator_id, value, notes in ROWS:
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": "2026", "value": value, "unit": "FCFA",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "administratif", "notes": notes,
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
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} MFB 2026 budget observations.")


if __name__ == "__main__":
    main()
