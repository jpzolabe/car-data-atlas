# geo/

GeoJSON boundaries, one file per entity per version — matching the versioning
rule in `data/entities.csv` (a redrawn préfecture is a new entity, so it gets
its own geometry file, the old one is kept).

Nothing here yet. This fills up in Phase 1 once the crosswalk resolves which
boundary source (COD-AB, the 2020 decree, etc.) is canonical for each level —
see `CLAUDE.md`'s administrative-geography table and `docs/plan.md` §4.1.

## Convention (planned)

```
geo/raw/{entity_id}.geojson          # as fetched, full precision
geo/simplified/{entity_id}.geojson   # mapshaper-simplified, for rendering
```

Keep raw and simplified separate; never overwrite raw. Simplified output must
stay under the 50 KB per-map budget in `CLAUDE.md`'s performance budget
section — checked in CI once maps exist.
