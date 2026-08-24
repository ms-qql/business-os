from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

VorgangStatus = Literal["Neu", "Rückruf", "Angebot offen", "Termin geplant", "Erledigt", "Abgeschlossen"]

VALID_STATUS: tuple[str, ...] = (
    "Neu", "Rückruf", "Angebot offen", "Termin geplant", "Erledigt", "Abgeschlossen",
)


class VorgangCreate(BaseModel):
    kunde_id: str
    objekt_id: Optional[str] = None
    anliegen: str = Field(min_length=1)
    quelle: str = Field(default="Sonstiges")
    notizen: Optional[str] = None
    status: VorgangStatus = "Neu"


class VorgangUpdate(BaseModel):
    status: Optional[VorgangStatus] = None
    anliegen: Optional[str] = Field(default=None, min_length=1)
    notizen: Optional[str] = None
    objekt_id: Optional[str] = None


class VorgangListItem(BaseModel):
    id: str
    status: str
    quelle: str
    anliegen: str
    kunde_id: str
    kunde_name: str
    objekt_id: Optional[str] = None
    objekt_adresse: Optional[str] = None
    zugewiesener_nutzer_id: Optional[str] = None
    created_at: datetime | str
    updated_at: datetime | str


class VorgangListResponse(BaseModel):
    items: list[VorgangListItem]
    total: int
    limit: int
    offset: int


class HistorieRead(BaseModel):
    id: str
    ereignis: str
    detail: Optional[str] = None
    nutzer_id: Optional[str] = None
    created_at: datetime | str


class DokumentRead(BaseModel):
    id: str
    dateiname: str
    content_type: str
    groesse_bytes: int
    hochgeladen_von: Optional[str] = None
    created_at: datetime | str


class VorgangDetail(BaseModel):
    id: str
    status: str
    quelle: str
    anliegen: str
    notizen: Optional[str] = None
    kunde_id: str
    objekt_id: Optional[str] = None
    zugewiesener_nutzer_id: Optional[str] = None
    created_at: datetime | str
    updated_at: datetime | str
    historie: list[HistorieRead]
    dokumente: list[DokumentRead]
    # PROJ-13: verknüpfte Formular-Einsendung (sofern die Anfrage daraus entstand).
    formular_einsendung: Optional[dict] = None


class ZuweisungCreate(BaseModel):
    nutzer_id: str


class DownloadRead(BaseModel):
    download_url: str


class UebernahmeCreate(BaseModel):
    kunde_id: Optional[str] = None


class UebernahmeResult(BaseModel):
    vorgang_id: str
    kunde_id: str
    objekt_id: Optional[str] = None
