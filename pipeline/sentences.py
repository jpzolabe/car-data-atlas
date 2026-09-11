"""Deterministic sentence templates -- CLAUDE.md: "no model call in the pipeline
and none on the page." Every sentence here is traceable to a template id plus
the values that filled it; same inputs always produce the same sentence.

Known limitation, stated rather than hidden: elide_de() handles the common French
vowel-elision case ("de l'Ouaka") but not full gender/number agreement in general.
It has been checked by hand against all 20 real prefecture names currently in
entities.csv (see docs/decisions.md) -- it is not a general-purpose French grammar
engine, and would need re-checking against any new name it hasn't seen.
"""

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

# Words starting with "h aspire" don't elide ("de Haut-Mbomou", not "de l'Haut-
# Mbomou") unlike "h muet" words, which do. There is no simple spelling rule for
# this in French -- it's a closed, irregular list, so it's handled as one here
# rather than guessed. Extend by hand if a new h-aspire name is ever added.
H_ASPIRE_PREFIXES = ("haut", "haute")

THOUSANDS_SEP = chr(32)  # plain ASCII space (0x20) -- verified below, not U+00A0


def elide_de(name: str) -> str:
    """'Bangui' -> 'de Bangui', 'Ouaka' -> "de l'Ouaka", 'Haut-Mbomou' -> 'de Haut-Mbomou'."""
    lowered = name.lower()
    if lowered.startswith(H_ASPIRE_PREFIXES):
        return "de " + name
    if name[0].lower() in "aeiouy":
        return "de l'" + name
    return "de " + name


def period_to_fr(period: str) -> str:
    """'2026-04' -> 'avril 2026'."""
    year, month = period.split("-")
    return MONTHS_FR[int(month) - 1] + " " + year


def format_int_fr(value: float) -> str:
    return format(round(value), ",").replace(",", THOUSANDS_SEP)


def sentence_population(
    prefecture: str, year: str, value: float, reconciled: bool
) -> tuple[str, str]:
    place = elide_de(prefecture)
    value_fr = format_int_fr(value)
    if reconciled:
        text = (
            f"En {year}, la population de la préfecture {place} "
            f"était estimée à {value_fr} habitants."
        )
        template_id = "population_totale_lieu_estime"
    else:
        text = (
            f"En {year}, la population de la préfecture {place} "
            f"était de {value_fr} habitants, selon le recensement."
        )
        template_id = "population_totale_lieu_recensement"
    return text, template_id


def sentence_prix(period: str, value: float, reconciled: bool) -> tuple[str, str]:
    period_fr = period_to_fr(period)
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    caveat = (
        " (valeur réconciliée par la source, non telle "
        "qu'originellement publiée)"
        if reconciled else ""
    )
    text = (
        f"En {period_fr}, l'indice des prix à la consommation en "
        f"République centrafricaine s'établissait à "
        f"{value_fr}{caveat}."
    )
    template_id = "prix_ihpc_global_pays_estime" if reconciled else "prix_ihpc_global_pays"
    return text, template_id
