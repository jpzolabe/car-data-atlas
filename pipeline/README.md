# pipeline/

The Python side: fetch, snapshot, extract, normalise, validate. Empty for now —
Phase 1 (`docs/plan.md` Part 5) starts here, with the geography crosswalk.

## Intended shape (not built yet)

Nothing below exists yet. Noted here so Phase 1 doesn't have to rediscover the
shape of this package before starting real work — but don't create empty
subpackages ahead of the code that belongs in them.

- **fetch** — one module per source, each: hit the source, write an immutable
  snapshot under `raw/{source_id}/{iso_date}/`, nothing else. No transformation
  here.
- **transform** — turn a raw snapshot into rows for `data/*.csv`. This is
  where alias normalisation (accents, casing, `Ouaka` vs `Wakka`) and entity
  resolution against `data/entities.csv` happens.
- **validate** — the CI quality gates from `CLAUDE.md`: every `source_id`
  resolves, every `entity_id` resolves, no unexplained series jumps. Likely
  DuckDB queries over the CSVs rather than a bespoke validation framework.

## Running it

Once dependencies are installed with `uv sync` (see root `pyproject.toml`),
pipeline scripts run with `uv run python -m pipeline.<module>`. Nothing to run
yet.
