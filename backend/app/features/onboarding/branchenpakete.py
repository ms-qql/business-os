from __future__ import annotations

"""Release-Katalog der Branchenpakete (PROJ-14, erweitert für PROJ-22).

Diese Pakete sind bewusst KEIN Datenbank-Release-Artefakt und keine
Betreiberoberfläche (ADR-14-1): zwei feste, mit dem Backend ausgelieferte
Produktkataloge. Sie enthalten nur die Startinhalte, die die bestehenden
bzw. von PROJ-22 vorgesehenen Fachmodule verstehen.

PROJ-22: Die Pakete liefern jetzt Kategorien und Gewerke mit echten
positiven Kostenzeilen (statt der flachen preisliste). Die atomare
Übernahme schreibt Kategorien, Gewerke und Kostenzeilen (siehe Tech Design
PROJ-22, Abschnitt Migration)."""

from app.errors import ValidationError

# --- SHK ---------------------------------------------------------------
SHK_LEISTUNGEN: list[tuple[str, str]] = [
    ("heizung", "Heizungsinstallation & -wartung"),
    ("sanitaer", "Sanitärinstallation"),
    ("bad", "Badsanierung"),
    ("notdienst", "Notdienst"),
    ("energie", "Energieberatung"),
]

SHK_KATEGORIEN: list[str] = ["Heizung & Sanitär", "Bad & Energie"]

# Jedes Gewerk: bezeichnung, einheit, kalkulationsart, steuersatz, kategorie
# (Name, wird beim Übernahmen angelegt) und Kostenzeilen. VK je Zeile =
# EK + (EK × Zuschlag/100); Gewerk-VK = Summe der Zeilen-VKs.
SHK_GEWERKE: list[dict] = [
    {
        "bezeichnung": "Wartung Heizungsanlage", "einheit": "Std.",
        "kalkulationsart": "je_einheit", "steuersatz": 19.0,
        "kategorie": "Heizung & Sanitär",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "Std.",
             "ek_einzelpreis": 70.0, "zuschlag_prozent": 27.14},
        ],
    },
    {
        "bezeichnung": "Reparatur Sanitär", "einheit": "Std.",
        "kalkulationsart": "je_einheit", "steuersatz": 19.0,
        "kategorie": "Heizung & Sanitär",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "Std.",
             "ek_einzelpreis": 65.0, "zuschlag_prozent": 21.54},
        ],
    },
    {
        "bezeichnung": "Badsanierung Beratung", "einheit": "Termin",
        "kalkulationsart": "gesamtpreis", "steuersatz": 19.0,
        "kategorie": "Bad & Energie",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "Termin",
             "ek_einzelpreis": 200.0, "zuschlag_prozent": 25.0},
        ],
    },
]

# SHK nutzt die vorhandene Formular-Startvorlage aus dem Formular-Baukasten.
SHK_FORMULAR_VORLAGE = "shk"

# --- Entrümpelung ------------------------------------------------------

ENTRUEMPELUNG_LEISTUNGEN: list[tuple[str, str]] = [
    ("flaeche", "Flächenrückbau & Demontage"),
    ("entsorgung", "Entsorgung & Recycling"),
    ("transport", "Transport & Logistik"),
    ("wertanrechnung", "Wertanrechnung"),
]

ENTRUEMPELUNG_KATEGORIEN: list[str] = ["Rückbau & Entsorgung", "Transport"]

ENTRUEMPELUNG_GEWERKE: list[dict] = [
    {
        "bezeichnung": "Komplette Wohnungsräumung", "einheit": "m²",
        "kalkulationsart": "je_einheit", "steuersatz": 19.0,
        "kategorie": "Rückbau & Entsorgung",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "m²",
             "ek_einzelpreis": 10.0, "zuschlag_prozent": 20.0},
        ],
    },
    {
        "bezeichnung": "Teilräumung / Keller", "einheit": "Std.",
        "kalkulationsart": "je_einheit", "steuersatz": 19.0,
        "kategorie": "Rückbau & Entsorgung",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "Std.",
             "ek_einzelpreis": 37.5, "zuschlag_prozent": 20.0},
        ],
    },
    {
        "bezeichnung": "Haushaltsauflösung", "einheit": "Termin",
        "kalkulationsart": "gesamtpreis", "steuersatz": 19.0,
        "kategorie": "Transport",
        "kostenzeilen": [
            {"kostenart": "lohn", "menge": 1.0, "einheit": "Termin",
             "ek_einzelpreis": 80.0, "zuschlag_prozent": 25.0},
        ],
    },
]

ENTRUEMPELUNG_FORMULAR_VORLAGE = "entruempelung"


class Branchenpaket:
    """Ein ausgeliefertes Paket: feste Kennung, deutsche Beschreibung, Version
    und die validierten Seed-Daten für die Zielmodule."""

    def __init__(self, kennung: str, name: str, beschreibung: str, version: int,
                 leistungen: list[tuple[str, str]], kategorien: list[str],
                 gewerke: list[dict], formular_vorlage: str) -> None:
        self.kennung = kennung
        self.name = name
        self.beschreibung = beschreibung
        self.version = version
        self.leistungen = leistungen
        self.kategorien = kategorien
        self.gewerke = gewerke
        self.formular_vorlage = formular_vorlage

    def validate(self) -> None:
        """Prüft die ausgelieferte Vorlage vor der Übernahme vollständig."""
        if not self.leistungen:
            raise ValidationError(
                f"Das Branchenpaket „{self.name}“ enthält keine Leistungsseiten."
            )
        for slug, titel in self.leistungen:
            if not slug or not titel:
                raise ValidationError(
                    f"Das Branchenpaket „{self.name}“ enthält eine unvollständige Leistungsseite."
                )
        if not self.kategorien:
            raise ValidationError(
                f"Das Branchenpaket „{self.name}“ enthält keine Kategorien."
            )
        if not self.gewerke:
            raise ValidationError(
                f"Das Branchenpaket „{self.name}“ enthält keine Gewerke."
            )
        for g in self.gewerke:
            if not g.get("bezeichnung"):
                raise ValidationError(
                    f"Das Branchenpaket „{self.name}“ enthält ein Gewerk ohne Bezeichnung."
                )
            if g.get("kalkulationsart") not in ("je_einheit", "gesamtpreis"):
                raise ValidationError(
                    f"Das Branchenpaket „{self.name}“ enthält eine ungültige Kalkulationsart."
                )
            zeilen = g.get("kostenzeilen") or []
            if not zeilen:
                raise ValidationError(
                    f"Das Gewerk „{g.get('bezeichnung')}“ enthält keine Kostenzeilen."
                )
            for z in zeilen:
                if z.get("kostenart") not in ("lohn", "material", "fremdleistung",
                                               "sonstiges_geraete"):
                    raise ValidationError(
                        f"Das Gewerk „{g.get('bezeichnung')}“ enthält eine ungültige Kostenart."
                    )
                if not (isinstance(z.get("ek_einzelpreis"), (int, float))
                        and z["ek_einzelpreis"] > 0):
                    raise ValidationError(
                        f"Das Gewerk „{g.get('bezeichnung')}“ enthält eine ungültige EK."
                    )
                if not (isinstance(z.get("menge"), (int, float)) and z["menge"] > 0):
                    raise ValidationError(
                        f"Das Gewerk „{g.get('bezeichnung')}“ enthält eine ungültige Menge."
                    )
                if not (isinstance(z.get("zuschlag_prozent"), (int, float))
                        and z["zuschlag_prozent"] >= 0):
                    raise ValidationError(
                        f"Das Gewerk „{g.get('bezeichnung')}“ enthält einen ungültigen Zuschlag."
                    )
        if self.formular_vorlage not in ("shk", "entruempelung"):
            raise ValidationError(
                f"Das Branchenpaket „{self.name}“ verweist auf eine unbekannte Formularvorlage."
            )


# Release-Fassung der beiden Pakete. Die Version ist die nachvollziehbare
# Releasefassung eines neuen Betriebs (siehe Tech Design).
PAKETE: dict[str, Branchenpaket] = {
    "shk": Branchenpaket(
        kennung="shk", name="SHK",
        beschreibung="Sanitär, Heizung und Klima: typische SHK-Leistungen, "
                     "Kontaktformular und Beispiel-Gewerke für Installateure.",
        version=1, leistungen=SHK_LEISTUNGEN, kategorien=SHK_KATEGORIEN,
        gewerke=SHK_GEWERKE, formular_vorlage=SHK_FORMULAR_VORLAGE,
    ),
    "entruempelung": Branchenpaket(
        kennung="entruempelung", name="Entrümpelung",
        beschreibung="Räumung, Entsorgung, Transport und Wertanrechnung: "
                     "Startinhalte für Entrümpelungs- und Auflösungsbetriebe.",
        version=1, leistungen=ENTRUEMPELUNG_LEISTUNGEN,
        kategorien=ENTRUEMPELUNG_KATEGORIEN, gewerke=ENTRUEMPELUNG_GEWERKE,
        formular_vorlage=ENTRUEMPELUNG_FORMULAR_VORLAGE,
    ),
}


def liste_optionen() -> list[dict]:
    """Nur Kennung, Name und Beschreibung — keine Version/Seed-Details."""
    return [
        {"kennung": p.kennung, "name": p.name, "beschreibung": p.beschreibung}
        for p in PAKETE.values()
    ]


def get_paket(kennung: str) -> Branchenpaket | None:
    return PAKETE.get(kennung)
