from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Feste Feldtypen laut Tech Design — identisch zur Frontend-Definition
# (features/PROJ-13-formular-baukasten.md API-Contracts). Kein frei
# erweiterbarer Katalog.
FeldTyp = Literal[
    "text", "mehrzeilig", "dropdown", "kachel", "radio",
    "zahl", "datum", "upload", "adresse", "consent",
]

# Übernahme-Zuordnung: optionaler Wert je Text-/Adress-/Auswahlfeld.
UebernahmeZiel = Literal["kontaktname", "email", "telefon", "adresse", "anliegen"]

# Typen, die eine Optionsliste führen.
OPTION_TYPEN = ("dropdown", "kachel", "radio")

# Obergrenzen gegen ungebundene Speicherung (ponytail).
MAX_SCHRITTE = 50
MAX_FELDER_PRO_SCHRITT = 100
MAX_OPTIONEN_PRO_FELD = 100
MAX_UPLOADS_PRO_FELD = 10
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB je Datei (fest laut Tech Design)


# --- Schreib-Requests (Editor) -------------------------------------------


class FeldOptionWrite(BaseModel):
    label: str = Field(min_length=1)
    wert: str = Field(min_length=1)


class FeldWrite(BaseModel):
    """Editor-Eingabe für ein Feld. Die typbezogene Konfiguration wird
    flach gesendet (wie das Frontend), nicht verschachtelt."""

    # Request-Feld heißt `type` (wie im Tech Design), intern `typ`.
    typ: FeldTyp = Field(alias="type")
    label: str = ""
    hilfetext: str = ""
    pflichtfeld: bool = False
    optional_in_einfach: bool = False
    uebernahme: Optional[UebernahmeZiel] = None
    optionen: list[FeldOptionWrite] = Field(default_factory=list)
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: bool = False
    reg_exp: Optional[str] = None
    minlaenge: Optional[int] = None
    maxlaenge: Optional[int] = None
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: int = 1

    model_config = ConfigDict(populate_by_name=True)


class SchrittWrite(BaseModel):
    titel: str = ""


class FormularCreate(BaseModel):
    # `vorlage`: leer | shk | entruempelung. Vorlagen sind Release-Inhalt,
    # keine vom Mandanten schreibbare Entität.
    vorlage: Literal["leer", "shk", "entruempelung"] = "leer"


class FormularPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    komplexitaet: Optional[Literal["einfach", "erweitert"]] = None


class SchrittReihenfolgeRequest(BaseModel):
    draft_revision: int
    ordered_ids: list[str] = Field(min_length=1)


class FeldReihenfolgeRequest(BaseModel):
    draft_revision: int
    ordered_ids: list[str] = Field(min_length=1)


class PublishRequest(BaseModel):
    draft_revision: int


class WithdrawRequest(BaseModel):
    draft_revision: int


# --- Lesedaten (Builder / Editor) ----------------------------------------


class FeldOptionRead(BaseModel):
    id: str
    label: str
    wert: str


class FeldRead(BaseModel):
    id: str
    typ: FeldTyp
    label: str
    hilfetext: str
    pflichtfeld: bool
    optional_in_einfach: bool
    uebernahme: Optional[UebernahmeZiel] = None
    optionen: list[FeldOptionRead] = Field(default_factory=list)
    # Flache Konfigurationsfelder (wie Frontend-Schema `Feld`).
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: bool = False
    reg_exp: Optional[str] = None
    maxlaenge: Optional[int] = None
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: int = 1


class SchrittRead(BaseModel):
    id: str
    titel: str
    felder: list[FeldRead] = Field(default_factory=list)


class FormularDraftRead(BaseModel):
    id: str
    name: str
    komplexitaet: Literal["einfach", "erweitert"]
    draft_revision: int
    veroeffentlicht: bool
    public_id: Optional[str] = None
    schritte: list[SchrittRead] = Field(default_factory=list)
    created_at: str
    updated_at: str


class FormularListeItem(BaseModel):
    id: str
    name: str
    komplexitaet: Literal["einfach", "erweitert"]
    draft_revision: int
    veroeffentlicht: bool
    public_id: Optional[str] = None
    updated_at: str


class FormularListeResponse(BaseModel):
    items: list[FormularListeItem]
    total: int
    limit: int
    offset: int


class FormularEinbindung(BaseModel):
    direktlink: str
    iframe: str
    snippet: str


# --- Öffentlich (Snapshot) -----------------------------------------------


class PublicFeld(BaseModel):
    id: str
    typ: FeldTyp
    label: str
    hilfetext: str
    pflichtfeld: bool
    optionen: list[FeldOptionRead] = Field(default_factory=list)
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: bool = False
    reg_exp: Optional[str] = None
    maxlaenge: Optional[int] = None
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: int = 1


class PublicSchritt(BaseModel):
    id: str
    titel: str
    felder: list[PublicFeld] = Field(default_factory=list)


class PublicFormular(BaseModel):
    name: str
    modus: Literal["einfach", "erweitert"]
    schritte: list[PublicSchritt] = Field(default_factory=list)


# --- Einsendung (öffentlich) ---------------------------------------------


class FeldWert(BaseModel):
    feld_id: str
    wert: Optional[str] = None
    zahl: Optional[float] = None
    datum: Optional[str] = None
    werte: Optional[list[str]] = None
    upload_ids: Optional[list[str]] = None


class EinsendungCreate(BaseModel):
    uebermittlungskennung: str = Field(min_length=1)
    client_start: Optional[str] = None  # ISO-Zeitstempel (Client)
    honeypot: str = ""  # muss leer bleiben
    werte: list[FeldWert] = Field(default_factory=list)


class EinsendungUploadRead(BaseModel):
    upload_id: str


class EinsendungResult(BaseModel):
    status: Literal["erfolgreich", "spam"] = "erfolgreich"


class FormularEinsendungRead(BaseModel):
    id: str
    formular_id: str
    formular_name: str
    uebermittlungskennung: str
    werte: dict[str, Any]
    consent_nachweis: dict[str, Any]
    spam_status: Literal["normal", "spam"]
    eingegangen_am: datetime | str
    anfrage_id: Optional[str] = None
    vorgang_id: Optional[str] = None


class FormularEinsendungListeResponse(BaseModel):
    items: list[FormularEinsendungRead]
    total: int
    limit: int
    offset: int
