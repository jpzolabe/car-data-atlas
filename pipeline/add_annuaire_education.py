"""Add national education headcounts (schools, students, teachers) from
ICASEES's Annuaire Statistique de l'Éducation 2024-2025, per Phase 3
source list item 1 (docs/plan.md) -- retried after being paused earlier
this session for apparent rate-limiting (docs/verification-debt.md); the
site responded normally this time, no sign of the earlier block.

Hand-transcribed, not auto-parsed, on purpose: the workbook
(raw/icasees-annuaire-education/2026-09-12/annuaire_statistique_2024_2025.xlsx)
is a single unstructured sheet mixing narrative text and tables at
irregular positions -- AGENTS.md itself names these yearbooks' layout as
irregular year to year, and a prior year's version of this same yearbook
uses a different file structure per its own multiple Word/Excel variants
on the publications page. A script parsing today's exact cell positions
would silently break or silently misread a future year's file rather than
fail loudly -- worse than not automating it. Re-verify cell positions by
hand for each future year's edition instead. See docs/decisions.md.

Table 1: national summary by education level (workbook rows ~168-179),
"Niveau d'enseignement" x établissements / salles de classe / effectifs
élèves / nombre d'enseignants, by sex and public/privé status. Only the
national total row per level was used here (columns 37, 87, 116 -- the
tables also break out Public/Privé beneath each level total, not
transcribed here to keep this first pass to the headline national
figures).

Table 2 (rows ~238-267): a PSE (Plan Sectoriel de l'Éducation) tracking
table with a clean, unambiguous header ("Valeur de base (2019)" /
"Valeur réalisée 2024" / "Cible 2029") -- row 257 gives the Baccalauréat
général pass rate directly: 25% (2019 baseline) and 36.66% (2024). This
closes a gap AGENTS.md names explicitly ("BEPC and Baccalauréat results
are not published in machine-readable form"). A second exam-results table
elsewhere in the workbook (row ~3789, "Résultats aux examens... de
l'année précédente (2020/2021)") looked promising but its data rows are
entirely empty -- a carried-over template from a prior year's file
structure, not real numbers -- checked directly rather than assumed
filled in, and not used here.

Usage: uv run python -m pipeline.add_annuaire_education
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "icasees-annuaire-education-2024-2025"
RETRIEVED_AT = "2026-09-12"
PERIOD = "2024"  # année scolaire 2024-2025 -- see notes below on this choice

# (niveau, établissements, élèves, enseignants) -- workbook rows 170, 173,
# 176, 179, national total row for each level (not the Public/Privé
# sub-rows beneath).
LEVELS = [
    ("Préscolaire", 357, 21_691, 979),
    ("Fondamental I", 3_415, 1_075_963, 13_261),
    ("Fondamental II et Secondaire Général", 273, 317_626, 4_189),
    ("Enseignement Technique et Professionnel", 33, 10_690, 530),
]

NOTES = (
    "Année scolaire 2024-2025, recensement scolaire administratif (pas un "
    "échantillon). Total national = somme des 4 niveaux d'enseignement "
    "(Préscolaire, Fondamental I, Fondamental II et Secondaire Général, "
    "Enseignement Technique et Professionnel) ; détail par niveau et par "
    "statut public/privé disponible dans le fichier source, non repris ici."
)

# (period, taux de réussite au Baccalauréat général) -- table de suivi PSE,
# ligne "Taux de réussite au Baccalauréat général", colonnes "Valeur de
# base (2019)" et "Valeur réalisée 2024".
BAC_RATES = [("2019", 0.25), ("2024", 0.3666)]
BAC_NOTES = (
    "Table de suivi du Plan Sectoriel de l'Éducation (PSE), colonnes "
    "\"Valeur de base (2019)\" et \"Valeur réalisée 2024\". Un second "
    "tableau de résultats d'examens existe dans le même fichier "
    "(session 2020/2021) mais ses lignes de données sont entièrement "
    "vides -- gabarit reconduit d'une année antérieure, pas des chiffres "
    "réels ; non utilisé."
)


def build_rows() -> list[dict]:
    total_etabs = sum(level[1] for level in LEVELS)
    total_eleves = sum(level[2] for level in LEVELS)
    total_enseignants = sum(level[3] for level in LEVELS)

    values = {
        "nombre_etablissements_scolaires": (total_etabs, "établissements"),
        "effectif_eleves": (total_eleves, "élèves"),
        "nombre_enseignants": (total_enseignants, "enseignants"),
    }

    rows = [
        {
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": PERIOD, "value": value, "unit": unit,
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "administratif", "notes": NOTES,
        }
        for indicator_id, (value, unit) in values.items()
    ]
    rows += [
        {
            "entity_id": COUNTRY_ID, "indicator_id": "taux_reussite_baccalaureat",
            "period": period, "value": round(rate * 100, 2), "unit": "%",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "administratif", "notes": BAC_NOTES,
        }
        for period, rate in BAC_RATES
    ]
    return rows


def main():
    new_rows = build_rows()

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    for row in new_rows:
        print(f"{row['indicator_id']}: {row['value']} {row['unit']} ({row['period']})")


if __name__ == "__main__":
    main()
