from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Postfach-Konfiguration -------------------------------------------------

class EmailKontoConfig(BaseModel):
    imap_host: str = Field(min_length=1)
    imap_port: int = 993
    imap_user: str = Field(min_length=1)
    imap_passwort: Optional[str] = Field(default=None, min_length=1)
    imap_tls: bool = True
    smtp_host: str = Field(min_length=1)
    smtp_port: int = 465
    smtp_user: Optional[str] = None
    smtp_passwort: Optional[str] = Field(default=None, min_length=1)
    smtp_tls: bool = True


class EmailKontoTest(BaseModel):
    imap_host: str = Field(min_length=1)
    imap_port: int = 993
    imap_user: str = Field(min_length=1)
    imap_passwort: str = Field(min_length=1)
    imap_tls: bool = True
    smtp_host: str = Field(min_length=1)
    smtp_port: int = 465
    smtp_user: Optional[str] = None
    smtp_passwort: Optional[str] = None
    smtp_tls: bool = True


class EmailKontoRead(BaseModel):
    imap_host: str
    imap_port: int
    imap_user: str
    imap_tls: bool
    smtp_host: str
    smtp_port: int
    smtp_user: Optional[str] = None
    smtp_tls: bool
    letzter_abruf_status: Optional[str] = None
    letzter_abruf_fehler_text: Optional[str] = None
    letzter_abruf_at: Optional[datetime | str] = None


class EmailKontoTestResult(BaseModel):
    ok: bool
    imap_ok: bool
    smtp_ok: bool
    detail: str = ""


# --- Nachrichten / Threads --------------------------------------------------

class EmailAnhangRead(BaseModel):
    id: str
    dateiname: str
    content_type: str
    groesse_bytes: int
    verarbeitet: bool
    fehler_text: Optional[str] = None


class EmailNachrichtRead(BaseModel):
    id: str
    thread_id: str
    vorgang_id: Optional[str] = None
    kunde_id: Optional[str] = None
    richtung: str
    absender: str
    empfaenger: str
    betreff: Optional[str] = None
    text_html: Optional[str] = None
    text_plain: Optional[str] = None
    empfangen_at: Optional[datetime | str] = None
    gesendet_von_nutzer_id: Optional[str] = None
    anhaenge: list[EmailAnhangRead] = Field(default_factory=list)
    created_at: datetime | str


class EmailThreadRead(BaseModel):
    id: str
    vorgang_id: Optional[str] = None
    kunde_id: Optional[str] = None
    betreff: Optional[str] = None
    nachrichten: list[EmailNachrichtRead] = Field(default_factory=list)


class EmailInboxItem(BaseModel):
    thread_id: str
    betreff: Optional[str] = None
    absender: str
    empfaenger: str
    vorgang_id: Optional[str] = None
    kunde_id: Optional[str] = None
    letzte_nachricht_am: Optional[datetime | str] = None
    letzte_nachricht_id: str


class EmailInboxResponse(BaseModel):
    items: list[EmailInboxItem]
    konto_status: Optional[str] = None
    konto_fehler_text: Optional[str] = None


class EmailCompose(BaseModel):
    empfaenger: Optional[str] = Field(default=None, min_length=1)
    betreff: str = Field(min_length=1)
    text: str = Field(min_length=1)
    antwort_an_nachricht_id: Optional[str] = None


class EmailZuordnen(BaseModel):
    vorgang_id: str = Field(min_length=1)


class EmailVorgangAusNachricht(BaseModel):
    anliegen: Optional[str] = None
    kunde_name: Optional[str] = None


class DownloadRead(BaseModel):
    download_url: str
