from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# Beginn/Ende werden einheitlich als UTC-ISO gespeichert (AC-7). Was der Browser
# als lokalen Wert schickt, wird vom Service bereits auf UTC normalisiert.
TERMIN_COLS = (
    "t.id, t.mandant_id, t.vorgang_id, t.beginn, t.ende, t.adresse, t.notiz, "
    "t.abgesagt_at, t.vorheriger_vorgang_status, t.created_at, t.updated_at"
)


# --- Termin ---------------------------------------------------------------


def create_termin(mandant_id: str, vorgang_id: str, beginn: str, ende: str,
                   adresse: str | None, notiz: str | None,
                   vorheriger_vorgang_status: str | None) -> dict:
    tid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO termin (id, mandant_id, vorgang_id, beginn, ende, adresse, notiz, "
        "vorheriger_vorgang_status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (tid, mandant_id, vorgang_id, beginn, ende, adresse, notiz,
         vorheriger_vorgang_status),
        mandant_id=mandant_id,
    )
    return get_termin_row(mandant_id, tid)


def get_termin_row(mandant_id: str, termin_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {TERMIN_COLS}, v.anliegen AS anliegen FROM termin t "
        f"JOIN vorgang v ON v.id = t.vorgang_id "
        f"WHERE t.mandant_id = %s AND t.id = %s",
        (mandant_id, termin_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_termine_rows(mandant_id: str, von: str, bis: str,
                      nutzer_ids: list[str] | None) -> list[dict]:
    sql = (
        f"SELECT {TERMIN_COLS}, v.anliegen AS anliegen FROM termin t "
        f"JOIN vorgang v ON v.id = t.vorgang_id "
        f"WHERE t.mandant_id = %s AND t.beginn < %s AND t.ende > %s"
    )
    params: list = [mandant_id, bis, von]
    if nutzer_ids:
        in_clause = ",".join(["%s"] * len(nutzer_ids))
        sql += (f" AND t.id IN (SELECT tz.termin_id FROM termin_zuweisung tz "
                f"WHERE tz.mandant_id = %s AND tz.nutzer_id IN ({in_clause}))")
        params.append(mandant_id)
        params.extend(nutzer_ids)
    sql += " ORDER BY t.beginn ASC"
    return db.engine.query(sql, tuple(params), mandant_id=mandant_id)


def count_termine_rows(mandant_id: str, von: str, bis: str,
                       nutzer_ids: list[str] | None) -> int:
    sql = ("SELECT COUNT(*) AS c FROM termin t WHERE t.mandant_id = %s "
           "AND t.beginn < %s AND t.ende > %s")
    params: list = [mandant_id, bis, von]
    if nutzer_ids:
        in_clause = ",".join(["%s"] * len(nutzer_ids))
        sql += (f" AND t.id IN (SELECT tz.termin_id FROM termin_zuweisung tz "
                f"WHERE tz.mandant_id = %s AND tz.nutzer_id IN ({in_clause}))")
        params.append(mandant_id)
        params.extend(nutzer_ids)
    rows = db.engine.query(sql, tuple(params), mandant_id=mandant_id)
    return int(rows[0]["c"]) if rows else 0


def update_termin(mandant_id: str, termin_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_termin_row(mandant_id, termin_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, termin_id]
    db.engine.command(
        f"UPDATE termin SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_termin_row(mandant_id, termin_id)


def cancel_termin(mandant_id: str, termin_id: str, abgesagt_at: str) -> dict | None:
    db.engine.command(
        "UPDATE termin SET abgesagt_at = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (abgesagt_at, _now(), mandant_id, termin_id), mandant_id=mandant_id,
    )
    return get_termin_row(mandant_id, termin_id)


def count_open_termine(mandant_id: str, vorgang_id: str,
                       exclude_termin_id: str | None = None) -> int:
    sql = ("SELECT COUNT(*) AS c FROM termin WHERE mandant_id = %s AND vorgang_id = %s "
           "AND abgesagt_at IS NULL")
    params: list = [mandant_id, vorgang_id]
    if exclude_termin_id:
        sql += " AND id != %s"
        params.append(exclude_termin_id)
    rows = db.engine.query(sql, tuple(params), mandant_id=mandant_id)
    return int(rows[0]["c"]) if rows else 0


# --- Zuweisungen ---------------------------------------------------------


def list_zuweisungen(mandant_id: str, termin_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT tz.nutzer_id AS nutzer_id, n.name AS name, "
        "(n.status = 'active') AS aktiv FROM termin_zuweisung tz "
        "JOIN nutzer n ON n.id = tz.nutzer_id "
        "WHERE tz.mandant_id = %s AND tz.termin_id = %s ORDER BY n.name ASC",
        (mandant_id, termin_id), mandant_id=mandant_id,
    )


def list_zuweisungen_for_termine(mandant_id: str, termin_ids: list[str]) -> list[dict]:
    if not termin_ids:
        return []
    in_clause = ",".join(["%s"] * len(termin_ids))
    return db.engine.query(
        "SELECT tz.termin_id AS termin_id, tz.nutzer_id AS nutzer_id, n.name AS name, "
        "(n.status = 'active') AS aktiv FROM termin_zuweisung tz "
        f"JOIN nutzer n ON n.id = tz.nutzer_id "
        f"WHERE tz.mandant_id = %s AND tz.termin_id IN ({in_clause})",
        (mandant_id, *termin_ids), mandant_id=mandant_id,
    )


def add_zuweisung(mandant_id: str, termin_id: str, nutzer_id: str) -> dict | None:
    zid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO termin_zuweisung (id, mandant_id, termin_id, nutzer_id, aktiv) "
        "VALUES (%s, %s, %s, %s, TRUE) "
        "ON CONFLICT (termin_id, nutzer_id) DO UPDATE SET aktiv = TRUE",
        (zid, mandant_id, termin_id, nutzer_id), mandant_id=mandant_id,
    )
    rows = db.engine.query(
        "SELECT n.name AS name, (n.status = 'active') AS aktiv FROM nutzer n "
        "WHERE n.id = %s", (nutzer_id,), mandant_id=mandant_id,
    )
    return {"nutzer_id": nutzer_id, "name": rows[0]["name"] if rows else "",
            "aktiv": bool(rows[0]["aktiv"]) if rows else False}


def remove_zuweisung(mandant_id: str, termin_id: str, nutzer_id: str) -> int:
    return db.engine.command(
        "DELETE FROM termin_zuweisung WHERE mandant_id = %s AND termin_id = %s AND nutzer_id = %s",
        (mandant_id, termin_id, nutzer_id), mandant_id=mandant_id,
    )


def termin_gehoert_zu_nutzer(mandant_id: str, termin_id: str, nutzer_id: str) -> bool:
    rows = db.engine.query(
        "SELECT 1 FROM termin_zuweisung WHERE mandant_id = %s AND termin_id = %s AND nutzer_id = %s",
        (mandant_id, termin_id, nutzer_id), mandant_id=mandant_id,
    )
    return bool(rows)


# --- Konfliktprüfung (AC-4, nicht-blockierend) ---------------------------


def find_konflikt_monteure(mandant_id: str, nutzer_ids: list[str], beginn: str, ende: str,
                           exclude_termin_id: str | None = None) -> list[str]:
    if not nutzer_ids:
        return []
    in_clause = ",".join(["%s"] * len(nutzer_ids))
    sql = (
        "SELECT DISTINCT tz.nutzer_id AS nutzer_id FROM termin_zuweisung tz "
        "JOIN termin t ON t.id = tz.termin_id "
        "WHERE tz.mandant_id = %s AND tz.nutzer_id IN (" + in_clause + ") "
        "AND t.abgesagt_at IS NULL AND t.beginn < %s AND t.ende > %s"
    )
    params: list = [mandant_id, *nutzer_ids, ende, beginn]
    if exclude_termin_id:
        sql += " AND tz.termin_id != %s"
        params.append(exclude_termin_id)
    rows = db.engine.query(sql, tuple(params), mandant_id=mandant_id)
    return [r["nutzer_id"] for r in rows]


# --- Vorgang/Kunde für eingebetteten Kontakt (AC-5) ----------------------


def list_termine_by_vorgang(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {TERMIN_COLS}, v.anliegen AS anliegen FROM termin t "
        f"JOIN vorgang v ON v.id = t.vorgang_id "
        f"WHERE t.mandant_id = %s AND t.vorgang_id = %s ORDER BY t.beginn DESC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


def list_eigene_termin_ids(mandant_id: str, nutzer_id: str) -> list[str]:
    rows = db.engine.query(
        "SELECT DISTINCT termin_id FROM termin_zuweisung "
        "WHERE mandant_id = %s AND nutzer_id = %s",
        (mandant_id, nutzer_id), mandant_id=mandant_id,
    )
    return [r["termin_id"] for r in rows]


def get_kontakt_for_vorgang(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT k.name AS name, k.telefon AS telefon, k.email AS email "
        "FROM vorgang v JOIN kunde k ON k.id = v.kunde_id "
        "WHERE v.mandant_id = %s AND v.id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None
