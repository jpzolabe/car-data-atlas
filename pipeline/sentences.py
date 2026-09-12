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


def sentence_electricity(
    period: str, value: float, previous_value: float | None
) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    if previous_value is not None and previous_value > 0:
        change = value - previous_value
        if abs(change) >= 0.1:
            direction = "en hausse" if change > 0 else "en baisse"
            text = (
                f"En {period}, {value_fr}% de la population avait accès à "
                f"l'électricité en République centrafricaine, {direction} "
                f"par rapport à l'année précédente."
            )
            return text, "acces_electricite_pays_tendance"
    text = (
        f"En {period}, {value_fr}% de la population avait accès à "
        f"l'électricité en République centrafricaine."
    )
    return text, "acces_electricite_pays"


# level_label_fr must fit "achevé {level_label_fr}" grammatically -- checked
# by hand against these 3 real cases, not a general noun-phrase inflector.
COMPLETION_LEVEL_LABELS = {
    "taux_achevement_primaire": "l'enseignement primaire",
    "taux_achevement_secondaire_1er_cycle": "le premier cycle du secondaire",
    "taux_achevement_secondaire_2nd_cycle": "le second cycle du secondaire",
}


def sentence_completion(
    indicator_id: str, period: str, value: float, quality_flag: str
) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    level = COMPLETION_LEVEL_LABELS[indicator_id]
    if quality_flag == "enquete":
        text = (
            f"En {period}, {value_fr}% d'une cohorte d'âge avait achevé "
            f"{level} en République centrafricaine, selon la dernière "
            f"enquête nationale disponible."
        )
        template_id = f"{indicator_id}_pays_enquete"
    else:
        text = (
            f"En {period}, {value_fr}% d'une cohorte d'âge aurait achevé "
            f"{level} en République centrafricaine, selon une estimation "
            f"modélisée."
        )
        template_id = f"{indicator_id}_pays_estime"
    return text, template_id


# label_fr must fit "{label_fr} s'établissait à" grammatically -- a noun
# phrase, checked by hand against these 11 real indicators, not a general
# French grammar engine.
EDUCATION_RATE_LABELS = {
    "taux_scolarisation_brut_primaire": "le taux brut de scolarisation dans le primaire",
    "taux_scolarisation_net_primaire": "le taux net de scolarisation dans le primaire",
    "taux_scolarisation_brut_secondaire_1er_cycle": (
        "le taux brut de scolarisation dans le premier cycle du secondaire"
    ),
    "taux_scolarisation_brut_secondaire_2nd_cycle": (
        "le taux brut de scolarisation dans le second cycle du secondaire"
    ),
    "taux_scolarisation_brut_superieur": (
        "le taux brut de scolarisation dans l'enseignement supérieur"
    ),
    "taux_redoublement_primaire": "le taux de redoublement dans le primaire",
    "taux_survie_primaire": "le taux de survie jusqu'à la dernière année du primaire",
    "taux_non_scolarisation_primaire": (
        "le taux de non-scolarisation des enfants d'âge du primaire"
    ),
    "taux_non_scolarisation_secondaire_1er_cycle": (
        "le taux de non-scolarisation des adolescents d'âge "
        "du premier cycle du secondaire"
    ),
    "taux_alphabetisation_jeunes": "le taux d'alphabétisation des jeunes de 15 à 24 ans",
    "taux_alphabetisation_adultes": "le taux d'alphabétisation des adultes de 15 ans et plus",
}


def sentence_education_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label = EDUCATION_RATE_LABELS[indicator_id]
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {value_fr}%."
    )
    return text, f"{indicator_id}_pays"
