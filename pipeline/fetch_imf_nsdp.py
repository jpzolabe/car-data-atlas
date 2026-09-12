"""Fetch the IMF e-GDDS National Summary Data Page (NSDP) for Central
African Republic, per Phase 3 source list item 6 (docs/plan.md).

Two dead ends before this worked, both checked directly rather than
assumed: the legacy dataservices.imf.org endpoint documented in most
third-party guides no longer resolves (DNS gone), and the AfDB/Knoema
mirror this project originally planned to scrape (car.opendataforafrica.org/nsdp)
turned out to be entirely JavaScript-rendered with no accessible public
API. IMF's current SDMX 2.1 API at api.imf.org (found by locating its
/dataflow listing directly, not guessed) has the same NSDP data live and
unauthenticated.

CAF's e-GDDS reporting is thin: of everything the NSDP framework covers
(GDP, prices, government operations, debt, monetary, external sector),
Central African Republic currently publishes exactly one series --
TEA (Total Economic Activity Index, quarterly) -- confirmed by querying
every dimension as a wildcard and checking what actually came back, not
assumed absent. CPI_WCA and QGDP_WCA (the regional Central Africa
dataflows) were also checked directly for CAF and returned no data.

Usage: uv run python -m pipeline.fetch_imf_nsdp
"""

import csv
import datetime
import xml.etree.ElementTree as ET

import httpx

SOURCE_ID = "imf-egdds-nsdp"
COUNTRY_ID = "cf-pays-centrafrique-v1"
INDICATOR_ID = "indice_activite_economique"
API_URL = "https://api.imf.org/external/sdmx/2.1/data/IMF.STA,NSDP,7.0.0/CAF...."


def fetch_series() -> list[dict]:
    resp = httpx.get(
        API_URL, params={"format": "jsondata"}, timeout=30.0,
        headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    today = datetime.date.today().isoformat()
    rows = []
    for series in root.iter("Series"):
        if series.get("INDICATOR") != "TEA":
            continue  # the only series CAF actually publishes -- checked live
        for obs in series.iter("Obs"):
            rows.append({
                "entity_id": COUNTRY_ID, "indicator_id": INDICATOR_ID,
                "period": obs.get("TIME_PERIOD"), "value": round(float(obs.get("OBS_VALUE")), 2),
                "unit": "indice", "source_id": SOURCE_ID, "retrieved_at": today,
                "quality_flag": "",
                "notes": (
                    "Indice d'activité économique totale (TEA), transmis par "
                    "l'ICASEES au FMI dans le cadre e-GDDS (National Summary "
                    "Data Page)."
                ),
            })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["indicator_id"] != INDICATOR_ID]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    rows = fetch_series()
    if not rows:
        raise SystemExit(
            "No TEA observations returned -- IMF's NSDP data for CAF may have changed shape."
        )
    replace_in_observations(rows)
    print(
        f"Fetched {len(rows)} observations for {INDICATOR_ID} "
        f"({rows[0]['period']} to {rows[-1]['period']})."
    )


if __name__ == "__main__":
    main()
