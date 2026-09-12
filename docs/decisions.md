# Decisions

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
