from __future__ import annotations

import uuid

from app import db


def list_users(mandant_id: str, limit: int) -> list[dict]:
    return db.engine.query(
        "SELECT id, name, email, role, status FROM nutzer "
        "WHERE mandant_id = %s ORDER BY created_at DESC LIMIT %s",
        (mandant_id, limit),
        mandant_id=mandant_id,
    )


def get_user(mandant_id: str, user_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, name, email, role, status FROM nutzer "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, user_id),
        mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def email_exists(mandant_id: str, email: str) -> bool:
    rows = db.engine.query(
        "SELECT 1 FROM nutzer WHERE mandant_id = %s AND email = %s",
        (mandant_id, email),
        mandant_id=mandant_id,
    )
    return bool(rows)


def create_user(mandant_id: str, name: str, email: str, role: str) -> dict:
    uid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO nutzer (id, mandant_id, name, email, role, status) "
        "VALUES (%s, %s, %s, %s, %s, 'invited')",
        (uid, mandant_id, name, email, role),
        mandant_id=mandant_id,
    )
    return get_user(mandant_id, uid)


def update_user(mandant_id: str, user_id: str, role: str | None,
                status: str | None) -> dict | None:
    sets = []
    params: list = []
    if role is not None:
        sets.append("role = %s")
        params.append(role)
    if status is not None:
        sets.append("status = %s")
        params.append(status)
    if not sets:
        return get_user(mandant_id, user_id)
    params.extend([mandant_id, user_id])
    db.engine.command(
        f"UPDATE nutzer SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params),
        mandant_id=mandant_id,
    )
    return get_user(mandant_id, user_id)


def count_active_owners(mandant_id: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM nutzer "
        "WHERE mandant_id = %s AND role = 'Inhaber' AND status = 'active'",
        (mandant_id,),
        mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0
