"""Populate unresolved.csv with the specific sous-préfecture-level disagreements
found between COD-AB v02 (our canonical entities.csv source) and citypopulation.de,
diagnosed name-by-name on 2026-09-09. See docs/verification-debt.md for the full
per-préfecture count table this refines.

Two different kinds of disagreement, logged distinctly:
- "missing": citypopulation.de simply doesn't list a sous-préfecture COD-AB has.
  citypopulation.de's own page admits its 2021 breakdown is based on "incomplete
  digital mapping" - plausible, not confirmed, explanation.
- "conflict": names/codes actively disagree between the two sources, not just
  presence/absence. Bangui's whole naming scheme differs; Kodi/Ndim have a genuine
  p-code collision, re-verified directly (not a fetch-summary artifact).

Usage: uv run python -m pipeline.add_unresolved_citypop_diff
"""

import csv

SOURCE_ID = "citypopulation-de-caf"

MISSING = [
    ("Mboki (CF635)", "Haut-Mbomou : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Am-Dafok (CF534)", "Vakaga : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Ouandja (CF533)", "Vakaga : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Ouandja-Kotto (CF524)",
     "Haute-Kotto : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Moboma (CF126)", "Lobaye : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Ndim (CF343 selon COD-AB v02)",
     "Lim-Pendé : présent dans COD-AB v02, absent de citypopulation.de."),
    ("Taley (CF345)", "Lim-Pendé : présent dans COD-AB v02, absent de citypopulation.de."),
]

CONFLICTS = [
    (
        "Kodi",
        "COD-AB v02 code CF344 ; citypopulation.de code CF343 pour la même "
        "sous-préfecture (re-vérifié directement le 2026-09-09, citypopulation.de "
        "note \"(← Ngaoundaye)\" suggérant une création récente par scission - "
        "hypothèse d'un désaccord de re-numérotation, non confirmée).",
    ),
    (
        "Bangui-Centre / Bangui-Kagas / Bangui-Fleuve / Bangui-Rapides (COD-AB v02) "
        "vs. Bangui / Bimbo / Bégoua (citypopulation.de)",
        "Bangui : les deux sources ne s'accordent pas seulement sur le nombre "
        "(4 vs 3) mais sur le schéma de nommage lui-même - COD-AB v02 utilise des "
        "zones (Centre/Kagas/Fleuve/Rapides), citypopulation.de utilise des noms "
        "de lieux (Bimbo, Bégoua) qui correspondent à des communes réelles. "
        "Chevauchement partiel des codes (CF711-713) mais avec des noms "
        "différents attachés. Non résolu - nécessite une source supplémentaire "
        "pour trancher plutôt qu'un choix arbitraire entre les deux schémas.",
    ),
]


def main():
    rows = []
    for raw_string, notes in MISSING:
        rows.append({
            "source_id": SOURCE_ID, "raw_string": raw_string,
            "level_guess": "sous_prefecture",
            "reason": "absent_from_source",
            "notes": notes,
        })
    for raw_string, notes in CONFLICTS:
        rows.append({
            "source_id": SOURCE_ID, "raw_string": raw_string,
            "level_guess": "sous_prefecture",
            "reason": "conflicting_name_or_code",
            "notes": notes,
        })

    with open("data/unresolved.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["source_id", "raw_string", "level_guess", "reason", "notes"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} unresolved.csv rows "
          f"({len(MISSING)} missing, {len(CONFLICTS)} conflicting).")


if __name__ == "__main__":
    main()
