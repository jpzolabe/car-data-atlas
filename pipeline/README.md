# pipeline/

The Python side: fetch, snapshot, transform, validate - a flat module of
scripts (`uv`, DuckDB), not the `fetch/`/`transform/`/`validate/` subpackage
layout once sketched here before any of it was built.

## Layout

- **`fetch_*.py`** (one per source or source group) - hit a live API, replace
  that source's own rows in `data/observations.csv` (filtered by `source_id`,
  never by `indicator_id` alone - an earlier version of several of these
  scripts got that wrong and could delete another source's rows for the same
  indicator; see the git history), and snapshot the raw response under
  `raw/{source_id}/{iso_date}/` where the source is file-based. Idempotent:
  running one twice in a row produces the same file, not duplicates. Two are
  on a schedule (`.github/workflows/fetch-ihpc.yml`,
  `fetch-wfp-prix.yml`); ten more run monthly via `fetch-monthly.yml`; the
  rest are run by hand.
- **`add_*.py`** - one-off scripts for data that can't be fetched
  programmatically (a hand-transcribed PDF table, a manually verified web
  page). Each documents its own provenance in its own docstring. Not meant
  to be re-run casually - several assume a specific prior state and are
  idempotent against it, not against an empty file.
- **`build_*.py`** - `build_entities_cod_ab.py` and `build_geo_prefectures.py`,
  the one-time construction of the geography crosswalk (`data/entities.csv`,
  `data/aliases.csv`) and the simplified GeoJSON from the COD-AB source.
- **`export_*.py`** - the CSV-to-JSON handoff: each reads `data/*.csv` via
  DuckDB and writes one `site/src/data/*.json` file the Astro site actually
  reads. Astro never touches the raw CSVs directly. Re-run the relevant one
  after hand-editing a CSV, or after any `fetch_*`/`add_*.py` run.
  `export_public_data.py` additionally copies the CSVs themselves into
  `site/public/donnees/` for the site's bulk-download page.
- **`validate.py`** - the CI quality gates: CSV well-formedness, every
  alias/observation's `entity_id`/`indicator_id`/`source_id` resolving, and
  a series-jump check (a value that more than doubles or halves
  year-over-year must have an explanatory note, or the gate fails). This is
  what CI calls.
- **`sentences.py`** - the deterministic French sentence templates every
  generated caption on the site is built from. No model call, ever - the
  same data always produces the same sentence, and every sentence is
  traceable to a template plus values.
- **`set_geographic_floor.py`, `fix_reform_date.py`** - small one-off
  maintenance scripts; each documents the specific fix it made.

## Running it

Once dependencies are installed (`uv sync` from the repo root), every script
runs as `uv run python -m pipeline.<module_name>`. Three are automated on a
schedule (see `.github/workflows/`); everything else is run by hand when
there's a reason to.
