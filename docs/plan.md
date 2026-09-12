# Données RCA - Work plan and product specification

Companion to `CLAUDE.md`. That file holds the standing rules; this one holds the
build plan and the detailed product spec.

Compiled September 2026. Assumes ~2–3 days per week of work. Total horizon to a
public launch: roughly six months.

**Rule zero applies to this document too.** Where a source is named without a URL, it
is because the URL was not verified. Search for it and confirm before use. Do not
invent links.

**This whole document is a working plan, not a contract.** Phases, timings and
"done when" criteria below are the current best guess, meant to be adjusted as Phase
1 actually teaches you things - see `CLAUDE.md`'s "how to read this document." In
particular: building v1 doesn't wait on every source's licence being fully cleared or
every figure being cross-verified - real logged gaps go in
`docs/verification-debt.md` and get resolved before v1 is presented as finished, not
before each step of building it.

---

# Part 1 - What is being built

## 1.1 The product in one sentence

A public reference work about the Central African Republic: national figures across
themes, drillable down to région, préfecture and sous-préfecture, where every
number carries its source and its date, and where the absence of data is stated rather
than hidden. (Commune/localité dropped from scope 2026-09-05 - see `CLAUDE.md`'s
scope note. Sous-préfecture is the current floor.)

Tagline for the site: *Explorer la République centrafricaine - ce que disent les
données, d'où elles viennent, et ce que personne n'a encore mesuré.*

## 1.2 Who it is for

In priority order. These are the people whose use validates the project.

1. **Central African journalists** - RJDH (Réseau des Journalistes pour les Droits de
   l'Homme), the Association des Factcheckers de Centrafrique, RMCC (Réseau des médias
   communautaires centrafricains), Radio Ndeke Luka. They need to check a figure
   quickly and cite it defensibly.
2. **NGO and ministry staff** sizing an intervention or writing a proposal.
3. **Central African students and the diaspora** - curious, not analytical, arriving
   via a shared link.
4. **Researchers** - the group most likely to find it, least important to serve.

Design test: if a journalist at RJDH would not open it twice, something is wrong.

## 1.3 What it is not

- Not a data portal. Not a catalogue of datasets. Nobody wants a file.
- Not a dashboard, and no composite indices or "vulnerability scores" - these require
  silently choosing one contested figure over another.
- Not a GIS product. Maps are navigation and illustration, not the subject.
- Not a competitor to ICASEES. It is a layer that makes their CC BY 4.0 output usable.
  Their attribution appears on every page carrying their data.

---

# Part 2 - Product specification

## 2.1 Site map

```
/                          Accueil - national picture
/themes/population         Theme page (national + breakdown)
/themes/economie
/themes/prix
/themes/sante
/themes/education
/themes/agriculture
/themes/infrastructures
/lieux/                    Index of places, searchable
/lieux/prefecture/ouaka    Place page
/lieux/sous-prefecture/bambari
/couverture                Coverage view - what is and isn't known
/sources                   Source register
/methode                   Methodology, incl. the authority ranking rule
/donnees                   Bulk downloads and the crosswalk
/a-propos                  About, licence, contact
```

All URLs French, lowercase, accent-free slugs. English mirror later under `/en/`,
not at launch.

## 2.2 The home page

Purpose: give a curious visitor the country in ninety seconds, and give everyone else
a way down.

**Structure, top to bottom:**

1. **Header** - site name, a prominent search box with placeholder
   `Rechercher une sous-préfecture, une préfecture…`. The search box is the primary
   navigation, not the menu.

2. **Country identity strip** - "République centrafricaine", then a quiet line:
   `7 régions · 20 préfectures · 85 sous-préfectures`. This line is itself a link to
   `/methode#geographie`, because those numbers are contested and the site should
   admit it from the first screen. (Counts verified against COD-AB v02 and the 2020
   reform on 2026-09-05 - see `CLAUDE.md`'s administrative-geography table. The 7
   régions → préfectures mapping is still open.)

3. **Headline cards** - 4 to 6 stat cards. Each has: label, large number,
   and beneath it a source-and-date line coloured by freshness.
   Candidates: population, croissance du PIB, inflation annuelle, accès à
   l'électricité, taux d'achèvement du primaire, prix du manioc.
   *Deliberately mixes fresh and stale figures.* Showing that electricity access
   comes from a 2018–19 survey is the point.

4. **Lead story block** - one theme given full treatment on the home page, currently
   population and the census. Chart, generated sentence, source line, the
   "N sources" disclosure link, and two buttons: `Données CSV`, `Voir par préfecture`.
   This block rotates as new data lands; it is configuration, not hard-coded.

5. **Theme grid** - one row per theme, showing the theme name and the vintage of the
   most recent data in it, colour-coded. This is simultaneously a menu and a coverage
   summary. A caption explains the colours.

6. **Footer** - licence, sources, contact, link to the repository.

**No map on the home page.** A national choropleth would force choosing one contested
population figure and hiding the other three.

## 2.3 Theme pages

The workhorse of the site. One per theme.

**Structure:**

1. **Theme header** - name, one-sentence description of what the theme covers, and a
   coverage summary: how many indicators, oldest and newest vintage, deepest
   geographic level reached.

2. **Headline figure** - required once a theme has more than one or two
   indicators, added 2026-09-12 after the éducation page shipped with 15
   indicators and no orienting summary (a reader hit three large multi-source
   disclosure blocks before anything else). One number, one generated
   sentence, a link down to the full breakdown - no chart or table here. Pick
   the single most legible, most commonly-understood figure in the theme as
   the headline, not necessarily whichever indicator happened to be added
   first.

3. **Indicator blocks**, one per indicator, repeated. Where indicators fall
   into natural categories (as éducation's completion/enrollment/retention/
   literacy do), group them, and order both the categories and the
   indicators within them by logical or causal sequence - e.g. éducation
   goes scolarisation → rétention → achèvement → alphabétisation, a
   student's actual path, not achievement-first - rather than by fetch order
   or an arbitrary list. Leading with an outcome before the causes that
   produce it reads like starting a story at the ending. Each block contains:
   - Indicator name and current value at national level
   - A chart - line for time series, horizontal bars for composition or ranking
   - **One generated French sentence** describing what the chart shows
   - A source line: producer, dataset, date of observation, date retrieved, licence
   - The `N sources` disclosure link where more than one source publishes it
   - A `Niveau le plus fin : sous-préfecture` badge, so the reader knows how deep it goes
   - Buttons: `Données CSV`, `Image PNG`, `Intégrer`

   **Rates need raw figures alongside them, where a real one is published.**
   Added 2026-09-12 after santé/économie/agriculture shipped as %-only pages
   (doctor *density* but never a doctor count, GDP *share* of trade but never
   the dollar figure). A rate alone hides scale - "0.074 doctors per 1,000
   people" doesn't land the way "532 doctors nationally" does. Prefer a
   second real published series (World Bank/FAO often publish both - e.g.
   `NE.EXP.GNFS.ZS` and `NE.EXP.GNFS.CD` are the same trade data as % of GDP
   and as current US$) over computing one. When no absolute figure is
   published anywhere (checked, not assumed - santé's doctor/bed density had
   no raw counterpart in World Bank's WDI at all), a second API is worth
   trying before giving up (WHO's GHO OData API had real doctor/nurse
   headcounts WDI didn't). Only when *that* comes up empty too is a computed
   estimate (e.g. density × population) acceptable - rule zero permits this
   as arithmetic on two real numbers, not invention, but it must be labelled
   as calculated, not presented as a directly-published figure, and dated to
   the same year as the input data it's built from (a 2011 density paired
   with a 2011 population, never a current one - see docs/decisions.md).

4. **Breakdown section** - a table or bar chart of the indicator by région or
   préfecture, with links down to place pages. Only rendered for indicators that
   genuinely reach that level.

5. **Ce qui n'est pas mesuré** - an explicit list. For the education theme, for
   example: no data on teacher qualifications since X, no data on secondary
   completion by sous-préfecture, exam results not published in machine-readable form.
   **This section is written by hand, not generated.** It is the most valuable
   content on the page and the least automatable.

6. **Related themes and next steps.** Where a theme is conceptually part of
   another (prix and agriculture both sit inside "the economy" the way most
   real economic dashboards treat them - IMF Article IV, World Bank country
   pages, Trading Economics all fold prices and sector breakdowns into one
   view; `CLAUDE.md`'s own original theme list even said "agriculture et
   prix" as one theme before this session split it into three pages),
   the parent theme's page carries a brief summary card for each related
   theme - headline figure, one sentence, a link to the full page - rather
   than merging the pages or moving their URLs. This is presentation only:
   the related theme's own JSON/indicators stay owned by its own export
   script. The Astro page (e.g. `economie.astro`) imports the related
   theme's already-built JSON (`prix.json`, `agriculture.json`) directly for
   the summary card; the parent theme's own export script
   (`export_economie_json.py`) never touches that data - no duplication in
   the pipeline layer, only in what's rendered. Added 2026-09-12 - see
   `docs/decisions.md`.

## 2.4 Place pages

Reached by search or by drilling down, not from the home page.

**Structure:**

1. **Identity block** - place name, administrative level, parent chain
   (`Bambari · sous-préfecture · préfecture de l'Ouaka · [région - mapping not yet
   verified]`), alternate spellings, the codes each source uses for it, and the
   version of the geography being shown with its validity dates. This block is
   unusual and it is a differentiator - no other product shows it.

2. **Headline cards** - 3 to 4 figures for this place.

3. **Locator map** - small static SVG, the place highlighted within the country. Not
   interactive.

4. **Theme sections** - the same indicator-block pattern as theme pages, but scoped to
   this place, and only for indicators that reach this level.

5. **Ce que l'on sait** - the freshness grid. Every theme, with the vintage of the
   most recent data for this specific place, or `aucune donnée`.

6. **Comparison** - this place against its siblings (other sous-préfectures in the
   same préfecture) and against the national figure. Simple bars. This is the most
   engaging interaction on the site; make it easy.

7. **Children** - links to the places inside this one. Empty by design at
   sous-préfecture level - that's the current floor, nothing renders as a dead end.

8. Downloads: `CSV de ce lieu`, `GeoJSON`.

## 2.5 The multi-source disclosure

The mechanism that makes the whole thing trustworthy.

**Resting state:** one figure, plainly, with source and date, and beside it a quiet
`4 sources ›` link.

**Expanded state**, in place, no navigation: a stack of rows, one per source. Each
row: the value, the producer and dataset, a label
(`provisoire` / `projection 2003` / `modélisé` / `source non citée`), and the year.
Below the stack: the spread between highest and lowest, as a percentage.
A link to `/methode` explaining how the default was chosen.

**Cost note:** most indicators have one source. The link then reads `1 source` and
nobody clicks it. The expensive case is real for population, health facilities and
school counts - perhaps five indicators of twenty-five.

## 2.6 The coverage view

`/couverture` - the single most novel page on the site.

A matrix: places down the rows (préfectures at first, sous-préfectures later), themes across
the columns, each cell coloured by the vintage of the most recent data. Plus a national
choropleth showing data completeness by préfecture - the one map where a single
authoritative figure is not required, because the value being mapped is *how much we
know*, not a contested statistic.

Beneath it, prose: the three largest gaps in national knowledge, updated as things
change. At time of writing those are road network data dating from 2009, electricity
access measured only in a 2018–19 survey, and development project data lacking
reliable sub-national geography below préfecture.

## 2.7 The sources register

`/sources` - one row per source: producer, dataset name, what it covers, geographic
level, vintage, update cadence, licence, date last retrieved by us, and a link.
Sortable. This page is what makes an institution take the project seriously.

## 2.8 The methodology page

`/methode` - publishes the rules, which is what separates this from an opinion.

- **The authority ranking.** National census > national survey > national
  administrative data > international modelled estimate > unattributed portal figure.
  Ties broken by recency of observation, not recency of publication.
- **The geography problem**, stated plainly with the version table.
- **How freshness colours are assigned** - the thresholds, per theme, because a
  three-year-old price series is stale while a three-year-old census is current.
- **How sentences are generated** - templates, deterministic, no model.
- **How to report an error.**

## 2.9 Cross-cutting behaviours

**Freshness colouring.** Three states - current, ageing, stale - with thresholds set
*per theme*, not globally. Prices stale after 6 months; census current for 10 years;
health facility lists ageing after 2 years. The thresholds live in `sources.csv` and
appear on `/methode`.

**Missing data.** Never render an empty chart, a zero, or a dash. Render an explicit
statement: `Aucune donnée disponible pour ce lieu.` plus, where known, why -
`Cet indicateur n'est publié qu'au niveau national.`

**Downloads.** Per chart, per place, per theme, and in bulk. Always CSV, always with a
companion metadata file naming the sources.

**Embeds.** Every chart embeddable as an iframe or downloadable as PNG with the source
line burned in. This is how a journalist uses you, and how you get attribution.

**Share cards.** For each place and each major finding, generate a static PNG at build
time - one number, source, date, in French, sized for Facebook. Facebook is the
dominant mobile social platform in CAR; this is the distribution channel, not the
website.

**Print.** A clean print stylesheet. People will print place pages.

## 2.10 Visual character

Reference work, not analytics tool. Dense with text and dates, light on graphics.
Closest relative: a well-made encyclopedia entry. Generous whitespace, one accent
colour, freshness colours reserved exclusively for vintage signalling so they always
mean the same thing. System fonts or one variable font. No animation.

Charts: line (time series), horizontal bar (composition and ranking), population
pyramid (once, for the census), locator map, choropleth (coverage only). Five types.
Nothing else.

---

# Part 3 - Data model

`data/` is the source of truth. Everything else is derived.

## 3.1 entities.csv

One row per administrative unit *per version*.

| column | notes |
|---|---|
| `entity_id` | stable forever, never reused. Format `cf-p-ouaka-v1` |
| `name_fr` | canonical French name with accents |
| `slug` | accent-free URL slug |
| `level` | `pays` / `region` / `prefecture` / `sous_prefecture` - commune/localite dropped from scope 2026-09-05, see `CLAUDE.md`. `marche` added 2026-09-12 for WFP food-price markets - a point, not an administrative area, and not part of the pays→region→prefecture→sous_prefecture hierarchy (its `parent_id` is the prefecture it sits within, for lack of a better anchor, not a claim of administrative nesting) |
| `parent_id` | entity_id of parent, empty for country |
| `valid_from` | ISO date. When this version came into effect |
| `valid_to` | ISO date or empty for current |
| `superseded_by` | entity_id, where a unit was split, merged or renamed |
| `notes` | free text, e.g. the decree that created it |

**A new version of a place is a new entity.** Never mutate an entity when geography
changes.

## 3.2 aliases.csv

`entity_id`, `source_id`, `alias`, `alias_type` (`name` / `code` / `pcode`).

Every spelling, every accent variant, every source's internal code. This table is what
makes joins possible and is the single most valuable artefact of the project.

## 3.3 sources.csv

`source_id`, `producer`, `dataset_name`, `url`, `licence`, `licence_notes`,
`geography_vintage`, `update_cadence`, `retrieved_at`, `staleness_thresholds`,
`authority_rank`, `access_notes`.

`authority_rank` is what drives default selection. `licence_notes` flags
redistribution restrictions.

## 3.4 indicators.csv

`indicator_id`, `name_fr`, `definition_fr`, `unit`, `theme`, `geographic_floor`,
`sentence_template_id`, `higher_is_better`.

`geographic_floor` is the deepest level the indicator genuinely reaches. Set it from
observation, never from hope.

## 3.5 observations.csv

`entity_id`, `indicator_id`, `period`, `value`, `unit`, `source_id`, `retrieved_at`,
`quality_flag`, `notes`.

Long format. `quality_flag` carries `provisoire`, `estime`, `projete`, `non_valide`.

## 3.6 unresolved.csv

Every case the crosswalk could not resolve: the source, the string, why it failed.
**This file is a deliverable, not a failure log.** Publishing it invites correction.

## 3.7 geo/

GeoJSON per entity per version, plus simplified derivatives for rendering. Keep raw
and simplified separately; never overwrite raw.

## 3.8 raw/

Immutable snapshots of everything fetched, organised `raw/{source_id}/{iso_date}/`.
Never edited, never deleted. When an extraction improves, re-run against the snapshot.

---

# Part 4 - Source inventory

Organised by theme. **Verify every URL before use.**

## 4.1 Geography - do this first

| Source | What | Notes |
|---|---|---|
| OCHA COD-AB (HDX), **v02 - fetched and used, 2026-09-05** | Admin boundaries with p-codes | **Verified, not assumed:** 20 préfectures, 85 sous-préfectures, no commune/localité layer in this version. `isopen: false` on HDX with a "humanitarian purposes only" usage caveat - see `docs/verification-debt.md`. Built `data/entities.csv`/`aliases.csv` for pays/préfecture/sous-préfecture from this snapshot. |
| OCHA COD-EM (HDX) | Edge-matched version | For cartography; does not replace COD-AB. Not yet fetched. |
| OCHA COD-PS (HDX) | Population statistics layer | **Built on the 2003 census projected to 2015.** Widely used and badly out of date. Not yet fetched. |
| December 2020 reform (adopted 10 Dec 2020) | 20 préfectures, 84 sous-préfectures | Corroborated via Oubangui Médias/Xinhua/Wikipedia reporting (2026-09-05) - matches COD-AB v02's préfecture count and the specific 4 new préfectures (Mambéré, Lim-Pendé, Ouham-Fafa, Bangui) exactly. Primary decree text/number still not located; the 84-vs-85 sous-préfecture gap against COD-AB is unexplained - both logged in `docs/verification-debt.md`. |
| ICASEES RGPH-4 cartography pages | Population by commune (2021), by ville and by sexe (2024), projections 2022–23 | On icasees.org under actualités/rgph-4 |
| RGPH-4 provisional results | 7 régions: Plateaux, Équateur, Yadé, Kagas, Fertit, Haut-Oubangui, Bas-Oubangui | Published ~23 Aug 2026 |
| citypopulation.de | Admin hierarchy with 2003 census and 2021 cartography figures | Useful cross-check. Notes prefectures went 17 → 20 in 2021. |
| OpenStreetMap | Boundaries, roads, facilities | Coverage largely from the 2013–14 HOT activation |

**The deliverable:** a crosswalk reconciling all of these.

## 4.2 Population

- ICASEES RGPH-4 provisional results (2025): 6,656,269 - 3,312,532 M / 3,343,737 F,
  density 10.7/km². Marked *données non encore validées*.
- Historical censuses: 1975, 1988, 2003. ICASEES publishes the 1975 report; the NADA
  catalogue holds the 1975 census entry.
- COD-PS (2003 projected to 2015).
- WorldPop modelled gridded estimates.
- AfDB portal figures - often unattributed; treat as lowest authority.

**Expect the census to shift every per-capita figure.** Most published statistics about
CAR assume roughly 5.5 million.

## 4.3 Économie

- ICASEES national accounts 2019–2021, published July 2026.
- GDP rebasing to a 2019 base year under SNA 2008 - in progress; there is an
  aide-mémoire on the ICASEES site.
- IMF e-GDDS National Summary Data Page, launched May 2025, hosted on
  car.opendataforafrica.org/nsdp. Covers national accounts, prices, government
  operations, debt, monetary, external sector. **JavaScript-rendered** - you may need
  a headless browser, or find the underlying SDMX feed, which the AfDB platform is
  documented to support.
- BEAC (Bank of Central African States) for monetary and balance of payments.
- World Bank indicator sets via API.

## 4.4 Prix

- **ICASEES IHPC** - monthly consumer price index, series 2015–2026, published
  monthly by the 10th per their dissemination calendar. Available as national index,
  monthly by locality, and annual by locality. Also monthly bulletins as PDFs.
  **This is your best time series: national, monthly, official, current, CC BY 4.0.**
  Start here for the first pipeline.
- WFP food prices via HDX - market-level, with coordinates, covering staples.
  Contributors include ACF, ACTED, ICASEES via FAO GIEWS, and WFP mVAM.
  Geographic floor is the market, a point, not an area.

## 4.5 Santé

- ICASEES statistical yearbooks and the AfDB portal's SANTE section
  (car.opendataforafrica.org/ymxfwg), which includes health establishments.
- MICS - 2000, 2006, 2010, 2018–19, and **MICS7 launched August 2026**, results
  expected during the project's lifetime.
- DHS - 1994–95, plus subnational DHS data on HDX.
- ENSNM (nutrition and mortality surveys) 2014, 2018 - in the NADA catalogue.
- Health workforce census - a *Recensement général des personnels du secteur de la
  santé*, report dated July/August 2024, available via a WHO extranet.
- **Verify these, mentioned but not confirmed:** WHO HeRAMS facility monitoring,
  healthsites.io facility coordinates.
- HDX travel-time-to-nearest-health-facility raster, 100m resolution, from the Data
  for Children Collaborative. Already exists - do not rebuild.

## 4.6 Éducation

- **ICASEES education statistical yearbooks** - 2015-16, 2022-23, 2024-25, published
  in Word *and Excel*. Machine-readable and current. Second-best starting pipeline
  after IHPC.
- Annuaire statistique Fondamental 1, alphabétisation et éducation de base non
  formelle 2021-2022.
- UNESCO UIS for international comparison.
- OSM school locations.
- **Gap worth naming:** BEPC and Baccalauréat results are not published in
  machine-readable form. Digitising them would be an original contribution.

## 4.7 Agriculture et sécurité alimentaire

- ICASEES annual agricultural surveys and communal monographs - listed among the six
  databases digitised under the World Bank Data for Decision Making project.
- ENSA (Évaluation Nationale de la Sécurité Alimentaire) 2019 - NADA catalogue.
- IPC acute food insecurity classifications via HDX.
- FAO / GIEWS.

## 4.8 Infrastructures

- **Weakest theme.** Road network data commonly traces back to 2009 AICD work.
- OSM roads - better in places, uneven.
- Electricity access: MICS 2018-19 gives 14.3% nationally. Little since.
- Water points: WPdx (Water Point Data Exchange) - **verify**.
- ICASEES quarterly telecom statistics, per the dissemination calendar.

## 4.9 Conflict and displacement - decide whether to include

- UCDP conflict events via HDX; ACLED (**restrictive licence - check before
  redistributing**); UNHCR and IOM DTM displacement data.

Politically the most exposed material on the list. Given you travel to CAR, decide
deliberately. Defensible position: include displacement, exclude conflict incidents.

## 4.10 Known access problems

| Problem | Where | Approach |
|---|---|---|
| JavaScript-only rendering | car.opendataforafrica.org, incl. the NSDP | Headless browser, or find the SDMX endpoint |
| PDF-only publication | Most ICASEES bulletins and reports | pdfplumber, then Claude API on page images for irregular layouts |
| Authorisation required | NADA microdata | Email the DG. Metadata is open; microdata is not. |
| Bare IP, no TLS | IMIS/REDATAM at 38.247.133.235 | Low priority; may be unstable |
| Restrictive licences | ACLED, DHS | Link rather than mirror where redistribution is not permitted |
| Frozen since 2021 | NADA catalogue | Useful for historical surveys only |

---

# Part 5 - Phases

Sized for 2–3 days a week. Weeks are working weeks, not calendar weeks.

## Phase 0 - Foundations (1 week)

- Repo, licence (CC BY 4.0 for data, MIT for code), `CLAUDE.md`, this plan under
  `docs/`, and `docs/decisions.md` capturing *why* the constraints exist.
- Python with `uv`, `ruff`; Node with `pnpm`; Astro scaffold.
- CI config written (lint, build); doesn't need to have *run* yet - see the ops
  checklist before Phase 2, where it starts running for real.
- Directory skeleton: `raw/`, `data/`, `geo/`, `pipeline/`, `site/`, `docs/`.
- A single dummy page, built locally, proving the toolchain works end to end.

**Done when:** `uv sync`, `ruff check`, and `pnpm build` all succeed locally, and the
built page is under the weight budget. No live URL required yet - see the note below
on deferring hosting/accounts.

**Ops deliberately deferred, not skipped.** Everything that needs an external account
(a GitHub remote, Cloudflare Pages, a domain, analytics) is pulled out of Phase 0 and
Phase 1 and batched into one checklist right before Phase 2 needs it - see the note at
the start of Phase 2. There's nothing worth showing publicly yet, and Phase 1 is pure
local data work that doesn't need a live site or even a remote to make progress.
**Local git commits are the exception - keep committing as you go.** That's hygiene,
not ops: it's what protects months of crosswalk work from a dead laptop being this
project's version of the abandonment risk in Part 7.

## Phase 1 - The geography crosswalk (4–5 weeks)

The unglamorous foundation. Resist the urge to build pages during this.

1. Fetch and snapshot COD-AB, COD-EM, COD-PS, ICASEES cartography tables, RGPH-4
   région definitions, OSM boundaries, citypopulation's hierarchy.
2. Build `entities.csv` - every unit, every version, with validity dates.
3. Build `aliases.csv` - every name and code from every source, normalised
   (accents, casing, punctuation, `Ouaka` vs `Wakka`).
4. Resolve the 16 / 17 / 20 préfecture question against the 2020 decree.
5. Map the 7 RGPH-4 régions onto préfectures explicitly.
6. Everything unresolvable goes to `unresolved.csv`.
7. Simplify geometries with mapshaper; check the size budget.
8. Write a README, publish the CSVs, announce them.

**Done when (v1):** the criteria in `CLAUDE.md` build order step 1 are met with real,
cited data - licence questions and cross-source veracity checks can still be open,
logged in `docs/verification-debt.md`, as long as they're logged rather than silently
assumed away. Downloadable with documentation, including an honest note on what's
still unresolved. Full clearance on every source's licence is a pre-*public-launch*
gate (Phase 5), not a pre-Phase-1-completion one.

**This is shippable on its own.** Announce it before the site exists. It is the
credential that gets you a meeting at ICASEES.

**Status as of 2026-09-11 - called "good enough for v1," moving to Phase 2 with two
items consciously carried forward, not dropped:**

- **OSM boundaries (step 1)** - not fetched. Only light research done (confirmed OSM
  models CAR admin boundaries via `admin_level` tags per the general OSM schema, no
  CAR-specific data pulled). Real integration needs geometry-level matching against
  COD-AB, not just name comparison - a bigger job than remaining Phase 1 time
  justified. Pick up anytime; not blocking anything in Phase 2.
- **`geo/` - mapshaper simplification (step 7)** - GeoJSON downloaded
  (`raw/cod-ab-caf/2026-09-05/`) but never simplified/published. Deliberately held
  back behind the still-open COD-AB licence question (`docs/verification-debt.md`) -
  simplifying and publishing derived geometry felt like a bigger redistribution
  commitment than keeping the raw snapshot for internal crosswalk-building use. Needed
  again once Phase 4 wants locator maps; revisit the licence question first.

Steps 2–6 and 8 are done for the levels in scope (pays/région/préfecture/
sous-préfecture - commune/localité dropped, see `CLAUDE.md`'s scope note): 113
entities, 168 aliases, 7 sources, `unresolved.csv` populated with 9 real
(not hypothetical) disagreements. Also resolved along the way and not originally
planned: the actual 2020 reform decree (Loi n°21.001 du 21 janvier 2021), which fixed
the 84-vs-85 sous-préfecture count question. See `docs/verification-debt.md` for
everything still open, and `data/README.md` for current file-by-file state.

## Phase 2 - First pipeline and the national site (4–5 weeks)

**Ops checklist - do this once, at the start of this phase, not before:**

- [ ] Create the GitHub repo, push the Phase 0/1 history to it
- [ ] Point CI at it, confirm the lint/build jobs actually go green (not just locally)
- [ ] Connect Cloudflare Pages to the repo; confirm the placeholder page deploys
- [ ] Decide the domain (or use the Cloudflare Pages default subdomain for now -
      doesn't need to be final)
- [ ] Set up Umami or Plausible (self-hosted, per `docs/decisions.md`)

Everything above needs your accounts/credentials - none of it happens unilaterally.
Once it's done, the GitHub Actions cron/PR-on-change automation below is core
pipeline architecture, not "ops" - it's what keeps the project self-updating without
manual work, which is the main defence against the abandonment risk in Part 7. Don't
defer that part again once it's set up here.

Pick **IHPC** as the first source: monthly, official, current, already tabular.

1. Scraper: fetch, snapshot, extract, normalise to `observations.csv`. GitHub Action
   on a cron, opening a PR on change.
2. Quality gates in CI.
3. Astro content collections reading from `data/`.
4. Build-time SVG chart rendering with Observable Plot - get this working early, it
   shapes everything.
5. The sentence template engine. Start with three templates. Get the French right.
6. Home page, one theme page (prix), `/sources`, `/methode`, `/a-propos`.
7. Pagefind search.
8. Analytics.

**Done when:** the site is public, showing real IHPC data, updating monthly without
manual work, under the page weight budget.

Announce it. Send it to RJDH and the Factcheckers association. Ask what they'd want next.

## Phase 3 - Breadth at national level (6–8 weeks)

Add sources in this order, easiest first, so each teaches you something before the
hard ones:

1. Education yearbooks (Excel - easy)
2. World Bank indicator API (easy)
3. WFP food prices via HDX (easy, but market-level geography)
4. National accounts and GDP (PDF extraction - medium)
5. MICS 2018-19 indicators (medium)
6. IMF NSDP / SDMX (hard - JavaScript or SDMX)
7. Health facilities (hard - multiple conflicting sources; the first real test of the
   disclosure mechanism)

Alongside: all seven theme pages, 15–20 indicators, the multi-source disclosure
component, share-card generation, embeds and PNG export.

**Done when:** every theme page exists with at least two indicators, and the
disclosure mechanism works on population and health facilities.

**Status as of 2026-09-12.** Item 2 (World Bank API) done for two indicators:
`acces_electricite` (infrastructures theme) and a World Bank cross-check row on
`population_totale`. Item 1 (education) done via a different path than
originally planned, then widened well past the original single-indicator
scope - the ICASEES education yearbooks (Excel) hit apparent rate-limiting
mid-session (`docs/verification-debt.md`) and were paused rather than pushed
further; UNESCO UIS's Data API was used instead, and turned out to have real
CAF data across 15 indicators (completion, enrollment, retention, literacy),
confirmed live rather than assumed from the catalogue - see
`docs/decisions.md`. ICASEES yearbooks remain a real to-do, not abandoned -
the education page's "Ce qui n'est pas mesuré" section names exam results
specifically as still missing.

**Update 2026-09-12 (later the same day).** Deliberate pass to bring
population/prix/infrastructures up towards éducation's depth, since having
one theme at 15 indicators and three at 1 each isn't a satisfying level of
completion. Prix went from 1 to 5: the IHPC dashboard file already
downloaded for `prix_ihpc_global` also had 12 COICOP sub-category rows and a
published inflation rate that were simply never parsed - added the
inflation rate plus 3 named sub-categories (alimentation, santé,
transports), the ones `prix.astro`'s own gap-note had already promised.
Zero new sourcing needed for this one. Infrastructures went from 1 to 5:
added 4 World Bank indicators (internet use, mobile subscriptions, basic
water access, basic sanitation access), all confirmed live with recent
(2022-2024) CAF data before adding. `export_electricity_json.py`/
`electricite.json` retired in favour of `export_infrastructures_json.py`/
`infrastructures.json` now that the theme covers more than electricity -
see `docs/decisions.md`. Population went from 1 to 4: added growth rate,
urban population %, and age dependency ratio, all World Bank, all with data
through 2025. All four existing theme pages met "at least two indicators":
éducation (15), prix (5), infrastructures (5), population (4).

**Update 2026-09-12 (still later the same day).** User asked to build the
remaining themes, starting with santé - the first brand-new theme page
built this session rather than a widening of an existing one. 10 World
Bank indicators (life expectancy, child/infant/maternal mortality, measles/
DPT vaccination, physicians and hospital beds per capita, health spending %
of GDP, HIV incidence), all confirmed live for CAF before adding, grouped
into 4 categories ordered système de santé → vaccination → mortalité et
espérance de vie → maladies - see `docs/decisions.md`. Espérance de vie is
the headline. One real gap flagged, not hidden: hospital-bed density's
most recent World Bank data point is from 2011.

**5 of 7 sitemap themes existed after santé; économie followed the same
day.** 10 more World Bank indicators (GDP total/per capita/growth, poverty,
unemployment, exports, imports, external debt, FDI, government revenue),
grouped production → commerce extérieur → finances publiques → niveau de
vie. PIB par habitant is the headline. First theme with non-percentage
indicators (GDP figures are US$) - `economie.astro` and
`sentence_economie_montant()` handle that explicitly rather than forcing
everything through a "%"-only formatter. Two gaps flagged: poverty rate has
only 3 data points ever (infrequent household surveys), government revenue
stops at 2021. Also: ICASEES's own GDP rebasing (2019 base, per
`CLAUDE.md`) hasn't been cross-checked against these World Bank figures -
see `docs/verification-debt.md`.

**6 of 7 sitemap themes existed after économie; agriculture followed the
same day.** 9 World Bank/FAO indicators (agricultural/arable/forest land
%, food production index, cereal yield, fertilizer use, agriculture's
share of GDP, undernourishment, agricultural employment), grouped terres
et ressources → production → emploi et alimentation. Emploi agricole (66%
of total employment) is the headline - the single most characteristic
fact about CAR's economy. Richest and freshest of the three new themes
this pass, no genuinely stale indicator.

**All 7 sitemap themes now exist: population, prix, infrastructures,
éducation, santé, économie, agriculture - 58 indicators total, up from 4
at the start of this session's completion pass.** Every theme page now
has a headline figure and logically-ordered categories per the rule
codified earlier today.

**Update 2026-09-12 (fourth pass the same day).** Two follow-ups from user
feedback on the newly-built themes. (1) Rates alone were hiding scale
(doctor density but no doctor count, GDP share of trade but no dollar
figure) - added real absolute counterparts across santé (+3: doctors and
nursing/midwifery headcounts from WHO's GHO API, since World Bank's WDI
had no raw counterpart at all; a calculated hospital-bed estimate where
*no* API had one), économie (+3: export/import/debt values in US$, real
World Bank counterparts already published alongside the % versions), and
agriculture (+2: agricultural land in km², cereal production in tonnes,
same pattern). (2) Reorganized économie to carry brief summary cards for
prix and agriculture with a link to each's full page - closer to
`CLAUDE.md`'s original "agriculture et prix" grouping, implemented as
cross-linking rather than a URL/data merge - see item 6 of §2.3 above.
**66 indicators total now.** Still open: the Phase 3 source list items 3-7
(WFP food prices - CLAUDE.md's own example indicator, `prix_manioc_kg`,
different geographic floor (market, a point) and different API (HDX);
national accounts/GDP via PDF extraction; MICS 2018-19; IMF NSDP/SDMX;
health facilities as the first 3-way disclosure test), the ICASEES
yearbooks (paused), and the `/themes/` URL structure inconsistency flagged
in `docs/decisions.md` - worth revisiting now, before Phase 4's place
pages make every theme's URL a link target from elsewhere.

**Update 2026-09-12 (fifth pass the same day) - item 3, WFP food prices.**
The first source at market-level geography - a point, not an
administrative area, and genuinely deeper than sous-préfecture. HDX's
"Central African Republic - Food Prices" dataset (CC BY-IGO) has 41 markets
and 39 commodities, 2004 to present; checked live rather than assumed
before picking anything. Bangui market, Retail pricetype, 5 staple
commodities with monthly `priceflag=actual` data continuing into 2026
(manioc, riz, maïs, bœuf, huile de palme) were added as 5 new indicators -
71 total now. Required a new entity level, `marche` (`cf-m-bangui-v1`,
parented to the Bangui prefecture entity for lack of a better anchor, not
an administrative claim) - see the entities.csv table above and
`docs/decisions.md`. Rendered as its own section on `/prix/`, separate from
the national IHPC series, with the geographic-floor difference stated
plainly per CLAUDE.md's transparency principle rather than blended in as
if it were the same kind of figure. 34 other commodities and 40 other
markets exist in the same source and are named as not-yet-covered rather
than silently absent.

**Update 2026-09-12 (sixth pass the same day) - item 4, national accounts
and GDP.** ICASEES published rebased comptes nationaux (base 2019, SCN
2008) for 2019-2021 on 2026-07-30 - fetched the actual PDF (pdfplumber,
`extract_tables()` used to rule out a column-merge misread) rather than
assumed from its announcement page. Added 2 new indicators (`pib_total_fcfa`,
`pib_par_habitant_fcfa`) rather than converting into the existing USD
figures, since that would need an assumed exchange rate this project
hasn't verified. More importantly, this resolved a real open item from
`docs/verification-debt.md`: ICASEES's growth rate for 2020-2021 (3.41%,
3.44%) disagrees substantially with the World Bank's modelled estimate for
the same years (0.90%, 0.98%) - a genuine ~250% relative spread, not a
rounding difference. Économie now has its first multi-source disclosure
(`taux_croissance_pib`), following the authority ranking (donnée
administrative nationale outranks estimation modélisée internationale) -
population and éducation already had this mechanism, so this is a third,
not the first, but the first for a macroeconomic figure. 73 indicators
total now. One thing found but not resolved: the PDF's own narrative
summary contradicts its own data table for the 2021 growth rate (1.6% vs
3.44%) - the table was used as authoritative, the inconsistency logged
rather than silently picked around.

**Update 2026-09-12 (seventh pass the same day) - item 5, MICS 2018-19.**
The actual MICS6-RCA report PDF is blocked behind what looks like a
referer/session gate on both mics.unicef.org and its S3 file host (even a
confirmed-real file URL from the World Bank's own microdata catalog page
403'd). Rather than force it, checked whether UNICEF republishes the same
survey data through a structured API - it does, `sdmx.data.unicef.org`,
live and unauthenticated, discovered via its own `/dataflow` listing.
7 new indicators: 5 into santé (new "Santé maternelle et infantile"
category - antenatal care, skilled birth attendance, exclusive
breastfeeding, stunting, wasting) and 2 into population (birth
registration, child marriage before 18 - demographic/legal-status facts,
not health facts). Sourcing is genuinely mixed, not uniformly MICS6 -
UNICEF's warehouse pulls whichever survey covers each indicator most
recently, so stunting/wasting's latest point is actually a 2022 SMART
survey, not MICS - each observation's real source is read from the API
response and recorded per-row rather than assumed. Also gave these
indicators a 10-year staleness threshold (matching éducation's existing
survey-linked band) instead of the flat 5-year one used for World Bank's
annual estimates, and updated méthode.astro's published threshold table
to say so. 80 indicators total now.

**Update 2026-09-12 (eighth pass the same day) - item 6, IMF NSDP/SDMX.**
Both routes this file originally named turned out wrong in a specific,
checkable way: `dataservices.imf.org` (documented everywhere) no longer
resolves at all, and the AfDB/Knoema mirror
(`car.opendataforafrica.org/nsdp`) is genuinely all client-side rendering
with every guessed API path 403ing. IMF's current SDMX 2.1 API lives at
`api.imf.org` instead - found via its own `/dataflow` listing, not
guessed. CAR's actual e-GDDS coverage turned out thin: of everything the
NSDP framework is meant to cover (GDP, prices, debt, monetary, external
sector), CAF publishes exactly one series - a quarterly Total Economic
Activity Index, 2017-Q1 to 2023-Q1 - confirmed by querying every
dimension as a wildcard, not assumed absent. Added it as
`indice_activite_economique`, and said on the page that the rest of the
framework isn't populated for this country yet, rather than implying
broader coverage than exists. 81 indicators total now, and all 7 Phase 3
source list items are now done except health facilities (item 7).

## Phase 4 - Descending (4–6 weeks)

1. Wire the crosswalk into the observation pipeline; backfill `entity_id` for
   subnational data.
2. Set `geographic_floor` per indicator **from observation**.
3. Breakdown sections on theme pages.
4. Place pages for 20 préfectures, then 85 sous-préfectures - sous-préfecture is the
   current floor (commune/localité dropped from scope, `CLAUDE.md`).
5. Locator maps.
6. Comparison component - siblings and national.
7. Handle the empty case properly everywhere.

**Done when:** every sous-préfecture has a page that either shows data or explains its
absence, and no page shows a misleading empty chart.

## Phase 5 - Coverage, polish, launch (3–4 weeks)

1. **Clear `docs/verification-debt.md`** - every open item resolved or, at minimum,
   consciously accepted and stated as a caveat on the relevant page. This is the gate
   that was deliberately deferred since Phase 1; it comes due here, not before.
2. The `/couverture` matrix and completeness choropleth.
3. Hand-written *ce qui n'est pas mesuré* sections for all seven themes.
4. Print stylesheet, accessibility pass, French copy edit by a native speaker.
5. Bulk downloads.
6. Error reporting mechanism.
7. Governance: association or institutional partner named on the site.
8. Public launch - press outreach to RJDH, RMCC, Radio Ndeke Luka; notify ICASEES,
   OCHA, the World Bank country office; post to HDX.

**Done when:** somebody who is not you has cited it.

## Phase 6 - Sustaining (ongoing)

- Monthly: verify scrapers, review PRs, one short editorial piece.
- Quarterly: re-check the source register, update freshness thresholds.
- On new data (MICS7, census definitive results, EHCVM2): a lead story on the home page
  and an editorial piece.

---

# Part 6 - Editorial

Templated sentences carry the ordinary pages. Reserve hand-written pieces for what
templates cannot do. One a month is enough; ten good pieces make the site feel alive.

Candidate first pieces:

1. **What the census changed** - every widely-quoted figure computed on the old
   denominator, and what it becomes at 6.66 million.
2. **How many préfectures does CAR have?** - the 16 / 17 / 20 story. Genuinely
   interesting, verifiable, and it explains why the project exists.
3. **The roads nobody has measured since 2009.**
4. **Four institutions, four populations for Ouaka.**

---

# Part 7 - Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Abandonment | **Highest.** NADA froze in 2021 and is still online. Data Africa froze around 2016 and still serves 2005 crop data. Both look alive. | Static files, git, no server, no database. An institutional owner besides you, named before launch. |
| Nobody in CAR uses it | High | Share cards for Facebook, embeds for journalists, strict weight budget, French-first, talk to RJDH in Phase 2 not Phase 5. |
| Building for yourself | High | Before Phase 2 ships, ask three Central African journalists what they had to look up last month and couldn't find. |
| Phase 1 tedium | High - most projects die here | It is publishable on its own. Ship it and get credit before starting Phase 2. |
| Scraper rot | Medium | Immutable snapshots, PR-on-change, CI validation, monthly check. |
| Political exposure | Medium | Mirror ICASEES's provisional caveat. Decide deliberately about conflict data. Institutional cover helps. |
| Licence violation | Medium | `licence_notes` per source. Link rather than mirror where redistribution is restricted. |
| Scope creep | Medium | Five chart types. No dashboards. No indices. No AI features. |

---

# Part 8 - Open questions to resolve early

1. **Who owns this besides you?** An association, a university, an ICASEES
   partnership. Resolve before launch, ideally before Phase 2.
2. **Conflict data: in or out?**
3. **Is 150 KB / zero client JS the right budget**, or leave room for one interactive
   island later? Decide before Phase 2 - it is hard to relax afterwards.
4. **Sango.** Is a Sango layer realistic, and for which pages? Probably not at launch,
   but the decision affects the i18n structure now.
5. **Does anyone in CAR actually use it?** Unanswerable until Phase 2 ships. It is the
   real test of the project and everything else is preparation for asking it.
