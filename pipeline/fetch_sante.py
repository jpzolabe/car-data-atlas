"""Fetch health indicators for CAR from the World Bank API, plus real
absolute health-workforce headcounts from WHO's Global Health Observatory
(GHO) -- World Bank's WDI only publishes doctor/bed *density* (per 1,000
people), never a raw count, so a second API was needed for that.

All 10 World Bank codes were confirmed to return real, non-empty CAF data
before being added -- most through 2023-2024, genuinely current. One real
exception, not smoothed over: SH.MED.BEDS.ZS (hospital beds) only has 6
points, the most recent from 2011 -- flagged in data/sources.csv and on the
page rather than hidden.

Added 2026-09-12: real absolute headcounts for doctors and nursing/
midwifery personnel, found via WHO's OData API (ghoapi.azureedge.net) after
confirming WDI has no such figure -- see docs/decisions.md for how the
indicator codes were found (querying Indicator?$filter=contains(...)).
No absolute hospital-bed count exists in either WDI or GHO (checked both
directly) -- rather than leave that gap unaddressed, a bed count is derived
for each of the 6 years SH.MED.BEDS.ZS actually has, by fetching that same
year's real World Bank population figure and multiplying (density/1000 x
population) -- explicitly labelled as calculated, not a directly-published
figure, and dated to the same year as the density point it's derived from
(never mixed with a more recent population estimate, which would misrepresent
a 2011 estimate as current).

Usage: uv run python -m pipeline.fetch_sante
"""

import csv

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
BASE_URL = "https://api.worldbank.org/v2/country/CAF/indicator/{code}?format=json&per_page=20&mrnev=15"
GHO_URL = "https://ghoapi.azureedge.net/api/{code}"
POP_URL = "https://api.worldbank.org/v2/country/CAF/indicator/SP.POP.TOTL?format=json&date={year}"

# WHO GHO indicator code -> (indicator_id, source_id, unit, quality_flag,
# dim1_filter, notes). dim1_filter picks one Dim1 value out of a
# sex-disaggregated series (e.g. "SEX_BTSX" for both sexes) -- None means
# the indicator has no such breakdown and every row is used as-is. Found
# via Indicator?$filter=contains(IndicatorName,'Medical doctors'/'Nursing')
# -- see docs/decisions.md.
GHO_INDICATORS = {
    "HWF_0002": (
        "nombre_medecins", "who-gho-health-workforce", "personnes", "administratif", None,
        "Effectif publié par l'OMS (National Health Workforce Accounts), "
        "pas une densité recalculée.",
    ),
    "HWF_0007": (
        "nombre_personnel_infirmier", "who-gho-health-workforce", "personnes", "administratif", None,
        "Effectif publié par l'OMS (National Health Workforce Accounts). "
        "Varie fortement d'une année à l'autre (ex. 835 en 2008, 5653 en "
        "2023, 2331 en 2024), probablement un changement de méthode de "
        "collecte plutôt qu'une vraie fluctuation de l'effectif ; non "
        "confirmé à ce jour.",
    ),
    "WHOSIS_000001": (
        "esperance_vie", "who-gho-life-expectancy", "ans", "estime", "SEX_BTSX",
        "Estimation OMS (World Health Statistics / Global Health Observatory), "
        "révisée par l'OMS le 2026-10-01 (couvre désormais 2000-2023, contre "
        "2000-2021 avant cette révision). La série Banque mondiale "
        "équivalente (SP.DYN.LE00.IN) montre le même profil - des creux "
        "ponctuels les mêmes années (voir ci-dessous), à une magnitude "
        "différente - confirmé en interrogeant les deux API en direct ; pas "
        "une erreur de récupération de ce projet sur l'une ou l'autre.",
    ),
}

# World Bank code -> (indicator_id, source_id, unit, notes)
INDICATORS = {
    "SH.DYN.MORT": (
        "taux_mortalite_moins_5ans", "world-bank-child-mortality",
        "pour 1 000 naissances vivantes",
        "Estimation UN IGME, compilée par la Banque mondiale.",
    ),
    "SP.DYN.IMRT.IN": (
        "taux_mortalite_infantile", "world-bank-child-mortality",
        "pour 1 000 naissances vivantes",
        "Estimation UN IGME, compilée par la Banque mondiale.",
    ),
    "SH.STA.MMRT": (
        "taux_mortalite_maternelle", "world-bank-maternal-mortality",
        "pour 100 000 naissances vivantes",
        "Estimation du groupe interagences OMS/UNICEF/UNFPA/Banque mondiale/UNPD.",
    ),
    "SH.IMM.MEAS": (
        "taux_vaccination_rougeole", "world-bank-immunization", "%",
        "Estimation conjointe OMS/UNICEF de la couverture vaccinale.",
    ),
    "SH.IMM.IDPT": (
        "taux_vaccination_dtc", "world-bank-immunization", "%",
        "Estimation conjointe OMS/UNICEF de la couverture vaccinale.",
    ),
    "SH.MED.PHYS.ZS": (
        "densite_medecins", "world-bank-health-workforce",
        "pour 1 000 habitants",
        "Estimation OMS Global Health Workforce Statistics, compilée par la Banque mondiale.",
    ),
    "SH.MED.BEDS.ZS": (
        "densite_lits_hopital", "world-bank-health-workforce",
        "pour 1 000 habitants",
        "Estimation OMS Global Health Workforce Statistics, réellement ancienne "
        "(dernier point 2011).",
    ),
    "SH.XPD.CHEX.GD.ZS": (
        "depenses_sante_pib", "world-bank-health-expenditure", "% du PIB",
        "Estimation OMS Global Health Expenditure Database, compilée par la Banque mondiale.",
    ),
    "SH.HIV.INCD.ZS": (
        "incidence_vih", "world-bank-hiv-incidence",
        "pour 1 000 personnes non infectées 15-49 ans",
        "Estimation ONUSIDA, compilée par la Banque mondiale.",
    ),
}


# UN IGME's own documented method for crisis countries: fit the trend with
# crisis years set aside, then add the crisis deaths back as a one-year
# spike in the year each mortality survey was run - not spread across the
# period it actually covers. Real, sourced excess-mortality data, not a
# fetch error; without this note the spike looks exactly like the corrupted
# esperance_vie series this project found and replaced. Checked on the web
# (Our World in Data's IGME methodology notes, cross-checked against the
# underlying academic source) rather than assumed from the shape of the jump.
CRISIS_YEAR_NOTE = {
    "SH.DYN.MORT": {
        "2022": (
            " Le pic de 2022 est réel, pas une erreur : selon la méthodologie "
            "publiée de l'UN IGME pour les pays en crise, la tendance est "
            "ajustée hors années de crise puis les décès de la crise sont "
            "réintégrés comme un pic d'une seule année, l'année où l'enquête "
            "de mortalité a eu lieu plutôt que répartis sur la période "
            "qu'elle couvre réellement. Pour la RCA, ce pic provient de "
            "l'enquête de Gang et al. (2023, Conflict and Health), qui a "
            "trouvé une mortalité environ 4 fois supérieure aux statistiques "
            "officielles de l'ONU sur la période étudiée."
        ),
        "2019": (
            " Le pic de 2019 suit la même méthodologie documentée par l'UN "
            "IGME pour les années de crise (décès réintégrés comme un pic "
            "d'une seule année, l'année de l'enquête plutôt que répartis sur "
            "la période couverte) ; l'enquête de mortalité spécifique à "
            "l'origine de ce pic n'a pas été identifiée avec certitude."
        ),
    },
}
CRISIS_YEAR_NOTE["SP.DYN.IMRT.IN"] = CRISIS_YEAR_NOTE["SH.DYN.MORT"]

# esperance_vie (WHOSIS_000001) shows the same four-year crisis-dip pattern,
# confirmed 2026-10-16 by cross-checking against World Bank's independent
# SP.DYN.LE00.IN series live: both show a one-year crash in exactly 2009,
# 2014, 2019 and 2022 (different magnitudes, same years), which is what
# rules out a fetch-side bug on either series - two independent pipelines
# landing on the same years is not a coincidence a filter mistake could
# produce. 2019 and 2022 reuse the Gang et al. (2023) excess-mortality
# citation already established above for the mortality-rate indicators,
# since life expectancy is calculated from the same underlying mortality
# estimates. 2014 lines up with the well-documented peak of the 2013
# Séléka/anti-balaka civil war, stated as historical context rather than a
# specific cited methodology paper. 2009 has no identified survey or event
# behind it - left unexplained rather than guessed at.
CRISIS_YEAR_NOTE["WHOSIS_000001"] = {
    "2022": (
        " Le creux de 2022 correspond au même pic de mortalité de crise que "
        "pour les indicateurs de mortalité ci-dessus (enquête de Gang et "
        "al., 2023, Conflict and Health) : l'espérance de vie calculée pour "
        "une année donnée reflète directement les taux de mortalité de "
        "cette année."
    ),
    "2019": (
        " Le creux de 2019 suit le même type d'ajustement que celui "
        "documenté pour les indicateurs de mortalité ci-dessus ; l'enquête "
        "spécifique à l'origine de ce pic n'a pas été identifiée avec "
        "certitude pour l'espérance de vie non plus."
    ),
    "2014": (
        " Le creux de 2014 correspond à l'année la plus intense du conflit "
        "Séléka/anti-balaka (2013-2015), largement documentée ; aucune "
        "méthodologie de calcul spécifique n'a cependant été identifiée "
        "pour confirmer ce lien précisément, contrairement à 2019 et 2022."
    ),
    "2009": (
        " Le creux de 2009 n'est pas expliqué : aucune enquête ou "
        "événement précis n'a été identifié pour cette année ; signalé "
        "tel quel plutôt que deviné."
    ),
}


def fetch_indicator(code: str, retrieved_at: str) -> list[dict]:
    indicator_id, source_id, unit, notes = INDICATORS[code]
    resp = httpx.get(
        BASE_URL.format(code=code), timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    _, records = resp.json()
    rows = []
    for r in records:
        if r["value"] is None:
            continue
        row_notes = notes + CRISIS_YEAR_NOTE.get(code, {}).get(r["date"], "")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": r["date"], "value": r["value"], "unit": unit,
            "source_id": source_id, "retrieved_at": retrieved_at,
            "quality_flag": "estime", "notes": row_notes,
        })
    return rows


def fetch_gho_indicator(code: str, retrieved_at: str) -> list[dict]:
    indicator_id, source_id, unit, quality_flag, dim1_filter, notes = GHO_INDICATORS[code]
    resp = httpx.get(
        GHO_URL.format(code=code),
        params={"$filter": "SpatialDim eq 'CAF'"},
        timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    rows = []
    for r in resp.json()["value"]:
        if r["NumericValue"] is None:
            continue
        if dim1_filter is not None and r.get("Dim1") != dim1_filter:
            continue
        period = str(r["TimeDim"])
        row_notes = notes + CRISIS_YEAR_NOTE.get(code, {}).get(period, "")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": period, "value": r["NumericValue"], "unit": unit,
            "source_id": source_id, "retrieved_at": retrieved_at,
            "quality_flag": quality_flag, "notes": row_notes,
        })
    return rows


def fetch_derived_hospital_beds(density_rows: list[dict], retrieved_at: str) -> list[dict]:
    """Bed density (SH.MED.BEDS.ZS, already fetched in-memory by
    fetch_indicator()) x that same year's real population = an estimated
    bed count, computed here rather than published directly anywhere.
    Fetches population for the *same year* as each density point, never a
    more recent one, so a 2011 estimate is never dressed up as current."""
    rows = []
    for d in density_rows:
        year = d["period"]
        resp = httpx.get(
            POP_URL.format(year=year), timeout=30.0,
            headers={"User-Agent": "rca-donnees-project/0.1"},
        )
        resp.raise_for_status()
        _, records = resp.json()
        if not records or records[0]["value"] is None:
            continue
        population = records[0]["value"]
        bed_count = round(float(d["value"]) / 1000 * population)
        population_fr = format(round(population), ",").replace(",", " ")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": "nombre_lits_hopital",
            "period": year, "value": bed_count, "unit": "lits",
            "source_id": "world-bank-health-workforce", "retrieved_at": retrieved_at,
            "quality_flag": "estime",
            "notes": (
                f"Estimation calculée : densité {d['value']} pour 1 000 "
                f"habitants x population {population_fr} en {year} "
                f"(World Bank SP.POP.TOTL), pas un décompte publié "
                f"directement."
            ),
        })
    return rows


def main():
    import datetime
    today = datetime.date.today().isoformat()
    new_rows = []
    for code in INDICATORS:
        new_rows.extend(fetch_indicator(code, today))
    for code in GHO_INDICATORS:
        new_rows.extend(fetch_gho_indicator(code, today))

    density_rows = [r for r in new_rows if r["indicator_id"] == "densite_lits_hopital"]
    new_rows.extend(fetch_derived_hospital_beds(density_rows, today))

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    replaced_indicators = (
        {v[0] for v in INDICATORS.values()}
        | {v[0] for v in GHO_INDICATORS.values()}
        | {"nombre_lits_hopital"}
    )
    existing = [
        r for r in existing
        if not (r["entity_id"] == COUNTRY_ID and r["indicator_id"] in replaced_indicators)
    ]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    by_indicator: dict[str, int] = {}
    for row in new_rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Added {len(new_rows)} health observations across {len(by_indicator)} indicators:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
