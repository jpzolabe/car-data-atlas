# data/

The source of truth. Everything else in this repo (the Astro site, generated
charts, generated sentences) is derived from these CSVs - never edit a derived
artifact by hand instead of fixing it here.

**Never put placeholder or invented rows here.** If a value is unknown, leave
it null and let it show as a gap rather than guessing. Sample data for tests
goes in `fixtures/` instead, with obviously fake values.

## Current state

Row counts change often enough that a hardcoded table here goes stale fast -
run `wc -l data/*.csv` (subtract 1 per file for the header), or
`uv run python -m pipeline.validate`, which also prints entity counts by
level and checks referential integrity, for the current numbers.

Commune/localité are out of scope for now - the current geography source
(COD-AB v02) doesn't publish anything finer than sous-préfecture.

**Real, open disagreements and gaps** the crosswalk hasn't resolved live in
`data/unresolved.csv` itself - a deliverable, not a failure log, split by
`reason` (`absent_from_source` vs. `conflicting_name_or_code`, since a
source being incomplete is a different situation from two sources actively
disagreeing). Licence caveats for a specific source live in that source's
own `licence_notes`/`access_notes` fields in `data/sources.csv`.

Run `uv run python -m pipeline.validate` after any change - it checks CSV
well-formedness, every cross-file reference (aliases → entities/sources,
observations → entities/indicators/sources, entity → parent), and that no
value jumps more than 2x (or drops below half) year-over-year without an
explanatory note.

## Files

- **entities.csv** - one row per administrative unit *per version*. A new
  version of a place (redrawn boundary, renamed, split) is a new row with a
  new `entity_id`, never an edit to the old one.
- **aliases.csv** - every spelling, accent variant, and source-specific code
  for every entity, mapping back to its canonical `entity_id`. This is what
  makes joins across sources possible.
- **sources.csv** - one row per data source: producer, licence, geography
  vintage, update cadence, and `authority_rank`, which drives which figure is
  shown by default when sources disagree.
- **indicators.csv** - one row per indicator: definition, unit, theme, and
  `geographic_floor` - the deepest administrative level that indicator
  genuinely reaches, set from observation, never from hope.
- **observations.csv** - the actual values, long format:
  `entity_id, indicator_id, period, value, ...`.
- **unresolved.csv** - every case the crosswalk couldn't resolve (see above).

## Column reference

Each CSV's own header row names its columns; the descriptions above say what
each file is for. There's no separate column-by-column spec beyond that -
if a column's meaning isn't clear from its name and the notes in the row
that uses it, that's worth fixing in the header or the data itself, not in
a document that has to be kept in sync with it separately.
