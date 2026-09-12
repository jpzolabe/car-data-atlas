# Decisions

## 2026-09-12 — Theme pages built flat, not under /themes/ as the sitemap specifies

`docs/plan.md`'s site map puts theme pages under a `/themes/` prefix
(`/themes/population`, `/themes/prix`, etc.), separate from place pages under
`/lieux/`. The first two real pages were built flat instead (`/population`,
`/prix`), matching the flat top-level pages (`/sources`, `/methode`) rather
than the plan's nested structure — not a deliberate choice, just what
happened. Noticed while adding a third theme page (`/infrastructures`).

**How to apply:** kept it flat for this third page too, to stay internally
consistent (all existing theme pages flat) rather than create a third,
mixed pattern (some flat, some nested) which would be worse than either
option alone. A bulk rename to match the plan's `/themes/` structure is
still on the table — cheap now (3 pages, no public URLs exist yet since
Cloudflare isn't connected), much more annoying once `/lieux/` place pages
exist and there are real inbound links. Revisit before Phase 4 (descending
to place pages) rather than after.

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

## UNESCO UIS Data API — endpoint found via its own error message, not documentation

Neither the UIS's public docs page (`api.uis.unesco.org/api/public/documentation/`,
a Swagger UI that doesn't render as fetchable text) nor the Python `unesco_reader`
package's own documentation spelled out the actual REST URL. The old bulk-download
pattern (`download.uis.unesco.org/bdds/...`) 404s — UIS has moved off it. Resolved
by requesting `api.uis.unesco.org/api/public/data/indicators` with no query
parameters at all: it returns HTTP 400 with a JSON body naming its own required
parameters (`geoUnit`, `indicator`), which was enough to construct a working call
directly (`?geoUnit=CAF&indicator=CR.1`). No API key required. Worth remembering
as a technique generally: a REST API's own validation error is sometimes a faster
path to its shape than either third-party docs or a wrapper library's source.

## Education widened from 1 to 14 indicators — checked live per indicator, not assumed from the catalogue

CLAUDE.md's own indicator-ID example (`taux_achevement_primaire`) was illustrative,
not a scope limit — stopping at one indicator when the same free, no-key API had
real CAF data across completion, enrollment, retention and literacy would have been
under-building for no real reason. The UIS indicator catalogue
(`/api/public/definitions/indicators`, ~5,000 entries) reports data availability
*globally*, not per country — a candidate indicator can show thousands of records
worldwide and zero for CAF. Every one of the 17 UIS codes actually used here
(`data/sources.csv`, `pipeline/fetch_education.py`) was confirmed by querying
`?geoUnit=CAF&indicator=<code>` directly and checking for non-empty `records` before
being added, not by trusting the catalogue's description. The API accepts a
comma-separated indicator list, so all 17 were fetched in one call.

## Education sources grouped by methodology family, not one row per indicator

`data/sources.csv` has one row per *methodology*, not per indicator: completion
(survey vs. modelled — already had 2 rows for the 1-indicator version, broadened to
cover 3 levels rather than renamed to 6), one row for the 9 administrative/EMIS-style
indicators (enrollment ratios, repetition, survival, out-of-school), one for the 2
literacy indicators. All 14 indicators share one producer and one API endpoint
pattern; a row per indicator would have been 14 near-identical rows saying the same
thing about licence and access method 14 times. The administrative-family row is
honest about what it doesn't know: the API response gives a value and a year, not a
methodology tag, so whether each point is genuinely EMIS-administrative data or
something else per-indicator isn't confirmed — logged in
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
(not all 45 modelled years) — comparing every modelled year against one survey
year would conflate "these two sources disagree" with "time has passed," which
is a different, less honest question.

## Education page reordered: one headline figure, then the student's actual path

The 14-indicator version led with three large multi-source disclosure blocks
(all 3 completion levels) immediately after the lede — the page's heaviest
content shown first, with no orienting summary. Two fixes: (1) a lightweight
headline block (one number, one generated sentence, a link down to the full
breakdown) now sits above the category sections, using primary completion —
the single most legible "state of education" figure and the one CLAUDE.md's
own indicator-ID example names. (2) The four categories were reordered from
achievement-first (Achèvement, Scolarisation, Rétention, Alphabétisation) to
the actual causal chain a student goes through: Scolarisation (does a child
enroll) → Rétention et abandon (do they stay, repeat, or drop out) →
Achèvement scolaire (do they finish) → Alphabétisation (the long-run societal
result). Leading with the outcome before the causes that produce it reads
like starting a story at the ending — this generalizes beyond this one page:
default to whatever order lets each section explain what feeds into the
next, not whatever order the data happened to get fetched in.

## Prix widened from 1 to 5 indicators — same file, zero new sourcing

Part of a deliberate pass to bring population/prix/infrastructures up
towards éducation's depth (all three had exactly one indicator). Unlike
éducation's UIS widening, this cost nothing in new sourcing: the IHPC
dashboard file (`pipeline/fetch_ihpc.py`) already downloaded for
`prix_ihpc_global` has 12 COICOP sub-category rows and a published
"Inflation" row that were simply never parsed — `prix.astro`'s own gap-note
already said so. Added the inflation rate plus 3 named sub-categories
(alimentation, santé, transports) — the ones the existing gap-note text
already promised, not an arbitrary subset. `IND11` (Enseignement) was
checked and deliberately skipped: only 76 of 136 months are populated,
unlike every other row's 136/136. `extract_rows()` in `fetch_ihpc.py` was
generalized from one hardcoded row lookup to a config dict
(`INDICATOR_CODES`) so adding a 6th indicator later means one dict entry,
not a new function. The published inflation rate doesn't reconcile with a
naive recomputation from the index — logged rather than silently
reinterpreted, see `docs/verification-debt.md`.

## Infrastructures widened 1 -> 5, JSON/export renamed off "electricite"

Same completion pass as prix. Added 4 World Bank indicators — internet use,
mobile subscriptions, basic drinking water access, basic sanitation access
— each confirmed live for CAF before adding (all 4 have real data through
2022-2024, genuinely fresher than most of education's indicators).
Électricité stays the page's headline/hero (CLAUDE.md's own domain fact
cites it, and it already has an independent MICS cross-check); the other 4
are additive cards below, following the headline-then-breakdown rule.

`pipeline/export_electricity_json.py` / `site/src/data/electricite.json`
were retired in favour of `export_infrastructures_json.py` /
`infrastructures.json` — the old names stopped describing the theme once it
covered more than electricity, and renaming now (before more pages or
scripts came to depend on the old name) was cheaper than renaming later.
`fetch_infrastructures.py` is a new script alongside (not replacing)
`fetch_electricity_access.py`, since the World Bank API takes one indicator
code per URL (unlike UIS's comma-separated list) — four indicators means
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
total (1992, one intermediate year, 2021 — depends on infrequent household
surveys), and `recettes_publiques_pib` stops at 2021. CLAUDE.md also notes
ICASEES has its own GDP rebasing (2019 base) underway — these World Bank
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
éducation, santé, économie, agriculture — 58 indicators total.**
