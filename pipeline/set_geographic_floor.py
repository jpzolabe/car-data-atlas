"""Set indicators.csv's geographic_floor column from what's actually in
data/observations.csv, rather than from a one-time audit's summary
judgment - docs/plan.md Phase 4 step 2 ("Set geographic_floor per
indicator from observation").

For each indicator_id, finds the finest entity level any observation
actually uses (pays -> region -> prefecture -> sous_prefecture, with
marche as WFP prices' own separate finest case - a point, not an area,
per CLAUDE.md) and writes that back to indicators.csv. This is
deliberately mechanical: it reports what has actually been wired into
observations.csv, not what a source might theoretically support if
extracted further (see docs/decisions.md's ICASEES éducation yearbook
entry for why "the source has it" and "it's safely wired in" are kept as
two different questions).

Usage: uv run python -m pipeline.set_geographic_floor
"""

import csv

import duckdb

# Coarsest to finest. "marche" is its own leaf (a point, not an area) -
# no indicator has observations at both marche and sous_prefecture, so it
# doesn't need to slot into the region/prefecture/sous_prefecture chain.
LEVEL_RANK = {"pays": 0, "region": 1, "prefecture": 2, "sous_prefecture": 3, "marche": 4}


def main():
    con = duckdb.connect()
    con.execute("""
        create view entities as select * from read_csv_auto('data/entities.csv');
        create view observations as select * from read_csv_auto('data/observations.csv');
    """)

    rows = con.execute("""
        select o.indicator_id, e.level
        from observations o
        join entities e on o.entity_id = e.entity_id
        group by o.indicator_id, e.level
    """).fetchall()

    finest_by_indicator: dict[str, str] = {}
    for indicator_id, level in rows:
        current = finest_by_indicator.get(indicator_id)
        if current is None or LEVEL_RANK[level] > LEVEL_RANK[current]:
            finest_by_indicator[indicator_id] = level

    with open("data/indicators.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        indicator_rows = list(reader)

    changes = []
    for row in indicator_rows:
        indicator_id = row["indicator_id"]
        actual = finest_by_indicator.get(indicator_id)
        if actual is None:
            continue  # no observations at all yet; leave whatever's there
        if row["geographic_floor"] != actual:
            changes.append((indicator_id, row["geographic_floor"], actual))
            row["geographic_floor"] = actual

    with open("data/indicators.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(indicator_rows)

    if changes:
        print(f"Updated {len(changes)} indicator(s):")
        for indicator_id, old, new in changes:
            print(f"  {indicator_id}: {old!r} -> {new!r}")
    else:
        print("No changes - every indicator's geographic_floor already matches its observations.")


if __name__ == "__main__":
    main()
