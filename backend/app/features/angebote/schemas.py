from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

RabattTyp = Literal["prozent", "betrag"]


class AngebotCreate(BaseModel):
    vorgaenger_angebot_id: Optional[str] = None
    gueltig_bis: Optional[date] = None
    freitext: Optional[str] = None


class AngebotUpdate(BaseModel):
    gueltig_bis: Optional[date] = None
    freitext: Optional[str] = None


class PositionCreate(BaseModel):
    bezeichnung: str = Field(min_length=1)
    menge: float = Field(gt=0)
    einheit: str = Field(min_length=1)
    einzelpreis: float = Field(ge=0)
    steuersatz: float = Field(ge=0, le=100)
    rabatt_typ: RabattTyp = "prozent"
    rabatt_wert: float = Field(default=0, ge=0)
    sortierung: int = 0


class PositionUpdate(BaseModel):
    bezeichnung: Optional[str] = Field(default=None, min_length=1)
    menge: Optional[float] = Field(default=None, gt=0)
    einheit: Optional[str] = Field(default=None, min_length=1)
    einzelpreis: Optional[float] = Field(default=None, ge=0)
    steuersatz: Optional[float] = Field(default=None, ge=0, le=100)
    rabatt_typ: Optional[RabattTyp] = None
    rabatt_wert: Optional[float] = Field(default=None, ge=0)
    sortierung: Optional[int] = None


class PositionRead(BaseModel):
    id: str
    bezeichnung: str
    menge: float
    einheit: str
    einzelpreis: float
    steuersatz: float
    rabatt_typ: RabattTyp
    rabatt_wert: float
    sortierung: int
    positions_summe: float


class AngebotListItem(BaseModel):
    id: str
    vorgang_id: str
    angebot_nummer: str
    version: int
    vorgaenger_angebot_id: Optional[str] = None
    status: str
    gueltig_bis: Optional[date | str] = None
    netto_summe: float
    steuer_summe: float
    brutto_summe: float
    empfaenger_email: Optional[str] = None
    versendet_at: Optional[datetime | str] = None
    created_at: datetime | str
    updated_at: datetime | str


class AngebotDetail(AngebotListItem):
    freitext: Optional[str] = None
    dokument_id: Optional[str] = None
    positionen: list[PositionRead]


class FreigabeResult(BaseModel):
    angebot_id: str
    empfaenger: Optional[str] = None
    betreff: str
    netto_summe: float
    steuer_summe: float
    brutto_summe: float
    pdf_download_url: str


class SendenRequest(BaseModel):
    empfaenger: Optional[EmailStr] = None
    betreff: Optional[str] = Field(default=None, min_length=1)
    text: Optional[str] = Field(default=None, min_length=1)


class DownloadRead(BaseModel):
    download_url: str


class SendenResult(BaseModel):
    angebot: AngebotDetail
    versendet: bool
    fehler_text: Optional[str] = None
