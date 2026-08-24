from __future__ import annotations

"""Release-Katalog der Branchenpakete (PROJ-14).

Diese Pakete sind bewusst KEIN Datenbank-Release-Artefakt und keine
Betreiberoberfläche (ADR-14-1): zwei feste, mit dem Backend ausgelieferte
Produktkataloge. Sie enthalten nur die Startinhalte, die die bestehenden
bzw. von PROJ-22 vorgesehenen Fachmodule verstehen.

Die Vorlagen werden pro Aufruf validiert (vollständige Startdaten), bevor sie
kopiert werden. Fehlt oder ist ein Eintrag ungültig, wird der Übernahmeweg mit
einer verständlichen deutschen Meldung (HTTP 422) abgelehnt — der Mandant wird
nicht eingerichtet.
"""

from app.errors import ValidationError

# --- SHK ---------------------------------------------------------------
SHK_LEISTUNGEN: list[tuple[str, str]] = [
    ("heizung", "Heizungsinstallation & -wartung"),
    ("sanitaer", "Sanitärinstallation"),
    ("bad", "Badsanierung"),
    ("notdienst", "Notdienst"),
    ("energie", "Energieberatung"),
]

SHK_PREISLISTE: list[dict] = [
    {"bezeichnung": "Wartung Heizungsanlage", "einheit": "Std.", "netto_einzelpreis": 89.0, "steuersatz": 19.0},
    {"bezeichnung": "Reparatur Sanitär", "einheit": "Std.", "netto_einzelpreis": 79.0, "steuersatz": 19.0},
    {"bezeichnung": "Badsanierung (Vorortbesichtigung)", "einheit": "Termin", "netto_einzelpreis": 0.0, "steuersatz": 19.0},
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

ENTRUEMPELUNG_PREISLISTE: list[dict] = [
    {"bezeichnung": "Komplette Wohnungsräumung", "einheit": "m²", "netto_einzelpreis": 12.0, "steuersatz": 19.0},
    {"bezeichnung": "Teilräumung / Keller", "einheit": "Std.", "netto_einzelpreis": 45.0, "steuersatz": 19.0},
    {"bezeichnung": "Haushaltsauflösung", "einheit": "Termin", "netto_einzelpreis": 0.0, "steuersatz": 19.0},
]

ENTRUEMPELUNG_FORMULAR_VORLAGE = "entruempelung"


class Branchenpaket:
    """Ein ausgeliefertes Paket: feste Kennung, deutsche Beschreibung, Version
    und die validierten Seed-Daten für die Zielmodule."""

    def __init__(self, kennung: str, name: str, beschreibung: str, version: int,
                 leistungen: list[tuple[str, str]], preisliste: list[dict],
                 formular_vorlage: str) -> None:
        self.kennung = kennung
        self.name = name
        self.beschreibung = beschreibung
        self.version = version
        self.leistungen = leistungen
        self.preisliste = preisliste
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
        for p in self.preisliste:
            if not p.get("bezeichnung"):
                raise ValidationError(
                    f"Das Branchenpaket „{self.name}“ enthält eine Katalogposition ohne Bezeichnung."
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
                     "Kontaktformular und Beispielpreise für Installateure.",
        version=1, leistungen=SHK_LEISTUNGEN, preisliste=SHK_PREISLISTE,
        formular_vorlage=SHK_FORMULAR_VORLAGE,
    ),
    "entruempelung": Branchenpaket(
        kennung="entruempelung", name="Entrümpelung",
        beschreibung="Räumung, Entsorgung, Transport und Wertanrechnung: "
                     "Startinhalte für Entrümpelungs- und Auflösungsbetriebe.",
        version=1, leistungen=ENTRUEMPELUNG_LEISTUNGEN, preisliste=ENTRUEMPELUNG_PREISLISTE,
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
