from __future__ import annotations

import datetime
from dataclasses import dataclass

from fastapi import Depends, Header

from app.errors import AuthError, ForbiddenError
from app.features.auth import repository as auth_repo
from app.security import decode_token


@dataclass
class CurrentUser:
    id: str
    mandant_id: str
    name: str
    email: str
    role: str
    status: str
    session_id: str = ""


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()
    return None


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    token = _bearer(authorization)
    if not token:
        raise AuthError("Nicht angemeldet.")
    try:
        claims = decode_token(token, "business")
    except Exception:
        raise AuthError("Sitzung ungültig.")

    session_id = claims.get("sub")
    if not session_id:
        raise AuthError("Sitzung ungültig.")

    session = auth_repo.get_session(session_id)
    if not session or session["revoked"]:
        raise AuthError("Sitzung beendet.")
    exp = datetime.datetime.fromisoformat(str(session["expires_at"]))
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    if exp < datetime.datetime.now(datetime.timezone.utc):
        raise AuthError("Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.")

    user = auth_repo.get_user_by_id(session["mandant_id"], session["nutzer_id"])
    if not user:
        raise AuthError("Sitzung ungültig.")
    if user["status"] == "disabled":
        raise AuthError("Konto deaktiviert.")

    return CurrentUser(
        id=user["id"], mandant_id=user["mandant_id"], name=user["name"],
        email=user["email"], role=user["role"], status=user["status"],
        session_id=session_id,
    )


def require_role(*roles: str):
    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise ForbiddenError("Erforderliche Rolle nicht vorhanden.")
        return user

    return _guard
