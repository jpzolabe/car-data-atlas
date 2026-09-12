# BeAfrika Data

*(named "Données RCA" until 2026-09-13 - renamed for the public site;
internal references to "RCA" as a project shorthand are unaffected)*

A public reference work about the Central African Republic: national figures
across themes, drillable down to région, préfecture, sous-préfecture and
commune - every number carrying its source and its date, and every gap stated
rather than hidden.

> Explorer la République centrafricaine - ce que disent les données, d'où
> elles viennent, et ce que personne n'a encore mesuré.

This repository is early - Phase 0 of the build plan (see below). There is no
public site yet.

## Start here

- **`CLAUDE.md`** - the standing rules: what this project is, rule zero
  (never invent data), the geographic-crosswalk problem this project exists
  to solve, and the technical constraints (zero client JS, 150 KB/page).
- **`docs/plan.md`** - the full product spec and six-phase build plan.
- **`docs/decisions.md`** - why the constraints in `CLAUDE.md` exist, and
  which technical decisions are still open.

## Layout

```
data/       source of truth - CSVs (entities, aliases, sources, indicators,
            observations, unresolved). See data/README.md.
raw/        immutable snapshots of everything fetched. See raw/README.md.
geo/        GeoJSON boundaries, per entity per version. See geo/README.md.
fixtures/   fake data for tests only, never real data. See fixtures/README.md.
pipeline/   Python: fetch, snapshot, transform, validate. See pipeline/README.md.
site/       the Astro site. See site/README.md.
docs/       plan, decisions, and other project documentation.
```

## Licence

Data (`data/`, `geo/`, and extractions from `raw/`) is CC BY 4.0 - see
`LICENCE-DONNEES.md`. Code (`pipeline/`, `site/`) is MIT - see `LICENSE`.
