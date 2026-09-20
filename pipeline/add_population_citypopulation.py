"""Add préfecture-level population_totale observations from the citypopulation.de
admin table (which relays ICASEES 2003 census and 2021 estimate figures).

Source: raw/citypopulation-de-caf/2026-09-09/admin_table_transcribed.csv, manually
transcribed from the fetched page (raw HTML snapshot alongside it). Not yet parsed
programmatically from the HTML - see data/sources.csv access_notes.

2003 column: recensement (RGPH-3), no quality_flag needed - a validated census result.
2021 column: quality_flag=estime - the source itself states this breakdown came from
"incomplete digital mapping done in preparation of the next population census."

Usage: uv run python -m pipeline.add_population_citypopulation
"""

import csv

SOURCE_ID = "citypopulation-de-caf"
RETRIEVED_AT = "2026-09-09"


def main():
    with open("data/entities.csv", encoding="utf-8", newline="") as f:
        entities = list(csv.DictReader(f))
    with open("data/aliases.csv", encoding="utf-8", newline="") as f:
        aliases = list(csv.DictReader(f))
    with open(
        "raw/citypopulation-de-caf/2026-09-09/admin_table_transcribed.csv",
        encoding="utf-8", newline="",
    ) as f:
        citypop_rows = list(csv.DictReader(f))

    pcode_to_entity = {
        a["alias"]: a["entity_id"] for a in aliases if a["alias_type"] == "pcode"
    }
    prefecture_ids = {e["entity_id"] for e in entities if e["level"] == "prefecture"}

    observations = []
    for row in citypop_rows:
        entity_id = pcode_to_entity.get(row["pcode"])
        if entity_id is None or entity_id not in prefecture_ids:
            raise SystemExit(f"pcode {row['pcode']} ({row['prefecture']}) did not "
                              "resolve to a known préfecture entity_id")

        observations.append({
            "entity_id": entity_id, "indicator_id": "population_totale",
            "period": "2003", "value": row["pop_2003"], "unit": "habitants",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "",
            "notes": "Recensement (RGPH-3), relayé par citypopulation.de.",
        })
        observations.append({
            "entity_id": entity_id, "indicator_id": "population_totale",
            "period": "2021", "value": row["pop_2021"], "unit": "habitants",
            "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
            "quality_flag": "estime",
            "notes": (
                "Estimation relayée par citypopulation.de ; la source déclare "
                "elle-même que ce chiffre provient d'une cartographie numérique "
                "incomplète en préparation du recensement suivant."
            ),
        })

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    # Filter by source_id, not indicator_id alone - other sources also
    # write population_totale rows (e.g. RGPH-4, World Bank), and an
    # indicator_id-only filter would silently delete their rows too. See
    # the same fix already applied in fetch_economie.py.
    existing = [r for r in existing if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(observations)

    print(f"Wrote {len(observations)} observations "
          f"({len(citypop_rows)} préfectures x 2 periods).")


if __name__ == "__main__":
    main()
