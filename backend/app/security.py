from __future__ import annotations

import datetime
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .config import settings


_hasher = PasswordHasher(
    time_cost=settings.argon_time_cost,
    memory_cost=settings.argon_memory_cost,
    parallelism=settings.argon_parallelism,
)


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(raw: str, hashed: str | None) -> bool:
    if not hashed:
        # Constant-time-ish: still run a hash to avoid timing leaks on absent pw.
        _hasher.hash("absent")
        return False
    try:
        return _hasher.verify(hashed, raw)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def make_token(sub: str, aud: str, extra: dict | None = None, ttl_minutes: int | None = None) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(minutes=ttl_minutes or settings.access_token_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": sub,
        "aud": aud,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_aud: str) -> dict:
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                        audience=expected_aud)
    return claims
