from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class OperatorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class MandantCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    owner_name: str = Field(min_length=1)
    owner_email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MandantRead(BaseModel):
    id: str
    name: str
    status: str
