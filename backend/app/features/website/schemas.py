from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Kontaktweg = Literal["Telefon", "E-Mail"]
Dringlichkeit = Literal["Normal", "Dringend"]


class LeistungRead(BaseModel):
    slug: str
    titel: str
    aktiv: bool
    kurzbeschreibung: str
    inhalt: str


class PublicLeistung(BaseModel):
    slug: str
    titel: str
    kurzbeschreibung: str


class PublicLeistungDetail(PublicLeistung):
    inhalt: str


class PublicSite(BaseModel):
    firmenname: str
    logo_url: Optional[str] = None
    marken_farbe: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    oeffnungszeiten: Optional[str] = None
    ueber_uns: Optional[str] = None
    leistungen: list[PublicLeistung]


class WebsiteSettingsRead(BaseModel):
    firmenname: str
    logo_url: Optional[str] = None
    marken_farbe: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    oeffnungszeiten: Optional[str] = None
    ueber_uns: Optional[str] = None
    domain: Optional[str] = None
    domain_status: Optional[str] = None
    leistungen: list[LeistungRead]


class LeistungPatch(BaseModel):
    slug: str
    aktiv: Optional[bool] = None
    kurzbeschreibung: Optional[str] = None
    inhalt: Optional[str] = None


class WebsiteSettingsPatch(BaseModel):
    firmenname: Optional[str] = Field(default=None, min_length=1)
    marken_farbe: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    oeffnungszeiten: Optional[str] = None
    ueber_uns: Optional[str] = None
    domain: Optional[str] = None
    leistungen: Optional[list[LeistungPatch]] = None


class LogoUploadRead(BaseModel):
    logo_url: str


class AnfrageUploadRead(BaseModel):
    upload_id: str


class AnfrageCreate(BaseModel):
    name: str = Field(min_length=1)
    kontaktweg: Kontaktweg
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresse: str = Field(min_length=1)
    anliegen: str = Field(min_length=1)
    dringlichkeit: Dringlichkeit
    zeitfenster: Optional[str] = None
    uebermittlungskennung: str = Field(min_length=1)
    upload_ids: list[str] = Field(default_factory=list)


class AnfrageResult(BaseModel):
    ok: bool = True
