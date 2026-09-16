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
        SOURCE_ID,
        "Kodi",
        "COD-AB v02 code CF344 ; citypopulation.de code CF343 pour la même "
        "sous-préfecture (re-vérifié directement le 2026-09-09, citypopulation.de "
        "note \"(← Ngaoundaye)\" suggérant une création récente par scission - "
        "hypothèse d'un désaccord de re-numérotation, non confirmée).",
    ),
    (
        # Updated 2026-09-11 to the real 3-way conflict, after ICASEES's own
        # published wording was found and quoted directly - not the earlier
        # 2-way COD-AB-vs-citypopulation.de version this script originally
        # wrote. source_id is icasees-site, not SOURCE_ID, because ICASEES's
        # own statement is what turned this into a 3-way disagreement.
        "icasees-site",
        "Bangui-Centre / Bangui-Kagas / Bangui-Fleuve / Bangui-Rapides (COD-AB v02) "
        "vs. Bangui / Bimbo / Bégoua (citypopulation.de) vs. 9 arrondissements + "
        "communes de Bimbo et Bégoua (ICASEES)",
        "Désaccord à TROIS voies, pas deux. ICASEES (icasees.org/index.php/"
        "actualites/316-..., cité verbatim, 2026-09-11) : \"les neuf (9) "
        "arrondissements de la capitale ainsi que les communes de Bimbo et "
        "Bégoua\" - Bimbo et Bégoua sont explicitement des communes, pas des "
        "sous-préfectures, et Bimbo n'apparaît dans aucune préfecture de "
        "COD-AB v02. Les trois sources semblent répondre à des questions "
        "différentes (cartographie humanitaire, démographie, logistique de "
        "recensement) plutôt qu'une seule étant simplement fausse. Non "
        "résolu à ce jour.",
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
    for source_id, raw_string, notes in CONFLICTS:
        rows.append({
            "source_id": source_id, "raw_string": raw_string,
            "level_guess": "sous_prefecture",
            "reason": "conflicting_name_or_code",
            "notes": notes,
        })

    # Merge, don't overwrite: this script previously rewrote unresolved.csv
    # from scratch every run, which would silently discard any row edited
    # or added by hand since - exactly what happened to the Bangui conflict
    # above before this fix. Replace only rows this script itself owns
    # (matched by source_id + raw_string), keep everything else untouched.
    own_keys = {(r["source_id"], r["raw_string"]) for r in rows}
    try:
        with open("data/unresolved.csv", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            existing = list(reader)
    except FileNotFoundError:
        fieldnames = ["source_id", "raw_string", "level_guess", "reason", "notes"]
        existing = []
    existing = [r for r in existing if (r["source_id"], r["raw_string"]) not in own_keys]

    with open("data/unresolved.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} unresolved.csv rows "
          f"({len(MISSING)} missing, {len(CONFLICTS)} conflicting), "
          f"{len(existing)} other existing rows preserved.")


if __name__ == "__main__":
    main()
