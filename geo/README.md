# geo/

GeoJSON boundaries, one file per entity per version - matching the versioning
rule in `data/entities.csv` (a redrawn préfecture is a new entity, so it gets
its own geometry file, the old one is kept).

**Filled 2026-09-12** (Phase 4, locator maps): the country outline plus all
20 préfectures, built by `pipeline/build_geo_prefectures.py` from the COD-AB
v02 snapshot already fetched for the crosswalk
(`raw/cod-ab-caf/2026-09-05/caf_admin_boundaries.geojson.zip`) - no new
fetch needed, just processing already-snapshotted data. Uses the zip's
"_em" (edge-matched) geometries specifically, not the plain admin0/admin1
ones: adjacent préfectures' shared borders line up exactly with no gaps or
overlaps, which plain COD-AB geometry doesn't guarantee. Every préfecture
joined to its entity_id via `adm1_pcode`, checked live against
`data/aliases.csv` - all 20 match exactly.

Sous-préfecture geometry (COD-AB's `admin2_em`) is not built yet - only
country + préfecture, matching the current place-page scope
(`docs/plan.md` Sec2.4).

## Convention

```
geo/raw/{entity_id}.geojson          # as fetched, full precision
geo/simplified/{entity_id}.geojson   # simplified for rendering
```

Keep raw and simplified separate; never overwrite raw. Simplified output must
stay under the 50 KB per-map budget in `CLAUDE.md`'s performance budget
section - the largest file today (the country outline) is ~13 KB.

**One deviation from this file's original plan, worth noting rather than
silently diverging from:** simplification uses `shapely.simplify()`
(Douglas-Peucker, tolerance 0.02° ≈ 2 km), not mapshaper as originally
named here. `shapely` was already an approved pipeline dependency
(`pyproject.toml`); mapshaper would have been a new one, and CLAUDE.md
asks to check before adding any dependency. Same algorithm either way.
