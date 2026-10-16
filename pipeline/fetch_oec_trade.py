"""Fetch CAR's top export products and top trading partners from the OEC
(Observatory of Economic Complexity) public API, which mirrors CEPII's
BACI international trade dataset. A real, re-queryable API (unlike
add_afdb_meo_2026.py's one-off PDF), so this follows the fetch_*.py
idempotent-replace pattern.

Deliberately NOT re-sourcing exportations_montant/importations_montant
(the existing World Bank-backed aggregate totals) - this is new content
(product/partner composition), not a competing source for a number the
site already shows. Bounded to a handful of each category for the most
recent year (2024) rather than the full ~73-product breakdown, since
these are meant as a small "what/who" snapshot alongside the trade
totals, not a full trade-statistics explorer. Products: top 4, not top
5 - "Aircraft and Spacecraft" was excluded (see EXPORT_PRODUCTS below),
leaving one fewer than the two partner lists.

BACI's HS6-depth edition used here (cube trade_i_baci_a_22) only covers
2022-2024 - that's the dataset's entire time span, not a fetch limitation.

API docs: https://oec.world/en/resources/api/data
Usage: uv run python -m pipeline.fetch_oec_trade
"""

import csv
import datetime

import httpx

COUNTRY_ID = "cf-pays-centrafrique-v1"
SOURCE_ID = "oec-baci-trade-2024"
BASE_URL = "https://api-v2.oec.world/tesseract/data.jsonrecords"
YEAR = "2024"

# HS2 product category (English, as returned by the API) -> indicator_id.
# Top export products by value for YEAR, picked after fetching the full
# ~73-category breakdown and sorting by Trade Value - see the chat history
# for that query. "Aircraft and Spacecraft" was the single largest category
# (~47% of 2024 export value on its own) but deliberately left out: almost
# certainly a one-off aircraft sale/transfer rather than a real export
# sector, and misleading to show as "what CAR exports" even with a caveat.
EXPORT_PRODUCTS = {
    "Wood, wood articles, & charcoal": "exportations_bois",
    "Precious stones, metals, & pearls": "exportations_pierres_precieuses",
    "Miscellaneous metal products": "exportations_metaux_divers",
    "Cars, tractors, trucks & parts thereof.": "exportations_vehicules",
}

# Top 5 export destinations and import origins by value for YEAR.
EXPORT_PARTNERS = {
    "Pakistan": "exportations_vers_pakistan",
    "Tunisia": "exportations_vers_tunisie",
    "China": "exportations_vers_chine",
    "Sri Lanka": "exportations_vers_sri_lanka",
    "Egypt": "exportations_vers_egypte",
}
IMPORT_PARTNERS = {
    "Cameroon": "importations_depuis_cameroun",
    "China": "importations_depuis_chine",
    "France": "importations_depuis_france",
    "United States": "importations_depuis_etats_unis",
    "Japan": "importations_depuis_japon",
}

DEFAULT_NOTE = "Donnée miroir de commerce (OEC/BACI, CEPII), {year}."


def fetch_rows(drilldown_dim: str, filter_dim: str, filter_value: str) -> list[dict]:
    resp = httpx.get(
        BASE_URL,
        params={
            "cube": "trade_i_baci_a_22",
            "drilldowns": f"{drilldown_dim},Year",
            "measures": "Trade Value",
            "include": f"{filter_dim}:{filter_value};Year:{YEAR}",
            "limit": "200,0",
        },
        timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    return resp.json()["data"]


def build_rows(retrieved_at: str) -> list[dict]:
    rows = []

    product_rows = fetch_rows("HS2 Official", "Exporter Country Official", "caf")
    by_product = {r["HS2 Official"]: r["Trade Value"] for r in product_rows}
    for product_name, indicator_id in EXPORT_PRODUCTS.items():
        value = by_product.get(product_name)
        if value is None:
            raise SystemExit(f"Expected product '{product_name}' not found in this year's data - "
                              f"the top-5 ranking may have changed, update EXPORT_PRODUCTS.")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": YEAR, "value": value, "unit": "US$",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "administratif",
            "notes": DEFAULT_NOTE.format(year=YEAR),
        })

    export_partner_rows = fetch_rows("Importer Country Official", "Exporter Country Official", "caf")
    by_export_partner = {r["Importer Country Official"]: r["Trade Value"] for r in export_partner_rows}
    for partner_name, indicator_id in EXPORT_PARTNERS.items():
        value = by_export_partner.get(partner_name)
        if value is None:
            raise SystemExit(f"Expected export partner '{partner_name}' not found - update EXPORT_PARTNERS.")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": YEAR, "value": value, "unit": "US$",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "administratif", "notes": DEFAULT_NOTE.format(year=YEAR),
        })

    import_partner_rows = fetch_rows("Exporter Country Official", "Importer Country Official", "caf")
    by_import_partner = {r["Exporter Country Official"]: r["Trade Value"] for r in import_partner_rows}
    for partner_name, indicator_id in IMPORT_PARTNERS.items():
        value = by_import_partner.get(partner_name)
        if value is None:
            raise SystemExit(f"Expected import partner '{partner_name}' not found - update IMPORT_PARTNERS.")
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": YEAR, "value": value, "unit": "US$",
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "administratif", "notes": DEFAULT_NOTE.format(year=YEAR),
        })

    return rows


def main():
    today = datetime.date.today().isoformat()
    new_rows = build_rows(today)
    if not new_rows:
        raise SystemExit("No OEC trade rows built - aborting rather than deleting existing rows.")

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

    print(f"Added {len(new_rows)} OEC trade composition observations "
          f"({len(EXPORT_PRODUCTS)} export products, {len(EXPORT_PARTNERS)} export "
          f"partners, {len(IMPORT_PARTNERS)} import partners, {YEAR}).")


if __name__ == "__main__":
    main()
