# raw/

Immutable snapshots of everything fetched from a file-based external source
(a PDF, an HTML page, a downloadable dataset file) - one subdirectory per
`source_id`, growing as new sources are added. A source that's a live API
with no file to snapshot (most World Bank/UNESCO/WHO/UNICEF/IMF indicators)
has no directory here; `data/sources.csv` is the full, current list of every
source either way.

## Convention

```
raw/{source_id}/{iso_date}/
```

`source_id` matches a row in `data/sources.csv`. `iso_date` is the date the
snapshot was retrieved (`retrieved_at`), not the date the source published it.

## Rules

- **Never edit a file under `raw/` after it's committed.** If a fetch was
  wrong, take a new snapshot under a new date rather than correcting the old
  one in place.
- **Never delete a snapshot.** When an extraction pipeline improves, re-run it
  against the existing raw snapshot rather than re-fetching.
- Extracted/normalised output derived from a raw snapshot belongs in `data/`
  (via the pipeline), not here.
