# Verification debt

The "come back to this" list. Per `CLAUDE.md`'s rule zero v1 note: real, sourced data
can be used in v1 before its licence is fully resolved or it's been cross-checked
against other sources — logged here instead of blocking. This list needs to be empty,
or at least reviewed item by item, before the site is presented as a finished public
v1 or promoted as authoritative. It is not a place to file things and forget them.

Each entry: what's unresolved, where it's used, what "resolved" would look like.

---

## Open

### COD-AB licence — "humanitarian purposes only" restriction

- **What:** The HDX listing for `cod-ab-caf` (fetched 2026-09-04) carries `isopen:
  false` in its own CKAN metadata and this caveat: *"Dataset is awaiting validation
  by ICASEES (government). The Humanitarian Coordinator granted special approval for
  the use of this dataset for humanitarian purposes only on 2025. If the dataset is
  shared or made public, users must include the following disclaimer: [...]"*
  `CLAUDE.md` assumed this was straightforwardly open ("the humanitarian sector
  standard"); it isn't, at least not for a public-facing non-humanitarian product.
- **Used in:** not yet used for anything committed. Surfaced during the first Phase 1
  fetch attempt, before any entities/geometry were pulled in.
- **Resolved when:** either (a) redistribution is swapped for citation-only (link to
  HDX, don't mirror the geometry/data), (b) an alternate boundary source without this
  restriction is found and used instead, or (c) an actual licence conversation
  clarifies this project qualifies for use/redistribution.

### COD-AB admin counts have moved since `CLAUDE.md` was compiled — now with a precise second-source cross-check

- **What:** `CLAUDE.md`'s administrative-geography table lists COD-AB as 17
  préfectures / 72 sous-préfectures / 175 communes. The live dataset (version 02,
  reviewed 2026-03-06) states **20 préfectures / 85 sous-préfectures**.

  **The 84-vs-85 gap is resolved as of 2026-09-11**, moved to Resolved below — see
  that entry. What follows here is the separate, still-open citypopulation.de
  cross-check.

  Cross-checked 2026-09-09 against citypopulation.de (which relays ICASEES data,
  admin page fetched and snapshotted at
  `raw/citypopulation-de-caf/2026-09-09/admin_index.html`): its total is **77**, not
  85, and the gap is concentrated in exactly 6 préfectures, not spread evenly —
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
  the next population census" — a plausible explanation for why it's *lower* than a
  2026-reviewed source, but that's a hypothesis, not confirmed.

  **Update 2026-09-09 — diagnosed name-by-name, not just by count.** Fetched
  citypopulation.de's actual named sous-préfecture lists (not just totals) for all 6
  préfectures. Two different kinds of disagreement, now split out in
  `data/unresolved.csv` (9 rows):

  - **5 straightforward "citypopulation is missing one entry"** cases where names and
    codes otherwise align exactly: Mboki (CF635, Haut-Mbomou), Am-Dafok (CF534) and
    Ouandja (CF533, both Vakaga), Ouandja-Kotto (CF524, Haute-Kotto), Moboma (CF126,
    Lobaye). Consistent with citypopulation.de's own "incomplete mapping" admission.
  - **2 genuine conflicts**, not just omissions:
    - **Kodi/Ndim (Lim-Pendé):** COD-AB v02 gives Kodi code CF344 and Ndim CF343.
      citypopulation.de gives **Kodi** code **CF343** — re-verified by fetching the
      exact page text directly (not trusting the first summarized pass), confirmed
      real. citypopulation.de's page annotates Kodi "(← Ngaoundaye)," suggesting a
      recent split, which may explain a re-numbering disagreement — not confirmed.
      Ndim doesn't appear on citypopulation.de at all. Taley (CF345) is also simply
      missing there, same as the 5 above.
    - **Bangui:** not a missing-entry case at all, and now a *three*-way
      disagreement, not two. COD-AB v02 names Bangui's 4 sous-préfectures by zone
      (Bangui-Centre/Kagas/Fleuve/Rapides, codes CF711–714). citypopulation.de names
      3 by place (Bangui itself as a city, Bimbo, Bégoua), codes CF711–713
      overlapping but attached to different names. **ICASEES itself** (fetched
      2026-09-11, `icasees.org/index.php/actualites/316-...`, quoted verbatim) uses a
      *third* model for RGPH-4 census-taking purposes: "the nine (9) arrondissements
      of the capital as well as the communes of Bimbo and Bégoua" — i.e. Bangui
      proper has 9 arrondissements (not 4 zones, not 1 city-unit), and Bimbo/Bégoua
      are explicitly called **communes**, not sous-préfectures, and may not even
      belong to Bangui préfecture administratively (Bimbo does not appear anywhere
      in COD-AB v02's sous-préfecture list under any préfecture). This is not
      converging — it's genuinely three different structural models for the same
      area, from three different institutional purposes (COD-AB: humanitarian
      mapping zones; citypopulation.de: demographic reporting; ICASEES: census
      logistics). Resolving this needs to identify which model, if any, matches the
      actual legal/administrative sous-préfecture structure — none of the three may
      be "wrong," they may just be answering different questions.
- **Used in:** not yet used to adjust any entity — `data/entities.csv` still follows
  COD-AB v02 as-is (85 sous-préfectures). This cross-check doesn't change that
  choice; it documents the disagreement precisely (`data/unresolved.csv`) instead of
  silently picking a side.
- **Resolved when:** for the 5 simple-missing cases, confirming they're genuinely
  post-2021 additions (would close them with no entity change needed). For Kodi/Ndim,
  finding a third source to settle the code assignment. For Bangui, finding a source
  that explains the relationship between the zone-based and place-based naming
  schemes — they may both be legitimate but describing different things (e.g.
  administrative zones vs. communes), not actually contradictory.

### Régions → préfectures mapping has only one source

- **What:** The 7 RGPH-4 régions were mapped onto the 20 préfectures using 7
  individual pages on `minurbanisme-rca.org` (Ministère de l'Urbanisme), fetched
  2026-09-05. This is a government site with administrative-directorate pages, not a
  law or decree, and no second independent source was checked. It's only internally
  consistent (the 7 lists sum to exactly 20 préfectures, no gaps or overlaps) — that's
  a good sign, not confirmation. Also: `CLAUDE.md` originally named one région
  "Kagas" (plural); the ministry site consistently calls it "Kaga" (singular) —
  entities.csv uses "Kaga" as canonical, "Kagas" not yet recorded as an alias.
- **Used in:** `data/entities.csv` (7 région rows, `cf-r-*-v1`), and to re-parent all
  20 préfecture rows from the country directly to their région.
- **Resolved when:** a second source (RGPH-4's own régions definition, if a primary
  ICASEES document naming the régions can be found, rather than reporting about it)
  confirms the same 7×préfectures composition.

### Région `valid_from` date is a governance date, not necessarily RGPH-4's

- **What:** Régions were given `valid_from = 2024-06-01`, based on reporting that
  regional governors were first named around June 2024 — found alongside the
  ministry pages, not independently verified as *the* date RGPH-4's 7-région
  structure itself took effect (which may predate the governors being appointed to
  administer it).
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
  `Archive_Base1981_Brute` sheet — this is unusually transparent. What's not
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
- **Used in:** not load-bearing — the pipeline (`add_ihpc_observations.py`) reads the
  actual data columns, not the metadata sheet's stated range, so this didn't produce
  a wrong result. Noted here so nobody trusts the metadata sheet's date range at face
  value in future work on this file.
- **Resolved when:** not urgent to resolve — informational.

---

## Resolved

### The 84-vs-85 decree/COD-AB sous-préfecture gap (2026-09-11)

The December 2020 reporting (Oubangui Médias, Xinhua) covered the bill as *adopted*
by the National Assembly on 10 Dec 2020, stating 84 sous-préfectures. The law was
promulgated over a month later as **Loi n°21.001 du 21 janvier 2021**, which two
independent secondary sources (limko.cm, fetched and quoted directly; a second
makanisi.org page returned 403 but agreed via search snippet) both state as: *"La
République Centrafricaine est divisée en 7 régions, 20 préfectures, 85
sous-préfectures et 175 communes."* — 85, matching COD-AB v02 exactly. The most
likely explanation is the number changed between adoption and promulgation, which is
ordinary legislative process, not a data error. The actual Journal Officiel PDF
itself still hasn't been located directly — if it turns up, worth a final check that
the promulgated text really says 85 — but this is corroborated by two independent
citations of the same law, which is enough to close this as resolved rather than
open. Bonus: this same law is confirmed to define **175 communes** as a real legal
level (not something an old COD-AB edition invented) — relevant if a commune source
is ever found, since 175 would be the expected target count.
