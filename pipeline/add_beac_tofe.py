"""Add government budget *execution* observations for RCA (TOFE - Tableau
des Opérations Financières de l'État), hand-extracted from BEAC's
deofe_rca-1.xlsx, per data/sources.csv's beac-tofe-rca row.

This is the execution counterpart to the existing budget_ressources_totales/
budget_depenses_totales/budget_solde_global indicators (mfb-note-
information-2026), which are the *voted* Loi de Finances forecast, not what
was actually collected/spent - genuinely complementary, not a duplicate.
Deliberately not reusing those indicator_ids: voted and executed figures are
different concepts and shouldn't silently share a series.

The file's own columns run 2012-2022, with 2020-2022 explicitly marked
"Estim" (estimated, not final) in the file itself - despite the filename
suggesting a 2023 vintage, there is no 2023+ column. This makes TOFE the
*oldest* économie data on the site, not the newest - stated plainly in each
observation's notes and via quality_flag rather than presented as current.

Three rows extracted from the file's single "deoferca" sheet (in milliards
FCFA, converted to FCFA here):
- Recettes totales -> tofe_recettes_totales_execution
- Dépenses totales -> tofe_depenses_totales_execution
- Solde global (base engagements dons compris, hors coût rest.banc.) ->
  tofe_solde_global_execution (chosen over the file's other 3 "solde global"
  variants as the closest conceptual match to budget_solde_global: overall
  balance, commitment basis, grants included)

Usage: uv run python -m pipeline.add_beac_tofe
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "beac-tofe-rca"
RETRIEVED_AT = "2026-10-16"

YEARS = [str(y) for y in range(2012, 2023)]
ESTIM_FROM = "2020"  # 2020-2022 marked "Estim" in the source file itself

RECETTES_TOTALES = [
    127.80000000000001, 43.205273733999995, 41.78423570922734, 66.49999999999999,
    62.85707820597544, 93.47800000000001, 112.38613338602073, 116.06746430326214,
    125.69999999999999, 125.89999999999999, 117.2,
]
DEPENSES_TOTALES = [
    162.9434, 111.90000000000002, 107.17418, 141.7647, 130.841, 166.8,
    205.93200000000002, 225.902, 335.5616, 281.90000000000003, 271.40000000000003,
]
SOLDE_GLOBAL_DONS_COMPRIS = [
    11.932600000000015, -47.99472626600003, 19.910055709227336, 4.6962999999999795,
    -5.783921794024565, -12.722000000000008, 4.6541333860207175, 18.90846430326215,
    -36.96160000000003, -86.20000000000006, -85.80000000000004,
]

NOTES = {
    "tofe_recettes_totales_execution": (
        "Recettes totales exécutées (TOFE), feuille deoferca de "
        "deofe_rca-1.xlsx. Exécution budgétaire réelle, pas le chiffre voté "
        "en loi de finances (voir budget_ressources_totales)."
    ),
    "tofe_depenses_totales_execution": (
        "Dépenses totales exécutées (TOFE), feuille deoferca de "
        "deofe_rca-1.xlsx. Exécution budgétaire réelle, pas le chiffre voté "
        "en loi de finances (voir budget_depenses_totales)."
    ),
    "tofe_solde_global_execution": (
        "Solde global exécuté, base engagements, dons compris, hors coût de "
        "restructuration bancaire (TOFE), feuille deoferca de "
        "deofe_rca-1.xlsx. Négatif = déficit. Pas le chiffre voté en loi de "
        "finances (voir budget_solde_global)."
    ),
}


def build_rows() -> list[dict]:
    rows = []
    for series, indicator_id in [
        (RECETTES_TOTALES, "tofe_recettes_totales_execution"),
        (DEPENSES_TOTALES, "tofe_depenses_totales_execution"),
        (SOLDE_GLOBAL_DONS_COMPRIS, "tofe_solde_global_execution"),
    ]:
        for period, value in zip(YEARS, series, strict=True):
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": period, "value": round(value * 1_000_000_000), "unit": "FCFA",
                "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
                "quality_flag": "estime" if period >= ESTIM_FROM else "",
                "notes": NOTES[indicator_id],
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

    print(f"Added {len(new_rows)} TOFE execution observations "
          f"({len(YEARS)} years x 3 indicators, 2020-2022 flagged 'estime').")


if __name__ == "__main__":
    main()
