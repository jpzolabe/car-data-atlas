# BêAfrîka Data

A public reference work about the Central African Republic: national figures
across themes, drillable down to région, préfecture and sous-préfecture -
every number carrying its source and its date, and every gap stated rather
than hidden.


## What this is

Not a dashboard, not a data portal - a reference work about places and themes
in the Central African Republic. Three rules shape every page:

- **Provenance.** No number is ever shown without its source, its date, and
  the geographic level it refers to.
- **Freshness is visible.** An old figure looks different from a current one
  on the page; stale data is never presented with the same confidence as
  fresh data.
- **Gaps are content.** Where nothing has been measured, the site says so
  explicitly, instead of leaving a silent hole.

Themes: population, économie, prix, agriculture, santé, éducation,
infrastructures. Built for readers on a slow connection first - the site
ships no client-side JavaScript beyond a search box and a dark-mode toggle,
and every page stays under 150 KB.

## Status

The site itself is built and functional locally, covering all seven themes
plus every préfecture. It has not been deployed to a public URL yet.

## Quickstart

Data pipeline (Python, [`uv`](https://docs.astral.sh/uv/)):

```
uv sync
uv run python -m pipeline.export_public_data   # regenerate site/public/donnees + site/src/data/donnees.json
uv run python -m pipeline.export_sources_json   # regenerate site/src/data/sources.json
```

Each `pipeline/export_*.py` script (10 of them) rebuilds one JSON file the
site reads from `data/*.csv` via DuckDB - re-run the relevant one after
editing a CSV. `uv run python -m pipeline.validate` checks CSV
well-formedness and referential integrity, and is what CI calls - run it
before committing a data change. See `pipeline/README.md` for the full
script inventory (fetch/add/build/export).

Most sources also fetch automatically: two scheduled GitHub Actions jobs run
weekly and monthly for the sources with real month-to-month movement
(`.github/workflows/fetch-ihpc.yml`, `fetch-wfp-prix.yml`), and a third
checks the remaining sources once a month (`fetch-monthly.yml`) - each run
opens a pull request if the data actually changed, reviewed by hand before
merging. One source (a static 2019 academic dataset) is excluded since it
will never be revised.

Site (Node, `pnpm`):

```
cd site
pnpm install
pnpm dev      # local dev server
pnpm build    # static build to site/dist, checked against the 150 KB/page budget
```

## Layout

```
data/       source of truth - CSVs (entities, aliases, sources, indicators,
            observations, unresolved). See data/README.md.
raw/        immutable snapshots of everything fetched. See raw/README.md.
geo/        GeoJSON boundaries, per entity per version. See geo/README.md.
fixtures/   fake data for tests only, never real data. See fixtures/README.md.
pipeline/   Python: fetch, snapshot, transform, validate. See pipeline/README.md.
site/       the Astro site. See site/README.md.
```

## Licence

Data (`data/`, `geo/`, and extractions from `raw/`) is CC BY 4.0 - see
`LICENCE-DONNEES.md`. Code (`pipeline/`, `site/`) is MIT - see `LICENSE`.
