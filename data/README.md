# data/

The source of truth. Everything else in this repo (the Astro site, generated
charts, generated sentences) is derived from these CSVs — never edit a derived
artifact by hand instead of fixing it here.

**Never put placeholder or invented rows here** — see rule zero in `CLAUDE.md`.
Sample data for tests goes in `fixtures/` instead, with obviously fake values.

## Current state (2026-09-11, Phase 1 in progress)

| File | Rows | Built by |
|---|---|---|
| `entities.csv` | 113 (1 pays, 7 régions, 20 préfectures, 85 sous-préfectures) | `pipeline/build_entities_cod_ab.py`, `add_regions.py`, `fix_reform_date.py` |
| `aliases.csv` | 168 | same, plus `add_citypopulation_aliases.py` |
| `sources.csv` | 7 | hand-maintained |
| `indicators.csv` | 1 (`population_totale`) | hand-maintained |
| `observations.csv` | 40 (population, 2003 + 2021, per préfecture) | `pipeline/add_population_citypopulation.py` |
| `unresolved.csv` | 9 | `pipeline/add_unresolved_citypop_diff.py` |

Commune/localité are out of scope for now — the current geography source doesn't
publish anything finer than sous-préfecture. See `CLAUDE.md`'s scope note.

**Known open questions** about what's in these files right now live in
`docs/verification-debt.md`, not here — check there before assuming a figure or a
boundary count is settled. As of this writing: COD-AB's licence terms aren't fully
resolved, the régions→préfectures mapping has only one source, and Bangui's internal
sous-préfecture structure is a genuine three-way disagreement between COD-AB,
citypopulation.de and ICASEES.

Run `uv run python -m pipeline.validate` after any change — it checks CSV
well-formedness plus every cross-file reference (aliases → entities/sources,
observations → entities/indicators/sources, entity → parent).

## Files

- **entities.csv** — one row per administrative unit *per version*. A new
  version of a place (redrawn boundary, renamed, split) is a new row with a
  new `entity_id`, never an edit to the old one. See `docs/plan.md` §3.1.
- **aliases.csv** — every spelling, accent variant, and source-specific code
  for every entity, mapping back to its canonical `entity_id`. This is what
  makes joins across sources possible. See §3.2.
- **sources.csv** — one row per data source: producer, licence, geography
  vintage, update cadence, and `authority_rank`, which drives which figure is
  shown by default when sources disagree. See §3.3.
- **indicators.csv** — one row per indicator: definition, unit, theme, and
  `geographic_floor` — the deepest administrative level that indicator
  genuinely reaches, set from observation, never from hope. See §3.4.
- **observations.csv** — the actual values, long format:
  `entity_id, indicator_id, period, value, ...`. See §3.5.
- **unresolved.csv** — every case the crosswalk couldn't resolve, split by
  `reason` (e.g. `absent_from_source` vs. `conflicting_name_or_code` — a
  source being incomplete is a different situation from two sources actively
  disagreeing, and they shouldn't be logged as if equally serious). This is a
  deliverable, not a failure log — see `docs/decisions.md`.

## Column reference

See `docs/plan.md` Part 3 for the full column-by-column spec of each file.
