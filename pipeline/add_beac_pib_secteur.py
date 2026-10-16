"""Add GDP-by-sector observations for RCA, hand-extracted from BEAC's
deor_rca-1.xlsx ("Produit Intérieur Brut (PIB) par secteur"), per
data/sources.csv's beac-pib-secteur-rca row.

Adds a primaire/secondaire/tertiaire sector breakdown that nothing else on
the site has - the only existing sector figure is valeur_ajoutee_agriculture_
pib (World Bank, % of GDP, agriculture/sylviculture/pêche only). This is
current-price GDP in FCFA per broad sector, not comparable to that World
Bank % indicator and not merged with it.

Same freshness ceiling and "Estim" caveat as add_beac_tofe.py: the file's
columns run 2012-2022 only, with 2020-2022 marked "Estim" in the file
itself, despite the filename suggesting a 2023 vintage. Current-price
series only (the file also has a constant-2005-price series, not extracted
here - current price is what the other FCFA économie indicators on this
site use).

Usage: uv run python -m pipeline.add_beac_pib_secteur
"""

import csv

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "beac-pib-secteur-rca"
RETRIEVED_AT = "2026-10-16"

YEARS = [str(y) for y in range(2012, 2023)]
ESTIM_FROM = "2020"

SECTEUR_PRIMAIRE = [
    497.753, 277.013, 322.168, 318.56600000000003, 347.646, 397.0400000000001,
    386.977, 413.3083137887445, 428.8636008904498, 454.9434936289614, 508.3306198707958,
]
SECTEUR_SECONDAIRE = [
    326.76800000000003, 194.602, 178.067, 219.35, 231.58399999999997, 247.068,
    252.01, 267.3361459958157, 266.1077236487685, 266.2011989508804, 258.80352207140896,
]
SECTEUR_TERTIAIRE = [
    385.408, 331.1379999999999, 391.00699999999995, 422.416, 450.78700000000003,
    503.947, 517.748, 556.0697147790817, 599.7129740110429, 587.6309420123282, 612.8646891244643,
]

NOTES = {
    "pib_secteur_primaire_fcfa": (
        "Secteur primaire (agriculture, élevage, chasse et pêche, "
        "sylviculture, industries extractives), prix courants du marché, "
        "PIB par secteur de la RCA (BEAC), feuille deorrca."
    ),
    "pib_secteur_secondaire_fcfa": (
        "Secteur secondaire (industrie manufacturière, énergie, "
        "construction), prix courants du marché, PIB par secteur de la RCA "
        "(BEAC), feuille deorrca."
    ),
    "pib_secteur_tertiaire_fcfa": (
        "Secteur tertiaire (services privés, administrations publiques), "
        "prix courants du marché, PIB par secteur de la RCA (BEAC), feuille "
        "deorrca."
    ),
}


def build_rows() -> list[dict]:
    rows = []
    for series, indicator_id in [
        (SECTEUR_PRIMAIRE, "pib_secteur_primaire_fcfa"),
        (SECTEUR_SECONDAIRE, "pib_secteur_secondaire_fcfa"),
        (SECTEUR_TERTIAIRE, "pib_secteur_tertiaire_fcfa"),
    ]:
        for period, value in zip(YEARS, series):
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
                "period": period, "value": round(value * 1_000_000_000), "unit": "FCFA",
                "source_id": SOURCE_ID, "retrieved_at": RETRIEVED_AT,
                "quality_flag": "estime" if period >= ESTIM_FROM else "",
                "notes": NOTES[indicator_id],
            })
    return rows


def main():
    new_rows = build_rows()

    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = list(reader)

    existing = [r for r in existing if r["source_id"] != SOURCE_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} BEAC GDP-by-sector observations "
          f"({len(YEARS)} years x 3 indicators, 2020-2022 flagged 'estime').")


if __name__ == "__main__":
    main()
