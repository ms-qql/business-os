from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

RechnungStatus = str  # 'entwurf' | 'versendet' | 'storniert'
Zahlungsstatus = str  # 'Offen' | 'Bezahlt' | 'Storniert'


# --- Rechnungsstellerprofil (Einstellungen) ------------------------------

class RechnungsstellerProfilIn(BaseModel):
    firma_name: str = Field(min_length=1)
    strasse: str = Field(min_length=1)
    hausnummer: str = Field(min_length=1)
    plz: str = Field(min_length=1)
    ort: str = Field(min_length=1)
    steuernummer: Optional[str] = None
    ust_id: Optional[str] = None


class RechnungsstellerProfilRead(BaseModel):
    firma_name: str
    strasse: str
    hausnummer: str
    plz: str
    ort: str
    steuernummer: Optional[str] = None
    ust_id: Optional[str] = None
    updated_at: datetime | str


# --- Rechnung anlegen / Kopf ---------------------------------------------

class RechnungCreate(BaseModel):
    rechnungsdatum: date
    leistungsdatum: date
    angebot_id: Optional[str] = None  # optionale Positionsübernahme


class RechnungKopfUpdate(BaseModel):
    rechnungsdatum: Optional[date] = None
    leistungsdatum: Optional[date] = None
    empfaenger_email: Optional[EmailStr] = None


# --- Positionen ----------------------------------------------------------

class PositionCreate(BaseModel):
    bezeichnung: str = Field(min_length=1)
    menge: float = Field(gt=0)
    einheit: str = Field(min_length=1)
    netto_einzelpreis: float = Field(ge=0)
    steuersatz: float = Field(ge=0, le=100)
    sortierung: int = 0


class PositionUpdate(BaseModel):
    bezeichnung: Optional[str] = Field(default=None, min_length=1)
    menge: Optional[float] = Field(default=None, gt=0)
    einheit: Optional[str] = Field(default=None, min_length=1)
    netto_einzelpreis: Optional[float] = Field(default=None, ge=0)
    steuersatz: Optional[float] = Field(default=None, ge=0, le=100)
    sortierung: Optional[int] = None


class PositionRead(BaseModel):
    id: str
    bezeichnung: str
    menge: float
    einheit: str
    netto_einzelpreis: float
    steuersatz: float
    positions_summe: float
    sortierung: int


# --- Lesen / Listen ------------------------------------------------------

class RechnungListItem(BaseModel):
    id: str
    vorgang_id: str
    rechnungsnummer: str
    rechnungsdatum: date | str
    leistungsdatum: date | str
    status: str
    zahlungsstatus: str
    netto_summe: float
    steuer_summe: float
    brutto_summe: float
    empfaenger_email: Optional[str] = None
    versendet_at: Optional[datetime | str] = None
    storniert_at: Optional[datetime | str] = None
    created_at: datetime | str
    updated_at: datetime | str


class RechnungDetail(RechnungListItem):
    fassung_id: Optional[str] = None
    positionen: list[PositionRead]


# --- Freigabe / Senden / Storno ------------------------------------------

class FreigabeRequest(BaseModel):
    empfaenger: Optional[EmailStr] = None
    betreff: Optional[str] = Field(default=None, min_length=1)


class FreigabeResult(BaseModel):
    rechnung_id: str
    empfaenger: str
    betreff: str
    rechnungsnummer: str
    netto_summe: float
    steuer_summe: float
    brutto_summe: float
    pdf_download_url: str


class SendenRequest(BaseModel):
    empfaenger: Optional[EmailStr] = None
    betreff: Optional[str] = Field(default=None, min_length=1)
    text: Optional[str] = Field(default=None, min_length=1)


class SendenResult(BaseModel):
    rechnung: RechnungDetail
    versendet: bool
    fehler_text: Optional[str] = None


class ZahlungsstatusUpdate(BaseModel):
    zahlungsstatus: str  # genau 'Offen'|'Bezahlt'|'Storniert' (Service prüft)


class StornoResult(BaseModel):
    rechnung: RechnungDetail
    storniert: bool
    fehler_text: Optional[str] = None


class DownloadRead(BaseModel):
    download_url: str
