from __future__ import annotations

import datetime
import uuid

from app import db
from app.config import settings


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def find_betreiber_by_email(email: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, email, password_hash FROM betreiber WHERE email = %s", (email,)
    )
    return rows[0] if rows else None


def create_betreiber_session(betreiber_id: str) -> dict:
    sid = str(uuid.uuid4())
    expires = _now() + datetime.timedelta(minutes=settings.access_token_ttl_minutes)
    db.engine.command(
        "INSERT INTO betreiber_sitzungen (id, betreiber_id, expires_at) VALUES (%s, %s, %s)",
        (sid, betreiber_id, expires.isoformat()),
    )
    return {"id": sid, "betreiber_id": betreiber_id, "expires_at": expires}


def get_betreiber_session(session_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, betreiber_id, revoked, expires_at FROM betreiber_sitzungen WHERE id = %s",
        (session_id,),
    )
    return rows[0] if rows else None


def revoke_betreiber_session(session_id: str) -> None:
    db.engine.command(
        "UPDATE betreiber_sitzungen SET revoked = TRUE WHERE id = %s", (session_id,)
    )


def create_mandant(name: str) -> dict:
    mid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO mandanten (id, name, status) VALUES (%s, %s, 'active')",
        (mid, name),
    )
    rows = db.engine.query("SELECT id, name, status FROM mandanten WHERE id = %s", (mid,))
    return rows[0]


def create_owner_user(mandant_id: str, name: str, email: str) -> dict:
    uid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO nutzer (id, mandant_id, name, email, role, status) "
        "VALUES (%s, %s, %s, %s, 'Inhaber', 'invited')",
        (uid, mandant_id, name, email),
    )
    rows = db.engine.query(
        "SELECT id, mandant_id, name, email, role, status FROM nutzer WHERE id = %s", (uid,)
    )
    return rows[0]
