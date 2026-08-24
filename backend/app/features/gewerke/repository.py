from __future__ import annotations

import uuid

from app import db


def _now() -> str:
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Kategorien ----------------------------------------------------------

KATEGORIE_COLS = "id, mandant_id, name, created_at, updated_at"


def list_kategorien(mandant_id: str) -> list[dict]:
    # Zählt die dem Mandanten zugeordneten Gewerke je Kategorie (PROJ-22 BUG-3).
    # Gewerke ohne Kategorie (kategorie_id IS NULL) werden nicht mitgezählt;
    # der LEFT JOIN + GROUP BY liefert auch für leere Kategorien anzahl_gewerke = 0.
    return db.engine.query(
        "SELECT k.id, k.mandant_id, k.name, k.created_at, k.updated_at, "
        "COUNT(g.id) AS anzahl_gewerke "
        "FROM gewerk_kategorie k "
        "LEFT JOIN gewerk g ON g.kategorie_id = k.id AND g.mandant_id = k.mandant_id "
        "WHERE k.mandant_id = %s "
        "GROUP BY k.id, k.mandant_id, k.name, k.created_at, k.updated_at "
        "ORDER BY k.name ASC",
        (mandant_id,), mandant_id=mandant_id,
    )


def find_kategorie_by_name(mandant_id: str, name: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {KATEGORIE_COLS} FROM gewerk_kategorie WHERE mandant_id = %s AND name = %s",
        (mandant_id, name), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_kategorie(mandant_id: str, kategorie_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {KATEGORIE_COLS} FROM gewerk_kategorie WHERE mandant_id = %s AND id = %s",
        (mandant_id, kategorie_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_kategorie(mandant_id: str, name: str, tx=None) -> dict | None:
    kid = str(uuid.uuid4())
    if tx is None:
        db.engine.command(
            "INSERT INTO gewerk_kategorie (id, mandant_id, name) VALUES (%s, %s, %s)",
            (kid, mandant_id, name), mandant_id=mandant_id,
        )
        return get_kategorie(mandant_id, kid)
    tx.command(
        "INSERT INTO gewerk_kategorie (id, mandant_id, name) VALUES (%s, %s, %s)",
        (kid, mandant_id, name),
    )
    rows = tx.query(
        f"SELECT {KATEGORIE_COLS} FROM gewerk_kategorie WHERE mandant_id = %s AND id = %s",
        (mandant_id, kid),
    )
    return rows[0] if rows else None


def rename_kategorie(mandant_id: str, kategorie_id: str, name: str) -> dict | None:
    db.engine.command(
        "UPDATE gewerk_kategorie SET name = %s, updated_at = %s WHERE mandant_id = %s AND id = %s",
        (name, _now(), mandant_id, kategorie_id), mandant_id=mandant_id,
    )
    return get_kategorie(mandant_id, kategorie_id)


def delete_kategorie(mandant_id: str, kategorie_id: str) -> None:
    # Löschen nur erlaubt, wenn kein Gewerk zugeordnet ist (Tech Design).
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM gewerk WHERE mandant_id = %s AND kategorie_id = %s",
        (mandant_id, kategorie_id), mandant_id=mandant_id,
    )
    if int(rows[0]["c"]) > 0:
        from app.errors import ConflictError

        raise ConflictError(
            "Die Kategorie enthält noch Gewerke und kann nicht gelöscht werden."
        )
    db.engine.command(
        "DELETE FROM gewerk_kategorie WHERE mandant_id = %s AND id = %s",
        (mandant_id, kategorie_id), mandant_id=mandant_id,
    )


# --- Gewerke -------------------------------------------------------------

GEWERK_COLS = (
    "id, mandant_id, kategorie_id, bezeichnung, langbeschreibung, einheit, "
    "kalkulationsart, steuersatz, created_at, updated_at"
)


def list_gewerke(mandant_id: str, suchbegriff: str | None = None,
                 kategorie_id: str | None = None) -> list[dict]:
    clauses = ["mandant_id = %s"]
    params: list = [mandant_id]
    if suchbegriff:
        clauses.append("bezeichnung ILIKE %s")
        params.append(f"%{suchbegriff}%")
    if kategorie_id:
        clauses.append("kategorie_id = %s")
        params.append(kategorie_id)
    return db.engine.query(
        f"SELECT {GEWERK_COLS} FROM gewerk WHERE {' AND '.join(clauses)} "
        f"ORDER BY bezeichnung ASC",
        tuple(params), mandant_id=mandant_id,
    )


def get_gewerk(mandant_id: str, gewerk_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {GEWERK_COLS} FROM gewerk WHERE mandant_id = %s AND id = %s",
        (mandant_id, gewerk_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def find_gewerk_by_bezeichnung_einheit(mandant_id: str, bezeichnung: str,
                                       einheit: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {GEWERK_COLS} FROM gewerk WHERE mandant_id = %s "
        f"AND bezeichnung = %s AND einheit = %s",
        (mandant_id, bezeichnung, einheit), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_gewerk(mandant_id: str, *, kategorie_id: str | None, bezeichnung: str,
                  langbeschreibung: str | None, einheit: str, kalkulationsart: str,
                  steuersatz: float, tx=None) -> dict | None:
    gid = str(uuid.uuid4())
    if tx is None:
        db.engine.command(
            "INSERT INTO gewerk (id, mandant_id, kategorie_id, bezeichnung, "
            "langbeschreibung, einheit, kalkulationsart, steuersatz) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (gid, mandant_id, kategorie_id, bezeichnung, langbeschreibung, einheit,
             kalkulationsart, steuersatz),
            mandant_id=mandant_id,
        )
        return get_gewerk(mandant_id, gid)
    tx.command(
        "INSERT INTO gewerk (id, mandant_id, kategorie_id, bezeichnung, "
        "langbeschreibung, einheit, kalkulationsart, steuersatz) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (gid, mandant_id, kategorie_id, bezeichnung, langbeschreibung, einheit,
         kalkulationsart, steuersatz),
    )
    rows = tx.query(
        f"SELECT {GEWERK_COLS} FROM gewerk WHERE mandant_id = %s AND id = %s",
        (mandant_id, gid),
    )
    return rows[0] if rows else None


def update_gewerk(mandant_id: str, gewerk_id: str, fields: dict) -> dict | None:
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, gewerk_id]
    db.engine.command(
        f"UPDATE gewerk SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_gewerk(mandant_id, gewerk_id)


def delete_gewerk(mandant_id: str, gewerk_id: str) -> None:
    # Kostenzeilen kaskadieren per FK (ON DELETE CASCADE).
    db.engine.command(
        "DELETE FROM gewerk WHERE mandant_id = %s AND id = %s",
        (mandant_id, gewerk_id), mandant_id=mandant_id,
    )


def count_gewerke(mandant_id: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM gewerk WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


# --- Kostenzeilen --------------------------------------------------------

KOSTENZEILE_COLS = (
    "id, mandant_id, gewerk_id, kostenart, menge, einheit, "
    "ek_einzelpreis, zuschlag_prozent, created_at, updated_at"
)


def list_kostenzeilen(mandant_id: str, gewerk_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {KOSTENZEILE_COLS} FROM gewerk_kostenzeile "
        f"WHERE mandant_id = %s AND gewerk_id = %s ORDER BY created_at ASC",
        (mandant_id, gewerk_id), mandant_id=mandant_id,
    )


def create_kostenzeile(mandant_id: str, gewerk_id: str, *, kostenart: str,
                       menge: float, einheit: str, ek_einzelpreis: float,
                       zuschlag_prozent: float) -> dict:
    kid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO gewerk_kostenzeile (id, mandant_id, gewerk_id, kostenart, "
        "menge, einheit, ek_einzelpreis, zuschlag_prozent) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (kid, mandant_id, gewerk_id, kostenart, menge, einheit, ek_einzelpreis,
         zuschlag_prozent),
        mandant_id=mandant_id,
    )
    return get_kostenzeile(mandant_id, kid)


def get_kostenzeile(mandant_id: str, kostenzeile_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {KOSTENZEILE_COLS} FROM gewerk_kostenzeile "
        f"WHERE mandant_id = %s AND id = %s",
        (mandant_id, kostenzeile_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def replace_kostenzeilen(mandant_id: str, gewerk_id: str, zeilen: list[dict],
                         tx=None) -> list[dict]:
    """Ersetzt den vollständigen Kostenzeilensatz eines Gewerks atomar (nur
    über den Gewerk-Editor-Pfad, nie lose)."""
    if tx is None:
        with db.engine.transaction(mandant_id=mandant_id) as ctx:
            return _replace_kostenzeilen_in(ctx, mandant_id, gewerk_id, zeilen)
    return _replace_kostenzeilen_in(tx, mandant_id, gewerk_id, zeilen)


def _replace_kostenzeilen_in(tx, mandant_id: str, gewerk_id: str, zeilen: list[dict]) -> list[dict]:
    tx.command(
        "DELETE FROM gewerk_kostenzeile WHERE mandant_id = %s AND gewerk_id = %s",
        (mandant_id, gewerk_id),
    )
    erzeugt = []
    for z in zeilen:
        kid = str(uuid.uuid4())
        tx.command(
            "INSERT INTO gewerk_kostenzeile (id, mandant_id, gewerk_id, kostenart, "
            "menge, einheit, ek_einzelpreis, zuschlag_prozent) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (kid, mandant_id, gewerk_id, z["kostenart"], z["menge"], z["einheit"],
             z["ek_einzelpreis"], z["zuschlag_prozent"]),
        )
        rows = tx.query(
            f"SELECT {KOSTENZEILE_COLS} FROM gewerk_kostenzeile "
            f"WHERE mandant_id = %s AND id = %s",
            (mandant_id, kid),
        )
        if rows:
            erzeugt.append(rows[0])
    return erzeugt


# --- Angebot-Position (Snapshot aus Gewerk) -------------------------------

POSITION_COLS = (
    "id, mandant_id, angebot_id, bezeichnung, menge, einheit, einzelpreis, steuersatz, "
    "rabatt_typ, rabatt_wert, sortierung, kalkulierter_einzelpreis, "
    "preis_override_begruendung, created_at, updated_at"
)


def get_position(mandant_id: str, angebot_id: str, position_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {POSITION_COLS} FROM angebot_position "
        f"WHERE mandant_id = %s AND angebot_id = %s AND id = %s",
        (mandant_id, angebot_id, position_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_position_aus_gewerk(mandant_id: str, angebot_id: str, *, bezeichnung: str,
                               einheit: str, steuersatz: float, menge: float,
                               einzelpreis: float, kalkulierter_einzelpreis: float,
                               sortierung: int) -> dict:
    pid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO angebot_position (id, mandant_id, angebot_id, bezeichnung, menge, "
        "einheit, einzelpreis, steuersatz, rabatt_typ, rabatt_wert, sortierung, "
        "kalkulierter_einzelpreis) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'prozent', 0, %s, %s)",
        (pid, mandant_id, angebot_id, bezeichnung, menge, einheit, einzelpreis,
         steuersatz, sortierung, kalkulierter_einzelpreis),
        mandant_id=mandant_id,
    )
    return get_position(mandant_id, angebot_id, pid)


def update_position_override(mandant_id: str, angebot_id: str, position_id: str,
                             fields: dict) -> dict | None:
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, angebot_id, position_id]
    db.engine.command(
        f"UPDATE angebot_position SET {', '.join(sets)} "
        f"WHERE mandant_id = %s AND angebot_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_position(mandant_id, angebot_id, position_id)
