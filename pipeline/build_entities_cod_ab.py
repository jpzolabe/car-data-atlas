"""Build entities.csv / aliases.csv rows for the pays/préfecture/sous-préfecture
levels from a COD-AB gazetteer snapshot.

Source: raw/cod-ab-caf/{date}/caf_admin_boundaries.xlsx (sheets caf_admin0,
caf_admin1, caf_admin2). See docs/verification-debt.md for what's still open about
this source (licence restriction, the 85-vs-84 sous-préfecture count, no
commune/localité layer in this COD-AB version).

Usage: uv run python -m pipeline.build_entities_cod_ab raw/cod-ab-caf/2026-09-05
"""

import csv
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# The four préfectures created outright by the 10 Dec 2020 reform (Oubangui
# Médias, Xinhua, Wikipedia all agree on this list). Everything else already
# existed before 2020 under the previous 16-préfecture structure, even though
# its boundary may have been redrawn in the same reform.
CREATED_2020 = {"Mambéré", "Lim-pendé", "Ouham-Fafa", "Bangui"}

REFORM_DATE = "2020-12-10"  # date the reform bill was adopted (Xinhua). The
# exact promulgation date and decree number are not yet verified against
# primary legal text - see docs/verification-debt.md.


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.replace("'", "").replace("’", "")
    slug = "".join(c if c.isalnum() else "-" for c in ascii_only.lower())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def main(snapshot_dir: str):
    src = Path(snapshot_dir) / "caf_admin_boundaries.xlsx"
    xl = pd.ExcelFile(src)
    a0 = xl.parse("caf_admin0")
    a1 = xl.parse("caf_admin1")
    a2 = xl.parse("caf_admin2")

    entities = []
    aliases = []

    # --- pays ---
    country_id = "cf-pays-centrafrique-v1"
    country_name = a0.loc[0, "adm0_name"]
    entities.append(
        {
            "entity_id": country_id,
            "name_fr": country_name,
            "slug": slugify(country_name),
            "level": "pays",
            "parent_id": "",
            "valid_from": "",
            "valid_to": "",
            "superseded_by": "",
            "notes": (
                "Niveau pays. Indépendance le 13 août 1960, confirmée via "
                "Encyclopædia Britannica le 2026-09-11 (source non contestée, "
                "contrairement au découpage administratif interne)."
            ),
        }
    )
    aliases.append(
        {
            "entity_id": country_id,
            "source_id": "cod-ab-caf",
            "alias": a0.loc[0, "adm0_pcode"],
            "alias_type": "pcode",
        }
    )

    # --- préfectures (admin1) ---
    pref_id_by_pcode = {}
    for _, row in a1.sort_values("adm1_name").iterrows():
        name = row["adm1_name"]
        pcode = row["adm1_pcode"]
        slug = slugify(name)
        entity_id = f"cf-p-{slug}-v1"
        pref_id_by_pcode[pcode] = entity_id

        created = name in CREATED_2020
        note = (
            f"Créée par la réforme administrative adoptée le {REFORM_DATE} "
            "(source : Oubangui Médias, Xinhua, Wikipédia - texte légal "
            "primaire/numéro de décret non encore vérifié)."
            if created
            else (
                f"Existait avant 2020 sous le découpage à 16 préfectures ; "
                f"limites redéfinies par la réforme du {REFORM_DATE}. Version "
                "antérieure à 2020 non modélisée dans ce crosswalk pour "
                "l'instant."
            )
        )
        entities.append(
            {
                "entity_id": entity_id,
                "name_fr": name,
                "slug": slug,
                "level": "prefecture",
                "parent_id": country_id,
                "valid_from": REFORM_DATE,
                "valid_to": "",
                "superseded_by": "",
                "notes": note,
            }
        )
        aliases.append(
            {
                "entity_id": entity_id,
                "source_id": "cod-ab-caf",
                "alias": pcode,
                "alias_type": "pcode",
            }
        )

    # --- sous-préfectures (admin2) ---
    for _, row in a2.sort_values(["adm1_name", "adm2_name"]).iterrows():
        name = row["adm2_name"]
        pcode = row["adm2_pcode"]
        parent_pcode = row["adm1_pcode"]
        parent_id = pref_id_by_pcode[parent_pcode]
        slug = slugify(name)
        entity_id = f"cf-sp-{slug}-v1"

        entities.append(
            {
                "entity_id": entity_id,
                "name_fr": name,
                "slug": slug,
                "level": "sous_prefecture",
                "parent_id": parent_id,
                "valid_from": REFORM_DATE,
                "valid_to": "",
                "superseded_by": "",
                "notes": (
                    f"Rattachée par COD-AB v02 à la préfecture correspondante "
                    f"à la date de la réforme ({REFORM_DATE}). Certaines "
                    "sous-préfectures actuelles étaient des communes avant "
                    "2020 (12 communes promues selon la réforme) - liste "
                    "précise des communes promues non encore vérifiée."
                ),
            }
        )
        aliases.append(
            {
                "entity_id": entity_id,
                "source_id": "cod-ab-caf",
                "alias": pcode,
                "alias_type": "pcode",
            }
        )

    write_csv("data/entities.csv", entities,
              ["entity_id", "name_fr", "slug", "level", "parent_id",
               "valid_from", "valid_to", "superseded_by", "notes"])
    write_csv("data/aliases.csv", aliases,
              ["entity_id", "source_id", "alias", "alias_type"])

    print(f"Wrote {len(entities)} entities, {len(aliases)} aliases.")
    print(f"Levels: pays=1, prefecture={len(a1)}, sous_prefecture={len(a2)}")


def write_csv(path: str, rows: list[dict], fieldnames: list[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
