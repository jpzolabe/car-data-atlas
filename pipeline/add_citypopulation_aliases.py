"""Add citypopulation.de as an alias source, but only for entities whose name+code
were actually fetched and confirmed directly - not the ~65 sous-préfectures that
were only compared by count in the discrepancy check (see docs/verification-debt.md).
Adding an alias for something never actually seen would be exactly the kind of
unverified claim rule zero warns against.

Covers:
- All 20 préfectures (full named table fetched 2026-09-09).
- Sous-préfectures individually confirmed while diagnosing the 6-préfecture gap:
  Haut-Mbomou, Vakaga, Haute-Kotto, Lobaye (all clean), and the 2 non-conflicting
  names from Lim-Pendé (Ngaoundaye, Paoua - Kodi is a logged conflict, not a clean
  alias; Ndim/Taley are logged as missing, not present to alias at all).
Bangui's sous-préfectures are deliberately excluded - see the 3-way unresolved entry.

Usage: uv run python -m pipeline.add_citypopulation_aliases
"""

import csv

SOURCE_ID = "citypopulation-de-caf"

# (entity pcode used to find the entity via existing cod-ab-caf alias, citypop code)
# Where citypop's code differs from COD-AB's, that's Kodi - excluded, see docstring.
PREFECTURES = [
    "CF51", "CF71", "CF61", "CF52", "CF63", "CF41", "CF34", "CF12", "CF24", "CF21",
    "CF62", "CF42", "CF22", "CF11", "CF43", "CF32", "CF33", "CF31", "CF23", "CF53",
]

# name as citypopulation.de writes it, its code, matches COD-AB's code for the same unit
SOUS_PREFECTURES = [
    ("Bambouti", "CF632"), ("Djemah", "CF634"), ("Obo", "CF631"), ("Zémio", "CF633"),
    ("Birao", "CF531"), ("Ouanda Djallé", "CF532"),
    ("Bria", "CF521"), ("Ouadda", "CF522"), ("Yalinga", "CF523"),
    ("Boda", "CF123"), ("Boganangone", "CF124"), ("Boganda", "CF125"),
    ("Mbaïki", "CF121"), ("Mongoumba", "CF122"),
    ("Ngaoundaye", "CF342"), ("Paoua", "CF341"),
]


def main():
    with open("data/aliases.csv", encoding="utf-8", newline="") as f:
        aliases = list(csv.DictReader(f))

    pcode_to_entity = {
        a["alias"]: a["entity_id"] for a in aliases if a["alias_type"] == "pcode"
    }

    new_rows = []
    for pcode in PREFECTURES:
        entity_id = pcode_to_entity[pcode]
        new_rows.append({
            "entity_id": entity_id, "source_id": SOURCE_ID,
            "alias": pcode, "alias_type": "pcode",
        })

    for name, pcode in SOUS_PREFECTURES:
        entity_id = pcode_to_entity[pcode]
        new_rows.append({
            "entity_id": entity_id, "source_id": SOURCE_ID,
            "alias": pcode, "alias_type": "pcode",
        })
        new_rows.append({
            "entity_id": entity_id, "source_id": SOURCE_ID,
            "alias": name, "alias_type": "name",
        })

    # Idempotency guard: dedupe against what's already in the file so a
    # rerun doesn't duplicate every row - this script previously had none.
    existing_keys = {
        (a["entity_id"], a["source_id"], a["alias"], a["alias_type"]) for a in aliases
    }
    new_rows = [
        r for r in new_rows
        if (r["entity_id"], r["source_id"], r["alias"], r["alias_type"]) not in existing_keys
    ]

    with open("data/aliases.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["entity_id", "source_id", "alias", "alias_type"],
            lineterminator="\n",
        )
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} new citypopulation.de aliases "
          f"({len(PREFECTURES)} préfecture pcodes, "
          f"{len(SOUS_PREFECTURES)} sous-préfecture pcode+name pairs already declared; "
          "already-present rows skipped).")


if __name__ == "__main__":
    main()
