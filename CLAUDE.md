# Projet - BêAfrîka Data

A public reference work about the Central African Republic: national figures across
themes, with the ability to drill down to région / préfecture / sous-préfecture.
French-first. Built by one person. Publicly named "BêAfrîka Data" as of 2026-09-13
(was "Données RCA"); "RCA" stays fine as informal shorthand in code/docs/commits.

**Scope note (2026-09-05):** commune and localité were originally in scope but are
dropped for now - the current authoritative geography source (COD-AB v02) doesn't
publish anything finer than sous-préfecture, and chasing a separate commune-level
source is deprioritized rather than blocking Phase 1. Sous-préfecture is the current
floor everywhere below. Revisit if a good commune source turns up.

## How to read this document

This is a set of working defaults for a solo-maintained project, not fixed law. It
exists so decisions don't have to be re-litigated from scratch every session - treat
it as the current best answer, not an unquestionable one, and every specific number
or restriction below (page-weight targets, the client-JS budget, indicator counts,
whatever) is a recommendation tuned for where the project was when it was written,
not a rule to defend for its own sake. When something here stops fitting reality,
change it here rather than quietly working around it, and note why in
`docs/decisions.md` if the reason isn't obvious. The one thing below that stays a
hard line regardless is not fabricating values outright - see rule zero - everything
else, including how strictly rule zero's *verification* half is enforced pre-launch
(see "v1 vs. later" below) and the client-JS line in the performance budget below, is
a judgment call that can flex with where the project actually is.

## Rule zero: never invent data

Never fabricate a value, a source, a date, a place name, or an administrative code -
not as a placeholder, not to fill a template, not to make a page render, not in an
example. Placeholder numbers survive into production and this project's entire value
is that its numbers can be trusted.

If a value is unknown: leave it null, let the page show the gap, and say so. If sample
data is genuinely needed for a test, put it under `fixtures/` with obviously fake
values (e.g. `999999`) and never in `data/`.

**v1 vs. later.** "Never fabricate" is permanent. How hard we chase full legal
clearance and cross-source veracity on every figure *before using it at all* is not -
for v1, real data from a real, cited source can be used even if its licence terms
aren't fully resolved or it hasn't been cross-checked against every other source yet.
The difference that matters: a number that came from somewhere real can be corrected
once we look closer; a number we made up can't be, because there's nothing underneath
it to correct. Track what's unverified or unresolved-licence in
`docs/verification-debt.md` as it comes up, and clear that list before the site is
presented as final or promoted as authoritative - it isn't a permanent exemption, it's
a queue.

## What this is

**A reference work about places and themes in CAR - not a data portal, not a dashboard.**

One-line description:
> Explore the Central African Republic - what the data says, where it comes from,
> and what nobody has measured yet.

Three non-negotiable principles:

1. **Provenance.** No number is ever displayed without its source, its date, and the
   geographic level it refers to.
2. **Freshness is visible.** A 2009 figure must look different from a 2025 figure on
   the page. Never present stale data with the same confidence as current data.
3. **Gaps are content.** Where nothing has been measured, say so explicitly. This is a
   feature, not an omission.

## Architecture: country → theme → place

Entry point is the **national** picture, not the sous-préfecture. Reasons: data coverage is
far denser nationally (GDP, CPI, trade, exam results exist nationally and not by
sous-préfecture), and curious readers arrive at the country before the sous-préfecture.

- **Home** - national headline figures across themes
- **Theme pages** - one per theme (population, économie, santé, éducation,
  agriculture, prix, infrastructures - 7 in total, all built as of 2026-09-12).
  National series over time, charts, sources, what is and isn't measured. Each
  offers a breakdown to descend. Once a theme has more than one or two indicators:
  lead with one orienting headline figure before any breakdown, and group/order
  indicators by logical sequence (e.g. a causal chain) rather than by fetch order
  or an arbitrary list - see docs/plan.md §2.3. Prix and agriculture are each a
  full page in their own right, but both are also conceptually part of the
  economy (most real economic dashboards fold prices and sector breakdowns into
  one view) - économie's own page carries a brief summary card and link for each,
  without merging the pages or moving their URLs.
- **Place pages** - a single place across all themes. Reached by drilling down or by
  direct search.

**Each indicator has its own geographic floor.** Population reaches sous-préfecture. Food
prices stop at the market (a point, not an area). GDP stops at the nation. The UI must
show how deep each indicator goes rather than offering breakdowns that return nothing.

## Handling conflicting sources

Most indicators have one source. A few (population especially) have several that
disagree. Rule:

- Show the **most authoritative** figure by default, plainly.
- Beside it, a small "N sources" link. Clicking expands in place to show every figure
  with its date and label (provisoire / projection / modélisé / source non citée) and
  the spread between them.
- The authority ranking is a **published, written rule** - a page on the site.
  Roughly: national census > national survey > international modelled estimate >
  unattributed portal figure. Ties broken by recency.

## Domain facts that matter

*Compiled September 2026. Figures, platform states and survey timings below were
accurate then and go stale. Re-verify against the source before relying on any of
them, especially the census results, which were provisional.*

**RGPH-4 (4th census).** Enumeration late 2025; provisional results published
~23 August 2026. Total 6,656,269 (3,312,532 M / 3,343,737 F), density 10.7/km².
Marked *données non encore validées* - always mirror that caveat. First census since
2003. This revises every per-capita statistic about CAR downward, since most sources
still assume ~5.5M.

**Administrative geography does not agree between sources.** This is the core technical
problem and the project's reason to exist:

| Source | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| OCHA COD-AB, **v02** (verified 2026-09-05, see below) | 20 préfectures | 85 sous-préfectures | none in v02 |
| **Loi n°21.001 du 21 janvier 2021** (promulgated; bill adopted 10 Dec 2020) | 20 préfectures | 85 sous-préfectures | 175 communes |
| Older survey documentation | 16 préfectures | 66 sous-préfectures | ~174 communes |
| RGPH-4 reporting | 7 régions | - | - |

**Correction, 2026-09-05:** the COD-AB row above was wrong when this file was first
written - it described an older COD-AB edition (17/72/175/860, sourced from
ACTED/ITOS) that this project never actually verified against the live dataset. The
live HDX listing (`cod-ab-caf`) is now **version 02**, last reviewed 2026-03-06, and
states 20 préfectures / 85 sous-préfectures - it has apparently migrated toward the
2020 decree's structure since this table was first drafted. It also **no longer
publishes a commune or localité layer at all** (its admin-points sheet is just
country + préfecture + sous-préfecture centroids, 1+20+85=106, nothing finer). The
85-vs-84 sous-préfecture gap against the initially-reported decree figure is now
resolved (2026-09-11): the law was promulgated over a month after the reported
adoption, as **Loi n°21.001 du 21 janvier 2021**, with the final figure of 85 -
see `docs/verification-debt.md`'s Resolved section. This project's
`data/entities.csv`/`aliases.csv` for
pays/préfecture/sous-préfecture are built from this v02 snapshot
(`pipeline/build_entities_cod_ab.py`). Commune/localité are dropped from project
scope for now rather than chased via a separate source - see the scope note above.

UNHCR dashboards were still publishing against 16 préfectures in 2023. **Administrative
geography is temporal data** - entities need valid_from / valid_to, and a crosswalk
mapping every source's names and codes to canonical IDs.

**Sources.**
- ICASEES (national statistics office) - publishes under **CC BY 4.0**. Site
  icasees.org. Active: MICS7 launched Aug 2026, EHCVM2 in field, national accounts
  2019–2021 published, GDP rebasing to 2019 base underway, monthly CPI (IHPC) on a
  published dissemination calendar. Education statistical yearbooks available in Excel.
- ICASEES NADA microdata catalogue - 26 surveys, 1,607 variables, frozen since May 2021,
  newest study 2019. Microdata access requires DG authorisation.
- car.opendataforafrica.org - AfDB / Knoema platform. Maintained but entirely
  JavaScript-dependent and login-prompting. Includes the IMF e-GDDS National Summary
  Data Page (launched May 2025).
- HDX - WFP food prices, UCDP conflict events, DHS, IPC, COD-AB boundaries, COD-PS
  population (2003 census projected to 2015), UNHCR displacement, World Bank and WHO
  indicators, a 100m walking-travel-time-to-health-facility raster.
- OpenStreetMap - coverage largely from the 2013–14 HOT crisis activation.

**Check redistribution rights per source.** ACLED and DHS have licence restrictions
that are not as open as their presence on HDX implies, and this turns out to be more
common than that - e.g. COD-AB itself currently carries a "humanitarian purposes
only" usage restriction on its HDX listing, discovered when actually fetched rather
than assumed from its reputation as "the humanitarian sector standard." **For v1,
this doesn't block using a source** - log it in `docs/verification-debt.md` with what
the restriction actually says, use what's needed to keep building, and resolve
properly (redistribution swapped for citation, alternate source, or an actual
licence conversation) before the data is presented as a final public v1, not before
every use.

**Political sensitivity.** Census results feed representation and resource allocation.
Publish provisional figures with their caveat; do not present them as settled.

## Stack

- **Astro** - static site, zero JS by default. Content collections drive place and
  theme pages. Built-in i18n, French primary.
- **Charts: build-time SVG.** Observable Plot running in Node during the build, output
  static SVG into the page. No chart library ships to the client. This is the decision
  that makes the site usable on 3G in Bangui - non-negotiable without a strong reason.
- **Maps:** build-time SVG from GeoJSON simplified with mapshaper. Defer interactive
  maps; if needed later, MapLibre GL + PMTiles (single-file archive, no tile server).
- **Pagefind** - static search index.
- **Cloudflare Pages** - hosting.
- **Python pipeline** - pandas, httpx, GeoPandas, shapely.
- **PDF extraction** - pdfplumber for text-based tables; Claude API with page images for
  irregular statistical-yearbook layouts. Always keep the raw PDF alongside the
  extraction output so extractions can be re-run.
- **DuckDB** - joins and validation over the CSVs. No database server.
- **GitHub Actions** - cron per source: fetch, snapshot, transform, open a PR if data
  changed. Human review before merge.
- **Umami or Plausible** - lightweight analytics. Key question to answer: is anyone in
  CAR actually reading this?

## Data layout

CSVs in git are the source of truth.

- `raw/` - immutable source snapshots, never overwritten
- `data/entities.csv` - every administrative unit ever: id, level, parent, valid_from,
  valid_to
- `data/aliases.csv` - every spelling, accent variant and source code → entity id
- `data/sources.csv` - source, licence, geography vintage, update cadence
- `data/observations.csv` - long format: entity_id, indicator_id, period, value, unit,
  source_id, retrieved_at
- `geo/` - GeoJSON per entity per version
- Frictionless datapackage JSON for metadata

## Performance budget

Concrete targets, checked in CI - the 3G-in-Bangui constraint made testable:

- Any page: under 150 KB total transferred, uncompressed, including HTML, CSS, fonts,
  SVG and images
- Client JavaScript: the default is 0 KB on place and theme pages, and that default
  stands for anything that would ship a framework, a chart library, or client-side
  data fetching - none of that belongs on this site regardless of size. It's not a
  hard 0, though: a few hundred bytes of hand-written vanilla JS for a real,
  justified piece of progressive enhancement is fine (the search box on the home
  page; the dark-mode toggle, sitewide - inline, no dependencies, reads/writes one
  stored preference). Each such exception should be small, dependency-free, and
  written down in `docs/decisions.md` when added - that's what keeps this a short,
  deliberate list instead of a drift back toward "just add a script."
- No web fonts beyond one weight-variable family, or use system fonts
- Simplified GeoJSON per map: under 50 KB

Fail the build if a page exceeds budget rather than shipping it.

## Conventions

- Python 3.12, `uv` for dependency management, `ruff` for lint and format
- Node with `pnpm`
- **Code, comments, commit messages, variable names, and file names in English.**
  Only user-facing content is French.
- Indicator IDs: lowercase snake_case, stable forever once published
  (`population_totale`, `prix_manioc_kg`, `taux_achevement_primaire`)
- Entity IDs: stable, never reused, never renumbered when geography changes - a new
  version of a sous-préfecture is a new entity with its own valid_from
- Conventional commits (`feat:`, `fix:`, `data:`)
- **Ask before adding any dependency.** The maintenance surface is the main risk to
  this project.

## Quality gates (run in CI)

- Every value has a source_id that exists in sources.csv
- Every entity_id resolves in the crosswalk
- No series jumps more than n% without an explicit flag
- Fail the build rather than publish unverified data

**v1 note:** these are the target gates for when the site is presented as a finished
public product. While actually building v1, "unverified" means *has a real source
attached but hasn't been cross-checked or legally cleared yet* - that's fine, log it
in `docs/verification-debt.md`, keep building. It does not mean a value with no
source at all - that's rule zero, and that one doesn't flex.

## Do not

- Do not use CKAN, a database server, Docker orchestration, a headless CMS, or a React SPA.
- Do not build dashboards, gauges, or composite "vulnerability scores" - they require
  silently picking one contested figure over others.
- Do not rebuild what exists: the World Bank 2023 Poverty Assessment already did
  access-to-services analysis; the travel-time raster already exists on HDX.
- Do not position this as a competitor to ICASEES. It is a layer that makes their
  CC BY 4.0 output usable. Their attribution is prominent on every page.
- Do not ship client-side JavaScript for charts.

## Build order

1. **Geography crosswalk**, published as a licensed CSV with documentation - before any
   website. Useful to the World Bank, OCHA and ICASEES on day one.

   *Done when:* every administrative unit appearing in COD-AB, the 2020 decree,
   RGPH-4 régions and ICASEES publications has a canonical entity ID; every source's
   name and code for it resolves through `aliases.csv`; the mapping between the
   7 régions and the préfectures is explicit; every entity has valid_from and
   valid_to; unresolved cases are listed in `data/unresolved.csv` rather than guessed;
   and the whole thing has a README and a licence.

2. **National theme pages**, 5 indicators. No crosswalk needed to descend yet.
   This is a shippable site.
3. Descend to préfecture, then sous-préfecture. Widen to 20–25 indicators.
4. Coverage view - the map of what is and isn't known.

## Voice

French, plain, short sentences. One generated sentence accompanies each chart:
*« En 2025, la population de la préfecture de l'Ouaka était de 386 400 habitants,
selon les résultats provisoires du RGPH-4. »*

**"Generated" means deterministic templates filled from the data at build time. No
model call in the pipeline and none on the page.** The same data must always produce
the same sentence, and every sentence must be traceable to a template plus values.

Templates must handle French agreement and plurals correctly, state only what the data
says, and never assert causation or a trend where there is a single observation. Where
a figure is provisional or old, the sentence says so.

The sentence templates are the hardest craft problem in the project - a bad template
produces 250 pages of stilted French, and that is what readers will judge.

**No em-dashes ("—"), anywhere** - reader-facing copy, code comments, docs, commit
messages, all of it. Use a plain hyphen ("-") or a semicolon (";") instead, whichever
reads better in context.
