from __future__ import annotations

import datetime
from dataclasses import dataclass

from fastapi import Header

from app.errors import AuthError
from app.features.operator import repository as op_repo
from app.security import decode_token


@dataclass
class CurrentOperator:
    id: str
    email: str
    session_id: str = ""


def get_current_operator(authorization: str | None = Header(default=None)) -> CurrentOperator:
    if not authorization or " " not in authorization:
        raise AuthError("Nicht angemeldet.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token, "operator")
    except Exception:
        raise AuthError("Sitzung ungültig.")
    session_id = claims.get("sub")
    session = op_repo.get_betreiber_session(session_id) if session_id else None
    if not session or session["revoked"]:
        raise AuthError("Sitzung beendet.")
    exp = datetime.datetime.fromisoformat(session["expires_at"])
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    if exp < datetime.datetime.now(datetime.timezone.utc):
        raise AuthError("Sitzung abgelaufen.")
    op = op_repo.find_betreiber_by_email(claims.get("username", ""))
    if not op:
        raise AuthError("Sitzung ungültig.")
    return CurrentOperator(id=op["id"], email=op["email"], session_id=session_id)
