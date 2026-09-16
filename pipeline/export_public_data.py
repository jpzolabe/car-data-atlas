"""Copy the data/ CSVs into site/public/donnees/ so they're downloadable from
the site's own domain - needed because the GitHub repo is currently private,
so linking to raw.githubusercontent.com would 404 for anyone else. Also writes
site/src/data/donnees.json (row counts + descriptions, plus the coverage
matrix - docs/plan.md Phase 5 item 2) for the /donnees page.
Re-run whenever data/ changes.

Coverage matrix (added 2026-09-13): per theme, how many indicators reach
each geographic level, computed from indicators.csv's own geographic_floor
column - not a separate hand-maintained claim. Levels nest coarse-to-fine
(pays > région > préfecture > sous-préfecture): an indicator whose floor is
sous_prefecture also counts at every coarser level, since a finer figure
can always be aggregated up. "marché" (prix's market-point indicators) is
a separate, non-nested floor - a market is a point, not an administrative
area, so it doesn't sit inside the pays/région/préfecture/sous-préfecture
ladder at all. Kept on /donnees per the user's direction (2026-09-13) -
originally sketched as a separate /couverture page in docs/plan.md, folded
in here instead since this page already inventories the data itself.

Usage: uv run python -m pipeline.export_public_data
"""

import csv
import json
import shutil
from pathlib import Path

# Coarse to fine - see the module docstring for why this hierarchy holds.
LEVELS = ["pays", "region", "prefecture", "sous_prefecture"]
THEME_LABELS = [
    ("population", "Population"),
    ("infrastructures", "Infrastructures"),
    ("education", "Éducation"),
    ("sante", "Santé"),
    ("economie", "Économie"),
    ("agriculture", "Agriculture"),
    ("prix", "Prix"),
]


def build_coverage():
    with open("data/indicators.csv", encoding="utf-8", newline="") as f:
        indicators = list(csv.DictReader(f))

    rows = []
    for theme_id, label in THEME_LABELS:
        theme_indicators = [i for i in indicators if i["theme"] == theme_id]
        total = len(theme_indicators)
        by_level = {}
        for level in LEVELS:
            level_rank = LEVELS.index(level)
            by_level[level] = sum(
                1 for i in theme_indicators
                if i["geographic_floor"] in LEVELS
                and LEVELS.index(i["geographic_floor"]) >= level_rank
            )
        marche = sum(1 for i in theme_indicators if i["geographic_floor"] == "marche")
        rows.append({
            "theme_id": theme_id, "label": label, "total": total,
            "by_level": by_level, "marche": marche,
        })
    return rows

# (filename, one-line description - same as data/README.md, kept in sync by hand)
FILES = [
    ("entities.csv", "Une ligne par unité administrative, par version. "
                      "Jamais modifié en place - un redécoupage crée une nouvelle entité."),
    ("aliases.csv", "Chaque orthographe, variante d'accent et code source, "
                     "rattachés à un identifiant canonique."),
    ("sources.csv", "Une ligne par source : producteur, licence, cadence, "
                     "vintage géographique, mise en garde éventuelle."),
    ("indicators.csv", "Un indicateur par ligne : définition, unité, thème, "
                        "et le niveau géographique le plus fin qu'il atteint réellement."),
    ("observations.csv", "Les valeurs elles-mêmes, format long : "
                          "entité, indicateur, période, valeur, source."),
    ("unresolved.csv", "Chaque cas que le rapprochement des sources n'a pas su résoudre - "
                        "un livrable, pas un journal d'échecs."),
]

OUT_DIR = Path("site/public/donnees")
JSON_OUT = Path("site/src/data/donnees.json")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files_meta = []
    for name, description in FILES:
        src = Path("data") / name
        dst = OUT_DIR / name
        shutil.copyfile(src, dst)
        with open(src, encoding="utf-8", newline="") as f:
            rows = sum(1 for _ in csv.reader(f)) - 1  # minus header
        files_meta.append({"name": name, "rows": rows, "description": description})
        print(f"Copied {name} ({rows} rows)")

    coverage = build_coverage()

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "generated_note": (
                "Généré depuis data/ via pipeline/export_public_data.py - "
                "ne pas éditer directement."
            ),
            "files": files_meta,
            "coverage": coverage,
        }, f, ensure_ascii=False, indent=2)
    print(f"Wrote metadata to {JSON_OUT}")


if __name__ == "__main__":
    main()
