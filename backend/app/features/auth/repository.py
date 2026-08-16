from __future__ import annotations

import datetime
import uuid

from app import db
from app.config import settings


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def find_user_by_email(email: str) -> dict | None:
    if db.engine.is_postgres:
        rows = db.engine.query(
            "SELECT id, mandant_id, name, email, password_hash, role, status "
            "FROM auth_find_user_by_email(%s)",
            (email,),
        )
    else:
        rows = db.engine.query(
            "SELECT id, mandant_id, name, email, password_hash, role, status "
            "FROM nutzer WHERE email = %s",
            (email,),
        )
    return rows[0] if rows else None


def get_user_by_id(mandant_id: str, user_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, name, email, role, status FROM nutzer "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, user_id),
        mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_session(mandant_id: str, nutzer_id: str, ip: str | None) -> dict:
    sid = str(uuid.uuid4())
    expires = _now() + datetime.timedelta(minutes=settings.access_token_ttl_minutes)
    db.engine.command(
        "INSERT INTO sitzungen (id, mandant_id, nutzer_id, ip, expires_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (sid, mandant_id, nutzer_id, ip, expires.isoformat()),
        mandant_id=mandant_id,
    )
    return {"id": sid, "mandant_id": mandant_id, "nutzer_id": nutzer_id,
            "expires_at": expires}


def get_session(session_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, nutzer_id, revoked, expires_at FROM sitzungen WHERE id = %s",
        (session_id,),
    )
    return rows[0] if rows else None


def revoke_session(session_id: str) -> None:
    db.engine.command(
        "UPDATE sitzungen SET revoked = TRUE WHERE id = %s", (session_id,)
    )


def revoke_user_sessions(nutzer_id: str) -> None:
    db.engine.command(
        "UPDATE sitzungen SET revoked = TRUE WHERE nutzer_id = %s", (nutzer_id,)
    )


def count_recent_failures(email: str, ip: str | None, window_minutes: int) -> int:
    since = (_now() - datetime.timedelta(minutes=window_minutes)).isoformat()
    if ip:
        rows = db.engine.query(
            "SELECT COUNT(*) AS c FROM login_versuche "
            "WHERE email = %s AND ip = %s AND erfolg = FALSE AND created_at >= %s",
            (email, ip, since),
        )
    else:
        rows = db.engine.query(
            "SELECT COUNT(*) AS c FROM login_versuche "
            "WHERE email = %s AND erfolg = FALSE AND created_at >= %s",
            (email, since),
        )
    return int(rows[0]["c"]) if rows else 0


def record_login_attempt(email: str, ip: str | None, success: bool) -> None:
    db.engine.command(
        "INSERT INTO login_versuche (id, email, ip, erfolg, created_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), email, ip, success, _now().isoformat()),
    )


def create_invitation(mandant_id: str, nutzer_id: str, token: str, ttl_hours: int) -> None:
    expires = _now() + datetime.timedelta(hours=ttl_hours)
    db.engine.command(
        "INSERT INTO einladungen (id, mandant_id, nutzer_id, token, expires_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, nutzer_id, token, expires.isoformat()),
        mandant_id=mandant_id,
    )


def get_invitation(token: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, nutzer_id, token, expires_at, used "
        "FROM einladungen WHERE token = %s",
        (token,),
    )
    return rows[0] if rows else None


def mark_invitation_used(token: str) -> None:
    db.engine.command(
        "UPDATE einladungen SET used = TRUE WHERE token = %s", (token,)
    )


def set_user_password(nutzer_id: str, password_hash: str) -> None:
    db.engine.command(
        "UPDATE nutzer SET password_hash = %s, status = 'active' WHERE id = %s",
        (password_hash, nutzer_id),
    )


def create_password_reset(mandant_id: str, nutzer_id: str, token: str, ttl_minutes: int) -> None:
    expires = _now() + datetime.timedelta(minutes=ttl_minutes)
    db.engine.command(
        "INSERT INTO passwort_resets (id, mandant_id, nutzer_id, token, expires_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, nutzer_id, token, expires.isoformat()),
        mandant_id=mandant_id,
    )


def get_password_reset(token: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, nutzer_id, token, expires_at, used "
        "FROM passwort_resets WHERE token = %s",
        (token,),
    )
    return rows[0] if rows else None


def mark_reset_used(token: str) -> None:
    db.engine.command(
        "UPDATE passwort_resets SET used = TRUE WHERE token = %s", (token,)
    )


def audit(mandant_id: str, nutzer_id: str | None, typ: str, erfolg: bool,
          detail: str | None, ip: str | None) -> None:
    db.engine.command(
        "INSERT INTO audit_events (id, mandant_id, nutzer_id, typ, erfolg, detail, ip, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, nutzer_id, typ, erfolg, detail, ip, _now().isoformat()),
        mandant_id=mandant_id,
    )
