# raw/

Immutable snapshots of everything fetched from an external source. Nothing
here yet — this fills up starting in Phase 1 (the geography crosswalk fetches:
COD-AB, COD-EM, COD-PS, ICASEES cartography tables, OSM boundaries).

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
