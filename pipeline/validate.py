"""Quality gates from CLAUDE.md, run over the data/ CSVs with DuckDB.

- Every CSV row has the same number of fields as its header (catches an unquoted
  comma inside a field silently shifting columns - has happened three times while
  hand-editing sources.csv, hence a real, not hypothetical, gate)
- Every alias's source_id exists in sources.csv
- Every alias's entity_id exists in entities.csv
- Every entity's parent_id (if set) exists in entities.csv
- Every observation's entity_id, indicator_id and source_id resolve
- No series jumps more than 2x (or drops below half) between consecutive
  annual points for the same entity/indicator/source, unless it's already
  explained in that observation's own notes field - added after finding
  the World Bank's esperance_vie series for CAR swinging 40.3 -> 18.8 -> 57.4
  years with no flag at all; every real jump already in the data at the
  time this gate was added already had a note explaining it, so the
  threshold is calibrated against real data, not picked in the abstract

Usage: uv run python -m pipeline.validate
Exits non-zero if any gate fails - this is what CI calls.
"""

import csv
import sys
from pathlib import Path

import duckdb

DATA_CSVS = [
    "data/entities.csv", "data/aliases.csv", "data/sources.csv",
    "data/indicators.csv", "data/observations.csv", "data/unresolved.csv",
]


def check_well_formed(path: str) -> list[str]:
    problems = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if len(row) != len(header):
                problems.append(
                    f"{path}:{i} has {len(row)} fields, expected {len(header)} "
                    "(likely an unquoted comma inside a field)"
                )
    return problems


def main() -> int:
    failures = []
    for path in DATA_CSVS:
        if Path(path).exists():
            failures.extend(check_well_formed(path))

    if failures:
        print("FAILED quality gates (well-formedness, checked before anything else):")
        for f in failures:
            print(f"  - {f}")
        return 1

    con = duckdb.connect()
    con.execute("""
        create view entities as select * from read_csv_auto('data/entities.csv');
        create view aliases as select * from read_csv_auto('data/aliases.csv');
        create view sources as select * from read_csv_auto('data/sources.csv');
        create view indicators as select * from read_csv_auto('data/indicators.csv');
        create view observations as select * from read_csv_auto('data/observations.csv');
    """)

    orphan_alias_sources = con.execute("""
        select distinct a.source_id from aliases a
        left join sources s on a.source_id = s.source_id
        where s.source_id is null
    """).fetchall()
    if orphan_alias_sources:
        failures.append(f"aliases.csv references unknown source_id(s): {orphan_alias_sources}")

    orphan_alias_entities = con.execute("""
        select distinct a.entity_id from aliases a
        left join entities e on a.entity_id = e.entity_id
        where e.entity_id is null
    """).fetchall()
    if orphan_alias_entities:
        failures.append(f"aliases.csv references unknown entity_id(s): {orphan_alias_entities}")

    orphan_parents = con.execute("""
        select distinct e.entity_id, e.parent_id from entities e
        left join entities p on e.parent_id = p.entity_id
        where e.parent_id != '' and p.entity_id is null
    """).fetchall()
    if orphan_parents:
        failures.append(f"entities.csv has entities with unresolved parent_id: {orphan_parents}")

    orphan_obs_entities = con.execute("""
        select distinct o.entity_id from observations o
        left join entities e on o.entity_id = e.entity_id
        where e.entity_id is null
    """).fetchall()
    if orphan_obs_entities:
        failures.append(f"observations.csv references unknown entity_id(s): {orphan_obs_entities}")

    orphan_obs_indicators = con.execute("""
        select distinct o.indicator_id from observations o
        left join indicators i on o.indicator_id = i.indicator_id
        where i.indicator_id is null
    """).fetchall()
    if orphan_obs_indicators:
        failures.append(
            f"observations.csv references unknown indicator_id(s): {orphan_obs_indicators}"
        )

    orphan_obs_sources = con.execute("""
        select distinct o.source_id from observations o
        left join sources s on o.source_id = s.source_id
        where s.source_id is null
    """).fetchall()
    if orphan_obs_sources:
        failures.append(f"observations.csv references unknown source_id(s): {orphan_obs_sources}")

    # indicators.csv's geographic_floor must match the finest entity level
    # actually used in observations.csv - "set from observation, never from
    # hope" (data/README.md). Read-only check: this gate flags drift, it
    # doesn't fix it - run `uv run python -m pipeline.set_geographic_floor`
    # to recompute and write the correct values.
    floor_mismatches = con.execute("""
        with level_rank(level, rank) as (
            values ('pays', 0), ('region', 1), ('prefecture', 2),
                   ('sous_prefecture', 3), ('marche', 4)
        ),
        finest as (
            select o.indicator_id, max(lr.rank) as finest_rank
            from observations o
            join entities e on o.entity_id = e.entity_id
            join level_rank lr on e.level = lr.level
            group by o.indicator_id
        )
        select i.indicator_id, i.geographic_floor as stored, lr2.level as should_be
        from indicators i
        join finest f on i.indicator_id = f.indicator_id
        join level_rank lr2 on lr2.rank = f.finest_rank
        where i.geographic_floor != lr2.level
    """).fetchall()
    if floor_mismatches:
        failures.append(
            "indicators.csv geographic_floor doesn't match observations.csv - "
            f"run pipeline.set_geographic_floor to fix: {floor_mismatches}"
        )

    # Only annual periods ("2021", not "2020-01" or "2023-Q1") - monthly and
    # quarterly series have different natural volatility and aren't what
    # this gate is calibrated against.
    unexplained_jumps = con.execute("""
        with numeric_obs as (
            select entity_id, indicator_id, source_id,
                   try_cast(period as integer) as year,
                   try_cast(value as double) as value,
                   notes
            from observations
            where regexp_matches(period, '^[0-9]{4}$')
        ),
        with_prev as (
            select *,
                lag(year) over w as prev_year,
                lag(value) over w as prev_value,
                lag(notes) over w as prev_notes
            from numeric_obs
            window w as (partition by entity_id, indicator_id, source_id order by year)
        )
        select entity_id, indicator_id, source_id, prev_year, prev_value, year, value
        from with_prev
        where prev_value is not null and prev_value != 0 and value != 0
          and (value / prev_value > 2.0 or value / prev_value < 0.5)
          and (trim(coalesce(notes, '')) = '' or trim(coalesce(prev_notes, '')) = '')
    """).fetchall()
    if unexplained_jumps:
        failures.append(
            "unexplained series jump(s) (>2x or <0.5x between consecutive years, "
            f"no note on one side): {unexplained_jumps}"
        )

    counts = con.execute("""
        select level, count(*) from entities group by level order by level
    """).fetchall()

    print("Entity counts by level:")
    for level, n in counts:
        print(f"  {level}: {n}")

    if failures:
        print("\nFAILED quality gates:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nAll quality gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
