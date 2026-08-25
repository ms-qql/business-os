from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

TriageStatus = Literal["gruen", "gelb", "rot", "nicht_bewertet"]
LeistungswertKlassifikation = Literal["passend", "unpassend"]


class TriageLeistungswertRead(BaseModel):
    wert: str
    klassifikation: LeistungswertKlassifikation


class TriageLeistungswertInput(BaseModel):
    wert: str = Field(min_length=1)
    klassifikation: LeistungswertKlassifikation


class TriageEinstellungRead(BaseModel):
    leistungs_formular_id: Optional[str] = None
    leistungs_feld_id: Optional[str] = None
    wunschtermin_feld_id: Optional[str] = None
    naechster_freier_termin: Optional[date] = None
    werte: list[TriageLeistungswertRead] = []


class TriageEinstellungPut(BaseModel):
    leistungs_formular_id: str
    leistungs_feld_id: str
    wunschtermin_feld_id: Optional[str] = None
    werte: list[TriageLeistungswertInput] = Field(default_factory=list)


class TriageKapazitaetPatch(BaseModel):
    # ISO-Kalendertag; null entfernt den Wert.
    naechster_freier_termin: Optional[date] = None


class TriageErgebnis(BaseModel):
    status: TriageStatus
    gruende: list[str] = []
    naechster_freier_termin: Optional[date] = None
