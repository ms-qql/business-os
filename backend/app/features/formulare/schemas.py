from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

FeldTyp = Literal[
    "text", "mehrzeilig", "dropdown", "kachel", "radio",
    "zahl", "datum", "upload", "adresse", "consent",
]
UebernahmeZuordnung = Literal[
    "kontaktname", "email", "telefon", "adresse", "anliegen",
]
Komplexitaet = Literal["einfach", "erweitert"]
SpamStatus = Literal["normal", "spam"]


# --- Angemeldete Routen: Entwurf -------------------------------------------


class FormularCreate(BaseModel):
    vorlage: Optional[Literal["shk", "entruempelung"]] = None


class FormularPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    komplexitaet: Optional[Komplexitaet] = None
    draft_revision: int = Field(ge=1)


class SchrittCreate(BaseModel):
    titel: str = Field(min_length=1)
    draft_revision: int = Field(ge=1)


class SchrittPatch(BaseModel):
    titel: str = Field(min_length=1)
    draft_revision: int = Field(ge=1)


class SchrittReorder(BaseModel):
    ordered_ids: list[str] = Field(min_length=1)
    draft_revision: int = Field(ge=1)


class FeldCreate(BaseModel):
    typ: FeldTyp
    draft_revision: int = Field(ge=1)


class FeldOptionInput(BaseModel):
    label: str = Field(min_length=1)
    wert: str = Field(min_length=1)


class FeldPatch(BaseModel):
    label: str = Field(min_length=1)
    hilfetext: Optional[str] = None
    pflichtfeld: bool = False
    optional_in_einfach: bool = False
    uebernahme: Optional[UebernahmeZuordnung] = None
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: Optional[bool] = None
    reg_exp: Optional[str] = None
    maxlaenge: Optional[int] = Field(default=None, ge=1)
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: Optional[int] = Field(default=None, ge=1)
    optionen: Optional[list[FeldOptionInput]] = None
    draft_revision: int = Field(ge=1)


class FeldReorder(BaseModel):
    ordered_ids: list[str] = Field(min_length=1)
    draft_revision: int = Field(ge=1)


class PublishRequest(BaseModel):
    draft_revision: int = Field(ge=1)


class FormularOptionRead(BaseModel):
    id: str
    label: str
    wert: str


class FeldRead(BaseModel):
    id: str
    typ: FeldTyp
    label: str
    hilfetext: Optional[str] = None
    pflichtfeld: bool
    optional_in_einfach: bool
    uebernahme: Optional[Optional[UebernahmeZuordnung]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: Optional[bool] = None
    reg_exp: Optional[str] = None
    maxlaenge: Optional[int] = None
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: Optional[int] = None
    optionen: list[FormularOptionRead] = []


class SchrittRead(BaseModel):
    id: str
    titel: str
    felder: list[FeldRead] = []


class FormularEntwurf(BaseModel):
    id: str
    name: str
    komplexitaet: Komplexitaet
    draft_revision: int
    veroeffentlicht: bool
    public_id: Optional[str] = None
    schritte: list[SchrittRead] = []
    created_at: datetime | str
    updated_at: datetime | str


class FormularListeItem(BaseModel):
    id: str
    name: str
    komplexitaet: Komplexitaet
    draft_revision: int
    veroeffentlicht: bool
    public_id: Optional[str] = None
    updated_at: datetime | str


class FormularListeResult(BaseModel):
    items: list[FormularListeItem]
    total: int
    limit: int
    offset: int


class FormularEinbindung(BaseModel):
    direktlink: str
    iframe: str
    snippet: str


# --- Öffentliche Routen ----------------------------------------------------


class PublicOption(BaseModel):
    label: str
    wert: str


class PublicFeld(BaseModel):
    id: str
    typ: FeldTyp
    label: str
    hilfetext: Optional[str] = None
    pflichtfeld: bool
    optional_in_einfach: bool = False
    optionen: list[PublicOption] = []
    min: Optional[float] = None
    max: Optional[float] = None
    ganzzahl: Optional[bool] = None
    maxlaenge: Optional[int] = None
    reg_exp: Optional[str] = None
    datum_min: Optional[str] = None
    datum_max: Optional[str] = None
    max_anzahl: Optional[int] = None


class PublicSchritt(BaseModel):
    id: str
    titel: str
    felder: list[PublicFeld] = []


class PublicFormular(BaseModel):
    name: str
    modus: Komplexitaet
    schritte: list[PublicSchritt] = []


class EinsendungUploadRead(BaseModel):
    upload_id: str


class FeldWert(BaseModel):
    feld_id: str
    wert: Optional[str] = None
    zahl: Optional[float] = None
    datum: Optional[str] = None
    werte: Optional[list[str]] = None
    upload_ids: Optional[list[str]] = None


class EinsendungCreate(BaseModel):
    uebermittlungskennung: str = Field(min_length=1)
    client_start: str = Field(min_length=1)
    honeypot: str = ""
    werte: list[FeldWert] = Field(default_factory=list)


class EinsendungResult(BaseModel):
    status: Literal["erfolgreich", "spam"]


# --- Listenansicht markierter Einsendungen --------------------------------


class EinsendungListItem(BaseModel):
    id: str
    formular_id: str
    formular_name: str
    version_id: str
    uebermittlungskennung: str
    spam_status: SpamStatus
    anfrage_id: Optional[str] = None
    vorgang_id: Optional[str] = None
    erstellt_am: datetime | str
    werte: dict


class EinsendungListResult(BaseModel):
    items: list[EinsendungListItem]
    total: int
    limit: int
    offset: int
