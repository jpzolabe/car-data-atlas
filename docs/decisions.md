# Decisions

## 2026-09-14 - Chart hover values: native SVG `<title>` tooltips, not a JS tooltip

User feedback: hovering over any chart showed nothing - every line chart on
the site is a static `<polyline>` with no per-point markers, titles, or JS.
Two ways to fix it were considered: (1) a small `<circle>` per data point
wrapped in `<title>`, giving the browser's own tooltip for free, zero added
client bytes; (2) a small hand-written hover script (track mouse position,
find the nearest point, show a custom-styled floating tooltip) - nicer UX
(no native-tooltip delay, works styled, could support touch), but a new
client-JS exception in the same category as the dark-mode toggle/search box,
needing to be logged here and wired into every chart individually since
there's no shared chart component.

Went with (1), consistent with CLAUDE.md's zero-client-JS-for-charts rule
being the default answer before reaching for JS. Added to every polyline/
sparkline across population, éducation, santé, économie, infrastructures
and agriculture (population's ranked-préfecture bar chart already prints
its value as visible text next to each bar, so it didn't need this).

**`prix.astro` was deliberately left out.** Its series are monthly, not
annual: the main IHPC chart alone has 136 points, and the 5 market-price
sparklines (Bangui since 2004) run 126-268 points each - about 1,585 points
total across the page's charts. Measured directly before deciding: adding
one `<circle>`+`<title>` per point there costs roughly 150 bytes each once
Astro's own scoped-style attribute is counted, pushing `/prix/` from 64.8 KB
to 296.8 KB - a hard fail against the 150 KB budget, not a close call. Every
other theme's series tops out at 45 points (éducation's completion/
out-of-school disclosure indicators), where the same technique costs a few
KB, not hundreds - confirmed by building and running
`site/check-page-weight.mjs` after the change, not assumed safe from the
main chart's cost alone.

**How to apply:** if prix's monthly charts get hover values later, this
same per-point `<circle>+<title>` technique is not the way - option (2)
above (a small shared JS tooltip driven by one compact embedded data array)
is the one that scales to dense series, since it doesn't repeat per-point
XML tag overhead. Re-check page weight after any change that adds markup
per data point, especially on a page with a long series - the cost model
breaks down well before 150+ points, not gradually.

`éducation.astro` is worth watching: it's now at 144.3 KB (was 89.5 KB),
the least headroom of any page under the budget, entirely from its six
45-point disclosure charts. Adding another éducation indicator with a long
series, or lengthening an existing one, could tip it over - check page
weight before assuming there's room.

## 2026-09-12 - Theme pages built flat, not under /themes/ as the sitemap specifies

`docs/plan.md`'s site map puts theme pages under a `/themes/` prefix
(`/themes/population`, `/themes/prix`, etc.), separate from place pages under
`/lieux/`. The first two real pages were built flat instead (`/population`,
`/prix`), matching the flat top-level pages (`/sources`, `/methode`) rather
than the plan's nested structure - not a deliberate choice, just what
happened. Noticed while adding a third theme page (`/infrastructures`).

**How to apply:** kept it flat for this third page too, to stay internally
consistent (all existing theme pages flat) rather than create a third,
mixed pattern (some flat, some nested) which would be worse than either
option alone. A bulk rename to match the plan's `/themes/` structure is
still on the table - cheap now (3 pages, no public URLs exist yet since
Cloudflare isn't connected), much more annoying once `/lieux/` place pages
exist and there are real inbound links. Revisit before Phase 4 (descending
to place pages) rather than after.

**Resolved 2026-09-12, all 7 theme pages built - kept flat, `docs/plan.md`
updated to match instead of renaming.** Two things tipped it: the plan's
own site map already had `/sources`, `/methode`, `/donnees` and `/a-propos`
flat, so only theme pages getting a prefix was itself the odd one out, not
the consistent choice; and `/lieux/` already has its own namespace for
place pages, so theme pages don't need a prefix to avoid colliding with
it. Shorter URLs are also a small real win for the sharing case `docs/plan.md`
Part 7 names explicitly (Facebook cards, journalist embeds). Still fully
reversible later if it turns out to matter once place pages exist and start
cross-linking into themes - nothing about Phase 4 depends on this either way.

## 2026-09-11 - CI silently never ran successfully until checked directly

`docs/plan.md`'s Phase 2 done-criteria requires the site to update "without manual
work," which depends on CI actually running - nobody had checked whether it did.
It hadn't: the one run that existed (triggered by the first push, to `main`) had
failed at `pnpm/action-setup@v4` with "No pnpm version is specified," and CI wasn't
even configured to trigger on `develop`, where all the actual work was happening.

Two real bugs, not one: (1) no pnpm version pinned anywhere - fixed via
`packageManager` in `site/package.json`. (2) `pnpm/action-setup@v4` reads
`package.json` from the **repo root** by default, not from wherever a later step's
`working-directory` happens to point - since this repo's `package.json` lives in
`site/`, the action never found the version even after fix (1). Needed the action's
own `package_json_file: site/package.json` input to point it at the right file.

**How to apply:** a green CI badge or "it ran once" is not the same as "CI actually
checks what gets pushed" - check the actual run logs, not just that a workflow file
exists. Any GitHub Action with a "look for a file in the working directory" default
needs an explicit path when the relevant file isn't at the repo root, which is the
case for every Node-related step here (site/ is not the repo root).

Why the constraints in `CLAUDE.md` and `docs/plan.md` exist, so a future change to
any of them is a deliberate decision rather than an accidental drift. Newest first.

## 2026-09-04 - PDF-to-Claude-API extraction paused

Irregular statistical-yearbook PDFs (the ones `pdfplumber` can't parse cleanly) were
going to fall back to the Claude API on page images. That path is paused: it's the
only piece of the stack with a marginal per-run cost, and it adds a real risk
(an LLM transposing digits in a table) that needs its own review discipline before
it's worth turning on. Until revisited, PDFs that don't parse cleanly with
`pdfplumber` are logged as a gap (in `data/unresolved.csv` or a theme's
*ce qui n'est pas mesuré* section) rather than extracted by any other means.

**How to apply:** don't add an LLM call to the pipeline without this decision being
revisited explicitly. If it is revisited, extracted rows must be spot-checked against
the source PDF before entering `data/` - treat them as higher-risk than a PR from a
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

The project isn't using Astro's main differentiator (islands / partial hydration) -
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

No charting library ships to the client - this part is fixed, and is the same
zero-JS reasoning as above applied specifically to charts. What's still open is
*how* the SVG gets generated at build time: Observable Plot running server-side
(via a DOM shim like `linkedom`) versus a small hand-written SVG-templating module.
Given the site has a fixed catalog of five chart types (line, horizontal bar,
population pyramid, locator map, choropleth) rather than open-ended charting needs,
hand-rolled generation may end up simpler and give more direct control over French
number formatting and the freshness-colour system. Decide with a small spike of both
before committing, in Phase 2.

**How to apply:** don't treat "Observable Plot" as settled just because it's named
in `CLAUDE.md` - the non-negotiable part is "no client-side charting library," not
the specific build-time tool.

## Two-language pipeline (Python) / site (Node) split

Python has the strongest tooling for the GIS- and PDF-heavy ETL work (GeoPandas,
shapely, pdfplumber have no equivalent-quality JS counterpart). Astro/Node has the
strongest tooling for static-output, i18n-aware page generation. Forcing either
language to do both jobs would be worse in both directions than maintaining two
toolchains for a solo maintainer.

**How to apply:** the handoff between them is CSV/Parquet artifacts materialized by
the Python pipeline (via DuckDB), consumed by Astro content collections - not a
live API call from the site into Python at build or request time.

## CC BY 4.0 for data, MIT for code

Data licence matches ICASEES's own licence for the underlying data this project
republishes and adds provenance/geography scaffolding around - keeping the same
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
maintainer's judgement alone - a reader can check the rule and see why a given
source won. Ties are broken by recency of **observation**, not recency of
**publication**, because a re-published old estimate shouldn't outrank a genuinely
newer one just because it appeared on the web more recently.

## UNESCO UIS Data API - endpoint found via its own error message, not documentation

Neither the UIS's public docs page (`api.uis.unesco.org/api/public/documentation/`,
a Swagger UI that doesn't render as fetchable text) nor the Python `unesco_reader`
package's own documentation spelled out the actual REST URL. The old bulk-download
pattern (`download.uis.unesco.org/bdds/...`) 404s - UIS has moved off it. Resolved
by requesting `api.uis.unesco.org/api/public/data/indicators` with no query
parameters at all: it returns HTTP 400 with a JSON body naming its own required
parameters (`geoUnit`, `indicator`), which was enough to construct a working call
directly (`?geoUnit=CAF&indicator=CR.1`). No API key required. Worth remembering
as a technique generally: a REST API's own validation error is sometimes a faster
path to its shape than either third-party docs or a wrapper library's source.

## Education widened from 1 to 14 indicators - checked live per indicator, not assumed from the catalogue

CLAUDE.md's own indicator-ID example (`taux_achevement_primaire`) was illustrative,
not a scope limit - stopping at one indicator when the same free, no-key API had
real CAF data across completion, enrollment, retention and literacy would have been
under-building for no real reason. The UIS indicator catalogue
(`/api/public/definitions/indicators`, ~5,000 entries) reports data availability
*globally*, not per country - a candidate indicator can show thousands of records
worldwide and zero for CAF. Every one of the 17 UIS codes actually used here
(`data/sources.csv`, `pipeline/fetch_education.py`) was confirmed by querying
`?geoUnit=CAF&indicator=<code>` directly and checking for non-empty `records` before
being added, not by trusting the catalogue's description. The API accepts a
comma-separated indicator list, so all 17 were fetched in one call.

## Education sources grouped by methodology family, not one row per indicator

`data/sources.csv` has one row per *methodology*, not per indicator: completion
(survey vs. modelled - already had 2 rows for the 1-indicator version, broadened to
cover 3 levels rather than renamed to 6), one row for the 9 administrative/EMIS-style
indicators (enrollment ratios, repetition, survival, out-of-school), one for the 2
literacy indicators. All 14 indicators share one producer and one API endpoint
pattern; a row per indicator would have been 14 near-identical rows saying the same
thing about licence and access method 14 times. The administrative-family row is
honest about what it doesn't know: the API response gives a value and a year, not a
methodology tag, so whether each point is genuinely EMIS-administrative data or
something else per-indicator isn't confirmed - logged in
`docs/verification-debt.md` rather than asserted.

## Out-of-school rate widened again (14 -> 15 indicators) after a real gap was caught

The first widening pass (1 -> 14 indicators) checked completion for a modelled
counterpart (`CR.MOD.*`) but didn't systematically check the other 8
administrative-family indicators the same way -- caught when asked directly
"couldn't you find newer data on education," which prompted re-checking every
family explicitly for a `*.MOD.*` variant rather than trusting the first pass.
Result: out-of-school rate does have one (`ROFST.MOD.1/2/3`, reaching 2025);
enrollment ratios, repetition and survival genuinely don't -- confirmed absent
from the catalogue, not just unfetched. Also found `ROFST.3.CP` (upper
secondary out-of-school), a level the first pass had skipped entirely. All
three out-of-school indicators were moved from the plain
latest-value-plus-series treatment into the same disclosure pattern as
completion (administrative figure as headline, modelled series as the
comparison/chart line) -- `pipeline/export_education_json.py`'s
`build_completion_indicator` was generalized into `build_disclosure_indicator`,
driven by a `DISCLOSURE_CONFIG` dict, rather than duplicated. Lesson for next
time: "checked the API" needs to mean "checked every plausible variant," not
"checked the first indicator code that matched."

## Education page combines two existing patterns instead of inventing a third

`taux_achevement_primaire` has the same shape of disagreement as national
population (a higher-authority but sparse source vs. a lower-authority but dense
one) plus the same shape of "changes over time" as électricité/prix (a real annual
series worth charting). Rather than design a new page pattern, `education.astro`
reuses population.astro's national multi-source `<details>` disclosure block
verbatim in structure, and infrastructures.astro's build-time SVG line chart,
overlaying the 4 real survey points as distinct markers on the denser modelled
line rather than picking one series to show. The disclosure table itself only
lists the 4 survey years paired with the modelled value for those *same* years
(not all 45 modelled years) - comparing every modelled year against one survey
year would conflate "these two sources disagree" with "time has passed," which
is a different, less honest question.

## Education page reordered: one headline figure, then the student's actual path

The 14-indicator version led with three large multi-source disclosure blocks
(all 3 completion levels) immediately after the lede - the page's heaviest
content shown first, with no orienting summary. Two fixes: (1) a lightweight
headline block (one number, one generated sentence, a link down to the full
breakdown) now sits above the category sections, using primary completion -
the single most legible "state of education" figure and the one CLAUDE.md's
own indicator-ID example names. (2) The four categories were reordered from
achievement-first (Achèvement, Scolarisation, Rétention, Alphabétisation) to
the actual causal chain a student goes through: Scolarisation (does a child
enroll) → Rétention et abandon (do they stay, repeat, or drop out) →
Achèvement scolaire (do they finish) → Alphabétisation (the long-run societal
result). Leading with the outcome before the causes that produce it reads
like starting a story at the ending - this generalizes beyond this one page:
default to whatever order lets each section explain what feeds into the
next, not whatever order the data happened to get fetched in.

## Prix widened from 1 to 5 indicators - same file, zero new sourcing

Part of a deliberate pass to bring population/prix/infrastructures up
towards éducation's depth (all three had exactly one indicator). Unlike
éducation's UIS widening, this cost nothing in new sourcing: the IHPC
dashboard file (`pipeline/fetch_ihpc.py`) already downloaded for
`prix_ihpc_global` has 12 COICOP sub-category rows and a published
"Inflation" row that were simply never parsed - `prix.astro`'s own gap-note
already said so. Added the inflation rate plus 3 named sub-categories
(alimentation, santé, transports) - the ones the existing gap-note text
already promised, not an arbitrary subset. `IND11` (Enseignement) was
checked and deliberately skipped: only 76 of 136 months are populated,
unlike every other row's 136/136. `extract_rows()` in `fetch_ihpc.py` was
generalized from one hardcoded row lookup to a config dict
(`INDICATOR_CODES`) so adding a 6th indicator later means one dict entry,
not a new function. The published inflation rate doesn't reconcile with a
naive recomputation from the index - logged rather than silently
reinterpreted, see `docs/verification-debt.md`.

## Infrastructures widened 1 -> 5, JSON/export renamed off "electricite"

Same completion pass as prix. Added 4 World Bank indicators - internet use,
mobile subscriptions, basic drinking water access, basic sanitation access
- each confirmed live for CAF before adding (all 4 have real data through
2022-2024, genuinely fresher than most of education's indicators).
Électricité stays the page's headline/hero (CLAUDE.md's own domain fact
cites it, and it already has an independent MICS cross-check); the other 4
are additive cards below, following the headline-then-breakdown rule.

`pipeline/export_electricity_json.py` / `site/src/data/electricite.json`
were retired in favour of `export_infrastructures_json.py` /
`infrastructures.json` - the old names stopped describing the theme once it
covered more than electricity, and renaming now (before more pages or
scripts came to depend on the old name) was cheaper than renaming later.
`fetch_infrastructures.py` is a new script alongside (not replacing)
`fetch_electricity_access.py`, since the World Bank API takes one indicator
code per URL (unlike UIS's comma-separated list) - four indicators means
four HTTP calls either way, so there was no efficiency reason to merge them
into one file, only a naming one, and the existing electricity fetch script
already works and is untouched.

## Population widened 1 -> 4, last of the three single-indicator themes

Completes the pass started with prix and infrastructures. Added 3 World Bank
indicators -- population growth rate, urban population %, age dependency
ratio -- all confirmed live with genuinely current (through 2025) CAF data.
`population_totale`'s national multi-source disclosure (RGPH-4 census vs.
World Bank estimate) stays the headline; the 3 new ones are additive
"Autres indicateurs" cards below the préfecture breakdown, same pattern as
prix/infrastructures. Unlike those two, the mini sparklines here don't use
a zero-based y-axis (`sMin = min * 0.9` instead of 0) -- these 3 series
move within a narrow band around a nonzero baseline (e.g. dependency ratio
~100%), and a zero-based axis would flatten the line to near-invisible
instead of showing the actual year-to-year movement.

## Santé: first brand-new theme page since the initial 3

Population, prix, infrastructures and éducation all existed before this
session's completion pass; santé didn't exist at all. Built the same way as
the widening passes -- 10 World Bank indicators, each confirmed live for
CAF before adding, grouped into 4 categories ordered by logical sequence
(système de santé -> vaccination -> mortalité et espérance de vie ->
maladies: what resources exist, what prevention happens, what the outcomes
are, disease-specific burden). Espérance de vie is the headline (most
legible single "state of health" figure). No disclosure blocks -- every
indicator has exactly one source so far, unlike éducation's completion/
out-of-school pairs.

One real, deliberately-not-hidden gap: `SH.MED.BEDS.ZS` (hospital beds) only
has 6 data points for CAF, the most recent from 2011 -- genuinely 15 years
stale, not a fetch artifact. Kept anyway (rule zero: real data can be used
even when old) and flagged with the existing "ancien" badge plus an
explicit line in "Ce qui n'est pas mesuré."

Also: the health-facility travel-time-to-nearest-facility raster already
exists on HDX (CLAUDE.md names it explicitly under "Do not rebuild what
exists"). Not ingested here -- linked instead. A raster wouldn't fit this
project's CSV/DuckDB pipeline without real GeoTIFF-handling work anyway,
and CLAUDE.md is explicit that duplicating existing HDX analysis isn't the
point of this project.

## Économie: second brand-new theme, first with non-percentage indicators

Same build as santé -- 10 World Bank indicators, each confirmed live for
CAF before adding, categories ordered production -> commerce extérieur ->
finances publiques -> niveau de vie (how big the economy is, how it trades
and finances itself, how the state finances itself, what it means for
people -- ending on the outcome, not starting there). PIB par habitant is
the headline.

First theme page where not every indicator shares a unit: `pib_total` and
`pib_par_habitant` are US$, not %, unlike every other indicator across
population/prix/infrastructures/éducation/santé so far. Rather than force
a generic "%"-only formatter, `economie.astro`'s `formatValue()` branches
by indicator_id, and `pipeline/sentences.py` gets a dedicated
`sentence_economie_montant()` (billions for the total, plain thousands-
separated dollars for per-capita) alongside the generic
`sentence_economie_rate()` used for the other 8. Also picked a genuinely
new accent color (`--t-eco: #3D6373`, steel blue) rather than reusing
`--ochre` (`#B8790F`), which is already the site-wide semantic color for
"estimated" badges -- a theme's brand color colliding with an existing
semantic color would have been confusing on every page, this one included.

Two real gaps flagged, not hidden: `taux_pauvrete` only has 3 data points
total (1992, one intermediate year, 2021 - depends on infrequent household
surveys), and `recettes_publiques_pib` stops at 2021. CLAUDE.md also notes
ICASEES has its own GDP rebasing (2019 base) underway - these World Bank
figures haven't been cross-checked against that once it's published; see
`docs/verification-debt.md`.

## Agriculture: third and last brand-new theme -- all 7 sitemap themes now exist

Same build as santé/économie: 9 World Bank/FAO indicators, each confirmed
live for CAF before adding, categories ordered terres et ressources (what
land exists to farm) -> production (what's grown on it) -> emploi et
alimentation (what it means for people). Emploi agricole (66% of total
employment) is the headline -- the single most characteristic fact about
CAR's economy, not just the theme's most legible number.

Third unit family after économie's %/US$ split: this page has %, "indice"
(food production index, base 2014-2016=100), and kg/ha (cereal yield,
fertilizer consumption). `formatValue()` branches by indicator_id again,
same pattern as `economie.astro`.

Caught the same class of precision bug as the earlier French-agreement
fixes, just numeric instead of grammatical: `consommation_engrais`'s real
value (~0.044 kg/ha) rounds to a misleading "0,0" at the 1-decimal
precision every other indicator uses. Fixed by adding a per-indicator
decimal-places field to `AGRICULTURE_LABELS` in `pipeline/sentences.py`
(default 1, this one 3) rather than forcing one precision on every
indicator regardless of its actual magnitude -- and matched the same fix
in `agriculture.astro`'s card display, so the visible number and the
generated sentence don't contradict each other.

This is also, notably, the richest and freshest of the three new themes --
no genuinely stale indicator, unlike santé's 2011 hospital-bed figure or
économie's 3-point poverty series. Worth remembering when thinking about
what "45 minutes of research per theme" actually buys: some domains
(health workforce, poverty surveys) are inherently harder to measure
frequently than others (agriculture, tracked continuously by FAO/remote
sensing) -- the staleness pattern reflects the underlying measurement
reality, not inconsistent effort.

**All 7 sitemap themes now exist: population, prix, infrastructures,
éducation, santé, économie, agriculture - 58 indicators total.**

## Raw figures alongside rates - checked for a real published one before computing anything

User feedback: rates alone were hiding scale across the three newest themes
(0.074 doctors per 1,000 people doesn't land like "532 doctors nationally"
does). Fixed per-theme, in order of preference: (1) a real published
absolute counterpart from the *same* source already in use - économie's
exports/imports/external debt already had US$ versions alongside the %-of-
GDP ones (`NE.EXP.GNFS.CD` next to `NE.EXP.GNFS.ZS`, etc.), agriculture's
land/cereal indicators the same (`AG.LND.AGRI.K2` next to `AG.LND.AGRI.ZS`).
(2) A second API, tried before giving up - santé's doctor and hospital-bed
*density* (World Bank WDI) had no raw-count counterpart anywhere in WDI;
checking WHO's GHO OData API directly (`ghoapi.azureedge.net`) found real
absolute headcounts for doctors (`HWF_0002`, National Health Workforce
Accounts) and nursing/midwifery personnel (`HWF_0007`) that WDI simply
doesn't carry. Indicator codes found the same way as UIS's endpoint
earlier this session: querying `Indicator?$filter=contains(IndicatorName,
'Medical doctors')` rather than guessing.

(3) Only when neither existed anywhere was a value computed: no hospital-
bed headcount is published in WDI or GHO (checked both directly, not
assumed). `nombre_lits_hopital` = bed density × population, computed in
`pipeline/fetch_sante.py` for each of the 6 years the density series
actually has, fetching that *same year's* real World Bank population
figure each time - not today's, which would misrepresent a 2011 estimate
as current. Labelled `quality_flag=estime` with the exact inputs and
formula in `notes`, and the sentence template
(`sentence_sante_effectif`) explicitly says "environ ... selon une
estimation calculée," never stated as a plain fact the way the two real
WHO headcounts are.

Also caught while building the nurse-count series: WHO's own numbers swing
hard year to year (835 in 2008, 5,653 in 2023, 2,331 in 2024) - logged as
probably a reporting-methodology change rather than a real workforce
swing, not smoothed over or hidden. See `docs/verification-debt.md`.

## Économie reorganized: brief summary cards for prix and agriculture, not a merge

User feedback, with a real precedent behind it: CLAUDE.md's *original*
theme list said "agriculture et prix" as one theme - this session split it
into three separate pages earlier without flagging the deviation. Rather
than reverse that (which would mean deleting or nesting `/prix/` and
`/agriculture/`, breaking every existing link to them), `economie.astro`
now imports `prix.json` and `agriculture.json` directly and renders one
brief card each (headline figure, one generated sentence, a link to the
full page) - presentation only. `pipeline/export_economie_json.py` was not
touched for this: it still only knows about économie's own 13 indicators,
never prix's or agriculture's. Categories reordered to match how real
economic dashboards are laid out (IMF Article IV, World Bank country
pages, Trading Economics): Production → **Prix** → Commerce extérieur →
Finances publiques → **Secteur agricole** → Niveau de vie - ending on the
living-standards outcome, consistent with the causal-ordering rule already
in place for every other theme.

Deliberately did not do the more invasive version of this (nesting
`/prix/` and `/agriculture/` under `/economie/` as URLs) - that would
compound the already-flagged `/themes/` URL-structure debt rather than
resolve it, and the brief-card approach delivers the actual ask (discover
prix/agriculture from économie, with a preview) without a routing change.

## Unit-suffix spacing bug found while adding the raw figures

`economie.astro`/`agriculture.astro`'s `formatValue()` returned unit
strings with no leading space ("Md US$", "km²"), and the card template
concatenated them directly onto the number with no space either
(`{val.display}<span class="unit">{val.unit}...`) - every non-"%" card on
both pages was rendering "3,07Md US$" instead of "3,07 Md US$" since first
being built. `%` never showed the bug (it's correct with no space), which
is presumably why it went unnoticed - none of the pages built before this
session's raw-figures pass had a non-percent unit to expose it. Fixed by
giving every non-"%" unit string its own leading space at the source
(`" Md US$"`, `" km²"`, etc.) rather than changing the template, since "%"
and everything else genuinely need different spacing rules.

## Économie hub, round 2: agriculture card moved up, home page nav trimmed

Follow-up user feedback on the reorg above. Two changes: (1) the "Secteur
agricole" satellite card moved from after Finances publiques to
immediately after Production, ahead of Prix - agriculture is a GDP sector,
so it now sits next to "how big is the economy" rather than at the far end
of the page. New order: Production → **Secteur agricole** → **Prix** →
Commerce extérieur → Finances publiques → Niveau de vie. (2) The home
page's top-level nav no longer links directly to `/prix/` or
`/agriculture/` - only `/economie/` does, matching the hub relationship:
if économie is where a reader discovers prix and agriculture, the home
page shouldn't also present all three as equal peers. Both pages are
otherwise unchanged (same URL, same content, still cross-linked from every
other page's footer nav) - this only affects the home page's primary
navigation and one page's card order.

## Purged internal/AI-facing language from reader-visible text

User feedback: several pages had text that read like notes-to-self rather
than content for a site visitor -- a "phrase générée · gabarit
population_totale_lieu_estime" tag under every generated sentence (4
pages: population, prix, infrastructures, éducation ×3), "Premier thème
santé du site" in santé's lede (meaningless to a reader -- of course it's
the only health theme), "cette session"/"cette passe" scattered across
gap-notes and even inside `data/sources.csv` fields rendered on `/sources/`
(licence_notes/access_notes are shown in `<details>` blocks there), and
several visible citations of `CLAUDE.md` by name -- an internal project
brief a reader has no way to interpret, not a data source.

Removed the sentence-tag entirely from all 4 pages (`.sentence-tag`
CSS and markup) -- `/methode/` keeps its one worked example
(`gabarit population_totale_lieu_estime`) since that page's actual purpose
is explaining the sentence-generation mechanism to a curious reader, unlike
the tag's use elsewhere as build-transparency clutter nobody asked to see.
Reworded every "cette session"/"cette passe" and "CLAUDE.md" reference in
visible copy to state the fact plainly instead (e.g. "le PIB rebasé...
n'a pas été comparé" instead of "...au moment de la rédaction de
CLAUDE.md..."). Left `CLAUDE.md` mentions inside `authority_rank` alone --
that field is never rendered on `/sources/` (checked `sources.astro`'s
template directly), so it's genuinely internal metadata, not reader-facing
content, same category as a code comment. `docs/verification-debt.md`
references were also left alone throughout -- unlike `CLAUDE.md` (a private
planning artifact), the "known gaps" file is a deliberate part of this
project's own transparency design (rule zero: "gaps are content"), and a
data-savvy reader who downloads the CSVs from `/donnees/` can genuinely
follow that reference.

## WFP food prices: first market-level source

Phase 3 source list item 3. HDX's "Central African Republic - Food Prices"
dataset (CC BY-IGO), checked live via the HDX API rather than assumed from
its catalogue listing: 41 markets, 39 commodities, 2004-01 to 2026-07,
updated roughly monthly. This is the source CLAUDE.md itself names as the
example of a different geographic floor ("food prices stop at the market,
a point, not an area") -- the first real test of that claim.

Scope for v1: Bangui market only (the capital, and this dataset's most
complete series), Retail pricetype, `priceflag=actual` rows only (no
aggregated/estimated values), and only the 5 staple commodities whose
monthly data continues into 2026 rather than stopping around 2018-2021 --
checked per-commodity before picking (`Cassava (cossette)`, `Rice`,
`Maize`, `Meat (beef)`, `Oil (palm)`; the plain `Cassava` row was skipped
in favor of `Cassava (cossette)` since it stops in 2021). 34 other
commodities and 40 other markets exist in the same file and are named on
the page as not yet covered.

**Required a new entity level.** `entities.csv` previously only had
`pays`/`region`/`prefecture`/`sous_prefecture` -- a strict administrative
hierarchy. A market doesn't fit that: it's a point, not an area, and WFP's
file gives no finer administrative attribution than the market name
itself. Added `marche` as a new level with a single entity so far
(`cf-m-bangui-v1`), `parent_id` set to the Bangui prefecture entity as the
least-wrong available anchor -- documented as exactly that, not as a claim
that markets nest inside prefectures the way sous-préfectures do. Its
`valid_from` (2004-01-15) is the date of the first observation available
in the source, not a claim about when the market itself came into
existence, which isn't documented anywhere -- worded that way in the
entity's own notes so it can't be misread later.

**Rendered as a distinct section on `/prix/`**, not blended into the IHPC
series -- different geography, different source, different unit (real
FCFA retail prices vs. an index). The section states the geographic-floor
difference in its own intro line rather than leaving a reader to infer it
from a change in numbers, per CLAUDE.md's "each indicator has its own
geographic floor" principle. `export_prix_json.py` gained a
`fetch_market_series()` that filters by `entity_id` in addition to
`indicator_id` -- the country-level series functions deliberately weren't
touched, since every existing indicator on this site is still
single-entity (national) and didn't need that filter until now.

**One template fix caught by reading the generated output, not assumed
correct:** "le litre de huile de palme" is wrong French ("huile" is
h-muet and elides) -- `elide_de()` already existed for a different case
(place names after "de"), so this needed its own small elision check
rather than reusing that function, since the two aren't the same
grammatical construction. Fixed and verified against all 5 real labels
before treating the template as done, same practice as every other
sentence template on this site.

## Per-indicator definitions surfaced; page-level meta-count phrasing removed; em-dashes banned project-wide

Two more rounds of the "does this read like a note to the reader, or a note
to myself" audit, prompted by user feedback on économie's "3 indicateurs
propres à cette page" line and similar phrasing elsewhere.

**Definitions.** `indicators.csv` has carried a `definition_fr` field since
the crosswalk was built, but no export script or page ever surfaced it -
every indicator card showed a name and a value with no explanation of what
was actually being measured or how to read it. Added `definition_fr` to
every export script's per-indicator JSON block and rendered it on every
card across all 7 theme pages. Rewrote the field itself for all 71
indicators (`update_definitions.py`, run once) from bare technical clauses
("Part de la population...") into short explanations that also say why the
indicator is tracked or how to avoid misreading it - what "can exceed
100%" implies, the difference between a rate and its absolute counterpart,
why GDP per capita is more comparable across countries than GDP total,
etc. No new claims beyond what the source itself already establishes -
interpretive framing, not invented methodology.

**Meta-count phrasing.** économie, agriculture, santé and éducation each
had a `.coverage` line ("`{allIndicatorCount}` indicateurs - données de
`{oldestVintage}` à `{newestVintage}` selon l'indicateur - niveau le plus
fin : pays") and repeated "les `{allIndicatorCount}` indicateurs propres à
cette page sont tous nationaux" bullets - both read as a build manifest,
not content. Removed the coverage line outright; reworded the ledes and
the "Ce qui n'est pas mesuré" bullets to state the substantive fact (no
sub-national breakdown; data is from the World Bank/OMS/UIS) without
counting the page's own indicators out loud. Also caught and fixed a
side-effect: agriculture.astro's gap list still said food-market prices
were "not yet integrated" - stale as of the WFP prices work earlier this
session; reworded to point at `/prix/`.

**Em-dashes.** Removed every "-" character from every file this project
authored (code, docs, data notes, page copy) - CLAUDE.md's own text
included - and added a Voice rule against using it going forward, in
favor of a plain hyphen or a semicolon. Left `raw/` snapshots untouched
(immutable source data, not this project's own prose) and regenerated
`site/src/data/*.json` and `site/public/donnees/*.csv` from the now-clean
source CSVs rather than hand-editing the generated copies.

## National accounts: ICASEES's rebased GDP added, and it disagrees with World Bank

Phase 3 source list item 4. ICASEES's national accounts PDF (published
2026-07-30) was fetched directly rather than guessed at from its
announcement page - the actual download link was found by fetching the
announcement page's raw HTML and grepping for the edocman download
pattern already used for the IHPC dashboard file, the same technique
worked a second time.

Table 1 (page 12) gives PIB total, PIB per capita and real growth rate for
2019-2021, all in FCFA on the new 2019 base. Extracted with pdfplumber's
`extract_tables()`, not just `extract_text()`, specifically to rule out a
column-merge misread before trusting the numbers - worth doing since the
document's own narrative summary (page 7) states a different 2021 growth
rate (1.6%) than its own table (3.44%) for the same figure. The table was
treated as authoritative (structured data over prose) and the discrepancy
logged in `data/sources.csv`, not resolved by guessing which one the
authors meant.

**Two new indicators** (`pib_total_fcfa`, `pib_par_habitant_fcfa`) rather
than merging into the existing World Bank USD figures - converting
between currencies would need an assumed exchange rate this project
hasn't verified, and the two sources also likely use different population
denominators (ICASEES's own RGPH-4-informed count vs whatever the World
Bank uses), so a direct numeric comparison would be comparing two things
that aren't quite the same measurement. Both are shown, neither is forced
to agree with the other.

**The growth rate is different: same unit (%), same concept, genuinely
comparable.** ICASEES's 2020/2021 figures (3.41%, 3.44%) disagree with
World Bank's modelled estimate for the same years (0.90%, 0.98%) by
roughly 250% relatively - not a rounding difference. This is exactly what
`CLAUDE.md`'s multi-source disclosure mechanism exists for, so
`taux_croissance_pib` on `/economie/` now has one: ICASEES is the headline
(donnée administrative nationale outranks estimation modélisée
internationale per the authority ranking), World Bank's full annual
series stays the chart, and a "N sources" disclosure shows both years
side by side with the spread. Implemented as a population.astro-style
disclosure (headline + expandable table) rather than éducation.astro's
dual-line chart with overlay points - there are only 2 overlapping years
to show, not a long modelled series needing survey points plotted on it,
so the simpler pattern fit better. This resolves a `docs/verification-debt.md`
item that had been open since économie was first built, moved to Resolved.

## MICS 2018-19 indicators added via UNICEF's live SDMX data warehouse

Phase 3 source list item 5. Went looking for the actual MICS6-RCA PDF
report first (icasees.org and mics.unicef.org both found via search), but
both mics-surveys-prod.s3.amazonaws.com (the report's actual file host)
and mics.unicef.org itself return 403 to a plain fetch - looks like
referer/session-gated access, not a wrong URL (even the exact "Snapshots"
pptx URL found via the World Bank's microdata catalog page 403'd the same
way). Rather than give up or scrape around the block, checked whether
UNICEF republishes MICS-derived indicators through a structured API
instead - it does: `sdmx.data.unicef.org`, the same kind of live SDMX
warehouse IMF/World Bank use, no authentication required, discovered by
querying its own `/dataflow` endpoint rather than guessing a URL.

7 new indicators, split across two themes rather than invented as a new
one: 5 into santé (a new "Santé maternelle et infantile" category -
antenatal care, skilled birth attendance, exclusive breastfeeding,
stunting, wasting) and 2 into population (birth registration, child
marriage before 18) - both are more demographic/legal-status facts than
health facts, so they fit population's existing "Autres indicateurs"
pattern better than a forced fit into santé.

**The source isn't uniformly MICS6, and that's stated rather than
smoothed over.** UNICEF's warehouse compiles each country-indicator from
whichever national survey covers it most recently - most of these 7
genuinely are MICS6 (2018-2019), but stunting and wasting have a more
recent point from a 2022 SMART nutrition survey, used here instead of the
older MICS point since it's real, more recent, and from the same
UNICEF-curated series. Each observation's own `DATA_SOURCE` attribute
from the API response was read and written into that row's `notes` field
rather than assumed uniform - checked per-indicator, not batch-labeled.

**Two sub-annual 2019 survey rounds were dropped for stunting/wasting**
(2019-03 and 2019-11, sitting between the 2018 and 2022 points used) -
keeping them would mix sub-annual and annual periods in what's otherwise
a clean annual-looking series, misrepresenting occasional point surveys as
continuously monitored. See `pipeline/fetch_unicef_mics.py`.

Also gave santé and population's affected indicators a 10-year staleness
threshold instead of the flat 5-year one used for World Bank's annually
modelled estimates - these are survey-linked (MICS-cadence, not annual),
same reasoning as éducation's existing `SURVEY_LINKED` split, and
`méthode.astro`'s published threshold table now has a row for it rather
than silently diverging from what the page tells readers. 80 indicators
total now.

## IMF NSDP: two dead ends checked directly before finding the live API

Phase 3 source list item 6, flagged in the plan itself as "hard -
JavaScript or SDMX". Both routes anticipated in `CLAUDE.md` turned out
wrong in a specific, checkable way rather than just difficult:

1. `dataservices.imf.org` (the endpoint most third-party guides and R/CRAN
   packages document) no longer resolves at all - DNS lookup fails, not a
   403 or a moved page. IMF retired it.
2. `car.opendataforafrica.org/nsdp` (the AfDB/Knoema-hosted mirror
   `CLAUDE.md` named) is genuinely all client-side rendering - fetching it
   returns an empty shell, and every guessed API/explorer subpath on that
   domain 403s. Confirmed, not assumed from "JavaScript-heavy sites are
   usually like this."

IMF's current SDMX 2.1 API lives at `api.imf.org` instead - found by
requesting its own `/external/sdmx/2.1/dataflow` listing rather than
guessing a URL, the same technique that worked for UIS, WHO GHO and
UNICEF earlier this session. `NSDP` is a real dataflow there
(`IMF.STA:NSDP`), live, unauthenticated.

**CAR's actual e-GDDS coverage is thin.** The NSDP framework is meant to
cover GDP, prices, government operations, debt, monetary and external
sector - querying every dimension as a wildcard for CAF returns exactly
one series: `TEA` (Total Economic Activity Index), quarterly, 2017-Q1 to
2023-Q1. The regional dataflows for the area (`CPI_WCA`, `QGDP_WCA`) were
also queried directly for CAF and returned nothing. Rather than either
skip the source entirely or overstate what it covers, added the one real
series as a new indicator (`indice_activite_economique`) and said plainly
on the page that the rest of the e-GDDS framework isn't populated yet for
this country - a gap that belongs to the source, not something this
project chose to leave out.

One new small case in `sentence_economie_activite()`: NSDP periods are
quarterly (`2023-Q1`), unlike every other économie indicator's plain
year - needed its own quarter-to-French mapping rather than reusing
`period_to_fr()`, which assumes a month. `economie.astro`'s `isStale()`
now takes the leading 4 characters of the period rather than the whole
string, so it keeps working for both shapes. 81 indicators total now.

## Health facilities: a real 2-source disagreement, not the planned 3-way test

Phase 3 source list item 7, flagged as "hard - multiple conflicting
sources" and, in an earlier pass this session, described as "the first
3-way disclosure test" - that turned out to be aspirational wording, not
a firm target: 2 genuinely independent sources were found, not 3, and
forcing a third would have meant double-counting one of them.

Checked HDX for Central African Republic health facility datasets and
found three candidates, not two:
- **Health Facilities in Sub-Saharan Africa** (Maina et al. 2019,
  Scientific Data) - an academic compilation from government and
  non-government facility registries across 50 countries, static since
  its 2019-07-25 publication. 555 rows for CAR (490 public, 63 private
  non-profit).
- **Central African Republic Healthsites** - an HDX export of
  OpenStreetMap health-facility tags via healthsites.io/HOTOSM, actively
  updated (last modified 2026-08-28). 425 rows.
- **hotosm_caf_health_facilities** - a second HDX listing, also OSM data
  via HOTOSM's raw-data-api. Checked its description directly: same
  underlying OpenStreetMap tags as the healthsites export, just packaged
  differently. Using both would have looked like two sources agreeing
  when it's really one source counted twice - left out rather than
  padding the disclosure to 3.

The 555-vs-425 gap (about 30%) is real and worth showing, not a rounding
difference - and it's not obviously explainable as "one is wrong": the
government registry is a static 2019 snapshot that could be missing
facilities opened since, while OSM coverage depends on where volunteer
mappers have been active and could be missing facilities in areas nobody
has mapped. Both plausible, neither confirmed, so both are shown with a
disclosure UI (population.astro's pattern, reused a third time this
session) rather than the page picking one.

This is santé's first disclosure indicator, so the disclosure CSS
(`.national-figure`, `.disclosure`, badges) had to be added to
`sante.astro` for the first time - copied from the économie/population
implementations rather than redesigned, keeping the pattern visually
consistent across the three pages that now use it.

**Quality-flag vocabulary needed a new value.** The existing badges
(`administratif`, `estime`, `provisoire`, `enquete`) don't fit
crowd-sourced OSM data - it's not a modelled estimate, an administrative
record, or a survey. Added `osm` as its own flag rather than force-fitting
an existing one that would misdescribe the methodology.

82 indicators total now - all 7 Phase 3 source list items are done.

## Follow-up: " -- " in French text read as nothing, fixed separately from the em-dash sweep

User feedback after the em-dash purge: several French sentences (mostly
new definition_fr text from update_definitions.py, and licence_notes/
access_notes written across this session's source additions) used " -- "
(a spaced double hyphen) as an em-dash substitute - a normal English
technical-writing convention, but one that reads as nothing in French.

Checked reader-facing Astro pages first and found zero instances in
actual rendered French copy - every "--" there is either a CSS custom
property (`var(--ink-faint)`, `--paper:`, etc., which must stay intact)
or inside an English frontmatter code comment, where the convention is
normal and CLAUDE.md's own "code and comments in English" rule already
covers it. The real fix was scoped to three files:
`data/indicators.csv` (28 occurrences, mostly definition_fr text),
`data/sources.csv` (30, mostly access_notes/licence_notes rendered on
`/sources/`), and `data/observations.csv` (352 raw occurrences, but only
a handful of distinct sentences repeated across many rows - e.g. the
calculated-hospital-beds note appears once per year). All replaced with
a single hyphen, consistent with the earlier em-dash sweep's choice, so
the project now has one punctuation convention instead of two. Confirmed
clean afterward by grepping every built HTML page in `dist/` and checking
that every remaining "--" is a `var(--...)` CSS reference, not text.

## ICASEES education yearbooks: retried successfully, real gaps closed

The rate-limiting block logged earlier this same session had cleared by
the time this was retried later: a single request each to the
publications listing page and the 2024-2025 Annuaire Statistique's Excel
download both succeeded cleanly, no corrupted content or 404s. Moved from
`docs/verification-debt.md`'s Open list to Resolved.

The workbook is exactly as irregular as `CLAUDE.md` warned - a single
3.7 MB sheet, narrative text and tables at inconsistent positions, a
multi-page acronym glossary before any real data. Found two usable
tables by reading through it, not by pattern-matching column headers
generically:

- A national summary by education level (établissements, élèves,
  enseignants), summed across the 4 levels into 3 new headline
  indicators (`nombre_etablissements_scolaires`, `effectif_eleves`,
  `nombre_enseignants`) - éducation's first absolute headcounts,
  matching the "raw figures alongside rates" pattern already established
  for santé/économie/agriculture. Added as a new "Ressources scolaires"
  category, first in the page's order (santé-style: what capacity exists
  before what happens to students).
- A PSE (Plan Sectoriel de l'Éducation) tracking table with an
  unambiguous "Valeur de base (2019) / Valeur réalisée 2024" header,
  giving a real Baccalauréat général pass rate (25% -> 36.66%) -
  `taux_reussite_baccalaureat`, closing a gap `CLAUDE.md` names by name
  ("BEPC and Baccalauréat results are not published in machine-readable
  form. Digitising them would be an original contribution."). Added to
  the existing "Achèvement scolaire" category alongside the completion
  disclosure indicators, as a plain single-source card.

**A second, more prominent-looking exam-results table was checked and
deliberately not used.** Row-labeled "Résultats aux examens... de
l'année précédente (2020/2021)," it looked like it would finally give
BEPC/CEPE figures too - but every data row beneath its header is empty,
a template structure carried over from an older year's file rather than
this year's real numbers. Confirmed by reading the actual cell values,
not assumed populated from the header alone. BEPC and CEPE results
remain genuinely unavailable in this source, not just unfetched -
`education.astro`'s gap-note says so plainly instead of implying they'd
simply been missed.

**Hand-transcribed, not parsed generically, on purpose.** A script
reading today's exact cell positions would silently misread a future
year's differently-laid-out edition instead of failing loudly - CLAUDE.md
itself flags this layout inconsistency as expected, not exceptional, for
these yearbooks. `pipeline/add_annuaire_education.py` documents this
explicitly: re-verify cell positions by hand for each future year's file
rather than trusting the same code to still be correct. 86 indicators
total now - the last item on this session's list before the
comptes-nationaux-style "one-off, hand-verified" pattern.

## Indicator definitions rewritten as complete French sentences, not noun-phrase fragments

User feedback on the économie headline caption: "PIB par habitant, le
chiffre le plus souvent cité... Produit intérieur brut par habitant, en
dollars américains courants - le PIB total divisé par la population ;
plus utile que..." read as ungrammatical. The root cause was structural,
not a one-off typo: most of `definition_fr` across `data/indicators.csv`
was written in a dictionary/glossary register - bare noun phrases chained
with dashes and semicolons, no article, no main verb - which reads fine
in isolation the way a dictionary entry does, but breaks down the moment
it follows an actual sentence (the headline caption's fixed phrase), or
whenever a reader expects a paragraph of French prose rather than a
label.

Rewrote all 86 definitions as complete sentences: every one now has a
proper subject (varying naturally - "Ce taux", "Cet indicateur", "Cet
indice", "Ce prix", "Le produit intérieur brut...") and a real verb
("mesure", "donne", "compte", "correspond à", "rapporte"), with any
second clause written as its own full sentence instead of a
dash-appended fragment. Kept the same facts and the same interpretive
additions from the earlier "surface indicator definitions" pass - this
was a grammar fix, not a content change.

Also fixed the 4 headline captions that concatenated `{name_fr}` +
a fixed phrase + `{definition_fr}` into one paragraph (économie,
agriculture, éducation, santé) - each headline indicator is fixed per
page, so the caption's opening clause is now hand-written with its
correct article ("Le PIB par habitant est...", "L'espérance de vie à la
naissance est...") instead of interpolating the bare `name_fr` without
one. Split into two separate `<p class="headline-caption">` paragraphs
rather than one run-on, matching the pattern infrastructures.astro/
population.astro/prix.astro already used for their headline definitions.

## Phase 4, first real step: WFP prices widened to every market, a genuine "by préfecture" breakdown

Started Phase 4 with the source that was already closest to ready: WFP's
food price file was fetched Bangui-only in the Phase 3 pass, but the same
already-downloaded file covers 41 markets - checked live before widening
(not assumed from Bangui's own coverage), 34 of them have real, recent
(2025-2026) monthly data for all or most of the same 5 staple commodities
already on the page, spread across 16 of the 20 préfectures.

**Every market is now its own `marche`-level entity** (40 new ones, plus
the existing `cf-m-bangui-v1`), parented to the préfecture its `admin1`
column names - matched by exact name against `data/entities.csv`, no
fuzzy matching needed, since WFP's own admin1 values are already spelled
the same way. Each entity's `valid_from` uses that market's true
first-observed date in the full file, computed directly rather than
using the truncated fetch window's start date, so the entity record
doesn't imply a market is newer than it actually is.

**Deliberately capped non-Bangui markets to 2025-01 onward, not full
history.** Fetching all 40 markets' complete history (back to 2004 for
some) would add roughly 14,000 rows to `observations.csv` for a
breakdown table that only needs "the current price, across the country,"
not two decades of trend per market - Bangui already carries that
detailed role. This is a scope decision, not a data quality shortcut:
every value kept is real and dated correctly, just deliberately not the
whole available history for markets that aren't the page's flagship one.

**New `/prix/` section: "Prix par préfecture"** - a small table per
préfecture, one row per market, one column per commodity, showing the
latest known price (real geographic price variation shows up
immediately: beef is 6 000 FCFA/kg in Bangui vs 3 000 in Ndélé). A
missing cell means no recent price exists for that denrée at that
market, stated as such rather than shown as zero. 4 préfectures
(Basse-Kotto, Lim-Pendé, Mambéré, Ouham-Fafa) have no market with recent
data in this source at all - named explicitly rather than silently
absent from the table.

This is Phase 4 step 1 ("wire the crosswalk into the observation
pipeline; backfill entity_id for subnational data") and step 3
("breakdown sections on theme pages") done together for one real theme,
before touching any place-page template - the plan's own point in
naming these steps first was to find out what data genuinely descends
before designing pages around it.

## Phase 4, first place-page template: `/lieux/prefecture/{slug}`

Built directly on the audit above rather than the full Sec2.4 spec:
population and prix are the only 2 themes with real préfecture-level
data today, so the template shows those two properly (headline
population figure with rank and share of national total, a régional
sibling comparison bar chart, a per-market price table reusing the
`prix.astro` breakdown shape) and states the other 5 themes plainly as
"no data at this level" in a 7-row freshness table, rather than faking a
breakdown or omitting them silently.

New export script `pipeline/export_lieux_prefecture_json.py` follows
the same CSV -> DuckDB -> JSON handoff as every other page (Astro never
touches the raw CSVs). One JSON entry per préfecture entity, keyed by
slug: population (2003 + 2021, rank, share of national), markets (from
the `marche`-level entities added in the WFP widening above), régional
siblings (for the comparison bars), pcode aliases, and the freshness
list. Wrote `site/src/data/lieux_prefectures.json`, 20 entries (all 20
préfectures have population data; 16 also have market prices, matching
the 16-of-20 préfecture coverage the WFP widening established).

`[slug].astro` is the project's first `getStaticPaths()` route - every
page before this was a flat file. New accent color `--t-lieu: #8B5E3C`
(warm terracotta) distinguishes place pages from every theme page's own
accent, while reusing the same layout conventions (crumb, headline
block, disclosure-style sections, site-nav footer) established on
population.astro/prix.astro. Also added `/lieux/` as an index page
(grouped by région, same accent palette as population.astro's régional
grid) since without it the 20 new pages would be reachable only by
guessing a URL or via search - and linked it from the home page nav.

Explicitly not in this pass, named on each page rather than left silent:
locator maps (needs new geo/mapshaper infrastructure, Sec2.4 item 3) and
sous-préfecture child pages (85 more pages, Sec2.4 item 7) - both
sized as separate steps, not part of this first template.

All 33 built pages (the 20 new ones included) pass the 150 KB budget
with room to spare - each place page is 6-8 KB, well under even the
lightest existing theme page.

## Sitewide dark-mode toggle: CLAUDE.md's client-JS budget flexed for the first time

Added a combined auto+manual dark mode: with no stored preference, every
page follows `prefers-color-scheme` (0 JS involved); a small sitewide
button lets a reader force "clair" or "sombre" instead, storing that
choice in `localStorage` and stamping `data-theme` on `<html>`, which
overrides the OS setting from then on for that visitor.

This is the first time CLAUDE.md's "0 KB client JS on place and theme
pages" line has been deliberately flexed rather than treated as
absolute - updated CLAUDE.md itself at the same time (both to name this
as an allowed exception, and to state more plainly, in "How to read this
document," that specific numbers/restrictions in the file are tuned
recommendations, not rules to defend for their own sake). The toggle
script is a few hundred bytes of hand-written vanilla JS, no
dependencies, no framework, on every page - unlike the chart/library ban
elsewhere in the performance budget, which is not up for the same kind
of exception.

Two new shared components, `site/src/components/ThemeInit.astro` and
`ThemeToggle.astro` - the project's first shared (non-page) Astro
components. `ThemeInit` is a synchronous inline script placed first in
`<head>` on every page, applying any stored preference before first
paint (avoids a flash of the wrong theme). `ThemeToggle` renders the
fixed-position button plus its click handler, styled only from tokens
every page already defines (`--surface`/`--ink`/`--ink-muted`/`--line`),
so it drops into any page unchanged regardless of that page's own accent
color.

Discovered along the way: importing the same component into every page
made Astro split page CSS into an external `/_astro/*.css` file once
enough of it was shared, breaking the project's "one self-contained HTML
file per page" assumption that `check-page-weight.mjs` relies on (its
own comment says so explicitly). Fixed by setting
`build.inlineStylesheets: "always"` in `astro.config.mjs` rather than
duplicating the toggle's CSS into all 14 pages - keeps the shared
component and the single-file invariant both intact.

Every one of the 14 existing pages (all 7 themes, home, sources, méthode,
données, à-propos, and the 2 new `/lieux/` pages) got a dark palette
added to its `:root` block, following the same 3-state CSS pattern:
`:root` for light defaults (unchanged), `@media (prefers-color-scheme:
dark)` guarded by `:root:not([data-theme="light"])` for the automatic
case, and `:root[data-theme="dark"]` for the explicit override - the
same set of hex values in both dark blocks per page, since only the
selector differs. Base tokens (`--paper`/`--surface`/`--ink`/etc.) got
one shared dark palette; each page's own accent color(s) got a
brightened variant of the same hue for legibility against a dark
ground.

While touching every page's frontmatter comment block for the toggle
import, also caught and fixed several `--` (double-hyphen) leftovers
from before the project's em-dash sweep - the sweep's script only
covered `.md`/`.csv`/`.py`/`.astro`/`.yml` at the time, but these were in
`.astro` files it should have caught; likely written after that pass ran.
All 33 pages still pass the 150 KB budget after these changes (biggest
is `/sources/` at 93.6 KB), and ruff/build are clean.

## Phase 4: santé widened to région level (7 régions), a genuine second subnational theme

Followed the same "check a source already fetched for Phase 3 before
assuming it's national-only" instinct that found WFP's other 40 markets:
the Master Facility List used for `nombre_etablissements_sante`'s
national count carries an `Admin1` column, live-checked (not assumed)
before use, and it resolves to exactly this project's 7 RGPH-4 régions
(labels differ slightly - "Kagas" vs. "Kaga", "Bangui" vs.
"Bas-Oubangui" - but the counts, 555 total split 23/95/48/109/85/112/83,
match the 7 régions one-to-one with no leftover or gap). That is one
level below national but one level short of préfecture - a genuinely
different case from population/prix, so it gets its own honest middle
category rather than being folded into either "available" or "not
available" at the préfecture level.

Also checked, before starting: whether ICASEES's education yearbook
(`raw/icasees-annuaire-education/2026-09-12/annuaire_statistique_2024_2025.xlsx`,
fetched in Phase 3) has équivalent préfecture-level ("IA" = Inspection
Académique) tables - it does, confirmed by reading the workbook directly
(over 80 separate "IA"-keyed tables spanning établissements, élèves,
enseignants, mobilier, infrastructure scolaire, résultats d'examens...).
Unlike the health facilities Admin1 column, this is not a quick win: the
workbook is a hand-formatted statistical yearbook with dozens of
near-duplicate table shapes, inconsistent headers ("Tot al Publ ic" with
stray spaces, mid-table header row repeats, IA name variants like "OUHAM
FAFA (UF)" vs. "Ouham Fafa"), and no consistent per-level Total column to
lean on the way the santé Admin1 breakdown had. Extracting even one clean
préfecture-level figure (say, total établissements across all 4
education levels) means correctly identifying and parsing 4+ separate
tables per figure, not 1. Deferred rather than attempted this pass -
logged as a real, scoped-out lead rather than silently skipped.

Implementation: `pipeline/fetch_etablissements_sante.py` now also writes
one `nombre_etablissements_sante` observation per région
(`REGION_ADMIN1_ALIASES` maps the Master List's 7 Admin1 labels to this
project's région entity_ids), alongside the existing national 2-source
row. `export_sante_json.py` attaches a `region_breakdown` list to the
établissements disclosure block; `sante.astro` renders it as a second,
separate `<details>` under the existing national disclosure, explicitly
noting there's no OpenStreetMap equivalent at this level (one source, not
two, unlike the national figure). `export_lieux_prefecture_json.py` now
looks up each préfecture's parent région's santé figure and exposes it as
`sante_region`; the place-page template shows it in its own section
labeled "niveau régional," and the freshness table gets a third state
(`level: "region"`) distinct from the préfecture-level population/prix
rows and the "aucune donnée" rows for the other 4 themes.

Also fixed while in `fetch_etablissements_sante.py`: it fetched both
source files straight into memory without ever writing a raw snapshot,
unlike every other fetch script in this project (CLAUDE.md's raw/
"immutable source snapshots, never overwritten" rule) - this had been
true since the file was first written in Phase 3 and only surfaced now
while extending it. Both files now land under `raw/` before parsing.

All 20 préfectures now carry a régional santé figure (every préfecture
belongs to exactly one of the 7 régions, and all 7 have data). Verified
idempotent (re-ran the fetch twice, `data/observations.csv` row count
unchanged) and all 33 pages still pass the 150 KB budget after rebuild.

## ICASEES education yearbook: préfecture-level extraction abandoned this attempt, worse than first assessed

Went back to the deferred lead above and tried to actually extract one
clean figure (Fondamental 1 établissements per IA, to sum against the
already-used national total of 2 508). Found the workbook's real
structure is worse than the first pass suggested: inspecting
`ws.merged_cells.ranges` around the F1 établissements table shows dozens
of separate merged-cell blocks spanning wildly different column ranges
(`A786:L786`, `M786:S786`, `T786:AC786`, `AD786:AI786`, ... out past
column `CM`) all sharing the *same* row numbers. That means this isn't
one wide table with a multi-row header - it's several unrelated tables
laid out side by side, sharing row ranges, on one sheet. Reading rows
with `values_only=True` and compacting non-null cells (the approach that
correctly found the santé régions and confirmed the "IA" tables exist at
all) silently interleaves values from *different, unrelated tables* into
one list once a row range holds more than one side-by-side block - which
is exactly what happened: a row that looked like "Bangui (IAB): 27, 0,
26, 29, 18, 19, 20, 21, 22" was not one 9-column établissements row, it
was fragments of at least two adjacent tables concatenated by the
compacting step.

This is a real risk, not just an inconvenience: a positional guess at
which numbers belong to which column would produce a plausible-looking
but silently wrong figure attributed to the wrong préfecture or the
wrong metric - worse than the honest "no data at this level" the site
already shows, and against rule zero's spirit even though nothing would
technically be fabricated (the numbers are real, just possibly
mis-attributed). Correct extraction would need per-table column mapping
from the actual merged-cell boundaries, not sequential row reading, and
a validation step cross-checking every extracted préfecture total against
the already-used national total (2 508 for F1) before trusting any of it
- a materially bigger and slower task than the already-deferred estimate
assumed. Stopped here rather than push a fragile heuristic through.
**Not revisited without that proper column-mapping approach.**

## Population reaches sous-préfecture: a genuinely fresh, clean source found via HDX's dataset metadata

Went back to the COD-PS lead named in CLAUDE.md's domain facts
("built on the 2003 census projected to 2015... not yet fetched") rather
than assume that description was still accurate - it wasn't. HDX's own
package metadata (`api/3/action/package_show?id=cod-ps-caf`, not the
dataset's HTML page, which 403s the same way car.opendataforafrica.org
does) shows the dataset now carries a 2025 projection resource,
"Projection de la population 2025 en Admin2 (ICASEES)," produced
directly by ICASEES for the annual HNRP (Humanitarian Needs and
Response Plan) cycle - not a third-party projection layered on old
census data.

Checked live before trusting it (same discipline as every other source
this session): the file's `Admin2_Pcode` column (85 rows, one per
sous-préfecture) matches every sous-préfecture pcode already in
`data/aliases.csv` from the COD-AB v02 build, 85-for-85, no leftover, no
gap, no fuzzy name matching needed - the cleanest join this project has
had all session. Two other resources in the same dataset (Admin2/Admin3
CSVs dated 2015) were checked and deliberately not used: their own HDX
descriptions admit they don't match COD-AB's current unit counts (73 vs.
72, 177 vs. 175) - built on the older 16-préfecture geography this
project's crosswalk already moved past, a second crosswalk problem not
worth taking on for an older, coarser number this new file already beats.

**`population_totale` now reaches sous-préfecture** -
`indicators.csv`'s `geographic_floor` updated from `prefecture` to
`sous_prefecture` accordingly (docs/plan.md step 2, done for this one
indicator). `pipeline/fetch_icasees_population_projection.py` writes both
the 85 sous-préfecture rows straight from the file and 20 préfecture-level
rows summed from them (grouped by `Admin1_Pcode`) - the first
préfecture-level population figure newer than the existing 2021 estimate.
`population.astro` gained a 2025 column on its région tables and a new
"Par sous-préfecture" section (85 rows, grouped by préfecture, 20 small
tables). Every préfecture place page now lists its own sous-préfectures'
2025 populations directly, ranked descending, with the honest caveat that
individual sous-préfecture pages don't exist yet - and the freshness
table's Population row now reads "2025 (jusqu'à la sous-préfecture)"
rather than "2021," reflecting the new floor. Sibling comparison bars on
place pages still use 2021 (kept as-is; not worth re-deriving from a
projection when the estimate is the one already anchoring rank/share
elsewhere on the page).

**Real gotcha hit while adding the new source row to `data/sources.csv`:**
DuckDB's `read_csv_auto` failed to "sniff" the file's dialect after
appending a field containing an escaped embedded ASCII double-quote
(`""not yet fetched""`) - even though Python's own `csv` module parsed
the row correctly as valid RFC 4180 (verified field-by-field). Confirmed
by bisection: the file read fine without that one row, and failed again
even in a 2-line reproduction of just the header plus that row. Fixed by
using guillemets (« ») instead of embedded double quotes for the quoted
phrase, matching the convention already used elsewhere in these CSVs.
Worth remembering: an embedded `""..""` sequence inside a quoted CSV
field, while valid CSV, isn't safe to assume DuckDB's sniffer will
accept - prefer guillemets for any in-CSV quoted phrase.

All 33 pages rebuilt clean and still pass the 150 KB budget (place pages
grew to ~18 KB with the new sous-préfecture table, `/population/` to
~59 KB); fetch verified idempotent on both `observations.csv` and
`sources.csv`.

## Phase 4 step 6, second half: national comparison on place pages

Picked from the 3 parked options (national comparison / geographic_floor
audit / locator maps) - the smallest, self-contained one, and no new
export data needed since `national_2021` and `total_prefectures` were
already in `lieux_prefectures.json` from the earlier place-page work.

Compares each préfecture against the **national average per préfecture**
(national 2021 population ÷ 20), not the whole-country total - dividing
first keeps both bars on a comparable scale, the same reasoning already
applied to the régional-sibling comparison above it. Rendered with the
same `.comparison-row`/`.comparison-bar-fill` markup already used for
that régional comparison, plus a one-line "Ouaka compte 1.7× cette
moyenne" caption. Verified on both a well-above-average préfecture
(Ouaka, 1.7×) and a well-below-average one (Vakaga, 0.3×) - bars scale
correctly in both directions. All 33 pages still pass the 150 KB budget.

## Phase 4 step 2: geographic_floor derived from observations, not re-audited from scratch

Re-read the step's own wording before starting ("Set `geographic_floor`
per indicator **from observation**") and took it literally: the right
check isn't re-chasing each of the ~80 national-floor sources for
theoretical subnational depth (that's a much bigger, separate kind of
work - each successful widening this phase, WFP/santé/population, was
its own multi-step effort), it's confirming `indicators.csv`'s stated
floor actually matches the finest entity level each indicator's own
observations use in `data/observations.csv` today.

New `pipeline/set_geographic_floor.py`: for every `indicator_id`, finds
the finest level (`pays` < `region` < `prefecture` < `sous_prefecture`,
with `marche` as WFP prices' own separate leaf) among its actual
observations, and writes that back if it disagrees with the current
value. Grouped the 80 "pays"-floor indicators by source first
(`world-bank-*`, `unesco-uis-*`, `unicef-data-warehouse`,
`who-gho-health-workforce`, `imf-egdds-nsdp` account for the great
majority) - all of those are aggregator platforms that are national-only
by construction, already confirmed live earlier this session via each
one's own API structure, not something worth re-querying again without
new reason to doubt it.

Running it found exactly one real, previously-missed mistake:
**`nombre_etablissements_sante` was still marked `pays`**, even though
the santé régional widening earlier this session had already written
région-level observations for it - a genuine oversight in that commit,
not something hypothetical the audit merely speculated about. Fixed to
`region` automatically. Every other indicator's stated floor already
matched its data; no other changes. Re-ran the script a second time to
confirm it reports "no changes" (idempotent, safe to leave as a
standing check rather than a one-off).

## Phase 4 step 5: locator maps, the last parked item

Checked first, rather than assumed: the COD-AB v02 snapshot already
fetched for the crosswalk
(`raw/cod-ab-caf/2026-09-05/caf_admin_boundaries.geojson.zip`) turned out
to already contain real boundary geometry, including the "_em"
(edge-matched) files CLAUDE.md's own source notes call out as
specifically meant for cartography - no new fetch needed, this was
processing work on data already sitting in `raw/`. Joined every
préfecture polygon to its entity_id via `adm1_pcode`, checked live
against `data/aliases.csv`: 20-for-20, no fuzzy matching, same clean-join
pattern as the WFP/santé/population widenings earlier this phase.

**No new dependency added.** `geo/README.md`'s original plan named
mapshaper for simplification; used `shapely.simplify()` instead (Douglas-
Peucker, tolerance 0.02° ≈ 2 km) since shapely was already an approved
pipeline dependency and mapshaper would have been a new one - CLAUDE.md's
"ask before adding any dependency" made this an easy call, not a
compromise. Verified valid geometry at that tolerance for the country
outline and all 20 préfectures, and checked the total point count first
(25 713 raw points across the 20 préfectures alone) before picking a
tolerance, rather than guessing: 0.02° gets that down to ~1 765 points
combined with the country outline, keeping every simplified file well
under the 50 KB per-map budget (largest is the country outline at 13 KB).

Two new pipeline scripts, matching the project's existing two-stage
build/export pattern: `build_geo_prefectures.py` writes the reusable
`geo/raw/{entity_id}.geojson` and `geo/simplified/{entity_id}.geojson`
files (21 each - country + 20 préfectures) that `geo/README.md` already
planned for; `export_prefecture_maps_json.py` reads those and does the
one piece of actual new geometry work this needed: a simple
equirectangular projection (longitude scaled by cos(mean latitude), one
shared scale factor fit to a 700px-wide viewBox from the country's own
bounding box) that turns each polygon into a ready `"M x,y L x,y ... Z"`
SVG path string. Astro pages do zero geometry math - they get plain path
data and a shared `view_box`, matching every other page's build-time-only
rule.

Verified the projection is geographically sane by checking real
préfectures' projected bounding boxes against where they actually sit in
CAR: Vakaga (far northeast) landed top-right, Haut-Mbomou (southeast)
landed right-and-lower-half, Nana-Mambéré (far west) landed at the
left edge, Bangui (south, on the river) landed near the bottom - all
correct, not just "a shape appeared."

Each préfecture place page now shows a locator map: the country outline,
all 20 préfecture boundaries in a thin neutral stroke, and the current
préfecture filled in the page's own `--t-lieu` accent. Place pages grew
from ~18 KB to ~44 KB with the added path data (the full map dataset,
~24 KB, is shared/repeated per page since every page is still one
self-contained HTML file) - still comfortably under the 150 KB budget.

**Also updated `docs/verification-debt.md`'s COD-AB licence entry:** its
"humanitarian purposes only" caveat was logged back in Phase 1 as "not
yet used for anything," which stopped being true once the crosswalk
itself started using COD-AB's tabular pcodes, and is now more concretely
true still - the maps redistribute the boundary *geometry* itself
(simplified, but derived from and shaped like the original) on public
pages, not just an internal ID crosswalk. Still fine for v1 per CLAUDE.md's
own rule, but noted as the thing to actually resolve before final launch.

## Widening the remaining 4 themes: checked live, all 4 come back negative

Asked to widen infrastructures/éducation/économie/agriculture the same
way population/prix/santé were - checked each theme's actual sources
live rather than assume the earlier general audit's summary still holds,
same discipline as every other widening this phase. Every check came
back negative, for a genuine reason each time, not just "didn't look":

- **Infrastructures, agriculture:** every indicator is a World Bank WDI
  series. Already established earlier this session that WDI's API is
  structurally national-only (no subnational endpoint exists to check) -
  not worth re-querying again without a reason to doubt that.
- **Économie, IHPC:** re-opened the already-fetched dashboard file's own
  metadata sheet - all 14 series (IND1-IND14) explicitly state "échelle
  nationale" in their own definition text. Not an assumption; the source
  says so about itself.
- **Économie, comptes nationaux:** text-scanned all 65 pages of the
  already-fetched PDF for région/préfecture/Bangui/provincial keywords.
  One hit, a staff title ("Chef de Service des Comptes nationaux
  Satellites et régionaux") - a service that exists at ICASEES, not a
  régional table in this particular document. No régional GDP breakdown
  published here.
- **Éducation:** this is the one worth real detail, since the yearbook
  genuinely does have IA/préfecture tables (confirmed earlier), and this
  time the check went further than the earlier abandoned attempt -
  actual verification, not just spotting the risk. Took the *simplest*
  candidate table (préscolaire établissements by zone: IA/Urbaine/Rurale/
  Total général, a single-level header, no nested sub-categories like the
  earlier-abandoned établissements-by-statut table) and derived its exact
  column boundaries from that row's own merged-cell ranges specifically
  (not reused from a different table), then ran the one check that
  actually proves correctness: does Urbaine + Rurale equal Total général
  for every préfecture? **It doesn't, for 3 of the 19 préfectures this
  particular table lists** (Lim-Pendé 21+4=25≠26, Mambéré-Kadéï
  24+7=31≠30, Ouaka 22+3=25≠26, each off by exactly 1 - Vakaga doesn't
  appear in this table at all, which is its own separate oddity). Column
  boundaries were verified correct against
  the row's own merged-cell metadata, so this isn't a parsing bug on this
  project's end - it's the source workbook's own published numbers not
  reconciling, on the simplest, cleanest-looking table available. There's
  no way to tell which of the three numbers is right when they disagree,
  so none of them can be published with confidence. This is stronger
  evidence than the earlier abandoned attempt had (that one hit a
  structural risk; this one hit a demonstrated data-quality problem in
  the source itself) and closes the door more firmly: **not worth
  revisiting without contacting ICASEES directly about the underlying
  data**, not just a better parsing approach.

Net: no code changes from this check - a real "checked and no" is itself
the useful output, so it's logged here rather than left unclear whether
this was tried. Phase 4's remaining subnational depth (population,
prix, santé) stays as scoped; these 4 themes stay national-only until a
genuinely new source appears.

## UI polish before Phase 5: the real home page, built at last

The home page was still the Phase 1 placeholder - its own comment said
so directly ("not the real home page from docs/plan.md Sec2.2 ... once
more than two indicators exist"). That condition was met a while ago (86
indicators, 7 themes); this was the first pass at actually building
Sec2.2's spec now that there's real content to show. Prompted by a UI
polish request ahead of Phase 5, with an explicit steer beforehand: keep
the sober, institutional tone (discussed and agreed - no decorative
icons; whatever "life" the page gets should come from real numbers and
the generated sentences already central to this project's voice, not
ornament).

Built Sec2.2's structure exactly: header + search (unchanged), a country
identity strip linking to `/methode/#geographie` (that anchor already
existed), 6 headline cards, a population lead-story block, a 7-row theme
grid, footer. Sec2.2's own explicit call - no map on the home page, since
a national choropleth would force picking one contested population
figure over the others - was followed too.

**Headline cards deliberately mix fresh and stale, per Sec2.2's own
instruction that this is the point, not an oversight:** population
(2025, 1 year old), inflation (2026-04, essentially live), and manioc
price (2026-07) sit next to taux d'achèvement du primaire (UNESCO 2019,
7 years old - flagged in the existing site-wide stale red, `>5` years,
the same threshold every theme page already uses). Reused each theme's
own accent color for its card and its theme-grid row, rather than
inventing home-page-specific colors - same "wayfinding, not decoration"
principle already established (population.astro's région colors, the
theme pages' own `--t-*` tokens).

Theme grid vintages are computed generically, not hand-picked per theme:
a small recursive walk collects every `{period: "..."}` field anywhere in
a theme's JSON and takes the max, since the 7 export scripts don't all
shape their JSON the same way (some have a flat top-level `series`,
others `categories` of indicator blocks) and hand-extracting "the latest
period" per theme would mean 7 different bespoke lookups to maintain.

Lead story reuses population.astro's own build-time SVG bar-chart
technique (scoped to the top 10 préfectures, smaller than the full
20-row version) and its multi-source disclosure block verbatim in shape,
rather than inventing new patterns for the home page specifically.

One real bug caught before shipping: `prix.inflation.value` doesn't
exist - `prix.inflation` is a full indicator block with the value nested
under `.latest.value`, not a flat `{period, value}` pair as briefly
assumed while first drafting the headline cards. Caught immediately by
the build itself (`Cannot read properties of undefined`), not a runtime
surprise.

Home page grew from 8.5 KB to ~26 KB with all this new content - still
far under the 150 KB budget. All 33 pages rebuilt clean.

## Second UI polish round: direct feedback on the new home page, plus sitewide fixes

A round of specific feedback on the home page just built, acted on in
full rather than piecemeal - each change below is small individually but
they interact (the theme grid's redesign and the footer's harmonization
both hinge on the same "what counts as a main theme" question, resolved
once and applied consistently).

**"Population par préfecture" renamed to "Population" everywhere** - it
was already inconsistent before this (some pages said "Population," one
said "Population par préfecture," the home page's old lead-story button
said "Voir par préfecture") - now uniform. Left the population chart's
own `aria-label` alone ("Population par préfecture, estimation 2021...")
since that's describing the chart's actual content, not a nav label -
different question from the one that was raised.

**Added répartition hommes/femmes to `/population/`** - the split
(3 312 532 / 3 343 737) was already sitting in the existing national
`population_totale` observation's own notes field, from the same RGPH-4
source already cited as the page's headline. Promoted to two real
indicators (`population_hommes`, `population_femmes`) rather than left
as free text, and rendered as a small labeled split bar next to the
national disclosure. Median age was asked about too but isn't in any
source checked yet - flagged to chase separately rather than block this
on it.

**"Par sous-préfecture" (population.astro) and "Sous-préfectures"
(place pages) are now collapsible, closed by default** - both are long
tables (85 and up to 8 rows) that were pushing genuinely important
content (the national disclosure, the régional/national comparisons)
below the fold. Implemented as native `<details>`, no JS - a new
`.section-toggle` class styled to match each page's own existing h2
convention (uppercase+bottom-border on population.astro,
larger+top-border on place pages) rather than introducing a third
heading style.

**Removed "À la une" from the home page entirely** - not trimmed, cut.
The headline cards and theme grid already do the "give a visitor the
country in ninety seconds" job Sec2.2 describes; a full lead-story block
underneath was one more thing between the fold and the actual menu.

**Theme grid redesigned around a real objection: "why put a year right
at this level?"** Two decisions here, both from direct answers rather
than guessed: (1) the grid now shows **5 main themes**, not 7 - prix and
agriculture keep their own URLs and are still directly linked (as small
secondary links on Économie's own card), but the top-level menu reflects
that they're conceptually part of économie rather than listing them as
equally-weighted siblings. (2) the freshness date is gone from this
level entirely - a plain one-line description per theme instead.
Freshness stays exactly where it already lived: each theme's own page,
indicator by indicator, which is where a bare date is actually
informative instead of just a number floating next to a name.

**Footer harmonized to an identical 9-link set on every single page** -
`Population, Infrastructures, Éducation, Santé, Économie, Sources,
Méthode, Données, À propos`. The real bug this fixes: every page's
footer previously *excluded a link back to itself* (population.astro's
footer had no "Population" link, prix.astro's had none for "Prix," etc.),
so no two pages' footers ever matched, and it looked accidental rather
than designed. Explicitly asked and confirmed: prix and agriculture are
intentionally *not* in this footer set either - "the footprint should
only point to the main theme pages." They're still reachable via
Économie's page and via search; this is a deliberate narrowing to 9
"main" entries, not an oversight.

**Added a fixed top navigation bar (`SiteNav.astro`)** so a reader on a
long page (the population page is the longest at ~63 KB now) isn't stuck
scrolling back to the top for a way home. One functional icon (a plain
line-drawn house, wayfinding not decoration - consistent with the
"sober, no decorative icons" call from earlier this session) plus the 5
main theme names, always visible. `ThemeToggle.astro` moved inside this
bar as a normal flex child rather than its own independently-fixed
widget - two separately-floating fixed elements in the same corner read
as two competing pieces of chrome, not one coherent one. Styled only
with the base tokens every page already defines
(`--paper`/`--ink`/`--ink-muted`/`--line`), so it renders identically
regardless of which page-specific `--t-*` accent exists - deliberately
neutral, since this bar's job is orientation, not theme identity. Every
page's `main` top padding increased (32px/40px -> 84px) to clear the new
bar's height.

All 33 pages rebuilt clean. Home page actually shrank (26 KB -> 18.7 KB)
with "À la une" gone; the longest page (`/population/`) is ~63 KB,
still far under the 150 KB budget even after the new sexe-split figure
and the fixed nav bar's markup landing on every page.

## Third UI polish round: stale croissance du PIB, a real bug caught fixing it, home page consolidation

**Croissance du PIB on the home page was showing 2021 - the actual bug
was in `index.astro`, not stale data.** Checked live before assuming
anything needed a new source (per the instruction not to restrain to
CLAUDE.md's list if the data was genuinely out of date): the World Bank
WDI API (`world-bank-gdp`, already used for this exact indicator) has
real data through 2025 (4.5%). Then checked further, since that's a
surprising thing to have missed - and found this project's own git
history already had 2025 in `data/observations.csv` from the *very
first* économie fetch, months of session-time before this round. The
World Bank series was never stale; `index.astro`'s headline card was
reading `taux_croissance_pib`'s `.latest` field, which is deliberately
ICASEES's 2021 figure on `/economie/` (administrative data outranks a
modelled estimate there, per méthode.astro's authority ranking - correct
and unchanged) rather than the World Bank series' own last point. Fixed
by having the home page card read the end of `.series` directly instead,
labelled "Banque mondiale" rather than "ICASEES" since it's genuinely a
different number for a different purpose (a quick current snapshot, not
the full ranked disclosure `/economie/` correctly leads with).

**Re-ran `fetch_economie.py` anyway to confirm currency directly rather
than trust the git-history check alone - and caught a real, separate
bug in the process:** the re-run silently deleted ICASEES's own 2
`taux_croissance_pib` rows (2020, 2021) - the script's replace-before-
insert logic filtered by `indicator_id` alone, not `source_id`, so
refreshing World Bank's rows under that same indicator_id wiped out the
*other* source's rows for it too. Restored both rows exactly (verified
byte-for-byte against the last commit) and fixed the filter to key on
`source_id` instead - this would have silently recurred on every future
re-run otherwise, including an eventual automated one. Worth
remembering for any future multi-source indicator: a fetch script's
"idempotent full-replace" is only safe when it owns every row under that
indicator_id, which stops being true the moment a second source starts
contributing to the same one. The re-run's actual data values came back
identical to what was already on disk (confirmed by diffing the
generated JSON) - the value was this bug-catch, not new figures.

**Home page redesign, second pass, per direct feedback that it still
felt like "too many blocks":** the 6 headline cards (each its own
bordered, shadowed box) are now one consolidated `.stat-strip` - a single
bordered surface with 6 columns divided by hairlines rather than 6
separate floating cards. Same information, same click-through behaviour,
one visual object instead of six. The theme grid now also carries one
small line-icon per theme (person/bolt/book/heart/bar-chart), same
stroke style as the nav bar's own home icon so the whole icon set reads
as one family - a considered exception to "no decorative icons," these
are wayfinding glyphs next to text that's already there, not ornament
replacing information.

**Nav bar centered**, per direct request: restructured `SiteNav.astro`
from a left-anchored flex row to a 3-column grid
(`grid-template-columns: 1fr auto 1fr`) so the theme links sit genuinely
centered in the bar regardless of viewport width, with the home icon
pinned left and the theme toggle pinned right in their own tracks.

All 33 pages rebuilt clean, still well under the 150 KB budget.

## Home page, fourth pass: a real composition instead of reactive patching

Asked directly whether the previous 3 passes were the best achievable,
and answered honestly: no. Those passes fixed real, valid complaints one
at a time (remove this, consolidate that, add an icon, center that), but
the result was still a stack of same-weight horizontal bands - identity
strip, stat grid, theme grid - with no real focal point, and no visual
element at all once "À la une" had been cut. Stepped back and did one
composition pass instead of another incremental fix.

**The actual structural change:** one clear hero moment instead of 6
equal boxes. Population - the single most-cited fact about the country,
per CLAUDE.md's own Voice section example - now gets its own distinct
`.hero-stat` panel: a big headline number, a source line, a link through
to `/population/`, and a real chart (the top 8 préfectures ranked,
build-time SVG, same technique population.astro's own full chart uses).
The other 5 quick figures (croissance PIB, inflation, électricité,
achèvement primaire, prix du manioc) are now a de-emphasized single-line
`.ticker` below it - compact label/value/period triples separated by
hairlines, deliberately smaller and quieter than the hero, not another
grid of equal-weight cards. This gives the page actual rhythm (big,
then quiet, then a menu) instead of repeating "here is a grid of boxes"
twice.

This also brings back the one thing the previous pass's "remove À la
une" cut entirely: a real chart. It's folded into the hero this time
rather than reintroduced as its own separate disclosure-heavy section -
the full multi-source disclosure (3 sources, spread %) stays on
`/population/` itself; the home page just needs the headline figure and
a sense of the spread across préfectures, not the complete ranked
argument for which source to trust.

Narrowed `main`'s max-width from 1080px to 900px and centered the hero
text, search box, and identity strip - the previous pass's left-aligned
header (title/tagline on one side, search box on the other, in a wide
1080px container) read more like a theme page's header than a home
page's front door. Search box got a visual upgrade to match being "the
primary navigation, not the menu" per Sec2.2: larger, rounded, with a
subtle shadow, rather than a plain theme-page-style input.

Theme grid cards lightened (no more shadow-lift-on-hover, no left
accent border) since the hero above now clearly carries the page's main
visual weight - the grid's job is to be a clean, obviously-secondary
menu, not compete with the hero for attention.

Honest caveat, stated directly to the user rather than glossed over:
this was verified structurally (build output, rendered HTML, page
weight) exactly like every previous pass - there is still no way to
visually confirm this actually *feels* right without opening it in a
browser, which this session cannot do. Asked the user to look at it
live before treating this as finished.

## Home page, fifth pass: real screenshot, real bug, chart cut again

The user sent an actual screenshot (light on this session's usual text-
only verification) - and it surfaced a genuine rendering bug the
previous pass's structural checks couldn't have caught: Bangui's value
label ("1 425 276") was clipped past the chart's right edge inside the
hero panel. Confirmed the cause - `MARGIN_R` was sized for the shorter
value labels of smaller préfectures, not Bangui's own (the largest, by
definition the widest text in its own chart).

Rather than just widen the margin, cut the embedded chart from the hero
entirely, per the user's own read of the screenshot: the block was
visually heavy, and a multi-row horizontal bar chart with right-aligned
value text is inherently a bad fit for narrow viewports regardless of
how its margins are tuned - the same clipping risk just resurfaces at a
different préfecture once the container narrows. The hero is now
label + big number + one-line source + a link through to `/population/`
only, a single flex row that wraps cleanly at any width since nothing
in it has a fixed pixel geometry. The full ranked chart already exists
on `/population/` itself, so nothing was actually lost by removing the
duplicate.

Also converted `.ticker` from flex-wrap with `border-right` dividers to
a CSS grid (`repeat(auto-fit, minmax(150px, 1fr))`) with `border-left`
dividers, the same pattern already used for the theme-appropriate
`.stat-strip` earlier in the session - the screenshot showed the
flex version's real failure mode too: the 5th item didn't fit the row
and wrapped alone, with no divider matching the row above it. Grid
handles that reflow predictably instead.

Net effect: home page dropped further, 25.6 KB -> 22.1 KB - removing a
whole SVG chart is not just a design call here, it's real bytes back
under budget. This is the first pass in this whole home-page saga
verified against an actual rendering rather than structural checks
alone, and it caught something none of the earlier structural-only
passes did - worth remembering: for anything genuinely about how a page
*looks*, a screenshot is doing verification work no amount of HTML/CSS
source-reading can substitute for.

## Site renamed to "BeAfrika Data"; landing page gets a map watermark and a real intro paragraph

Second screenshot from the user, this time asking for three things
rather than pointing at a bug: an actual name instead of the generic
"Données RCA," a visual element on the home page echoing the country
itself, and a fuller introduction than the one-sentence tagline.

**Name.** Went through two rounds of offered options (Repères RCA /
Kodro / Centrafrique en Chiffres / Boussole Centrafrique, then narrowed
to Centrafrique Data / Kodro Data / Chiffres RCA / RCA Data) before the
user picked their own: **BeAfrika Data** - a stylized nod to "Bêafrîka,"
the country's own Sango name (as in Ködörösêse tî Bêafrîka, the Central
African Republic's Sango name), paired with "Data" to keep the identity
the user asked for explicitly across both rounds. Replaced "Données
RCA" everywhere it appeared: every page's `<title>`, the home page's
`<h1>` (styled as a two-part wordmark - "BeAfrika" in the page's ink
color, "Data" in the population accent, lighter weight), `SiteNav`'s
home-link `aria-label`, and the top-level headers of `README.md` and
`CLAUDE.md` (both left a one-line note that "RCA" stays fine as
shorthand in code/docs/commits - this renames the public-facing brand,
not the whole project's internal vocabulary).

**Map watermark.** Reused `site/src/data/prefecture_maps.json`'s
`country_path` - already-projected, already-simplified real boundary
geometry from the locator-maps work earlier this session, not a new
asset - as a large, very-low-opacity silhouette behind the hero title.
Picked this over drawing the national flag: the flag has an official
spec (colors, proportions, star position) that would need verifying
rather than reusing something already known-correct, while the map
outline is real geographic data this project already fetched, simplified
and verified once. Lower risk, and more in the spirit of a data-driven
reference site than an illustrated flag would have been.

**Intro text.** Expanded the one-sentence tagline into a real paragraph:
what the site actually does (compiles what already exists - censuses,
national surveys, international statistics), the concrete provenance
promise (source, date, geographic level on every figure), and the two
non-negotiable principles from CLAUDE.md's own three - not rounding a
number to look more solid than it is, and stating gaps rather than
hiding them - in plain language rather than restating the file's own
wording verbatim.

Home page grew to 27.8 KB with the map path added - still far under the
150 KB budget. All 33 pages rebuilt clean with the new title everywhere.

## Spelling correction, a user-supplied tagline, and a visible map

Three quick fixes from the next round of feedback:

**Spelling.** The brand name is "BêAfrîka," not "BeAfrika" - a direct
nod to the country's own Sango name spelled correctly (Bêafrîka), not
the stripped-diacritics version guessed at when the name was first
picked. Fixed everywhere in one pass rather than piecemeal: every page's
`<title>`, the home page's `<h1>` wordmark, `SiteNav`'s `aria-label`, and
`README.md`/`CLAUDE.md`'s headers.

**Tagline.** Replaced with the user's own proposed text, corrected for
grammar/spelling but kept faithful to the original structure and
content (their own instruction: "you can rephrase but basically that is
the idea"). States plainly what the site does (aggregates data that
already exists about the country), why (a simple, fast, reliable tool
that makes the data more accessible - "vulgariser"), and the one
concrete promise that matters (every figure carries its source and
year).

**Map visibility.** The watermark's opacity was too subtle to read as
anything - bumped from 0.07 to 0.28 and added a matching stroke
(`stroke-width: 1.5`) so the outline itself stays crisp at that
visibility rather than just being a soft fill blob. Still can't confirm
this looks right without another screenshot, but the fourfold opacity
increase should be an unambiguous, easily-noticed change either way.

## Map redesign: from background watermark to a small emblem

Third screenshot confirmed the guess in the previous entry was wrong in
a specific, useful way: the 0.28-opacity full-width watermark didn't
read as a subtle backdrop - it sat as a solid, fairly saturated
blue-grey mass directly behind the tagline and search box, and its
bottom edge visibly overlapped the identity-strip line below the hero
("7 régions - ..."), muddying text it was never supposed to touch.
Confirms the same lesson as the earlier chart removal: guessing an
opacity/size number for something meant to share space with real copy
is fragile regardless of the specific value chosen, because any value
opaque enough to be visible risks fighting with whatever text happens
to sit on top of it.

Fixed by removing the sharing-space problem entirely rather than
re-tuning the opacity again: the map is now a small (84px), fully solid
emblem sitting in its own block *above* the title, not layered behind
any text. No more absolute positioning, no more z-index juggling on
`h1`/`.tagline`/`#search` to keep them readable over it - none of that
is needed once the graphic and the copy no longer occupy the same
space. Reads as a small crest paired with the wordmark below it, a
common and legible pattern, rather than a hero background treatment
that has to negotiate with everything on top of it.

Home page essentially unchanged in weight (27.5 KB) - same path data,
just restyled.

## Tagline revised again; a phone screenshot confirms the emblem fix worked

A phone screenshot this time confirmed the small-emblem redesign in the
previous entry actually solved the problem it was meant to: the map now
sits fully contained above the title, nothing overlaps, and the whole
hero reads cleanly at that width - including the nav bar's own
narrow-viewport fallback (theme links hidden below 560px, just the home
icon and toggle) not looking cramped either.

Also swapped in a second user-proposed tagline revision, corrected for
grammar (subject doubled with both "qu'elles" and "les données";
"servent elles" in inverted word order where none was called for; "sur
RCA" missing its article; "d'entre" for "d'entrée") but keeping the
new framing intact: leads with "à travers ses données" rather than the
plain "-", and reframes the platform's goal as a single, unique entry
point ("un point d'entrée unique") rather than the previous wording's
"vulgariser ces données." Kept the closing sentence about every figure
carrying its source and year - not explicitly asked to be removed, and
it states the site's single most load-bearing promise.

## Home page: single-point charts, the manioc ticker, and left vs. centered tagline

Three small population/home fixes on 2026-09-13. First, a real rendering
bug: two population indicators (enregistrement des naissances, mariage
avant 18 ans) each have exactly one observation - a single 2019 MICS
point - so their sparkline drew a 1-point polyline, which SVG renders
as nothing visible. Fixed by showing a short note ("Une seule mesure
disponible... - pas d'évolution à montrer") instead of an empty chart
whenever a series has fewer than 2 points; matches the voice rule
against implying a trend from a single observation. The same pattern
exists on education.astro (3 count indicators with 1 point each) but
wasn't touched - flagged to the user, not fixed, since it wasn't asked.

Second, dropped "Manioc, Bangui" from the home page's secondary-stats
ticker on request - a single market-level price sat oddly next to 4
national aggregates (PIB growth, inflation, electricity, primary
completion) in the same row.

Third, the tagline went through three more alignment passes after a
phone screenshot: centered (looked ragged once real sentences wrapped
across lines - centering only reads as deliberate for short, hand-broken
lines, not flowing prose); reverted to left-aligned, capped at 480px so
the block still centers as a unit; then restructured entirely into a
short bold centered lead line ("Explorer la République centrafricaine à
travers ses données !") plus a longer centered detail paragraph below
it, per a further user-supplied structure. Lesson repeated from the map
watermark saga: alignment/centering choices need to be evaluated against
the actual wrapped shape of the actual text, not decided in the
abstract - the same CSS property can look right or wrong purely as a
function of how many words fit per line at a given width.

## Croissance du PIB: recency beats authority ranking on the économie page

CLAUDE.md's default rule ("show the most authoritative figure by
default") had the économie page's Croissance du PIB card showing
ICASEES's 2021 comptes-nationaux figure (3,44%) as the headline, per
méthode.astro's authority ranking (national administrative data outranks
an international modelled estimate) - correct by that rule, but the
user pointed out on 2026-09-13 that a 2021 figure reads as stale on a
page about the current economy, and that économie's numbers specifically
should lead with the most current figure available rather than the
oldest-but-most-authoritative one.

This is a deliberate, page-specific override of the general rule, not a
retraction of it: `build_croissance_disclosure` in
pipeline/export_economie_json.py now sets the headline to World Bank's
latest annual point (2025, an "estime" modelled figure) instead of
ICASEES's. ICASEES's 2020-2021 figures stay fully visible in the "N
sources" disclosure table, still labelled "administratif", with a note
explaining that the headline shown is the most current figure available,
not necessarily the most authoritative one, and linking to Méthode for
the actual ranking. Nothing about the ranking itself changed - the
première page (home) already made this same recency-over-authority call
for its own ticker figure a few hours earlier in the same session; this
just extends it to économie's own page for the same indicator.

A companion request in the same message asked to add real government
budget data to the Finances publiques section, sourced from wherever
necessary (not just ICASEES) since national budgets are published
annually and sometimes twice a year - in progress, see the next entry
once it lands.

## Real 2026 budget data, and a CSV that quietly had the wrong line endings

ICASEES doesn't publish the state budget (comptes nationaux measure
economic output, not government finance), so the new `budget_*`
indicators went to the actual primary source instead: the Ministère des
Finances et du Budget's own "Note d'Information du Marché des Titres
Publics de la RCA" (January 2026), found via web search since
finances.gouv.cf doesn't link it from anywhere obvious. It's a scanned,
image-based PDF with no extractable text - read page by page as images
(the same technique CLAUDE.md prescribes for irregular statistical-yearbook
layouts) to transcribe Tableaux 2, 4 and 5: the Loi de Finances 2026,
adopted by the Assemblée Nationale on 10 December 2025, projects total
resources of 368,43 milliards FCFA against total expenditure of 396,35
milliards FCFA, a voted deficit of 27,92 milliards FCFA (-1,2% of PIB).
Three new indicators (`budget_ressources_totales`, `budget_depenses_totales`,
`budget_solde_global`) carry these as a single 2026 observation each,
explicitly labelled "administratif" and worded in the lead sentence as a
voted projection ("étaient budgétisées à...", "prévoyait un déficit
de...") rather than an observed outturn, since a Loi de Finances is what
parliament approved for the year, not what actually got spent. Logged in
`docs/verification-debt.md`: the source document states no reuse licence
anywhere in its 52 pages, unlike ICASEES's explicit CC BY 4.0.

Also reused the single-point-chart fix from earlier today
(`ind.series.length > 1` guard around the sparkline, else a short note)
on économie.astro's generic indicator cards - the same invisible-chart bug
would otherwise have hit all three new indicators, each a single 2026
observation with nothing to draw a line between yet.

Separately, a real infrastructure bug surfaced while adding these three
rows to `data/sources.csv`: appending them with Python's `csv` module
(`lineterminator="\n"`) made DuckDB's `read_csv_auto` fail to sniff the
file's dialect at all, on every delimiter/quote candidate it tried, with
an error that gave no hint the actual problem was line endings. Root
cause, found by bisection (a file with just 54 of the original rows
parsed fine; the same 54 rows plus a *duplicate* of an existing row, with
no new content, failed the same way): `data/sources.csv` already had
Windows CRLF line endings on disk (54 `\r\n`, apparently left over from
whenever it was last through an actual `git checkout` under this
environment's `core.autocrlf`), while `data/indicators.csv` and
`data/observations.csv` are plain LF throughout, having been edited
in-place by earlier pipeline sessions since their last checkout. Appending
a bare-LF row to the CRLF file left exactly one line with a different
terminator than the other 54, and that inconsistency - not any actual
delimiter or quoting problem - was what broke DuckDB's sniffer completely
(confirmed: `strict_mode=false` parsed the file correctly despite the
mixed endings; `sample_size=-1` alone did not help, ruling out a
sample-truncation theory first). Fixed by normalizing the whole file to
LF, matching the other two CSVs. Lesson for next time: if
`read_csv_auto` ever again fails to "detect a dialect" on a file that
looks fine to the eye and to Python's own `csv` module, check line-ending
consistency (`grep -c $'\r'` vs. total line count) before assuming the
content itself is at fault.

## Dark mode becomes the default, and the dark background gets lighter

Two related requests on 2026-09-13: make dark mode the site's default
(not just an OS-follow option), and the dark background itself read as
"too black" - wanted something closer to dark gray.

Previously every page's dark palette lived behind two guards: a
`@media (prefers-color-scheme: dark)` block (for visitors whose OS
prefers dark and haven't chosen explicitly) and a `:root[data-theme="dark"]`
block (for an explicit in-page choice) - the bare `:root` was always the
light palette, meaning an OS-light visitor with no stored preference saw
light by default. Making dark unconditionally the default meant flipping
which selector is which: the bare `:root` on all 14 page templates now
*is* the dark palette, with `:root[data-theme="light"]` as the explicit
opt-out; the `@media` block is gone entirely since there's no OS-conditional
behavior left to express. This also means dark applies correctly even
with JavaScript disabled - the old approach depended on ThemeInit.astro's
inline script to stamp `data-theme`, which never ran for a no-JS visitor.

`ThemeToggle.astro` simplified from a 3-state Auto/Clair/Sombre cycle to
a plain Sombre/Clair toggle: "Auto" (follow OS) doesn't mean anything
coherent anymore once the default is unconditionally dark rather than
OS-dependent. Choosing Clair stores that choice and stamps the attribute;
choosing Sombre again just clears both, falling back to the new default
rather than storing a redundant explicit "dark" - localStorage only ever
holds "light" or nothing now. `ThemeInit.astro` shrank to match: it only
needs to handle the one opt-out case (a stored "light" preference) before
first paint, since dark needs no attribute to render.

For the "too black" background itself: `--paper` (page background) moves
from `#171912` (~8% lightness) to `#23251F` (~14%), and `--surface` (card
background) from `#1F221A` to `#2B2E27`, keeping the same warm,
slightly-green undertone as the rest of the palette rather than jumping
to a cold neutral gray that would clash with the site's ochre/indigo
accents. Applied identically across all 14 page templates via a script
(the dark-value block was character-identical across every file, verified
per-file before rewriting) rather than by hand, to guarantee consistency;
verified afterward that no `#171912`/`#1F221A` or `prefers-color-scheme`
reference survived anywhere in `site/src/pages/`.

## Phase 5 kickoff: the four items doable without a human decision

Phase 5's checklist has 8 items; 3 of them (a governance partner, an error-reporting
mechanism plus a real public contact address, and the actual launch outreach) need a
decision only the user can make. This pass does the other 4.

**"Ce qui n'est pas mesuré" on the 3 remaining themes.** 4 of 7 theme pages already
had this section; population, infrastructures and prix didn't. Wrote real, specific
gaps for each rather than generic filler - checked each page's actual JSON data
model first so nothing claimed as "missing" was already covered elsewhere. Dropped
one draft bullet for population (a claim that the 2003 and 2025 préfecture columns
aren't directly comparable due to boundary changes) after realizing it wasn't
actually verified against how the pipeline sources the 2003 figure - said nothing
rather than assert an unconfirmed caveat.

**Bulk downloads, reviewed rather than rebuilt.** Found a real bug while reviewing:
`site/src/data/donnees.json` and the actual files under `site/public/donnees/` were
stale copies from 2026-09-12, undercounting every table (`observations.csv` said
5,435 rows; the real file has 5,552) - missing everything added since, including this
week's budget indicators and the population sex breakdown. `pipeline/export_public_data.py`
isn't wired into any routine rebuild step - nothing re-runs it when `data/*.csv`
changes, so it goes stale silently. Re-ran it now; still worth building a proper
"run everything" step before launch so this can't recur unnoticed.

**A print stylesheet.** Added `@media print` to all 14 page templates, forcing the
light palette's own token values regardless of the visitor's dark/light choice (most
browsers strip background images/colors from print by default, but not text color -
a dark-mode visitor printing a page would otherwise get pale text on white paper) and
forcing `body`'s background to plain white. Hid the fixed `SiteNav` bar (chrome, not
content) centrally in `SiteNav.astro` rather than per-page, and hid the home page's
search box specifically - both have no meaning on paper.

**A real accessibility pass**, not a nominal one - found and fixed actual bugs rather
than just adding ARIA decoration:
- Every `<th>` sitewide (37 across 7 files) had no `scope="col"` - added it
  everywhere; screen readers can't reliably associate header and data cells without
  it, especially outside a `<thead>`.
- The home page's search input had only a `placeholder`, which isn't a reliable
  accessible name - added a real `aria-label`. Its live result-count status span had
  no `aria-live`, so a screen-reader user typing would never hear how many results
  came back - added `aria-live="polite"`.
- No skip-to-content link existed anywhere, meaning a keyboard user had to tab
  through the fixed nav bar on every single page load - added one, centrally, in
  `SiteNav.astro`.
- Computed actual WCAG contrast ratios for every badge color pair rather than
  eyeballing them (the same rigor as the earlier dark-mode `--ink-faint` fix): found
  the light-mode "estime" badge (`--ochre` text on `--ochre-soft` background,
  `#B8790F` on `#F1E3C6`) at 2.86:1 - a real, pre-existing fail, well under the 4.5:1
  AA threshold for normal-size text, unrelated to and predating this session's dark
  mode work. Darkened `--ochre`'s light value to `#8C5A0C` (4.62:1) across all 10
  files that declare it; checked every other place it's used (an SVG chart label on
  prix.astro, a progress-bar fill on population.astro) to confirm nothing else broke.
  Heading hierarchy and focus-outline suppression were also checked sitewide and
  came back clean - not everything found was broken.

## Nine sources.csv rows were in English, on a French site

Caught on the /sources/ page (spotted by the user): the Encyclopædia Britannica
row's licence note and access note were plain English sentences, rendered directly
to readers. CLAUDE.md's own convention ("code, comments, commit messages... in
English; only user-facing content is French") already covered this - `data/sources.csv`'s
`licence_notes`/`access_notes`/`geography_vintage`/`update_cadence`/`authority_rank`
fields are reader-facing (rendered on /sources/ inside the "Note sur la licence" and
"Comment cette source est utilisée ici" disclosures, and `geography_vintage`/
`update_cadence` sit directly in each card's visible meta row, not hidden behind a
click) - this had just never been checked as a body of content before.

Scanned every row for genuine English prose rather than trusting a keyword match
(early passes over-matched: "via" and "and" both appear legitimately in French
text - "via l'API", "PIB, PIB par habitant et..." - so the real filter needed at
least 2 strong English-only markers - "the", "used", "fetched", "only", "with" -
not just one). Found 9 rows written entirely in English, all evidently from earlier
sessions before this convention was enforced as strictly: `cod-ab-caf`,
`wikipedia-fr-prefectures`, `citypopulation-de-caf`, `britannica-car-history`,
`loi-21-001-2021`, `icasees-ihpc-dashboard`, `minurbanisme-rca-regions`,
`who-gho-health-workforce`, `icasees-projection-population-2025`. Translated all 9
in full, preserving every fact, number, date and URL exactly - only the descriptive
prose changed language. Also used the pass to fix a couple of things noticed along
the way rather than translate stale content faithfully: `minurbanisme-rca-regions`'s
note still said the régions-préfectures mapping rested on one source, when this
session's own earlier work had already found a second one - updated to reflect
that; `who-gho-health-workforce`'s note now mentions the live re-check that already
happened.

**Deliberately left as-is:** `dataset_name` fields (e.g. "GDP, GDP per capita and
GDP growth..." for World Bank, "Individuals using the Internet, % of population"
for a WDI indicator) stay in their original language - these are citations of the
source's own actual published title, not this project's own descriptive prose, the
same way a French text would cite an English book's real title rather than
inventing a translated one.

**Real bug found while fixing this:** several theme pages' own JSON files
(`population.json`, `prix.json`, `sante.json`) embed a source's producer/dataset
name directly at export time via a live join against `data/sources.csv` - so fixing
the CSV wasn't enough on its own; every export script that touches an affected
source needed re-running, or the fix wouldn't actually reach the live page. Caught
by re-scanning every page's actual rendered text for English words after the CSV
fix, not by assuming the CSV fix was sufficient: population.astro's footer still
said "citypopulation.de (relaying ICASEES data, per the page's own stated data
source)" until `export_population_json.py` was re-run.

Also checked the whole site for other leftover internal-instruction content (the
kind of thing the "À FAIRE" TODO boxes removed earlier this session were) - scanned
every rendered page for TODO/FIXME/placeholder/WIP-style markers. Found nothing
beyond the search input's legitimate HTML `placeholder` attribute.

**Follow-up, same day:** the previous fix didn't go far enough - the user pointed out
`citypopulation-de-caf`'s `dataset_name` was still in English ("Central African
Republic: Administrative Division (Prefectures and Sub-Prefectures)"). Checked
whether that was actually the source's own literal published title before deciding
whether to translate it (it wasn't - the real page heading is just "Central African
Republic: Administrative Division"; the parenthetical was this project's own
English commentary from an earlier session, not a quotation). That reopened the
whole "keep dataset_name in its original language" judgment call from the earlier
entry - checked precedent properly this time instead of assuming: UNESCO UIS's own
`dataset_name` rows were already translated to French with the API code kept in
parens (e.g. "Taux d'achèvement (...) (CR.1, CR.2, CR.3)"), while every World Bank
row was left in raw English. Inconsistent, not a deliberate two-tier policy - the
World Bank ones were evidently added in one bulk pass that never got the French
treatment. Translated all 35 remaining English `dataset_name` fields (`cod-ab-caf`,
`citypopulation-de-caf`, `britannica-car-history`, `wfp-food-prices-hdx`,
`who-gho-health-workforce`, and 30 `world-bank-*` rows) to match the UNESCO
convention: French description, technical API/indicator code left as-is in
parentheses since that's a literal identifier, not prose.

Regenerated every export script this time, not just the three that broke last
time - dataset_name (unlike the licence/access notes from the first pass) is
embedded and rendered on theme pages too (population/economie/education/
infrastructures/sante/agriculture/prix), not just on /sources/. Re-ran the full
rendered-text scan afterward; every remaining English-looking match checked by hand
and confirmed legitimate (a literal API code, a URL, or an organization's own
official name like "World Food Programme" or a cited page title like "Terms and
Conditions" - the same category of exception as `dataset_name` itself, applied
consistently rather than case-by-case).
