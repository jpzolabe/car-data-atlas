"""Copy the data/ CSVs into site/public/donnees/ so they're downloadable from
the site's own domain — needed because the GitHub repo is currently private,
so linking to raw.githubusercontent.com would 404 for anyone else. Also writes
site/src/data/donnees.json (row counts + descriptions) for the /donnees page.
Re-run whenever data/ changes.

Usage: uv run python -m pipeline.export_public_data
"""

import csv
import json
import shutil
from pathlib import Path

# (filename, one-line description — same as data/README.md, kept in sync by hand)
FILES = [
    ("entities.csv", "Une ligne par unité administrative, par version. "
                      "Jamais modifié en place — un redécoupage crée une nouvelle entité."),
    ("aliases.csv", "Chaque orthographe, variante d'accent et code source, "
                     "rattachés à un identifiant canonique."),
    ("sources.csv", "Une ligne par source : producteur, licence, cadence, "
                     "vintage géographique, mise en garde éventuelle."),
    ("indicators.csv", "Un indicateur par ligne : définition, unité, thème, "
                        "et le niveau géographique le plus fin qu'il atteint réellement."),
    ("observations.csv", "Les valeurs elles-mêmes, format long : "
                          "entité, indicateur, période, valeur, source."),
    ("unresolved.csv", "Chaque cas que le rapprochement des sources n'a pas su résoudre — "
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

    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump({
            "generated_note": (
                "Généré depuis data/ via pipeline/export_public_data.py — "
                "ne pas éditer directement."
            ),
            "files": files_meta,
        }, f, ensure_ascii=False, indent=2)
    print(f"Wrote metadata to {JSON_OUT}")


if __name__ == "__main__":
    main()
