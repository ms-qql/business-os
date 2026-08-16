from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    role: str


class UserUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class UserRead(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
