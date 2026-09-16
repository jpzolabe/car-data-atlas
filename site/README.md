# site/

The Astro site. Six pages so far:

- `/` - still a placeholder for the real home page in `docs/plan.md` §2.2
  (that needs the headline-card/lead-story/theme-grid structure), but it
  links everywhere real and carries the search box
- `/population/`, `/prix/` - real indicator pages, reading from
  `src/data/*.json`, which `pipeline/export_*.py` materialize from `data/`
- `/sources/`, `/methode/`, `/a-propos/` - the supporting pages from
  `docs/plan.md` §2.7/§2.8/§2.1

## Running locally

```
cd site
pnpm install
pnpm dev       # local dev server - search is inert here, see below
pnpm build     # static build to dist/, then runs Pagefind indexing
pnpm preview   # serve the real built output, including working search
```

## Search

`/` is the only page with any client JS, per `CLAUDE.md`'s explicit
exception. It's hand-built against Pagefind's raw JS API
(`dist/pagefind/pagefind.js`, ~45 KB), not Pagefind's default UI bundle
(`pagefind-ui.js` + CSS, ~134 KB) - the default bundle is real functionality
but it's styled widget chrome this project's page-weight budget doesn't have
room for. See the script in `src/pages/index.astro`.

**Search only works after a full `pnpm build`** - Pagefind indexes the built
`dist/` output as a build step, so `astro dev` never has an index to query
against. Use `pnpm preview` to test it for real.

## Notes

- `robots.txt` currently disallows all crawling, and every page carries
  `<meta name="robots" content="noindex">` - both are a deliberate pre-launch
  guard so search engines don't index an unfinished, undeployed site. Remove
  both once the site is actually meant to be found (i.e. once it's deployed
  for real and presented as ready, not before).
- No i18n config yet - French-only until the `/en/` mirror actually starts
  (`docs/plan.md` §2.1). See `astro.config.mjs` for the note.
- Page-weight budget (150 KB/page, `CLAUDE.md`) is enforced in CI via
  `check-page-weight.mjs`, run as part of `pnpm build` in
  `.github/workflows/ci.yml`.
- `/methode` and `/a-propos` each have a couple of explicit "à faire" markers
  (a public contact address, an institutional owner) rather than invented
  placeholders - see `docs/plan.md` Part 8 and Phase 5.
