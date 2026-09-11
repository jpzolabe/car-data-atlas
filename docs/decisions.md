# Decisions

## 2026-09-11 — CI silently never ran successfully until checked directly

`docs/plan.md`'s Phase 2 done-criteria requires the site to update "without manual
work," which depends on CI actually running — nobody had checked whether it did.
It hadn't: the one run that existed (triggered by the first push, to `main`) had
failed at `pnpm/action-setup@v4` with "No pnpm version is specified," and CI wasn't
even configured to trigger on `develop`, where all the actual work was happening.

Two real bugs, not one: (1) no pnpm version pinned anywhere — fixed via
`packageManager` in `site/package.json`. (2) `pnpm/action-setup@v4` reads
`package.json` from the **repo root** by default, not from wherever a later step's
`working-directory` happens to point — since this repo's `package.json` lives in
`site/`, the action never found the version even after fix (1). Needed the action's
own `package_json_file: site/package.json` input to point it at the right file.

**How to apply:** a green CI badge or "it ran once" is not the same as "CI actually
checks what gets pushed" — check the actual run logs, not just that a workflow file
exists. Any GitHub Action with a "look for a file in the working directory" default
needs an explicit path when the relevant file isn't at the repo root, which is the
case for every Node-related step here (site/ is not the repo root).

Why the constraints in `CLAUDE.md` and `docs/plan.md` exist, so a future change to
any of them is a deliberate decision rather than an accidental drift. Newest first.

## 2026-09-04 — PDF-to-Claude-API extraction paused

Irregular statistical-yearbook PDFs (the ones `pdfplumber` can't parse cleanly) were
going to fall back to the Claude API on page images. That path is paused: it's the
only piece of the stack with a marginal per-run cost, and it adds a real risk
(an LLM transposing digits in a table) that needs its own review discipline before
it's worth turning on. Until revisited, PDFs that don't parse cleanly with
`pdfplumber` are logged as a gap (in `data/unresolved.csv` or a theme's
*ce qui n'est pas mesuré* section) rather than extracted by any other means.

**How to apply:** don't add an LLM call to the pipeline without this decision being
revisited explicitly. If it is revisited, extracted rows must be spot-checked against
the source PDF before entering `data/` — treat them as higher-risk than a PR from a
scripted parser, not the same.

## Zero client JS / 150 KB page budget

The primary user (a journalist at RJDH, on the priority list ahead of researchers)
is assumed to be on a slow connection in Bangui, not a fast one elsewhere. This is
the single highest-leverage constraint in the project for actually reaching that
user. It is checked in CI, not just aspired to.

**How to apply:** don't relax it to make a component easier to build. If an
interactive feature seems to need client JS, the default answer is to find the
zero-JS version first (see: `<details>`/`<summary>` for the multi-source disclosure,
which needs no JS at all).

## Astro over a simpler static-site generator

The project isn't using Astro's main differentiator (islands / partial hydration) —
every page today is fully static, which a simpler tool like Eleventy would also
produce. Astro was chosen anyway because of the open question in `docs/plan.md`
Part 8.3: whether to leave room for one interactive island later. Astro gives that
escape hatch at zero cost today (it behaves identically to a simpler SSG while
unused) without a framework migration if the answer to that question ever changes.

**How to apply:** don't reach for islands/hydration to solve a problem that a static
page or a native HTML element (`<details>`, forms, anchors) already solves.

## CSVs in git, DuckDB for joins, no database server

Abandonment is the highest-severity risk in `docs/plan.md` Part 7, with named
precedents (NADA frozen since 2021, Data Africa since ~2016, both still online and
still looking alive). A database server is one more thing that can silently stop
running. Static files under version control can't go down; DuckDB gives real SQL
joins over those files at build/pipeline time without a server to maintain.

**How to apply:** if a feature seems to need a database, look for the build-time or
query-time DuckDB answer first. Don't add a server to solve a data-shape problem.

## Charts: build-time SVG, generation method still open

No charting library ships to the client — this part is fixed, and is the same
zero-JS reasoning as above applied specifically to charts. What's still open is
*how* the SVG gets generated at build time: Observable Plot running server-side
(via a DOM shim like `linkedom`) versus a small hand-written SVG-templating module.
Given the site has a fixed catalog of five chart types (line, horizontal bar,
population pyramid, locator map, choropleth) rather than open-ended charting needs,
hand-rolled generation may end up simpler and give more direct control over French
number formatting and the freshness-colour system. Decide with a small spike of both
before committing, in Phase 2.

**How to apply:** don't treat "Observable Plot" as settled just because it's named
in `CLAUDE.md` — the non-negotiable part is "no client-side charting library," not
the specific build-time tool.

## Two-language pipeline (Python) / site (Node) split

Python has the strongest tooling for the GIS- and PDF-heavy ETL work (GeoPandas,
shapely, pdfplumber have no equivalent-quality JS counterpart). Astro/Node has the
strongest tooling for static-output, i18n-aware page generation. Forcing either
language to do both jobs would be worse in both directions than maintaining two
toolchains for a solo maintainer.

**How to apply:** the handoff between them is CSV/Parquet artifacts materialized by
the Python pipeline (via DuckDB), consumed by Astro content collections — not a
live API call from the site into Python at build or request time.

## CC BY 4.0 for data, MIT for code

Data licence matches ICASEES's own licence for the underlying data this project
republishes and adds provenance/geography scaffolding around — keeping the same
licence keeps the attribution chain simple and avoids a licence mismatch on
redistribution. MIT for code is a low-friction default for a project that wants
outside contribution and reuse (the crosswalk in particular is meant to be useful to
the World Bank, OCHA and ICASEES independent of the rest of the site).

## Entities are never mutated; a new geography version is a new entity

Administrative geography is temporal data (`CLAUDE.md`: "UNHCR dashboards were still
publishing against 16 préfectures in 2023"). Mutating an existing entity when a
préfecture is redrawn would silently corrupt every historical join against the old
boundary. A new `entity_id` with its own `valid_from` keeps old observations
correctly attached to the geography that was actually in effect when they were
recorded.

## `unresolved.csv` is a deliverable, not a failure log

Per `CLAUDE.md` build order step 1 and `docs/plan.md` §3.6: cases the crosswalk
can't resolve are published, not hidden. Publishing them invites correction from
people closer to the source data than the project maintainer, and is honest about
the actual state of the crosswalk rather than presenting it as more complete than
it is.

## Authority ranking: census > survey > admin data > modelled > unattributed, ties by observation date

Stated in `CLAUDE.md` and `docs/plan.md` §2.8 as a *published, written* rule
specifically so the site's default figure is never silently picked by the
maintainer's judgement alone — a reader can check the rule and see why a given
source won. Ties are broken by recency of **observation**, not recency of
**publication**, because a re-published old estimate shouldn't outrank a genuinely
newer one just because it appeared on the web more recently.
