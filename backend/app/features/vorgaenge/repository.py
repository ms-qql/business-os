from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


VORGANG_COLS = (
    "v.id, v.kunde_id, v.objekt_id, v.status, v.quelle, v.anliegen, v.notizen, "
    "v.zugewiesener_nutzer_id, v.ist_test, v.created_at, v.updated_at"
)
LIST_ITEM_SELECT = (
    f"SELECT {VORGANG_COLS}, k.name AS kunde_name, o.adresse AS objekt_adresse "
    "FROM vorgang v JOIN kunde k ON k.id = v.kunde_id "
    "LEFT JOIN objekt o ON o.id = v.objekt_id"
)


# --- Vorgang --------------------------------------------------------------

def list_vorgaenge(mandant_id: str, status: str | None, q: str | None, kunde_id: str | None,
                   zugewiesener_nutzer_id: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    where = ["v.mandant_id = %s", "v.ist_test = FALSE"]
    params: list = [mandant_id]
    if status:
        where.append("v.status = %s")
        params.append(status)
    if kunde_id:
        where.append("v.kunde_id = %s")
        params.append(kunde_id)
    if zugewiesener_nutzer_id:
        where.append("v.zugewiesener_nutzer_id = %s")
        params.append(zugewiesener_nutzer_id)
    if q:
        where.append("(LOWER(v.anliegen) LIKE LOWER(%s) OR LOWER(k.name) LIKE LOWER(%s))")
        like = f"%{q}%"
        params.extend([like, like])
    where_sql = " AND ".join(where)

    total_rows = db.engine.query(
        f"SELECT COUNT(*) AS c FROM vorgang v JOIN kunde k ON k.id = v.kunde_id WHERE {where_sql}",
        tuple(params), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0

    rows = db.engine.query(
        f"{LIST_ITEM_SELECT} WHERE {where_sql} ORDER BY v.created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (limit, offset), mandant_id=mandant_id,
    )
    return rows, total


def get_vorgang(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {VORGANG_COLS} FROM vorgang v WHERE v.mandant_id = %s AND v.id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_vorgang_list_item(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        f"{LIST_ITEM_SELECT} WHERE v.mandant_id = %s AND v.id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_vorgang(mandant_id: str, kunde_id: str, objekt_id: str | None, status: str,
                   quelle: str, anliegen: str, notizen: str | None) -> dict:
    vid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO vorgang (id, mandant_id, kunde_id, objekt_id, status, quelle, anliegen, notizen) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (vid, mandant_id, kunde_id, objekt_id, status, quelle, anliegen, notizen),
        mandant_id=mandant_id,
    )
    return get_vorgang(mandant_id, vid)


def update_vorgang(mandant_id: str, vorgang_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_vorgang(mandant_id, vorgang_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, vorgang_id]
    db.engine.command(
        f"UPDATE vorgang SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_vorgang(mandant_id, vorgang_id)


def assign_vorgang(mandant_id: str, vorgang_id: str, nutzer_id: str) -> dict | None:
    db.engine.command(
        "UPDATE vorgang SET zugewiesener_nutzer_id = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (nutzer_id, _now(), mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return get_vorgang(mandant_id, vorgang_id)


def list_nutzer_by_role(mandant_id: str, role: str, status: str | None = None) -> list[dict]:
    sql = "SELECT id, name, email, role, status FROM nutzer WHERE mandant_id = %s AND role = %s"
    params: list = [mandant_id, role]
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY name ASC"
    return db.engine.query(sql, tuple(params), mandant_id=mandant_id)


def get_nutzer(mandant_id: str, nutzer_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, name, role, status FROM nutzer WHERE mandant_id = %s AND id = %s",
        (mandant_id, nutzer_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


# --- Historie ---------------------------------------------------------

def add_historie(mandant_id: str, vorgang_id: str, ereignis: str, detail: str | None,
                 nutzer_id: str | None) -> None:
    db.engine.command(
        "INSERT INTO vorgang_historie (id, mandant_id, vorgang_id, ereignis, detail, nutzer_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, vorgang_id, ereignis, detail, nutzer_id),
        mandant_id=mandant_id,
    )


def list_historie(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, ereignis, detail, nutzer_id, created_at FROM vorgang_historie "
        "WHERE mandant_id = %s AND vorgang_id = %s ORDER BY created_at ASC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


# --- Dokumente ----------------------------------------------------------

def list_dokumente(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, vorgang_id, dateiname, objektpfad, content_type, groesse_bytes, "
        "hochgeladen_von, created_at FROM vorgang_dokument "
        "WHERE mandant_id = %s AND vorgang_id = %s ORDER BY created_at DESC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


def get_dokument(mandant_id: str, vorgang_id: str, dokument_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, vorgang_id, dateiname, objektpfad, content_type, groesse_bytes, "
        "hochgeladen_von, created_at FROM vorgang_dokument "
        "WHERE mandant_id = %s AND vorgang_id = %s AND id = %s",
        (mandant_id, vorgang_id, dokument_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_dokument(mandant_id: str, vorgang_id: str, dateiname: str, objektpfad: str,
                    content_type: str, groesse_bytes: int, hochgeladen_von: str | None) -> dict:
    did = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO vorgang_dokument (id, mandant_id, vorgang_id, dateiname, objektpfad, "
        "content_type, groesse_bytes, hochgeladen_von) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (did, mandant_id, vorgang_id, dateiname, objektpfad, content_type, groesse_bytes,
         hochgeladen_von),
        mandant_id=mandant_id,
    )
    return get_dokument(mandant_id, vorgang_id, did)


def delete_dokument(mandant_id: str, vorgang_id: str, dokument_id: str) -> None:
    db.engine.command(
        "DELETE FROM vorgang_dokument WHERE mandant_id = %s AND vorgang_id = %s AND id = %s",
        (mandant_id, vorgang_id, dokument_id), mandant_id=mandant_id,
    )


# --- Anfragen-Übernahme (PROJ-2 -> PROJ-3) -----------------------------

def get_anfrage(mandant_id: str, anfrage_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, name, kontaktweg, telefon, email, adresse, anliegen, dringlichkeit, "
        "zeitfenster, quelle, vorgang_id FROM anfrage WHERE mandant_id = %s AND id = %s",
        (mandant_id, anfrage_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_anfrage_fuer_vorgang(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, formular_einsendung_id FROM anfrage "
        "WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


def list_anfragebilder(mandant_id: str, anfrage_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, objektpfad, dateiname FROM anfragebild "
        "WHERE mandant_id = %s AND anfrage_id = %s",
        (mandant_id, anfrage_id), mandant_id=mandant_id,
    )


def mark_anfrage_uebernommen(mandant_id: str, anfrage_id: str, vorgang_id: str) -> None:
    db.engine.command(
        "UPDATE anfrage SET vorgang_id = %s WHERE mandant_id = %s AND id = %s",
        (vorgang_id, mandant_id, anfrage_id), mandant_id=mandant_id,
    )
