from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Kostenart = Literal["lohn", "material", "fremdleistung", "sonstiges_geraete"]
Kalkulationsart = Literal["je_einheit", "gesamtpreis"]


# --- Kostenzeilen --------------------------------------------------------

class KostenzeileBase(BaseModel):
    kostenart: Kostenart
    beschreibung: Optional[str] = None
    menge: float = Field(gt=0)
    einheit: str = Field(min_length=1)
    ek_einzelpreis: float = Field(gt=0)
    zuschlag_prozent: float = Field(ge=0)


class KostenzeileRead(KostenzeileBase):
    id: str
    gewerk_id: str
    # Serverseitig berechneter Verkaufspreis der Zeile (2 Dezimalstellen).
    vk_preis: float


# --- Kategorie -----------------------------------------------------------

class KategorieCreate(BaseModel):
    name: str = Field(min_length=1)


class KategorieRead(BaseModel):
    id: str
    name: str
    # Anzahl der dem Mandanten zugeordneten Gewerke je Kategorie.
    anzahl_gewerke: int = 0


# --- Gewerk --------------------------------------------------------------

class GewerkCreate(BaseModel):
    bezeichnung: str = Field(min_length=1)
    einheit: str = Field(min_length=1)
    kalkulationsart: Kalkulationsart = "je_einheit"
    kategorie_id: Optional[str] = None
    langbeschreibung: Optional[str] = None
    steuersatz: float = Field(ge=0, le=100, default=19)
    kostenzeilen: list[KostenzeileBase] = Field(min_length=1, max_length=50)
    duplikat_bestaetigt: bool = False


class GewerkUpdate(BaseModel):
    bezeichnung: Optional[str] = Field(default=None, min_length=1)
    einheit: Optional[str] = Field(default=None, min_length=1)
    kalkulationsart: Optional[Kalkulationsart] = None
    kategorie_id: Optional[str] = None
    langbeschreibung: Optional[str] = None
    steuersatz: Optional[float] = Field(default=None, ge=0, le=100)
    kostenzeilen: Optional[list[KostenzeileBase]] = Field(default=None, min_length=1, max_length=50)
    duplikat_bestaetigt: bool = False


class GewerkRead(BaseModel):
    id: str
    bezeichnung: str
    einheit: str
    kalkulationsart: Kalkulationsart
    kategorie_id: Optional[str] = None
    langbeschreibung: Optional[str] = None
    steuersatz: float
    kostenzeilen: list[KostenzeileRead]
    # Berechnete Projektion: VK-Summe der Zeilen (Verkaufspreis des Gewerks).
    vk_preis: float


class GewerkListeItem(BaseModel):
    id: str
    bezeichnung: str
    einheit: str
    kalkulationsart: Kalkulationsart
    kategorie_id: Optional[str] = None
    vk_preis: float


class GewerkListe(BaseModel):
    items: list[GewerkListeItem]


class DuplikatInfo(BaseModel):
    bestaetigung_erforderlich: bool = True
    hinweis: str = (
        "Es existiert bereits ein Gewerk mit derselben Bezeichnung und Einheit. "
        "Zum Speichern bitte bestätigen."
    )
