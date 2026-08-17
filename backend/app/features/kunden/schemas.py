from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class KundeCreate(BaseModel):
    name: str = Field(min_length=1)
    email: Optional[str] = None
    telefon: Optional[str] = None
    notiz: Optional[str] = None


class KundeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = None
    telefon: Optional[str] = None
    notiz: Optional[str] = None


class KundeRead(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    telefon: Optional[str] = None
    notiz: Optional[str] = None
    created_at: str
    updated_at: str


class KundeCreateRead(KundeRead):
    # Edge Case: gleiche E-Mail/Telefon erzeugt nur einen Hinweis, keine
    # automatische Zusammenführung.
    moegliche_duplikate: list[KundeRead] = Field(default_factory=list)


class ObjektCreate(BaseModel):
    adresse: str = Field(min_length=1)
    notiz: Optional[str] = None


class ObjektRead(BaseModel):
    id: str
    kunde_id: str
    adresse: str
    notiz: Optional[str] = None
    created_at: str


class KundenListResponse(BaseModel):
    items: list[KundeRead]
    total: int
    limit: int
    offset: int
