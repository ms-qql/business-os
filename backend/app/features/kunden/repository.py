from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Kunde ------------------------------------------------------------

def list_kunden(mandant_id: str, q: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    where = "WHERE mandant_id = %s"
    params: list = [mandant_id]
    if q:
        where += " AND (LOWER(name) LIKE LOWER(%s) OR LOWER(email) LIKE LOWER(%s) OR LOWER(telefon) LIKE LOWER(%s))"
        like = f"%{q}%"
        params.extend([like, like, like])

    total_rows = db.engine.query(
        f"SELECT COUNT(*) AS c FROM kunde {where}", tuple(params), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0

    rows = db.engine.query(
        f"SELECT id, name, email, telefon, notiz, created_at, updated_at FROM kunde "
        f"{where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (limit, offset), mandant_id=mandant_id,
    )
    return rows, total


def get_kunde(mandant_id: str, kunde_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, name, email, telefon, notiz, created_at, updated_at FROM kunde "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, kunde_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_kunde_by_email(mandant_id: str, email: str) -> dict | None:
    if not email:
        return None
    rows = db.engine.query(
        "SELECT id, name, email, telefon, notiz, created_at, updated_at FROM kunde "
        "WHERE mandant_id = %s AND LOWER(email) = LOWER(%s) LIMIT 1",
        (mandant_id, email), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def find_moegliche_duplikate(mandant_id: str, email: str | None, telefon: str | None) -> list[dict]:
    if not email and not telefon:
        return []
    where = []
    params: list = [mandant_id]
    if email:
        where.append("email = %s")
        params.append(email)
    if telefon:
        where.append("telefon = %s")
        params.append(telefon)
    rows = db.engine.query(
        f"SELECT id, name, email, telefon, notiz, created_at, updated_at FROM kunde "
        f"WHERE mandant_id = %s AND ({' OR '.join(where)})",
        tuple(params), mandant_id=mandant_id,
    )
    return rows


def create_kunde(mandant_id: str, name: str, email: str | None, telefon: str | None,
                 notiz: str | None) -> dict:
    return create_kunde_status(mandant_id, name, email, telefon, notiz, "aktiv")


def create_kunde_status(mandant_id: str, name: str, email: str | None, telefon: str | None,
                        notiz: str | None, status: str) -> dict:
    kid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO kunde (id, mandant_id, name, email, telefon, notiz, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (kid, mandant_id, name, email, telefon, notiz, status), mandant_id=mandant_id,
    )
    return get_kunde(mandant_id, kid)


def update_kunde(mandant_id: str, kunde_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_kunde(mandant_id, kunde_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, kunde_id]
    db.engine.command(
        f"UPDATE kunde SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_kunde(mandant_id, kunde_id)


def delete_kunde(mandant_id: str, kunde_id: str) -> None:
    db.engine.command(
        "DELETE FROM kunde WHERE mandant_id = %s AND id = %s",
        (mandant_id, kunde_id), mandant_id=mandant_id,
    )


def has_vorgaenge(mandant_id: str, kunde_id: str) -> bool:
    rows = db.engine.query(
        "SELECT 1 FROM vorgang WHERE mandant_id = %s AND kunde_id = %s LIMIT 1",
        (mandant_id, kunde_id), mandant_id=mandant_id,
    )
    return bool(rows)


# ponytail: keine rechnung-Tabelle existiert im Code (PROJ-8 "PDF-Rechnungen"
# ist laut features/INDEX.md noch "Planned"). Die AC verlangt eine Löschsperre
# auch bei bestehenden Rechnungen — sobald PROJ-8 die Tabelle anlegt, hier
# einen zweiten Check ergänzen (has_rechnungen). Siehe Abschlussbericht.


# --- Objekt -------------------------------------------------------------

def list_objekte(mandant_id: str, kunde_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, kunde_id, adresse, notiz, created_at FROM objekt "
        "WHERE mandant_id = %s AND kunde_id = %s ORDER BY created_at DESC",
        (mandant_id, kunde_id), mandant_id=mandant_id,
    )


def get_objekt(mandant_id: str, objekt_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, kunde_id, adresse, notiz, created_at FROM objekt "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, objekt_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_objekt(mandant_id: str, kunde_id: str, adresse: str, notiz: str | None) -> dict:
    oid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO objekt (id, mandant_id, kunde_id, adresse, notiz) "
        "VALUES (%s, %s, %s, %s, %s)",
        (oid, mandant_id, kunde_id, adresse, notiz), mandant_id=mandant_id,
    )
    return get_objekt(mandant_id, oid)
