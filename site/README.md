# site/

The Astro site. 14 page templates, 33 built pages:

- `/` - the real home page: headline population figure, a secondary ticker
  of other themes, the theme grid, and the search box.
- `/population/`, `/prix/`, `/economie/`, `/education/`, `/sante/`,
  `/infrastructures/`, `/agriculture/` - the seven theme pages, reading from
  `src/data/*.json`, which `pipeline/export_*.py` materialize from `data/`.
- `/lieux/` - the place-browsing index, grouped by région.
- `/lieux/prefecture/[slug]` - one page per préfecture (20 built), each with
  a locator map, headline population figure, régional comparison, and a
  per-theme freshness table.
- `/sources/`, `/methode/`, `/donnees/`, `/a-propos/` - the supporting pages
  (source register, methodology, bulk downloads, about).

## Running locally

```
cd site
pnpm install
pnpm dev       # local dev server - search is inert here, see below
pnpm build     # static build to dist/, then runs Pagefind indexing
pnpm preview   # serve the real built output, including working search
```

## Client JS

Two sitewide exceptions to the project's zero-client-JS default, both small
and dependency-free:

- **Search**, on `/` only. Hand-built against Pagefind's raw JS API
  (`dist/pagefind/pagefind.js`, ~45 KB), not Pagefind's default UI bundle
  (`pagefind-ui.js` + CSS, ~134 KB) - the default bundle is real functionality
  but it's styled widget chrome this project's page-weight budget doesn't have
  room for. See the script in `src/pages/index.astro`.
- **Dark-mode toggle**, on every page (`ThemeInit.astro`, `ThemeToggle.astro`)
  - inline, no dependencies, reads/writes one stored preference.

**Search only works after a full `pnpm build`** - Pagefind indexes the built
`dist/` output as a build step, so `astro dev` never has an index to query
against. Use `pnpm preview` to test it for real.

## Notes

- `robots.txt` currently disallows all crawling, and every page carries
  `<meta name="robots" content="noindex">` - both are a deliberate pre-launch
  guard so search engines don't index an unfinished, undeployed site. Remove
  both once the site is actually meant to be found (i.e. once it's deployed
  for real and presented as ready, not before).
- No i18n config yet - French-only until an `/en/` mirror actually starts.
  See `astro.config.mjs` for the note.
- Page-weight budget (150 KB/page) is enforced in CI via
  `check-page-weight.mjs`, run as part of `pnpm build` in
  `.github/workflows/ci.yml`.
- `/methode` and `/a-propos` each have a couple of explicit "à faire" markers
  (a public contact address, an institutional owner) rather than invented
  placeholders.
