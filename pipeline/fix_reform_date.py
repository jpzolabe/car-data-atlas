"""Correct valid_from on préfecture/sous-préfecture entities from the bill's
adoption date (2020-12-10) to the law's actual promulgation date (2021-01-21,
Loi n°21.001) — a law takes legal effect on promulgation, not adoption. Found and
corroborated 2026-09-11, see docs/verification-debt.md's Resolved section.

Usage: uv run python -m pipeline.fix_reform_date
"""

import csv

OLD_DATE = "2020-12-10"
NEW_DATE = "2021-01-21"


def main():
    with open("data/entities.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    changed = 0
    for row in rows:
        if row["valid_from"] == OLD_DATE:
            row["valid_from"] = NEW_DATE
            row["notes"] = (
                row["notes"]
                .replace(
                    "la réforme administrative adoptée le 2020-12-10",
                    "la Loi n°21.001 du 21 janvier 2021 (adoptée par "
                    "l'Assemblée nationale le 2020-12-10, promulguée le "
                    "2021-01-21)",
                )
                .replace(
                    "limites redéfinies par la réforme du 2020-12-10",
                    "limites redéfinies par la Loi n°21.001 du 21 janvier 2021 "
                    "(adoptée le 2020-12-10, promulguée le 2021-01-21)",
                )
                .replace(
                    "à la date de la réforme (2020-12-10)",
                    "à la date de promulgation de la Loi n°21.001 (2021-01-21)",
                )
            )
            changed += 1

    with open("data/entities.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated valid_from on {changed} entities: {OLD_DATE} -> {NEW_DATE}")


if __name__ == "__main__":
    main()
