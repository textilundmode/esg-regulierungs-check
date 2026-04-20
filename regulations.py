"""Kuratierte Liste der 22 ESG-/CSR-Regulierungen mit Anwendbarkeitskriterien.

Die `criteria`-Felder sind bewusst in natürlicher Sprache gehalten, damit
Claude sie gemeinsam mit dem Unternehmensprofil auswerten kann.
"""

REGULATIONS = [
    {
        "nr": 1,
        "key": "CSDDD",
        "name": "CSDDD",
        "full_name": "Richtlinie (EU) 2024/1760 - Sorgfaltspflichten von Unternehmen im Hinblick auf Nachhaltigkeit",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024L1760-20260318",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024L1760-20260318",
        "scope": "EU",
        "criteria": (
            "Gilt für EU-Unternehmen mit >1000 Beschäftigten UND Nettoumsatz >450 Mio EUR weltweit. "
            "Für Nicht-EU-Unternehmen: Nettoumsatz >450 Mio EUR in der EU. "
            "Stufenweise Einführung: ab 2027 (>5000 MA & >1500 Mio EUR), ab 2028 (>3000 MA & >900 Mio EUR), "
            "ab 2029 (>1000 MA & >450 Mio EUR). Branche: alle."
        ),
        "key_article": "Art. 2 (Anwendungsbereich)",
    },
    {
        "nr": 2,
        "key": "LkSG",
        "name": "LkSG",
        "full_name": "Lieferkettensorgfaltspflichtengesetz",
        "url": "https://www.bafa.de/DE/Lieferketten/Ueberblick/ueberblick_node.html",
        "text_url": "https://www.bafa.de/DE/Lieferketten/Ueberblick/ueberblick_node.html",
        "scope": "DE",
        "criteria": (
            "Gilt für Unternehmen mit Hauptverwaltung, Hauptniederlassung, Verwaltungssitz, satzungsmäßigem "
            "Sitz oder Zweigniederlassung in Deutschland ab 1000 Arbeitnehmern im Inland "
            "(inkl. entsandte Arbeitnehmer, Leiharbeitnehmer wenn >6 Monate). Branche: alle."
        ),
        "key_article": "§ 1 LkSG (Anwendungsbereich)",
    },
    {
        "nr": 3,
        "key": "EUDR",
        "name": "EUDR",
        "full_name": "Verordnung (EU) 2023/1115 über entwaldungsfreie Lieferketten",
        "url": "https://eur-lex.europa.eu/eli/reg/2023/1115/oj",
        "text_url": "https://eur-lex.europa.eu/eli/reg/2023/1115/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für alle Marktteilnehmer und Händler, die in der EU bestimmte Rohstoffe "
            "(Rinder, Kakao, Kaffee, Ölpalme, Kautschuk, Soja, Holz) oder daraus hergestellte Erzeugnisse "
            "in Verkehr bringen, bereitstellen oder ausführen. KMU-Erleichterungen möglich, aber keine Befreiung. "
            "Relevanz hängt an Branche/Produktportfolio, nicht an Mitarbeiterzahl."
        ),
        "key_article": "Art. 1, 3 (Gegenstand & Verbot)",
    },
    {
        "nr": 4,
        "key": "FLR",
        "name": "FLR (Zwangsarbeitsverordnung)",
        "full_name": "Verordnung (EU) 2024/3015 - Verbot von in Zwangsarbeit hergestellten Produkten",
        "url": "https://eur-lex.europa.eu/eli/reg/2024/3015/oj",
        "text_url": "https://eur-lex.europa.eu/eli/reg/2024/3015/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für alle Wirtschaftsakteure, die Produkte in der EU in Verkehr bringen, auf dem Markt "
            "bereitstellen oder ausführen. Keine MA-Schwelle. Risikobasierter Ansatz; Fokus auf Unternehmen "
            "mit globalen Lieferketten in Hochrisikoregionen. Branche: alle."
        ),
        "key_article": "Art. 1, 3",
    },
    {
        "nr": 5,
        "key": "CSRD",
        "name": "CSRD",
        "full_name": "Richtlinie (EU) 2022/2464 - Nachhaltigkeitsberichterstattung",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02022L2464-20260318",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02022L2464-20260318",
        "scope": "EU",
        "criteria": (
            "Nach Omnibus I (2026/470) geänderter Anwendungsbereich: Große Unternehmen mit >1000 Beschäftigten "
            "UND Bilanzsumme >25 Mio EUR ODER Nettoumsatzerlöse >50 Mio EUR. "
            "Börsennotierte KMU ausgenommen (nur freiwillig). Nicht-EU-Unternehmen mit >450 Mio EUR EU-Umsatz "
            "ab 2028. Branche: alle."
        ),
        "key_article": "Art. 19a, 29a (aktualisiert)",
    },
    {
        "nr": 6,
        "key": "CSRD_DE",
        "name": "CSRD-Umsetzungsgesetz (DE)",
        "full_name": "Gesetz zur Umsetzung der Richtlinie (EU) 2022/2464",
        "url": "https://dserver.bundestag.de/btd/21/018/2101857.pdf",
        "scope": "DE",
        "criteria": (
            "Deutsche Umsetzung der CSRD; gilt für in Deutschland ansässige große Unternehmen und "
            "Konzerne gemäß den CSRD-Schwellen (siehe CSRD). Berichtspflicht im Lagebericht (§ 289b HGB-E)."
        ),
        "key_article": "§§ 289b-289h HGB-E",
    },
    {
        "nr": 7,
        "key": "ESRS",
        "name": "ESRS",
        "full_name": "Delegierte Verordnung (EU) 2023/2772 - Nachhaltigkeitsberichterstattung (Standards)",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02022L2464-20260318",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02022L2464-20260318",
        "scope": "EU",
        "criteria": (
            "Technische Standards für die Nachhaltigkeitsberichterstattung. Gelten für alle Unternehmen, "
            "die unter die CSRD fallen. Anwendung abhängig von CSRD-Pflicht."
        ),
        "key_article": "Annex I (ESRS 1, ESRS 2, E1-E5, S1-S4, G1)",
    },
    {
        "nr": 8,
        "key": "NFRD",
        "name": "NFRD",
        "full_name": "Richtlinie 2014/95/EU - nichtfinanzielle Berichterstattung",
        "url": "https://eur-lex.europa.eu/eli/dir/2014/95/oj",
        "text_url": "https://eur-lex.europa.eu/eli/dir/2014/95/oj",
        "scope": "EU",
        "criteria": (
            "Vorläufer der CSRD. Ersetzt für Geschäftsjahre ab 2024 schrittweise durch CSRD. "
            "Historisch: große Unternehmen von öffentlichem Interesse mit >500 MA. "
            "Für aktuelle Prüfung i.d.R. nicht mehr relevant."
        ),
        "key_article": "Art. 19a",
    },
    {
        "nr": 9,
        "key": "CSR-RUG",
        "name": "CSR-RUG",
        "full_name": "Gesetz zur Stärkung der nichtfinanziellen Berichterstattung",
        "url": "https://www.bgbl.de/",
        "scope": "DE",
        "criteria": (
            "Deutsche Umsetzung der NFRD (§§ 289b ff. HGB alte Fassung). "
            "Große kapitalmarktorientierte Unternehmen >500 MA. "
            "Wird durch CSRD-Umsetzung abgelöst."
        ),
        "key_article": "§§ 289b-289e HGB a.F.",
    },
    {
        "nr": 10,
        "key": "TaxonomieVO",
        "name": "Taxonomie-Verordnung",
        "full_name": "Verordnung (EU) 2020/852 - Rahmen für nachhaltige Investitionen",
        "url": "https://eur-lex.europa.eu/eli/reg/2020/852/oj",
        "text_url": "https://eur-lex.europa.eu/eli/reg/2020/852/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für Unternehmen, die unter die NFRD/CSRD fallen, sowie für Finanzmarktteilnehmer. "
            "Offenlegung der Taxonomie-Konformität (Umsatz-, CapEx-, OpEx-Anteile). "
            "Relevanz gekoppelt an CSRD-Pflicht."
        ),
        "key_article": "Art. 8",
    },
    {
        "nr": 11,
        "key": "SFDR",
        "name": "SFDR",
        "full_name": "Verordnung (EU) 2019/2088 - nachhaltigkeitsbezogene Offenlegungspflichten",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02019R2088-20240109",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02019R2088-20240109",
        "scope": "EU",
        "criteria": (
            "Gilt ausschließlich für Finanzmarktteilnehmer (Vermögensverwalter, Versicherer, AIFM, UCITS) "
            "und Finanzberater. Nicht für Realwirtschaft. "
            "Anwendbar wenn Branche = Finanzdienstleistungen/Versicherungen."
        ),
        "key_article": "Art. 2, 3",
    },
    {
        "nr": 12,
        "key": "ESGRatingVO",
        "name": "ESG Rating VO",
        "full_name": "Verordnung (EU) 2024/3005 - ESG-Ratings",
        "url": "https://eur-lex.europa.eu/eli/reg/2024/3005/oj",
        "text_url": "https://eur-lex.europa.eu/eli/reg/2024/3005/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für Anbieter von ESG-Ratings mit Tätigkeit in der EU. "
            "Nicht für bewertete Unternehmen selbst. Relevant nur bei Branche = ESG-Rating-Anbieter."
        ),
        "key_article": "Art. 2",
    },
    {
        "nr": 13,
        "key": "WhistleblowerRL",
        "name": "Whistleblower-Richtlinie",
        "full_name": "Richtlinie (EU) 2019/1937 - Schutz von Hinweisgebern",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02019L1937-20241230",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02019L1937-20241230",
        "scope": "EU",
        "criteria": (
            "Richtet sich an Mitgliedstaaten. In DE umgesetzt durch HinSchG. "
            "Direkte Anwendung für Unternehmen über HinSchG."
        ),
        "key_article": "Art. 8",
    },
    {
        "nr": 14,
        "key": "HinSchG",
        "name": "HinSchG",
        "full_name": "Hinweisgeberschutzgesetz",
        "url": "https://www.gesetze-im-internet.de/hinschg/",
        "scope": "DE",
        "criteria": (
            "Gilt für Beschäftigungsgeber in Deutschland ab 50 Beschäftigten. "
            "Pflicht zur Einrichtung interner Meldestellen. Branche: alle."
        ),
        "key_article": "§ 12 HinSchG",
    },
    {
        "nr": 15,
        "key": "RightToRepair",
        "name": "Right to Repair",
        "full_name": "Richtlinie (EU) 2024/1799 - Reparatur von Waren",
        "url": "https://eur-lex.europa.eu/eli/dir/2024/1799/oj",
        "text_url": "https://eur-lex.europa.eu/eli/dir/2024/1799/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für Hersteller bestimmter Warenkategorien (z.B. Haushaltsgeräte, Smartphones, Tablets) "
            "die in der EU in Verkehr gebracht werden. Branche relevant: Konsumgüterhersteller, Elektronik. "
            "Keine MA-Schwelle."
        ),
        "key_article": "Art. 2, 5",
    },
    {
        "nr": 16,
        "key": "Oekodesign",
        "name": "Ökodesign-VO",
        "full_name": "Verordnung (EU) 2024/1781 - nachhaltige Produkte (ESPR)",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024R1781-20240628",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024R1781-20240628",
        "scope": "EU",
        "criteria": (
            "Gilt für Hersteller, Importeure, Händler von physischen Produkten (mit Ausnahmen wie Lebensmittel) "
            "die in der EU in Verkehr gebracht werden. Branche: nahezu alle warenproduzierenden. "
            "Keine MA-Schwelle."
        ),
        "key_article": "Art. 1, 2",
    },
    {
        "nr": 17,
        "key": "PPWR",
        "name": "PPWR",
        "full_name": "Verordnung (EU) 2025/40 - Verpackungen und Verpackungsabfälle",
        "url": "https://eur-lex.europa.eu/eli/reg/2025/40/oj",
        "text_url": "https://eur-lex.europa.eu/eli/reg/2025/40/oj",
        "scope": "EU",
        "criteria": (
            "Gilt für Hersteller, Importeure, Händler, Fulfilment-Dienstleister und Endvertreiber von "
            "Verpackungen in der EU. Branche relevant: alle Unternehmen mit physischen Produkten/Verpackungen. "
            "Keine MA-Schwelle."
        ),
        "key_article": "Art. 1, 3",
    },
    {
        "nr": 18,
        "key": "KonfliktminVO",
        "name": "Konfliktmineralien-VO",
        "full_name": "Verordnung (EU) 2017/821 - Konfliktmineralien",
        "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02017R0821-20201119",
        "text_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02017R0821-20201119",
        "scope": "EU",
        "criteria": (
            "Gilt für Unionseinführer von Zinn, Tantal, Wolfram, deren Erzen und Gold. "
            "Volumenschwellen pro Mineral in Anhang I. Branche relevant: Metallimporteure, Elektronik, "
            "Schmuck, Automobil mit Direktimport."
        ),
        "key_article": "Art. 1, Anhang I",
    },
    {
        "nr": 19,
        "key": "MinRohSorgG",
        "name": "MinRohSorgG",
        "full_name": "Mineralische-Rohstoffe-Sorgfaltspflichtengesetz",
        "url": "https://www.gesetze-im-internet.de/minrohsorgg/",
        "scope": "DE",
        "criteria": (
            "Deutsche Durchführung der Konfliktmineralien-VO. Gilt für Unionseinführer mit Sitz in DE "
            "oberhalb der Volumenschwellen aus Anhang I der VO (EU) 2017/821."
        ),
        "key_article": "§ 3 MinRohSorgG",
    },
    {
        "nr": 20,
        "key": "UmweltstrafRL",
        "name": "EU Umweltstrafrechts-RL",
        "full_name": "Richtlinie (EU) 2024/1203 - strafrechtlicher Schutz der Umwelt",
        "url": "https://eur-lex.europa.eu/eli/dir/2024/1203/oj",
        "text_url": "https://eur-lex.europa.eu/eli/dir/2024/1203/oj",
        "scope": "EU",
        "criteria": (
            "Richtet sich primär an Mitgliedstaaten (Umsetzung ins nationale Strafrecht). "
            "Unternehmen sind indirekt betroffen: juristische Personen haftbar für definierte Umweltstraftaten. "
            "Alle Branchen, insbes. Industrie/Chemie/Abfall."
        ),
        "key_article": "Art. 3, 7",
    },
    {
        "nr": 21,
        "key": "EmpCo",
        "name": "EmpCo",
        "full_name": "Richtlinie (EU) 2024/825 - Stärkung der Verbraucher für den ökologischen Wandel (UWG-Umsetzung DE)",
        "url": "https://www.gesetze-im-internet.de/uwg_2004/BJNR141400004.html",
        "text_url": "https://www.gesetze-im-internet.de/uwg_2004/BJNR141400004.html",
        "scope": "EU",
        "criteria": (
            "Gilt für alle Unternehmen, die Verbrauchern gegenüber Umweltaussagen machen oder Nachhaltigkeits"
            "siegel verwenden (B2C). Keine MA-Schwelle. Branchenrelevanz: alle B2C-Unternehmen."
        ),
        "key_article": "Art. 1",
    },
    {
        "nr": 22,
        "key": "GreenClaims",
        "name": "Green Claims Directive (Entwurf)",
        "full_name": "Vorschlag Richtlinie - Begründung/Kommunikation ausdrücklicher Umweltaussagen",
        "url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:52023PC0166",
        "text_url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:52023PC0166",
        "scope": "EU",
        "criteria": (
            "Entwurf (noch nicht in Kraft). Gilt nach Verabschiedung für B2C-Unternehmen mit ausdrücklichen "
            "Umweltaussagen. Kleinstunternehmen (<10 MA & Umsatz <2 Mio EUR) ausgenommen."
        ),
        "key_article": "Art. 1, 3",
    },
]


# ---------------------------------------------------------------------------
# Guidelines je Regulierung.
#
# Quelle: offizielle Kommissions-/Behörden-Leitlinien (EU Commission, BAFA,
# EFRAG, ESMA ...). Werden beim Analyse-Lauf zusätzlich zum Gesetzestext
# gefetched und als Kontext an das LLM übergeben. Auf der Seite
# "Regulierungsliste" werden sie mit Link + Stand angezeigt.
#
# Schema: {reg_key: [{"name": str, "url": str}, ...]}
# Nicht aufgeführte reg_keys haben aktuell keine kuratierten Guidelines.
# ---------------------------------------------------------------------------
GUIDELINES_BY_REG_KEY: dict[str, list[dict]] = {
    "CSDDD": [
        {"name": "EU-Kommission – Corporate Sustainability Due Diligence",
         "url": "https://commission.europa.eu/business-economy-euro/doing-business-eu/sustainability-due-diligence-responsible-business/corporate-sustainability-due-diligence_en"},
    ],
    "LkSG": [
        {"name": "BAFA – Handreichungen zum LkSG",
         "url": "https://www.bafa.de/DE/Lieferketten/Handreichungen/handreichungen_node.html"},
        {"name": "BMAS/CSR in Deutschland – LkSG FAQ",
         "url": "https://www.csr-in-deutschland.de/DE/Wirtschaft-Menschenrechte/Ueber-das-Gesetz/FAQ/faq_node.html"},
    ],
    "EUDR": [
        {"name": "EU-Kommission – Entwaldungsfreie Lieferketten (EUDR)",
         "url": "https://environment.ec.europa.eu/topics/forests/deforestation/regulation-deforestation-free-products_en"},
    ],
    "FLR": [
        {"name": "EU-Kommission – Forced Labour Regulation",
         "url": "https://commission.europa.eu/business-economy-euro/doing-business-eu/sustainable-economy/forced-labour-regulation_en"},
    ],
    "CSRD": [
        {"name": "EU-Kommission – CSRD Implementierung & Q&A",
         "url": "https://finance.ec.europa.eu/regulation-and-supervision/financial-services-legislation/implementing-and-delegated-acts/corporate-sustainability-reporting-directive_en"},
    ],
    "CSRD_DE": [
        {"name": "IDW – CSRD-Umsetzung in Deutschland",
         "url": "https://www.idw.de/idw/im-fokus/csrd"},
    ],
    "ESRS": [
        {"name": "EFRAG – European Sustainability Reporting Standards",
         "url": "https://www.efrag.org/en/projects/european-sustainability-reporting-standards-esrs"},
    ],
    "NFRD": [
        {"name": "EU-Kommission – Non-Financial Reporting (Historie)",
         "url": "https://finance.ec.europa.eu/capital-markets-union-and-financial-markets/company-reporting-and-auditing/company-reporting/corporate-sustainability-reporting_en"},
    ],
    "CSR-RUG": [
        {"name": "DRSC – Deutsche Anwendungshinweise zur nichtfinanziellen Berichterstattung",
         "url": "https://www.drsc.de/themen/nachhaltigkeitsberichterstattung/"},
    ],
    "TaxonomieVO": [
        {"name": "EU-Kommission – EU-Taxonomie",
         "url": "https://finance.ec.europa.eu/sustainable-finance/tools-and-standards/eu-taxonomy-sustainable-activities_en"},
    ],
    "SFDR": [
        {"name": "EU-Kommission – SFDR Offenlegungspflichten",
         "url": "https://finance.ec.europa.eu/sustainable-finance/disclosures/sustainability-related-disclosure-financial-services-sector_en"},
    ],
    "ESGRatingVO": [
        {"name": "ESMA – ESG Ratings",
         "url": "https://www.esma.europa.eu/esmas-activities/sustainable-finance/esg-ratings"},
    ],
    "WhistleblowerRL": [
        {"name": "EU-Kommission – Schutz von Hinweisgebern",
         "url": "https://commission.europa.eu/aid-development-cooperation-fundamental-rights/your-rights-eu/whistleblowers-protection_en"},
    ],
    "HinSchG": [
        {"name": "Bundesamt für Justiz – Externe Meldestelle (HinSchG)",
         "url": "https://www.bundesjustizamt.de/DE/MeldestelledesBundes/MeldestelledesBundes_node.html"},
    ],
    "RightToRepair": [
        {"name": "EU-Kommission – Right to Repair",
         "url": "https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/european-green-deal/right-repair_en"},
    ],
    "Oekodesign": [
        {"name": "EU-Kommission – Ecodesign for Sustainable Products Regulation (ESPR)",
         "url": "https://commission.europa.eu/energy-climate-change-environment/standards-tools-and-labels/products-labelling-rules-and-requirements/sustainable-products/ecodesign-sustainable-products-regulation_en"},
    ],
    "PPWR": [
        {"name": "EU-Kommission – Verpackungen und Verpackungsabfälle",
         "url": "https://environment.ec.europa.eu/topics/waste-and-recycling/packaging-waste_en"},
    ],
    "KonfliktminVO": [
        {"name": "EU-Kommission – Konfliktmineralien-Verordnung",
         "url": "https://policy.trade.ec.europa.eu/development-and-sustainability/conflict-minerals-regulation_en"},
    ],
    "MinRohSorgG": [
        {"name": "BAFA – Mineralische Rohstoffe",
         "url": "https://www.bafa.de/DE/Wirtschaft_Rohstoffe/Mineralische_Rohstoffe/mineralische_rohstoffe_node.html"},
    ],
    "UmweltstrafRL": [
        {"name": "EU-Kommission – Environmental Crime Directive",
         "url": "https://environment.ec.europa.eu/law/environmental-crime_en"},
    ],
    "EmpCo": [
        {"name": "EU-Kommission – Stärkung der Verbraucher für den grünen Wandel",
         "url": "https://commission.europa.eu/law/law-topic/consumer-protection-law/empowering-consumers-green-transition_en"},
    ],
    "GreenClaims": [
        {"name": "EU-Kommission – Green Claims",
         "url": "https://environment.ec.europa.eu/topics/circular-economy/green-claims_en"},
    ],
}


def guidelines_for(reg_key: str) -> list[dict]:
    """Liefert die kuratierten Guidelines für eine Regulierung (oder leere Liste)."""
    return GUIDELINES_BY_REG_KEY.get(reg_key, [])


# ---------------------------------------------------------------------------
# Veroeffentlichungsdatum je Regulierung (statisch gepflegt).
#
# Fuer EU-Verordnungen/Richtlinien das Datum der Veroeffentlichung im
# Amtsblatt (OJ). Fuer deutsche Gesetze das Datum der Bundesgesetzblatt-
# Veroeffentlichung. Format: DD.MM.YYYY.
# ---------------------------------------------------------------------------
PUBLISHED_BY_REG_KEY: dict[str, str] = {
    "CSDDD":           "05.07.2024",
    "LkSG":            "16.07.2021",
    "EUDR":            "09.06.2023",
    "FLR":             "12.12.2024",
    "CSRD":            "16.12.2022",
    "CSRD_DE":         "Entwurf 2025",
    "ESRS":            "22.12.2023",
    "NFRD":            "15.11.2014",
    "CSR-RUG":         "11.04.2017",
    "TaxonomieVO":     "22.06.2020",
    "SFDR":            "09.12.2019",
    "ESGRatingVO":     "12.12.2024",
    "WhistleblowerRL": "26.11.2019",
    "HinSchG":         "02.06.2023",
    "RightToRepair":   "10.07.2024",
    "Oekodesign":      "28.06.2024",
    "PPWR":            "22.01.2025",
    "KonfliktminVO":   "19.05.2017",
    "MinRohSorgG":     "18.12.2020",
    "UmweltstrafRL":   "30.04.2024",
    "EmpCo":           "06.03.2024",
    "GreenClaims":     "Entwurf 22.03.2023",
}


def published_for(reg_key: str) -> str:
    """Veroeffentlichungsdatum (oder leerer Platzhalter)."""
    return PUBLISHED_BY_REG_KEY.get(reg_key, "—")


# Branchen: sprachneutrale Keys (= DE-String mit Umlauten) für DB-Persistenz.
# Übersetzungen: siehe i18n.BRANCH_LABELS
BRANCHES = [
    "Land-/Forstwirtschaft, Fischerei",
    "Bergbau / Gewinnung von Steinen und Erden",
    "Verarbeitendes Gewerbe / Industrie",
    "Chemie / Pharma",
    "Metallverarbeitung / Maschinenbau",
    "Automobil / Fahrzeugbau",
    "Elektronik / Elektrotechnik",
    "Textil / Bekleidung / Leder",
    "Lebensmittel / Getränke",
    "Möbel / Holz / Papier",
    "Energieversorgung",
    "Wasser- / Abfallwirtschaft",
    "Bauwirtschaft",
    "Handel (Groß-/Einzelhandel)",
    "Verkehr / Logistik",
    "Gastgewerbe / Tourismus",
    "Information / Telekommunikation / IT",
    "Finanzdienstleistungen",
    "Versicherungen",
    "Immobilien",
    "Beratung / Recht / Wirtschaftsprüfung",
    "Forschung / Entwicklung",
    "Bildung",
    "Gesundheit / Soziales",
    "Kunst / Unterhaltung / Medien",
    "Sonstige Dienstleistungen",
]

SITE_TYPES = [
    "Hauptsitz",
    "Produktionsstätte",
    "Vertriebsbüro",
    "Lager / Logistikzentrum",
    "Forschung / Entwicklung",
    "Filiale / Niederlassung",
]

LOCATIONS = ["Deutschland", "EU (ohne Deutschland)", "Weltweit (außerhalb EU)"]

LEGAL_FORMS = [
    "AG / SE",
    "GmbH",
    "GmbH & Co. KG",
    "KG / OHG",
    "Einzelunternehmen",
    "Genossenschaft",
    "Stiftung / Verein",
    "Limited / Ltd.",
    "Sonstige",
]

GROUP_ROLES = [
    "Eigenständig (kein Konzern)",
    "Mutterunternehmen mit Sitz in EU",
    "Mutterunternehmen mit Sitz außerhalb EU",
    "Tochter, EU-Muttergesellschaft",
    "Tochter, Nicht-EU-Muttergesellschaft",
]

PRODUCT_CATEGORIES = [
    "Verpackungen (eigene oder vertriebene)",
    "Elektronik / Haushaltsgeräte / IT-Hardware",
    "Holz / Holzprodukte / Papier",
    "Kaffee / Kakao",
    "Palmöl / Soja",
    "Kautschuk / Gummi",
    "Rinder / Rindsprodukte / Leder",
    "Zinn / Tantal / Wolfram / Gold (Direktimport)",
    "Chemische Stoffe",
    "Textilien / Bekleidung / Leder",
    "Möbel / Baustoffe",
    "Lebensmittel / Getränke",
    "Keine physischen Produkte (nur Dienstleistung/Software)",
]
