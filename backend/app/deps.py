from __future__ import annotations

import datetime
from dataclasses import dataclass

from fastapi import Depends, Header

from app import db
from app.errors import AuthError, ForbiddenError
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
    # Schreibgeschützte Branchenpaket-Kennzeichnung (PROJ-14). Nie vom Client
    # gesetzt; dient nur der Anzeige für Inhaber/Büro ohne Inhaber-only-Route.
    paket_kennung: str | None = None
    paket_name: str | None = None


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()
    return None


def _get_session(session_id: str) -> dict | None:
    # Direkter DB-Zugriff statt auth.repository-Import, um den zirkulären
    # Import (deps <-> auth.__init__ <-> auth.routes) zu vermeiden.
    rows = db.engine.query(
        "SELECT id, mandant_id, nutzer_id, revoked, expires_at FROM sitzungen WHERE id = %s",
        (session_id,),
    )
    return rows[0] if rows else None


def _get_user_by_id(mandant_id: str, user_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, name, email, role, status FROM nutzer "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, user_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def _mandant_paket(mandant_id: str) -> tuple[str | None, str | None]:
    """Liefert (kennung, name) des übernommenen Branchenpakets des Mandanten,
    soweit vorhanden. Namen aus dem Release-Katalog (PROJ-14)."""
    rows = db.engine.query(
        "SELECT branchenpaket_kennung FROM mandanten WHERE id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    kennung = rows[0]["branchenpaket_kennung"] if rows else None
    if not kennung:
        return None, None
    from app.features.onboarding import branchenpakete
    paket = branchenpakete.get_paket(kennung)
    return kennung, (paket.name if paket else None)


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

    session = _get_session(session_id)
    if not session or session["revoked"]:
        raise AuthError("Sitzung beendet.")
    exp = datetime.datetime.fromisoformat(str(session["expires_at"]))
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    if exp < datetime.datetime.now(datetime.timezone.utc):
        raise AuthError("Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.")

    user = _get_user_by_id(session["mandant_id"], session["nutzer_id"])
    if not user:
        raise AuthError("Sitzung ungültig.")
    if user["status"] == "disabled":
        raise AuthError("Konto deaktiviert.")

    paket_kennung, paket_name = _mandant_paket(session["mandant_id"])
    return CurrentUser(
        id=user["id"], mandant_id=user["mandant_id"], name=user["name"],
        email=user["email"], role=user["role"], status=user["status"],
        session_id=session_id, paket_kennung=paket_kennung, paket_name=paket_name,
    )


def require_role(*roles: str):
    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise ForbiddenError("Erforderliche Rolle nicht vorhanden.")
        return user

    return _guard
