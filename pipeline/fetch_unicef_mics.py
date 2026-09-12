"""Fetch child health/nutrition and child-protection indicators from
UNICEF's Data Warehouse (GLOBAL_DATAFLOW, SDMX), per Phase 3 source list
item 5 (MICS 2018-19 indicators, docs/plan.md).

Not a single-survey feed: UNICEF compiles GLOBAL_DATAFLOW from whichever
national survey covers each indicator most recently for a country -- for
Central African Republic this means most of these are genuinely from MICS6
(2018-2019), but two (stunting, wasting) have a more recent point from a
2022 SMART nutrition survey, used here in preference to the older MICS
point since it's real, more recent, and from the same UNICEF-curated
series. The actual source varies row by row -- read from each
observation's own DATA_SOURCE attribute in the API response and written to
observations.csv's notes field, rather than assumed to be uniformly MICS6.
Checked live before writing anything, not assumed from the indicator's
usual reputation as "the MICS one".

Stunting and wasting also have two extra points at 2019-03 and 2019-11
(sub-annual MICS6/ENSNM survey rounds) between the 2018 and 2022 points
used here -- dropped deliberately, not missed: mixing sub-annual and
annual periods in the same series would misrepresent it as continuously
monitored when it's really occasional point-in-time surveys. See
docs/decisions.md.

Usage: uv run python -m pipeline.fetch_unicef_mics
"""

import csv
import datetime
import re

import httpx

SOURCE_ID = "unicef-data-warehouse"
COUNTRY_ID = "cf-pays-centrafrique-v1"
API_URL = "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/UNICEF,GLOBAL_DATAFLOW,1.0/CAF.{code}._T"

# UNICEF indicator code -> (indicator_id, unit, periods to keep -- None means
# keep every _T period returned; a set restricts to specific years, used for
# stunting/wasting to drop the sub-annual 2019 survey rounds).
INDICATORS = {
    "NT_ANT_HAZ_NE2": ("retard_croissance_enfants", "%", {"2018", "2022"}),
    "NT_ANT_WHZ_NE2": ("emaciation_enfants", "%", {"2018", "2022"}),
    "NT_BF_EXBF": ("allaitement_exclusif", "%", None),
    "MNCH_SAB": ("accouchement_assiste", "%", None),
    "MNCH_ANC4": ("soins_prenatals_4visites", "%", None),
    "PT_CHLD_Y0T4_REG": ("enregistrement_naissances", "%", None),
    "PT_F_20-24_MRD_U18": ("mariage_precoce_filles", "%", None),
}

YEAR_ONLY = re.compile(r"^\d{4}$")


def fetch_indicator(
    code: str, indicator_id: str, unit: str, keep_periods, retrieved_at: str
) -> list[dict]:
    resp = httpx.get(
        API_URL.format(code=code),
        params={"format": "sdmx-json", "dimensionAtObservation": "AllDimensions"},
        timeout=30.0, headers={"User-Agent": "rca-donnees-project/0.1"},
    )
    resp.raise_for_status()
    payload = resp.json()

    struct = payload["data"]["structure"]
    obs_dims = struct["dimensions"]["observation"]
    dim_values = {d["id"]: [v["id"] for v in d["values"]] for d in obs_dims}
    dim_order = [d["id"] for d in obs_dims]

    attr_defs = struct["attributes"]["observation"]
    attr_order = [a["id"] for a in attr_defs]
    attr_values = {
        a["id"]: [v.get("id", v.get("name")) for v in a.get("values", [])]
        for a in attr_defs
    }

    rows = []
    for key, obs in payload["data"]["dataSets"][0]["observations"].items():
        idx = [int(x) for x in key.split(":")]
        period = dim_values["TIME_PERIOD"][idx[dim_order.index("TIME_PERIOD")]]
        if keep_periods is not None and period not in keep_periods:
            continue
        if not YEAR_ONLY.match(period):
            continue

        attrs_raw = obs[1:]
        attrs = {}
        for i, aid in enumerate(attr_order):
            if i < len(attrs_raw) and attrs_raw[i] is not None:
                vals = attr_values[aid]
                attrs[aid] = vals[attrs_raw[i]] if vals else attrs_raw[i]

        data_source = attrs.get("DATA_SOURCE", "").strip() or "non précisé"
        rows.append({
            "entity_id": COUNTRY_ID, "indicator_id": indicator_id,
            "period": period, "value": round(float(obs[0]), 1), "unit": unit,
            "source_id": SOURCE_ID, "retrieved_at": retrieved_at,
            "quality_flag": "",
            "notes": f"Enquête source : {data_source}.",
        })
    return rows


def replace_in_observations(new_rows: list[dict]) -> None:
    replaced_indicators = {v[0] for v in INDICATORS.values()}
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["indicator_id"] not in replaced_indicators]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    today = datetime.date.today().isoformat()
    all_rows = []
    for code, (indicator_id, unit, keep_periods) in INDICATORS.items():
        rows = fetch_indicator(code, indicator_id, unit, keep_periods, today)
        all_rows.extend(rows)

    replace_in_observations(all_rows)

    by_indicator: dict[str, int] = {}
    for row in all_rows:
        by_indicator[row["indicator_id"]] = by_indicator.get(row["indicator_id"], 0) + 1
    print(f"Fetched {len(by_indicator)} indicators, {len(all_rows)} observations total:")
    for indicator_id, count in sorted(by_indicator.items()):
        print(f"  {indicator_id}: {count}")


if __name__ == "__main__":
    main()
