from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TERMIN_STATUS_OFFEN = "Termin geplant"

# --- Eingabe ---------------------------------------------------------------


class TerminCreate(BaseModel):
    vorgang_id: str = Field(min_length=1)
    beginn: datetime
    ende: datetime
    adresse: Optional[str] = None
    notiz: Optional[str] = None
    monteure: list[str] = Field(default_factory=list)


class TerminCreateNested(BaseModel):
    # Wie TerminCreate, aber ohne vorgang_id (kommt aus dem URL-Pfad).
    beginn: datetime
    ende: datetime
    adresse: Optional[str] = None
    notiz: Optional[str] = None
    monteure: list[str] = Field(default_factory=list)


class TerminUpdate(BaseModel):
    # Alle Felder optional; PATCH aktualisiert nur mitgeschickte Werte.
    vorgang_id: Optional[str] = None
    beginn: Optional[datetime] = None
    ende: Optional[datetime] = None
    adresse: Optional[str] = None
    notiz: Optional[str] = None
    monteure: Optional[list[str]] = None


class ZuweisungCreate(BaseModel):
    nutzer_id: str = Field(min_length=1)


# --- Ausgabe ---------------------------------------------------------------


class TerminMonteur(BaseModel):
    nutzer_id: str
    name: str
    aktiv: bool


class TerminKontakt(BaseModel):
    name: str
    telefon: Optional[str] = None
    email: Optional[str] = None


class TerminListItem(BaseModel):
    id: str
    vorgang_id: str
    beginn: str
    ende: str
    adresse: Optional[str] = None
    notiz: Optional[str] = None
    abgesagt_at: Optional[str] = None
    anliegen: str
    monteure: list[TerminMonteur]
    konflikt: bool
    konflikt_monteure: list[str]


class TerminDetail(TerminListItem):
    kontakt: Optional[TerminKontakt] = None
    ist_eigen: Optional[bool] = None


class TerminErgebnis(BaseModel):
    termin: TerminDetail
    konflikt: bool
    konflikt_monteure: list[str]


class TerminListResult(BaseModel):
    items: list[TerminListItem]
    konflikt_monteure: list[str]
    total: int


class MonteurOption(BaseModel):
    id: str
    name: str
    aktiv: bool


class KonfliktHinweis(BaseModel):
    konflikt: bool
    konflikt_monteure: list[str]
