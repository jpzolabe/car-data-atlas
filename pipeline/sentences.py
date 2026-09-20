"""Deterministic sentence templates -- AGENTS.md: "no model call in the pipeline
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


# label_fr must fit "l'indice des prix à la consommation {label_fr}"
# grammatically -- checked by hand against these 3 real categories.
PRIX_CATEGORY_LABELS = {
    "prix_ihpc_alimentation": "des produits alimentaires et boissons non alcoolisées",
    "prix_ihpc_sante": "de la santé",
    "prix_ihpc_transports": "des transports",
}


def sentence_prix_categorie(
    indicator_id: str, period: str, value: float, reconciled: bool
) -> tuple[str, str]:
    period_fr = period_to_fr(period)
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label = PRIX_CATEGORY_LABELS[indicator_id]
    caveat = (
        " (valeur réconciliée par la source, non telle "
        "qu'originellement publiée)"
        if reconciled else ""
    )
    text = (
        f"En {period_fr}, l'indice des prix à la consommation {label} "
        f"en République centrafricaine s'établissait à {value_fr}{caveat}."
    )
    template_id = f"{indicator_id}_pays_estime" if reconciled else f"{indicator_id}_pays"
    return text, template_id


# label_fr must fit "le kilogramme de {label_fr} se vendait à" (or "le litre
# de ... " for the one non-kg unit) grammatically -- checked by hand against
# these 5 real commodities. unit_word distinguishes "kilogramme" from "litre".
PRIX_DENREE_LABELS = {
    "prix_manioc_kg": ("manioc (cossette séchée)", "kilogramme"),
    "prix_riz_kg": ("riz", "kilogramme"),
    "prix_mais_kg": ("maïs", "kilogramme"),
    "prix_boeuf_kg": ("viande de bœuf", "kilogramme"),
    "prix_huile_palme_l": ("huile de palme", "litre"),
}


def sentence_prix_denree(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    period_fr = period_to_fr(period)
    value_fr = format_int_fr(value)
    label, unit_word = PRIX_DENREE_LABELS[indicator_id]
    # "huile" is h-muet (elides); reusing elide_de's h-aspire exception list
    # would be wrong here since none of these 5 labels start with one, but
    # the check is kept explicit rather than assumed for the same reason
    # elide_de documents its own limits above.
    elides = label[0].lower() in "aeiouy" or label.lower().startswith("huile")
    de_label = "d'" + label if elides else "de " + label
    text = (
        f"En {period_fr}, le {unit_word} {de_label} se vendait à "
        f"{value_fr} francs CFA au marché de Bangui."
    )
    return text, f"{indicator_id}_marche"


def sentence_inflation(period: str, value: float) -> tuple[str, str]:
    period_fr = period_to_fr(period)
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    text = (
        f"En {period_fr}, le taux d'inflation publié par l'ICASEES pour la "
        f"République centrafricaine s'établissait à {value_fr}%."
    )
    return text, "taux_inflation_pays"


# (label_fr, unit_suffix) -- label_fr must fit "{label_fr} en République
# centrafricaine s'établissait à" grammatically, checked by hand against
# these 4 real indicators. unit_suffix distinguishes "%" (no space before
# the sign) from "pour 100 habitants" (a count, not a percentage).
INFRASTRUCTURE_LABELS = {
    "taux_utilisation_internet": ("le taux d'utilisation d'Internet", "%"),
    "abonnements_mobiles": ("le nombre d'abonnements mobiles", "pour 100 habitants"),
    "acces_eau_potable_base": (
        "le taux d'accès à un service de base d'eau potable", "%",
    ),
    "acces_assainissement_base": (
        "le taux d'accès à un service de base d'assainissement", "%",
    ),
}


def sentence_infrastructure_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label, unit = INFRASTRUCTURE_LABELS[indicator_id]
    suffix = f"{value_fr}%" if unit == "%" else f"{value_fr} {unit}"
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {suffix}."
    )
    return text, f"{indicator_id}_pays"


# (label_fr, unit_suffix) -- label_fr must fit "{label_fr} en République
# centrafricaine s'établissait à" grammatically, checked by hand against
# these 10 real indicators. unit_suffix carries the varied units these
# health indicators use (years, per-1000, per-100000, % of GDP) -- "%" gets
# no space before the sign, everything else does.
SANTE_LABELS = {
    "esperance_vie": ("l'espérance de vie à la naissance", "ans"),
    "taux_mortalite_moins_5ans": (
        "le taux de mortalité des moins de 5 ans", "pour 1 000 naissances vivantes",
    ),
    "taux_mortalite_infantile": (
        "le taux de mortalité infantile", "pour 1 000 naissances vivantes",
    ),
    "taux_mortalite_maternelle": (
        "le taux de mortalité maternelle", "pour 100 000 naissances vivantes",
    ),
    "taux_vaccination_rougeole": ("le taux de vaccination contre la rougeole", "%"),
    "taux_vaccination_dtc": ("le taux de vaccination DTC", "%"),
    "densite_medecins": ("la densité de médecins", "pour 1 000 habitants"),
    "densite_lits_hopital": ("la densité de lits d'hôpital", "pour 1 000 habitants"),
    "depenses_sante_pib": ("le poids des dépenses de santé dans le PIB", "%"),
    "incidence_vih": (
        "l'incidence du VIH",
        "pour 1 000 personnes non infectées de 15 à 49 ans",
    ),
    "soins_prenatals_4visites": ("le taux de suivi prénatal (4 visites ou plus)", "%"),
    "accouchement_assiste": ("le taux d'accouchement assisté par du personnel qualifié", "%"),
    "allaitement_exclusif": ("le taux d'allaitement exclusif chez les 0-5 mois", "%"),
    "retard_croissance_enfants": ("le taux de retard de croissance chez les moins de 5 ans", "%"),
    "emaciation_enfants": ("le taux d'émaciation chez les moins de 5 ans", "%"),
}


def sentence_sante_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label, unit = SANTE_LABELS[indicator_id]
    suffix = f"{value_fr}%" if unit == "%" else f"{value_fr} {unit}"
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {suffix}."
    )
    return text, f"{indicator_id}_pays"


# label_fr must fit "{label_fr} en République centrafricaine s'établissait
# à" grammatically -- checked by hand against these 3 real indicators.
POPULATION_RATE_LABELS = {
    "taux_croissance_population": "le taux de croissance de la population",
    "taux_urbanisation": "la part de la population urbaine",
    "taux_dependance_demographique": "le taux de dépendance démographique",
    "enregistrement_naissances": "le taux d'enregistrement des naissances chez les moins de 5 ans",
    "mariage_precoce_filles": "la part des femmes de 20 à 24 ans mariées avant 18 ans",
}


def sentence_population_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label = POPULATION_RATE_LABELS[indicator_id]
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {value_fr}%."
    )
    return text, f"{indicator_id}_pays"


# label_fr must fit "{label_fr} en République centrafricaine s'établissait
# à" grammatically -- checked by hand against these 8 real indicators. All
# use "%", unlike santé's varied units, so no unit-branching needed here.
ECONOMIE_RATE_LABELS = {
    "taux_croissance_pib": "le taux de croissance du PIB",
    "taux_pauvrete": "le taux de pauvreté (seuil de 3,00 $ par jour, PPA 2021)",
    "taux_chomage": "le taux de chômage",
    "exportations_pib": "la part des exportations dans le PIB",
    "importations_pib": "la part des importations dans le PIB",
    "dette_exterieure_rnb": "le poids de la dette extérieure dans le revenu national brut",
    "investissements_directs_etrangers": (
        "la part des investissements directs étrangers dans le PIB"
    ),
    "recettes_publiques_pib": "la part des recettes publiques dans le PIB",
}


def sentence_economie_croissance_admin(period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    text = (
        f"En {period}, le produit intérieur brut de la République "
        f"centrafricaine a progressé de {value_fr}% en volume, selon les "
        f"comptes nationaux rebasés de l'ICASEES."
    )
    return text, "taux_croissance_pib_administratif"


def sentence_economie_croissance_modele(period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    text = (
        f"En {period}, le produit intérieur brut de la République "
        f"centrafricaine aurait progressé de {value_fr}% en volume, selon "
        f"l'estimation modélisée de la Banque mondiale."
    )
    return text, "taux_croissance_pib_modele"


def sentence_economie_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label = ECONOMIE_RATE_LABELS[indicator_id]
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {value_fr}%."
    )
    return text, f"{indicator_id}_pays"


# label_fr must fit "{label_fr} de la République centrafricaine
# s'établissait à" grammatically -- singular subjects throughout (checked
# by hand), same fix as depenses_sante_pib/dette_exterieure_rnb's labels:
# a plural subject here ("les exportations...") would need a plural verb.
ECONOMIE_MONTANT_LABELS = {
    "pib_total": "le produit intérieur brut",
    "exportations_montant": "le montant des exportations de biens et services",
    "importations_montant": "le montant des importations de biens et services",
    "dette_exterieure_montant": "l'encours de la dette extérieure",
}


QUARTER_FR = {
    "Q1": "premier trimestre", "Q2": "deuxième trimestre",
    "Q3": "troisième trimestre", "Q4": "quatrième trimestre",
}


def sentence_economie_activite(period: str, value: float) -> tuple[str, str]:
    """period looks like '2023-Q1' -- IMF's e-GDDS NSDP indicator is
    quarterly, unlike every other économie indicator."""
    year, quarter = period.split("-")
    quarter_fr = QUARTER_FR[quarter]
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    text = (
        f"Au {quarter_fr} {year}, l'indice d'activité économique totale de "
        f"la République centrafricaine s'établissait à {value_fr}."
    )
    return text, "indice_activite_economique_pays"


def sentence_economie_montant(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    if indicator_id == "pib_par_habitant":
        value_fr = format(round(value), ",").replace(",", THOUSANDS_SEP)
        text = (
            f"En {period}, le produit intérieur brut par habitant en "
            f"République centrafricaine s'établissait à {value_fr} "
            f"dollars américains courants."
        )
        return text, f"{indicator_id}_pays"

    if indicator_id == "pib_par_habitant_fcfa":
        value_fr = format(round(value), ",").replace(",", THOUSANDS_SEP)
        text = (
            f"En {period}, le produit intérieur brut par habitant en "
            f"République centrafricaine s'établissait à {value_fr} francs "
            f"CFA, selon les comptes nationaux rebasés de l'ICASEES."
        )
        return text, f"{indicator_id}_pays"

    if indicator_id == "pib_total_fcfa":
        amount_fr = format(value / 1e9, ",.1f").replace(",", THOUSANDS_SEP).replace(".", ",")
        text = (
            f"En {period}, le produit intérieur brut de la République "
            f"centrafricaine s'établissait à {amount_fr} milliards de "
            f"francs CFA, selon les comptes nationaux rebasés de l'ICASEES."
        )
        return text, f"{indicator_id}_pays"

    label = ECONOMIE_MONTANT_LABELS[indicator_id]
    if value >= 1e9:
        amount_fr = format(round(value / 1e9, 2), ".2f").replace(".", ",")
        unit_phrase = "milliards de dollars américains courants"
    else:
        amount_fr = format(round(value / 1e6, 1), ".1f").replace(".", ",")
        unit_phrase = "millions de dollars américains courants"
    text = (
        f"En {period}, {label} de la République centrafricaine "
        f"s'établissait à {amount_fr} {unit_phrase}."
    )
    return text, f"{indicator_id}_pays"


BUDGET_LABELS = {
    "budget_ressources_totales": "les ressources totales votées au budget de l'État",
    "budget_depenses_totales": "les dépenses totales votées au budget de l'État",
}


def sentence_economie_budget(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    amount_fr = format(round(abs(value) / 1e9, 2), ".2f").replace(".", ",")

    if indicator_id == "budget_solde_global":
        etat = "un déficit" if value < 0 else "un excédent"
        text = (
            f"Pour {period}, la loi de finances centrafricaine prévoyait "
            f"{etat} budgétaire de {amount_fr} milliards de francs CFA."
        )
        return text, f"{indicator_id}_pays"

    label = BUDGET_LABELS[indicator_id]
    text = (
        f"Pour {period}, {label} de la République centrafricaine "
        f"étaient budgétisées à {amount_fr} milliards de francs CFA."
    )
    return text, f"{indicator_id}_pays"


# (label_fr, unit, decimals) -- label_fr must fit "{label_fr} en République
# centrafricaine s'établissait à" grammatically, checked by hand against
# these 9 real indicators. decimals defaults to 1 everywhere except
# consommation_engrais, whose real value (~0.04) rounds to a misleading
# "0,0" at 1 decimal -- checked by hand, not a guess.
AGRICULTURE_LABELS = {
    "valeur_ajoutee_agriculture_pib": (
        "le poids de l'agriculture, de la sylviculture et de la pêche dans le PIB", "%", 1,
    ),
    "terres_agricoles": ("la part du territoire consacrée à l'agriculture", "%", 1),
    "terres_arables": ("la part du territoire en terres arables", "%", 1),
    "couverture_forestiere": ("la couverture forestière du territoire", "%", 1),
    "indice_production_alimentaire": ("l'indice de production alimentaire", "indice", 1),
    "rendement_cereales": ("le rendement des céréales", "kg/ha", 1),
    "consommation_engrais": ("la consommation d'engrais", "kg/ha", 3),
    "taux_sous_alimentation": ("la part de la population en sous-alimentation", "%", 1),
    "emploi_agricole": ("la part de l'emploi total dans l'agriculture", "%", 1),
}


def sentence_agriculture_rate(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    label, unit, decimals = AGRICULTURE_LABELS[indicator_id]
    value_fr = format(round(value, decimals), f".{decimals}f").replace(".", ",")
    if unit == "%":
        suffix = f"{value_fr}%"
    elif unit == "indice":
        suffix = value_fr
    else:
        suffix = f"{value_fr} {unit}"
    text = (
        f"En {period}, {label} en République centrafricaine "
        f"s'établissait à {suffix}."
    )
    return text, f"{indicator_id}_pays"


# (label_fr, unit) -- label_fr must fit "{label_fr} de la République
# centrafricaine s'établissait à" grammatically -- singular subjects,
# same reasoning as ECONOMIE_MONTANT_LABELS.
AGRICULTURE_MONTANT_LABELS = {
    "superficie_agricole": ("la superficie agricole", "km²"),
    "production_cereales": ("la production de céréales", "tonnes"),
}


def sentence_agriculture_montant(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    label, unit = AGRICULTURE_MONTANT_LABELS[indicator_id]
    value_fr = format(round(value), ",").replace(",", THOUSANDS_SEP)
    text = (
        f"En {period}, {label} de la République centrafricaine "
        f"s'établissait à {value_fr} {unit}."
    )
    return text, f"{indicator_id}_pays"


# (label_fr, is_estimate) -- label_fr is the plural noun that follows
# "comptait {value} {label_fr}". is_estimate adds a calculated-estimate
# caveat and drops the false precision of stating it as a plain fact.
SANTE_EFFECTIF_LABELS = {
    "nombre_medecins": ("médecins", False),
    "nombre_personnel_infirmier": ("membres du personnel infirmier et de sages-femmes", False),
    "nombre_lits_hopital": ("lits d'hôpital", True),
}


def sentence_sante_effectif(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format(round(value), ",").replace(",", THOUSANDS_SEP)
    label, is_estimate = SANTE_EFFECTIF_LABELS[indicator_id]
    if is_estimate:
        text = (
            f"En {period}, la République centrafricaine comptait environ "
            f"{value_fr} {label}, selon une estimation calculée à partir "
            f"de la densité et de la population de cette année-là."
        )
    else:
        text = f"En {period}, la République centrafricaine comptait {value_fr} {label}."
    return text, f"{indicator_id}_pays"


def sentence_sante_etablissements(period: str, value: float, source_label: str) -> tuple[str, str]:
    value_fr = format(round(value), ",").replace(",", THOUSANDS_SEP)
    text = (
        f"En {period}, {source_label} recensait {value_fr} établissements "
        f"de santé en République centrafricaine."
    )
    return text, "nombre_etablissements_sante_pays"


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
    "taux_alphabetisation_jeunes": "le taux d'alphabétisation des jeunes de 15 à 24 ans",
    "taux_alphabetisation_adultes": "le taux d'alphabétisation des adultes de 15 ans et plus",
    "taux_reussite_baccalaureat": "le taux de réussite au baccalauréat général",
}


# label must fit "la République centrafricaine comptait {value} {label}"
# grammatically -- checked by hand against these 3 real indicators.
EDUCATION_EFFECTIF_LABELS = {
    "nombre_etablissements_scolaires": "établissements scolaires",
    "effectif_eleves": "élèves",
    "nombre_enseignants": "enseignants",
}


def sentence_education_effectif(indicator_id: str, period: str, value: float) -> tuple[str, str]:
    value_fr = format_int_fr(value)
    label = EDUCATION_EFFECTIF_LABELS[indicator_id]
    text = (
        f"Pour l'année scolaire {period}-{int(period) + 1}, la République "
        f"centrafricaine comptait {value_fr} {label}."
    )
    return text, f"{indicator_id}_pays"


def sentence_education_rate(
    indicator_id: str, period: str, value: float, quality_flag: str | None = None
) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    label = EDUCATION_RATE_LABELS[indicator_id]
    if quality_flag == "provisoire":
        text = (
            f"En {period}, {label} en République centrafricaine "
            f"s'établissait à {value_fr}%, un résultat provisoire."
        )
    else:
        text = (
            f"En {period}, {label} en République centrafricaine "
            f"s'établissait à {value_fr}%."
        )
    return text, f"{indicator_id}_pays"


# group_label_fr must fit "des {group_label_fr} n'était pas scolarisée"
# grammatically -- checked by hand against these 3 real cases.
OUT_OF_SCHOOL_GROUP_LABELS = {
    "taux_non_scolarisation_primaire": "enfants d'âge du primaire",
    "taux_non_scolarisation_secondaire_1er_cycle": (
        "adolescents d'âge du premier cycle du secondaire"
    ),
    "taux_non_scolarisation_secondaire_2nd_cycle": "jeunes d'âge du second cycle du secondaire",
}


def sentence_out_of_school(
    indicator_id: str, period: str, value: float, quality_flag: str
) -> tuple[str, str]:
    value_fr = format(round(value, 1), ".1f").replace(".", ",")
    group = OUT_OF_SCHOOL_GROUP_LABELS[indicator_id]
    if quality_flag == "administratif":
        text = (
            f"En {period}, {value_fr}% des {group} n'étaient pas scolarisés "
            f"en République centrafricaine, selon la dernière donnée "
            f"administrative disponible."
        )
        template_id = f"{indicator_id}_pays_administratif"
    else:
        text = (
            f"En {period}, {value_fr}% des {group} n'auraient pas été "
            f"scolarisés en République centrafricaine, selon une "
            f"estimation modélisée."
        )
        template_id = f"{indicator_id}_pays_estime"
    return text, template_id
