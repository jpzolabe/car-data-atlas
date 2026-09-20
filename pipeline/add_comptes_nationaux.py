"""Add national accounts (comptes nationaux) observations hand-transcribed
from ICASEES's PDF, per Phase 3 source list item 4 (docs/plan.md). No live
API exists for this source -- it is a periodic PDF publication, not a data
feed -- so this follows add_national_population.py's pattern rather than
fetch_*.py's: values are typed in directly from Tableau 1 (page 12) of
raw/icasees-comptes-nationaux/2026-09-12/comptes_nationaux_definitifs_2019_2021.pdf,
extracted and cross-checked with pdfplumber (extract_tables(), not just
extract_text(), to rule out a column-merge misread) before being typed here.

Two new indicators, both genuinely different from what the site already has
(World Bank USD figures): PIB total and PIB per capita in FCFA, straight
from ICASEES's own rebased (base 2019) national accounts. Also adds two
years (2020, 2021) of real growth-rate observations from the same table
under the existing `taux_croissance_pib` indicator_id -- these disagree
substantially with the World Bank's modelled estimate for the same years
(3.41%/3.44% here vs 0.90%/0.98% from World Bank), a genuine conflict
between two national-accounts-based sources, not a manufactured one. See
docs/decisions.md for how the économie page discloses this.

Table 1 itself has an internal inconsistency worth flagging, not silently
resolved: the document's own narrative summary (page 7) states a 2021
growth rate of 1.6%, which does not match Tableau 1's own 3.44% for the
same year. Tableau 1 (the structured data) is used here as the source of
truth over the narrative prose -- see docs/verification-debt.md.

Usage: uv run python -m pipeline.add_comptes_nationaux
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "icasees-comptes-nationaux"
RETRIEVED_AT = "2026-09-12"

# (period, PIB à prix courant en millions FCFA, PIB/habitant en FCFA, taux de
# croissance réel en % -- vide en 2019 car c'est l'année de base, aucune
# évolution n'est calculée contre une année antérieure dans le même repère).
TABLE_1 = [
    ("2019", 1_952_925, 364_333, None),
    ("2020", 2_056_035, 376_225, 3.41),
    ("2021", 2_149_622, 352_912, 3.44),
]

PIB_NOTES = (
    "Comptes nationaux rebasés (base 2019, SCN 2008), Tableau 1, page 12 de "
    "raw/icasees-comptes-nationaux/2026-09-12/"
    "comptes_nationaux_definitifs_2019_2021.pdf."
)
CROISSANCE_NOTES = (
    "Comptes nationaux rebasés (base 2019, SCN 2008), Tableau 1, page 12. "
    "Le résumé narratif du même document (page 7) donne 1,6% pour 2021, en "
    "désaccord avec cette valeur tabulée, non encore résolu."
)


def build_rows() -> list[dict]:
    rows = []
    for period, pib_total, pib_par_habitant, croissance in TABLE_1:
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "pib_total_fcfa",
            "period": period, "value": pib_total * 1_000_000, "unit": "FCFA",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "", "notes": PIB_NOTES,
        })
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "pib_par_habitant_fcfa",
            "period": period, "value": pib_par_habitant, "unit": "FCFA",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "", "notes": PIB_NOTES,
        })
        if croissance is not None:
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": "taux_croissance_pib",
                "period": period, "value": croissance, "unit": "%",
                "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
                "quality_flag": "administratif", "notes": CROISSANCE_NOTES,
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

    print(f"Added {len(new_rows)} national accounts observations "
          f"({len(TABLE_1)} years x up to 3 indicators).")


if __name__ == "__main__":
    main()
