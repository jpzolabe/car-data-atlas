"""Add the 7 RGPH-4 régions to entities.csv and re-parent the 20 préfectures under
them (they currently point straight at the country, from before régions existed in
the crosswalk).

Source: 7 individual pages on minurbanisme-rca.org (Ministère de l'Urbanisme), each
naming one région's constituent préfectures and chef-lieu, fetched and quoted
2026-09-05. Not a law/decree - this is the ministry's own regional-directorate
structure, cross-checked only by the fact that its 7 lists sum to exactly 20
préfectures with no overlaps or gaps against data/entities.csv.

Usage: uv run python -m pipeline.add_regions
"""

import csv

REGIONS = [
    # (slug, name_fr, chef_lieu, [préfecture names as they appear in entities.csv name_fr])
    ("plateaux", "Plateaux", "Boali", ["Ombella M'Poko", "Lobaye"]),
    ("equateur", "Équateur", "Berbérati",
     ["Sangha-Mbaéré", "Mambéré-Kadéï", "Mambéré", "Nana-Mambéré"]),
    ("yade", "Yadé", "Bossangoa", ["Ouham", "Ouham-Fafa", "Ouham Pendé", "Lim-pendé"]),
    ("kaga", "Kaga", "Sibut", ["Kémo", "Nana-Gribizi", "Ouaka"]),
    ("fertit", "Fertit", "Bria", ["Haute-Kotto", "Vakaga", "Bamingui-Bangoran"]),
    ("haut-oubangui", "Haut-Oubangui", "Bangassou", ["Basse-Kotto", "Mbomou", "Haut-Mbomou"]),
    ("bas-oubangui", "Bas-Oubangui", "Bangui", ["Bangui"]),
]

SOURCE_ID = "minurbanisme-rca-regions"
REGION_VALID_FROM = "2024-06-01"  # governors for the new régions were first named
# June 2024 per reporting found alongside these pages - this is the régions-as-a-
# governance-layer date, not necessarily RGPH-4's own régions definition date.
# Not independently verified further than that reporting - see verification-debt.md.


def main():
    with open("data/entities.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        entities = list(reader)

    by_name = {e["name_fr"]: e for e in entities if e["level"] == "prefecture"}
    country_id = next(e["entity_id"] for e in entities if e["level"] == "pays")

    new_aliases = []
    unmatched = []

    for i, (slug, name_fr, chef_lieu, pref_names) in enumerate(REGIONS, start=1):
        region_id = f"cf-r-{slug}-v1"
        entities.append({
            "entity_id": region_id,
            "name_fr": name_fr,
            "slug": slug,
            "level": "region",
            "parent_id": country_id,
            "valid_from": REGION_VALID_FROM,
            "valid_to": "",
            "superseded_by": "",
            "notes": (
                f"Chef-lieu régional : {chef_lieu}. Composition et chef-lieu "
                "confirmés sur une page dédiée de minurbanisme-rca.org "
                "(2026-09-05) ; ce n'est pas un texte de loi, et n'a été "
                "recoupé que par le fait que les 7 régions couvrent "
                "exactement les 20 préfectures sans chevauchement ni "
                "manque - voir docs/verification-debt.md."
            ),
        })
        new_aliases.append({
            "entity_id": region_id, "source_id": SOURCE_ID,
            "alias": f"https://www.minurbanisme-rca.org/{i}-{slug}/",
            "alias_type": "code",
        })

        for pn in pref_names:
            pref = by_name.get(pn)
            if pref is None:
                unmatched.append((name_fr, pn))
                continue
            pref["parent_id"] = region_id

    if unmatched:
        raise SystemExit(f"Unmatched préfecture names, fix REGIONS mapping: {unmatched}")

    with open("data/entities.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(entities)

    with open("data/aliases.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["entity_id", "source_id", "alias", "alias_type"],
                                 lineterminator="\n")
        writer.writerows(new_aliases)

    print(f"Added {len(REGIONS)} régions, re-parented "
          f"{sum(len(p) for *_, p in REGIONS)} préfectures.")


if __name__ == "__main__":
    main()
