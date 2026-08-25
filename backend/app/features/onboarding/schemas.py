from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Onboarding-Status (read-only, aus echten Daten berechnet) ----------

OnboardingStatusWert = Literal["offen", "in_bearbeitung", "erledigt"]


class OnboardingSchritt(BaseModel):
    id: str
    titel: str
    status: OnboardingStatusWert
    pflicht: bool
    fehlende_eingabe: Optional[str] = None
    bearbeitungsziel: Optional[str] = None
    # Schritt-spezifische Zusatzinfos (nur in den betroffenen Schritten belegt).
    domain_status: Optional[str] = None
    postfach_test: Optional["PostfachTestInfo"] = None
    testvorgang: Optional["OnboardingTestvorgang"] = None


class PostfachTestInfo(BaseModel):
    imap_ok: bool
    smtp_ok: bool
    tested_at: Optional[datetime | str] = None


class OnboardingTestvorgang(BaseModel):
    vorgang_id: str
    anfrage_id: Optional[str] = None
    erstellt_am: Optional[datetime | str] = None


class OnboardingStatus(BaseModel):
    schritte: list[OnboardingSchritt]
    veroeffentlicht: bool
    veroeffentlicht_am: Optional[datetime | str] = None
    warnung: Optional[str] = None
    postfach_test: Optional[PostfachTestInfo] = None
    domain_status: Optional[str] = None
    testvorgang_id: Optional[str] = None
    paket_info: Optional["BranchenpaketInfo"] = None


# --- Domain-Reservierung / Veröffentlichung ------------------------------

class DomainReserve(BaseModel):
    hostname: str = Field(min_length=1)


class DomainReserveResponse(BaseModel):
    hostname: str
    status: str


class VeroeffentlichenResult(BaseModel):
    ok: bool = True
    domain_status: str
    veroeffentlicht_am: Optional[datetime | str] = None
    fehlende_schritte: list[str] = Field(default_factory=list)


# --- Postfach-Test (gegen das gespeicherte Konto) ------------------------

class PostfachTestResult(BaseModel):
    ok: bool
    imap_ok: bool
    smtp_ok: bool
    detail: str = ""


# --- Testvorgang ----------------------------------------------------------

class TestvorgangResult(BaseModel):
    vorgang_id: str
    anfrage_id: Optional[str] = None
    ist_test: bool = True
    erstellt_am: Optional[datetime | str] = None


# --- Branchenpaket (PROJ-14) --------------------------------------------

class BranchenpaketOption(BaseModel):
    kennung: str
    name: str
    beschreibung: str


class BranchenpaketUebernahme(BaseModel):
    kennung: str


class BranchenpaketUebernahmeResult(BaseModel):
    kennung: str
    name: str
    version: int
    uebernommen_am: str | None
    onboarding_status: "OnboardingStatus"


class BranchenpaketInfo(BaseModel):
    kennung: str | None = None
    name: str | None = None
    version: int | None = None
    uebernommen_am: str | None = None


OnboardingSchritt.model_rebuild()
OnboardingStatus.model_rebuild()
