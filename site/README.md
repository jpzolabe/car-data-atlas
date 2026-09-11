# site/

The Astro site. Currently one placeholder page (`src/pages/index.astro`)
proving the build chain works — the real home page, theme pages and place
pages come in Phases 2–4 (`docs/plan.md` Part 5).

## Running locally

Requires Node and `pnpm` — neither is installed on this machine yet. Once
available:

```
cd site
pnpm install
pnpm dev       # local dev server
pnpm build     # static build to dist/
pnpm preview   # serve the built output locally
```

## Notes

- `robots.txt` currently disallows all crawling — this is a Phase 0
  placeholder, not the real site. Remove that once there's something worth
  indexing.
- No i18n config yet — French-only until the `/en/` mirror actually starts
  (`docs/plan.md` §2.1). See `astro.config.mjs` for the note.
- No client JS anywhere, no chart/search/map libraries installed yet — those
  arrive in Phase 2 alongside the first real pipeline, one dependency at a
  time, per `CLAUDE.md`'s "ask before adding any dependency."
- Page-weight budget (150 KB/page, CLAUDE.md) isn't enforced in CI yet since
  there's no real page to check against — that check lands with the CI update
  in Phase 2.
