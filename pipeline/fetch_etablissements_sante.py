"""Fetch a national count of health facilities from two genuinely
independent sources, specifically to exercise the multi-source disclosure
mechanism with a real conflict - Phase 3 source list item 7 (docs/plan.md),
flagged there as "hard - multiple conflicting sources."

- Master Facility List (Maina et al. 2019, "A spatial database of health
  facilities managed by the public health sector in sub-Saharan Africa",
  Scientific Data) via HDX: government/non-government facility registries
  compiled into one spatial dataset, static since its 2019-07-25
  publication. 555 rows for Central African Republic.
- OpenStreetMap health facilities via healthsites.io's HDX export
  (HOTOSM-curated, actively updated): 425 rows as of this fetch.

These are not two views of the same underlying data - one is a static
2019 government-facility-registry compilation, the other a live,
crowd-mapped OSM extract - so the ~30% gap between them is a real
disagreement worth disclosing, not a rounding difference. See
docs/decisions.md for why hotosm_caf_health_facilities (a second HDX
listing) was NOT also added as a third source: it's the same underlying
OpenStreetMap data as the healthsites.io export, just repackaged, and
counting it separately would look like independent corroboration when
it's really one source counted twice.

Phase 4 addition (2026-09-12): the Master List's own "Admin1" column
carries the RGPH-4 7-région scheme (Bangui/Équateur/Fertit/Haut
Oubangui/Kagas/Plateaux/Yadé), not the 20-préfecture level - confirmed
live by inspecting the fetched dataframe before wiring anything up, per
this project's usual practice. That is genuinely one level below
national, so this file now also writes a per-région breakdown - the
same indicator_id, at entity level "region" instead of "pays". This
breakdown is Master List only: healthsites.io's CSV export doesn't carry
an equivalent admin field, so there's no matching régional figure from
the second source to disclose (unlike the two-source national figure).

Also fixed here: earlier versions of this script fetched both files
straight into memory without saving a raw snapshot, unlike every other
fetch script in this project (AGENTS.md's raw/ "immutable source
snapshots, never overwritten" rule). Both files are now written under
raw/ before being parsed.

Usage: uv run python -m pipeline.fetch_etablissements_sante
"""

import csv
import datetime
import io
from pathlib import Path

import httpx
import pandas as pd

COUNTRY_ID = "cf-pays-centrafrique-v1"
INDICATOR_ID = "nombre_etablissements_sante"

MASTER_LIST_SOURCE_ID = "maina-master-facility-list-2019"
MASTER_LIST_URL = (
    "https://data.humdata.org/dataset/eb1ba830-9464-43c8-9370-28cee0c99f5d/"
    "resource/758d5c17-88f4-42b2-9d4b-4bfe32d4acf7/download/"
    "sub-saharan_health_facilities.xlsx"
)

HEALTHSITES_SOURCE_ID = "hotosm-healthsites-caf"
HEALTHSITES_URL = (
    "https://data.humdata.org/dataset/eedeabac-e17c-4143-bb30-9ef0e55e8dbc/"
    "resource/4a8ebf99-155d-42f4-9693-3d53dbcc104b/download/"
    "central-african-republic.csv"
)

# Master List "Admin1" label -> this project's région entity_id. "Bangui"
# here means the RGPH-4 région whose sole préfecture is Bangui, which this
# project's crosswalk calls "Bas-Oubangui" (see data/entities.csv) - the
# label mismatch is naming only, not a different geography: Bas-Oubangui's
# own entity notes confirm it is exactly Bangui's préfecture.
REGION_ADMIN1_ALIASES = {
    "Bangui": "cf-r-bas-oubangui-v1",
    "Equateur": "cf-r-equateur-v1",
    "Fertit": "cf-r-fertit-v1",
    "Haut Oubangui": "cf-r-haut-oubangui-v1",
    "Kagas": "cf-r-kaga-v1",
    "Plateaux": "cf-r-plateaux-v1",
    "Yade": "cf-r-yade-v1",
}


def fetch_master_list_df(today: str) -> pd.DataFrame:
    resp = httpx.get(MASTER_LIST_URL, follow_redirects=True, timeout=60.0,
                      headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    out_dir = Path(f"raw/maina-master-facility-list/{today}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sub-saharan_health_facilities.xlsx").write_bytes(resp.content)
    df = pd.read_excel(io.BytesIO(resp.content))
    return df[df["Country"] == "Central African Republic"]


def master_list_national_row(car: pd.DataFrame, retrieved_at: str) -> dict:
    count = len(car)
    public = int((car["Ownership"] == "Public").sum())
    return {
        "entity_id": COUNTRY_ID, "indicator_id": INDICATOR_ID,
        "period": "2019", "value": count, "unit": "établissements",
        "source_id": MASTER_LIST_SOURCE_ID, "retrieved_at": retrieved_at,
        "quality_flag": "administratif",
        "notes": (
            f"Compilation à partir de registres publics/gouvernementaux, "
            f"publiée le 2019-07-25 (donnée statique, non mise à jour "
            f"depuis) ; {public} établissements publics, "
            f"{count - public} privés à but non lucratif."
        ),
    }


def master_list_region_rows(car: pd.DataFrame, retrieved_at: str) -> list[dict]:
    counts = car["Admin1"].value_counts()
    rows = []
    for admin1_label, entity_id in REGION_ADMIN1_ALIASES.items():
        if admin1_label not in counts:
            continue
        rows.append({
            "entity_id": entity_id, "indicator_id": INDICATOR_ID,
            "period": "2019", "value": int(counts[admin1_label]),
            "unit": "établissements", "source_id": MASTER_LIST_SOURCE_ID,
            "retrieved_at": retrieved_at, "quality_flag": "administratif",
            "notes": (
                "Répartition régionale du même registre 2019 (Master "
                "Facility List) que le chiffre national ; pas de chiffre "
                "OpenStreetMap équivalent à ce niveau, donc pas de "
                "second avis à comparer ici, contrairement au total "
                "national."
            ),
        })
    return rows


def fetch_healthsites_count(retrieved_at: str) -> dict:
    resp = httpx.get(HEALTHSITES_URL, follow_redirects=True, timeout=60.0,
                      headers={"User-Agent": "rca-donnees-project/0.1"})
    resp.raise_for_status()
    out_dir = Path(f"raw/hotosm-healthsites-caf/{retrieved_at}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "central-african-republic.csv").write_bytes(resp.content)
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    return {
        "entity_id": COUNTRY_ID, "indicator_id": INDICATOR_ID,
        "period": str(datetime.date.today().year), "value": len(rows),
        "unit": "établissements", "source_id": HEALTHSITES_SOURCE_ID,
        "retrieved_at": retrieved_at, "quality_flag": "",
        "notes": (
            "Extraction OpenStreetMap (cartographie collaborative, via "
            "healthsites.io), mise à jour en continu ; pas une enquête "
            "administrative, un décompte des points effectivement "
            "cartographiés par des bénévoles."
        ),
    }


def replace_in_observations(new_rows: list[dict]) -> None:
    replaced_sources = {MASTER_LIST_SOURCE_ID, HEALTHSITES_SOURCE_ID}
    with open("data/observations.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing = [r for r in reader if r["source_id"] not in replaced_sources]

    with open("data/observations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(new_rows)


def main():
    today = datetime.date.today().isoformat()
    car = fetch_master_list_df(today)
    rows = [
        master_list_national_row(car, today),
        *master_list_region_rows(car, today),
        fetch_healthsites_count(today),
    ]
    replace_in_observations(rows)
    for row in rows:
        print(
            f"{row['entity_id']} / {row['source_id']}: "
            f"{row['value']} établissements ({row['period']})"
        )


if __name__ == "__main__":
    main()
