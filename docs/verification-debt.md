# Verification debt

The "come back to this" list. Per `CLAUDE.md`'s rule zero v1 note: real, sourced data
can be used in v1 before it's been cross-checked against other sources - logged here
instead of blocking. This list needs to be reviewed item by item before the site is
presented as a finished public v1 or promoted as authoritative. It is not a place to
file things and forget them.

**Revised 2026-09-13:** this list no longer tracks plain licence ambiguity or an
unstated licence - per `CLAUDE.md`'s revised licensing stance, that's not this
project's problem to solve for a non-commercial reference work, only to disclose via
citation. Several entries below that were purely about licence status were closed on
this date for that reason (see each entry's note). What's still tracked here: an
*explicit* usage restriction on a source (a real constraint, not ambiguity), and
genuine data-quality problems - numbers that don't reconcile, gaps, stale figures -
regardless of licence.

Each entry: what's unresolved, where it's used, what "resolved" would look like.

---

## Open

### ICASEES éducation yearbook has internal arithmetic inconsistencies in at least one table (2026-09-12)

- **What:** While checking whether the éducation yearbook's IA
  (préfecture) tables could be safely extracted for a Phase 4 widening,
  found that its préscolaire établissements-by-zone table
  (IA/Urbaine/Rurale/Total général, 19 préfectures listed - Vakaga is
  missing from this particular table, its own separate oddity) doesn't
  reconcile for 3 of those 19: Urbaine + Rurale ≠ Total général, each off
  by exactly 1 (Lim-Pendé 21+4≠26, Mambéré-Kadéï 24+7≠30, Ouaka 22+3≠26).
  Column boundaries were verified against the row's own merged-cell
  metadata first, so this isn't a parsing mistake on this project's
  side - it's the source workbook's own published numbers not adding up.
- **Used in:** not used anywhere on the site - this was found precisely
  while deciding whether to extract from this table, and the finding is
  why nothing was extracted. The existing national
  `nombre_etablissements_scolaires` figure (3015, used on `/education/`)
  is unaffected: it's ICASEES's own stated headline total, taken directly
  from a different summary row, not computed by aggregating the
  inconsistent table.
- **Re-checked live 2026-09-13:** checked ICASEES's publications listing for
  a newer édition since this was found - the file used
  (`annuaire_statistique_2024_2025.xlsx`) is still the most recent one
  available; no corrected version has been published. Genuinely can't
  reconcile this without ICASEES issuing a fix.
- **Resolved when:** either ICASEES publishes a corrected version, or
  someone with a reason to use this specific table confirms which of the
  three numbers is right for the affected préfectures - not something to
  guess at. See `docs/decisions.md` for the full check.

### Dark-mode toggle not yet clicked in an actual browser (2026-09-12)

- **What:** The sitewide dark-mode toggle (`ThemeInit.astro` /
  `ThemeToggle.astro`, added 2026-09-12) was verified by reading the built
  HTML/CSS/JS output directly - script ordering, selector correctness,
  the minified `data-theme` rules, the toggle button present exactly once
  on all 33 pages - not by actually clicking it in a browser. No browser
  automation tool is available in this environment. Static-analysis
  verification is solid for structural correctness (does the right markup
  exist, in the right order) but doesn't catch things only a real render
  would show: whether the three-state cycle feels right, whether any
  page's dark palette has a legibility problem in practice, whether the
  fixed-position button collides with anything on a narrow viewport.
- **Used in:** every page (`site/src/components/ThemeInit.astro`,
  `ThemeToggle.astro`, and the dark `:root` overrides added to all 14
  page files - see `docs/decisions.md`'s dark-mode entry).
- **Resolved when:** someone (the user, most likely) runs `pnpm dev` or
  `pnpm preview` from `site/` and clicks the "Thème" button on a few
  pages - confirming the three states cycle correctly, dark mode reads
  cleanly on at least one light-heavy page (e.g. `/sources/`) and one
  chart-heavy page (e.g. `/prix/`), and the button doesn't overlap page
  content on mobile widths.

### COD-AB licence - "humanitarian purposes only" restriction

- **What:** The HDX listing for `cod-ab-caf` (fetched 2026-09-04) carries `isopen:
  false` in its own CKAN metadata and this caveat: *"Dataset is awaiting validation
  by ICASEES (government). The Humanitarian Coordinator granted special approval for
  the use of this dataset for humanitarian purposes only on 2025. If the dataset is
  shared or made public, users must include the following disclaimer: [...]"*
  `CLAUDE.md` assumed this was straightforwardly open ("the humanitarian sector
  standard"); it isn't, at least not for a public-facing non-humanitarian product.
- **Used in:** `data/entities.csv`/`aliases.csv` (the crosswalk itself, tabular
  pcodes only) since Phase 1. Now also the actual boundary geometry, as of
  2026-09-12's locator maps (`geo/raw/`, `geo/simplified/`,
  `pipeline/build_geo_prefectures.py`) - this is the point where the caveat
  above stops being hypothetical: the geometry itself is now redistributed
  (simplified, but derived from and shaped like the original) on public
  pages, not just used internally to build an ID crosswalk. Not blocking for
  v1 per CLAUDE.md's own rule, but this is the item to resolve before the
  site is presented as a finished public v1 - see "Resolved when" below.
- **Resolved when:** either (a) redistribution is swapped for citation-only (link to
  HDX, don't mirror the geometry/data), (b) an alternate boundary source without this
  restriction is found and used instead, or (c) an actual licence conversation
  clarifies this project qualifies for use/redistribution.

### COD-AB admin counts have moved since `CLAUDE.md` was compiled - now with a precise second-source cross-check

- **What:** `CLAUDE.md`'s administrative-geography table lists COD-AB as 17
  préfectures / 72 sous-préfectures / 175 communes. The live dataset (version 02,
  reviewed 2026-03-06) states **20 préfectures / 85 sous-préfectures**.

  **The 84-vs-85 gap is resolved as of 2026-09-11**, moved to Resolved below - see
  that entry. What follows here is the separate, still-open citypopulation.de
  cross-check.

  Cross-checked 2026-09-09 against citypopulation.de (which relays ICASEES data,
  admin page fetched and snapshotted at
  `raw/citypopulation-de-caf/2026-09-09/admin_index.html`): its total is **77**, not
  85, and the gap is concentrated in exactly 6 préfectures, not spread evenly -
  computed precisely via DuckDB, not eyeballed:

  | Préfecture | COD-AB v02 | citypopulation.de | diff |
  |---|---|---|---|
  | Lim-Pendé | 5 | 3 | +2 |
  | Vakaga | 4 | 2 | +2 |
  | Haute-Kotto | 4 | 3 | +1 |
  | Lobaye | 6 | 5 | +1 |
  | Haut-Mbomou | 5 | 4 | +1 |
  | Bangui | 4 | 3 | +1 |

  All other 14 préfectures match exactly. citypopulation.de's own page states its
  2021 figures are "result of an incomplete digital mapping done in preparation of
  the next population census" - a plausible explanation for why it's *lower* than a
  2026-reviewed source, but that's a hypothesis, not confirmed.

  **Update 2026-09-09 - diagnosed name-by-name, not just by count.** Fetched
  citypopulation.de's actual named sous-préfecture lists (not just totals) for all 6
  préfectures. Two different kinds of disagreement, now split out in
  `data/unresolved.csv` (9 rows):

  - **5 straightforward "citypopulation is missing one entry"** cases where names and
    codes otherwise align exactly: Mboki (CF635, Haut-Mbomou), Am-Dafok (CF534) and
    Ouandja (CF533, both Vakaga), Ouandja-Kotto (CF524, Haute-Kotto), Moboma (CF126,
    Lobaye). Consistent with citypopulation.de's own "incomplete mapping" admission.
  - **2 genuine conflicts**, not just omissions:
    - **Kodi/Ndim (Lim-Pendé):** COD-AB v02 gives Kodi code CF344 and Ndim CF343.
      citypopulation.de gives **Kodi** code **CF343** - re-verified by fetching the
      exact page text directly (not trusting the first summarized pass), confirmed
      real. citypopulation.de's page annotates Kodi "(← Ngaoundaye)," suggesting a
      recent split, which may explain a re-numbering disagreement - not confirmed.
      Ndim doesn't appear on citypopulation.de at all. Taley (CF345) is also simply
      missing there, same as the 5 above.
    - **Bangui:** not a missing-entry case at all, and now a *three*-way
      disagreement, not two. COD-AB v02 names Bangui's 4 sous-préfectures by zone
      (Bangui-Centre/Kagas/Fleuve/Rapides, codes CF711–714). citypopulation.de names
      3 by place (Bangui itself as a city, Bimbo, Bégoua), codes CF711–713
      overlapping but attached to different names. **ICASEES itself** (fetched
      2026-09-11, `icasees.org/index.php/actualites/316-...`, quoted verbatim) uses a
      *third* model for RGPH-4 census-taking purposes: "the nine (9) arrondissements
      of the capital as well as the communes of Bimbo and Bégoua" - i.e. Bangui
      proper has 9 arrondissements (not 4 zones, not 1 city-unit), and Bimbo/Bégoua
      are explicitly called **communes**, not sous-préfectures, and may not even
      belong to Bangui préfecture administratively (Bimbo does not appear anywhere
      in COD-AB v02's sous-préfecture list under any préfecture). This is not
      converging - it's genuinely three different structural models for the same
      area, from three different institutional purposes (COD-AB: humanitarian
      mapping zones; citypopulation.de: demographic reporting; ICASEES: census
      logistics). Resolving this needs to identify which model, if any, matches the
      actual legal/administrative sous-préfecture structure - none of the three may
      be "wrong," they may just be answering different questions.
- **Used in:** not yet used to adjust any entity - `data/entities.csv` still follows
  COD-AB v02 as-is (85 sous-préfectures). This cross-check doesn't change that
  choice; it documents the disagreement precisely (`data/unresolved.csv`) instead of
  silently picking a side.
- **Resolved when:** for the 5 simple-missing cases, confirming they're genuinely
  post-2021 additions (would close them with no entity change needed). For Kodi/Ndim,
  finding a third source to settle the code assignment. For Bangui, finding a source
  that explains the relationship between the zone-based and place-based naming
  schemes - they may both be legitimate but describing different things (e.g.
  administrative zones vs. communes), not actually contradictory.

### Région `valid_from` date is a governance date, not necessarily RGPH-4's

- **What:** Régions were given `valid_from = 2024-06-01`, based on reporting that
  regional governors were first named around June 2024 - found alongside the
  ministry pages, not independently verified as *the* date RGPH-4's 7-région
  structure itself took effect (which may predate the governors being appointed to
  administer it).

  **Re-checked live 2026-09-13:** fetched limko.cm's "nouvelles divisions
  administratives" page directly (the same page that independently confirmed the
  7×préfectures composition, see Resolved) looking specifically for whether it ties
  the régions to a creation date separate from the governors' appointment. It
  doesn't - it mentions Loi n°21.001 du 21 janvier 2021 only in connection with
  "circonscriptions administratives" broadly, without saying explicitly whether that
  same law defined the 7 régions or a different, later reform did. Genuinely still
  unresolved; this attempt didn't find grounds to change the stored date either way.
- **Used in:** all 7 région rows in `data/entities.csv`.
- **Resolved when:** the actual date the 7-région structure was defined (as opposed
  to when it was staffed) is found and it's confirmed those are the same reform, or
  the dates are split apart if they're not.

### IHPC dashboard file's pre-2020 reconciliation isn't independently confirmed

- **What:** ICASEES's own published IHPC dashboard file (CC BY 4.0, no licence
  issue) documents, in its own methodology notes, that values from 2015-01 to
  2019-12 were reconciled onto the post-2020 base by whoever compiled the file
  ("à la demande de l'utilisateur"), using an official coefficient (4.12919) quoted
  from ICASEES's own bulletin warnings. The math checks out (verified independently:
  Dec-2019 raw 412.10 / 4.12919 ≈ 99.78, matching Jan-2020's as-published 99.14), and
  the raw pre-2020 values are preserved unmodified in the same file's
  `Archive_Base1981_Brute` sheet - this is unusually transparent. What's not
  confirmed: whether this specific reconciliation is itself an ICASEES-endorsed
  position or a working calculation for whichever user requested this dashboard
  export. Marked `quality_flag=estime` in `observations.csv` for the affected 60
  months rather than treated as equivalent to as-published data.
- **Used in:** `data/observations.csv`, `prix_ihpc_global`, periods 2015-01 through
  2019-12 (60 of 136 rows).
- **Resolved when:** an ICASEES publication (a bulletin, a methodology note) confirms
  this same reconciliation independently of this one dashboard file.

### IHPC dashboard file's own metadata is internally inconsistent

- **What:** The file's `Métadonnées` sheet states temporal coverage as "2015M1 à
  2025M9," but the actual data columns in the `Données` sheet run through 2026M4 (a
  note elsewhere in the file says the series was "prolongée jusqu'à avril 2026").
  The metadata description wasn't updated when the series was extended.
- **Used in:** not load-bearing - the pipeline (`add_ihpc_observations.py`) reads the
  actual data columns, not the metadata sheet's stated range, so this didn't produce
  a wrong result. Noted here so nobody trusts the metadata sheet's date range at face
  value in future work on this file.
- **Resolved when:** not urgent to resolve - informational.

### UNESCO UIS education data - underlying survey/methodology not named per point

- **What:** 15 education indicators are fetched live from the UIS Data API
  (`api.uis.unesco.org/api/public/data/indicators`) - completion (primary,
  lower secondary, upper secondary; survey `CR.1/2/3` + modelled
  `CR.MOD.1/2/3`), enrollment and repetition/survival (`GER.1/2/3/5T8`,
  `NERT.1.CP`, `REPR.1.CP`, `SR.1.GLAST.CP` - no modelled counterpart exists
  for any of these, confirmed by searching the full indicator catalogue for
  `*.MOD.*` variants of each, not assumed), out-of-school (primary/lower
  secondary/upper secondary; administrative `ROFST.1/2/3.CP` + modelled
  `ROFST.MOD.1/2/3`), and literacy (`LR.AG15T24`, `LR.AG15T99`). Originally
  just `taux_achevement_primaire` (`CR.1`/`CR.MOD.1`); widened 2026-09-12 in
  two passes once the same API was confirmed to have real CAF data well
  beyond that - see `docs/decisions.md`. Two open gaps, both about what the
  underlying methodology actually is, not licence (the licence-comparison
  gap that used to be listed here - CC BY-SA 3.0 vs 4.0 - is closed per
  `CLAUDE.md`'s revised licensing stance, 2026-09-13): (1) for the
  completion and out-of-school indicators, the API's response gives only a
  year per point for the higher-authority series, not which underlying
  survey/administrative round produced it - plausibly the same MICS/EHCVM
  rounds that produced other CLAUDE.md-cited figures, but that's an
  inference, not confirmed by the API. (2) for the enrollment/repetition/
  survival indicators, the API doesn't tag methodology at all - this
  project has labelled them "administrative" (school-census/EMIS data, the
  standard UIS approach for this indicator family) based on general
  knowledge of UIS methodology, not a per-point confirmation from the API
  response itself.
- **Used in:** `data/sources.csv` (`unesco-uis-completion-survey`,
  `unesco-uis-completion-modelled`, `unesco-uis-education-administrative`,
  `unesco-uis-outofschool-modelled`, `unesco-uis-literacy`),
  `data/observations.csv` (404 rows across 15 `taux_*` indicators),
  `site/src/pages/education.astro`.
- **Resolved when:** the UIS indicator metadata endpoint
  (`/api/public/definitions/indicators`) or a published methodology note is
  checked for a per-point survey/methodology citation across all 15
  indicators, not just completion. Low priority - a completeness
  improvement, not a correctness problem (the values themselves aren't in
  question).


### Poverty rate (économie) has only 3 real data points

- **What:** `taux_pauvrete` (World Bank SI.POV.DDAY, poverty headcount
  ratio at $3.00/day 2021 PPP) has exactly 3 non-null observations for CAF
  across the entire available history: 1992, one intermediate year, and
  2021 - it depends on infrequent household survey rounds, not an annual
  series. The 71.6% figure shown (2021) is real but old relative to most
  other économie indicators on the same page (which run through 2024-2025).

  **Re-checked live 2026-09-13:** no MICS7 or EHCVM2 poverty results
  published yet (both still in progress per `CLAUDE.md`'s own domain
  facts). Search did surface other CAR poverty figures in circulation -
  a World Bank national-poverty-line estimate around 68.8-69% and the
  2023 "Central African Republic Poverty Assessment" report - but those
  use a different methodology (national poverty line, not the $3/day 2021
  PPP international line this project's indicator tracks), so they're not
  a fresher point on the *same* series, just a different measure entirely.
  Genuinely can't reconcile or freshen this one; 2021 remains the latest
  real point for this specific indicator.
- **Used in:** `data/observations.csv`, `taux_pauvrete` (3 rows),
  `site/src/pages/economie.astro`.
- **Resolved when:** a newer household survey round (MICS7, EHCVM2 - both
  named as in-progress in `CLAUDE.md`) publishes an updated poverty
  estimate, or ICASEES publishes its own national poverty line calculation
  independently of the World Bank's $-a-day methodology.

### WHO GHO health workforce data - nurse counts swing implausibly year to year

- **What:** `nombre_medecins` and `nombre_personnel_infirmier` are fetched
  from WHO's Global Health Observatory OData API (`ghoapi.azureedge.net`,
  indicators `HWF_0002`/`HWF_0007`) rather than World Bank WDI, since WDI
  only publishes density for these, never a headcount. (The licence-unclear
  concern that used to be listed here is closed per `CLAUDE.md`'s revised
  licensing stance, 2026-09-13 - this is properly cited regardless.) The
  nursing/midwifery count swings hard between reporting years for CAF: 835
  (2008) → 1,097 (2009) → 1,195 (2018) → 1,042 (2021) → 2,545 (2022) → 5,653
  (2023) → 2,331 (2024). A near-5x jump in one year (2022→2023) and a
  near-halving the next (2023→2024) is far more volatile than a real
  national nursing workforce plausibly changes.

  **Re-checked live 2026-09-13**, attempting reconciliation rather than
  re-describing the problem: queried the GHO OData API directly for every
  CAF data point on this indicator. All of it matches what's already in
  `data/observations.csv` exactly - nothing has changed or been corrected
  upstream since this was first fetched. Every single point, from 2004
  through 2024, carries the identical generic comment ("NHWA data portal,
  December 2025 update") with no per-year distinction - so the API itself
  gives no basis to tell whether 2023's spike or 2024's drop reflects a
  real event, a reporting-completeness change, or a data-entry issue at
  WHO's National Health Workforce Accounts portal. Genuinely can't
  reconcile this from the data available; it's not a case of us using
  stale data, WHO's own published series is this volatile.
- **Used in:** `data/observations.csv`, `nombre_medecins` (7 rows),
  `nombre_personnel_infirmier` (8 rows), `site/src/pages/sante.astro`.
- **Resolved when:** ICASEES or a WHO country profile document is checked
  for a methodology note explaining the nursing-count discontinuity, since
  the API itself won't yield one.

### Derived hospital-bed count - a calculation, not a published figure

- **What:** `nombre_lits_hopital` doesn't come from any source directly -
  neither World Bank WDI nor WHO GHO publishes an absolute hospital-bed
  count for CAF anywhere (checked both APIs directly before deciding to
  compute this). Each of the 6 values is bed density (`SH.MED.BEDS.ZS`,
  per 1,000 people) × that *same year's* real World Bank population figure
  (`SP.POP.TOTL`) ÷ 1,000, rounded to the nearest whole bed. The most
  recent point is 2011 (4,565 beds, from a density of 1.0/1,000 and a
  population of 4,565,021) - as stale as the density it's built from, not
  independently more current.

  **Re-checked live 2026-09-13:** queried `SH.MED.BEDS.ZS` directly against
  the World Bank API for 2012-2025 - every single year is `null`. 2011 is
  confirmed as genuinely the latest bed-density figure that exists anywhere
  for CAF, not a stale cache on this project's end.
- **Used in:** `data/observations.csv`, `nombre_lits_hopital` (6 rows),
  `site/src/pages/sante.astro`. Labelled `quality_flag=estime` with the
  exact density/population/year used in each row's `notes` field, and the
  page's generated sentence explicitly says "estimation calculée," not
  stated as a plain published fact.
- **Resolved when:** ICASEES, WHO AFRO, or another primary source publishes
  an actual hospital-bed census for CAR, which would replace this
  calculation rather than supplement it.

---

## Resolved

### Ministère des Finances budget note - closed, licence policy revised (2026-09-13)

Was: `data/sources.csv`'s `mfb-note-information-2026` (the Ministère des Finances et
du Budget's "Note d'Information du Marché des Titres Publics de la RCA", January
2026) carries no licence statement anywhere in the 52-page document. Closed same-day
per `CLAUDE.md`'s revised licensing stance: this is a real, official government
document, properly cited (producer, dataset name, retrieval date, URL in
`data/sources.csv`), and an unstated licence on a non-commercial reference site isn't
a blocker. Still worth a real cross-check against a second primary source (the Loi de
Finances 2026 text itself, or a future IMF Article IV / e-GDDS publication) if one
surfaces, but that's an accuracy improvement now, not a licence gate.

### Régions → préfectures mapping, confirmed by a second independent source (2026-09-13)

The 7 régions' composition (which préfectures belong to which) had only ever been
checked against one source: 7 individual pages on `minurbanisme-rca.org`. Found a
genuine second, independent source - limko.cm's "nouvelles divisions administratives
de la République centrafricaine" (13 July 2024, the same page also used elsewhere in
this project's decree research) - and it lists all 7 régions with their préfectures
explicitly. Compared directly against `data/entities.csv`'s stored mapping: exact
match on all 7 régions × 20 préfectures, no gaps, no overlaps, no reassignments
(one minor spelling variant, "Nana-Grébizi" vs. stored "Nana-Gribizi" - not a
structural disagreement). The régions→préfectures composition is now confirmed by
two independent sources. What's still open: whether this same source or law also
fixes the régions' own creation date - see the `valid_from` entry below, which this
same page didn't resolve.

### ICASEES IHPC "Inflation" row, cross-checked against World Bank's independent series (2026-09-13)

The IHPC dashboard file's `IND14 "Inflation"` row couldn't be reproduced by a naive
month-over-month or year-over-year recomputation from the file's own `IND1` global
index series - logged as unreconciled rather than guessed at. Resolved by doing the
independent cross-check its own "resolved when" suggested: queried World Bank's
`FP.CPI.TOTL.ZG` (inflation, consumer prices, annual %) for CAF directly and compared
it against this project's stored December value for each year -

| Year | `taux_inflation` (ICASEES, December) | World Bank `FP.CPI.TOTL.ZG` (annual) |
|---|---|---|
| 2021 | 4.26% | 4.26% |
| 2022 | 5.58% | 5.58% |
| 2023 | 2.99% | 2.98% |
| 2024 | 1.48% | 1.48% |

Matches exactly or within rounding at every single point checked. The published row
is a genuine year-over-year ("glissement annuel") inflation rate, externally
validated against an independent source - not an unexplained or suspect number. The
exact internal formula ICASEES uses still isn't confirmed (the file itself gives no
methodology note), but that's no longer a live concern about the *values* being
wrong, just an unanswered "how," which isn't blocking.

### RGPH-4 national total's primary source, now independently located (2026-09-13)

Two prior research attempts (2026-09-05, 2026-09-12) both failed to find ICASEES's
own RGPH-4 results page directly - several `icasees.org/rgph-4/*` URLs returned 404,
and the site's search results were polluted with what looked like injected spam
(`?prizes%2F...` URLs, avoided rather than visited). Found on the third attempt: the
actual results page is `https://www.icasees.org/index.php?q=statistiques&r=resultats`
(a query-string URL, not a clean `/rgph-4/` path, which is likely why it hadn't
surfaced before). It states, verbatim: "RCA en 2025 selon les résultats provisoires
du RGPH-4" - Total 6 656 269 (3 312 532 hommes / 3 343 737 femmes), superficie
623 000 km², densité 10,7/km², with the same "données non encore validées" caveat
this project already carried. Matches `data/observations.csv`'s stored figure
exactly. `data/sources.csv`'s `icasees-rgph4-provisional` row updated with the
confirmed URL and licence/access notes rewritten to reflect direct verification
instead of a compiled, unverified chain of provenance.

### The 84-vs-85 decree/COD-AB sous-préfecture gap (2026-09-11)

The December 2020 reporting (Oubangui Médias, Xinhua) covered the bill as *adopted*
by the National Assembly on 10 Dec 2020, stating 84 sous-préfectures. The law was
promulgated over a month later as **Loi n°21.001 du 21 janvier 2021**, which two
independent secondary sources (limko.cm, fetched and quoted directly; a second
makanisi.org page returned 403 but agreed via search snippet) both state as: *"La
République Centrafricaine est divisée en 7 régions, 20 préfectures, 85
sous-préfectures et 175 communes."* - 85, matching COD-AB v02 exactly. The most
likely explanation is the number changed between adoption and promulgation, which is
ordinary legislative process, not a data error. The actual Journal Officiel PDF
itself still hasn't been located directly - if it turns up, worth a final check that
the promulgated text really says 85 - but this is corroborated by two independent
citations of the same law, which is enough to close this as resolved rather than
open. Bonus: this same law is confirmed to define **175 communes** as a real legal
level (not something an old COD-AB edition invented) - relevant if a commune source
is ever found, since 175 would be the expected target count.

### World Bank GDP figures cross-checked against ICASEES's own rebasing (2026-09-12)

ICASEES published its rebased comptes nationaux (base 2019, SCN 2008) for
2019-2021 on 2026-07-30. Fetched the actual PDF and cross-checked its
Tableau 1 growth-rate figures against the World Bank's modelled estimate
for the same years: they disagree substantially (ICASEES 3.41%/3.44% for
2020/2021 vs World Bank 0.90%/0.98%, a roughly 250% relative spread for
2021). This is now surfaced as a real multi-source disclosure on
`/economie/` rather than silently picking one, per `CLAUDE.md`'s authority
ranking (donnée administrative nationale outranks estimation modélisée
internationale, so ICASEES is the headline). GDP total and per-capita in
FCFA were also added as new indicators (`pib_total_fcfa`,
`pib_par_habitant_fcfa`) rather than forced into the existing USD ones,
since converting between the two currencies would require an assumed
exchange rate this project hasn't verified - see
`pipeline/add_comptes_nationaux.py`.

One loose end, not resolved: the PDF's own narrative summary (page 7)
states a 2021 growth rate of 1.6%, which contradicts its own Tableau 1
value of 3.44% for the same year and the same concept. The tabulated
value was used as authoritative (structured data over prose), and the
inconsistency is logged in `data/sources.csv`'s `licence_notes` for
`icasees-comptes-nationaux` rather than resolved by guessing which one the
document's authors meant.

### ICASEES education yearbook fetch, retried and resolved (2026-09-12)

The earlier block (likely rate-limiting from this project's own request
volume against icasees.org, logged the same day) had genuinely cleared by
the time this was retried later the same session: the publications
listing page and the 2024-2025 Annuaire Statistique's Excel download both
returned clean, complete responses on the first try, no sign of the
earlier corrupted-content or 404 failures. A single request each was
enough, not a retry loop.

The workbook itself is exactly as irregular as `CLAUDE.md` warned - one
unstructured sheet (3.7 MB) mixing narrative text and tables at
inconsistent positions, with a multi-page acronym glossary before any
data starts. Found two genuinely usable tables by hand: a national
summary by education level (établissements, élèves, enseignants - now
`nombre_etablissements_scolaires`, `effectif_eleves`, `nombre_enseignants`)
and a PSE sector-plan tracking table with a clean "Valeur de base (2019) /
Valeur réalisée 2024" header giving a real Baccalauréat général pass rate
(`taux_reussite_baccalaureat`: 25% in 2019, 36.66% in 2024) - closing the
gap `CLAUDE.md` named explicitly ("BEPC and Baccalauréat results are not
published in machine-readable form"). A second, more prominent-looking
exam-results table (session 2020/2021) turned out to have entirely empty
data rows - a template carried over from an earlier year's file, checked
directly rather than assumed populated - so BEPC/CEPE results are still
genuinely unavailable, not just unfetched.

Given the layout inconsistency `CLAUDE.md` itself flags, this was
transcribed by hand into `pipeline/add_annuaire_education.py` rather than
parsed generically - a script hard-coded to today's cell positions would
silently misread a future year's differently-laid-out edition rather than
fail loudly. Re-verify cell positions by hand for each future year rather
than trusting the same code to still be correct.
