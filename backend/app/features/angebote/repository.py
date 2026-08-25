from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Nummernkreis (siehe Tech Design PROJ-5, Abschnitt E) -----------------

def next_angebot_nummer(mandant_id: str) -> str:
    """Zieht die nächste Angebotsnummer für den Mandanten, atomar innerhalb
    einer eigenen Transaktion (SELECT ... FOR UPDATE, dann Hochzählen). Rollt
    die Transaktion zurück, entsteht keine Nummernlücke, weil der Zähler dann
    ebenfalls nicht erhöht wird."""
    jahr = datetime.datetime.now(datetime.timezone.utc).year
    with db.engine.transaction(mandant_id=mandant_id) as tx:
        if db.engine.is_postgres:
            rows = tx.query(
                "SELECT letzte_nummer FROM angebot_nummernkreis WHERE mandant_id = %s FOR UPDATE",
                (mandant_id,),
            )
        else:
            rows = tx.query(
                "SELECT letzte_nummer FROM angebot_nummernkreis WHERE mandant_id = %s",
                (mandant_id,),
            )
        if rows:
            naechste = int(rows[0]["letzte_nummer"]) + 1
            tx.command(
                "UPDATE angebot_nummernkreis SET letzte_nummer = %s WHERE mandant_id = %s",
                (naechste, mandant_id),
            )
        else:
            naechste = 1
            tx.command(
                "INSERT INTO angebot_nummernkreis (mandant_id, letzte_nummer) VALUES (%s, %s)",
                (mandant_id, naechste),
            )
    return f"AN-{jahr}-{naechste:04d}"


# --- Angebot ----------------------------------------------------------------

ANGEBOT_COLS = (
    "id, mandant_id, vorgang_id, angebot_nummer, version, vorgaenger_angebot_id, status, "
    "gueltig_bis, freitext, netto_summe, steuer_summe, brutto_summe, dokument_id, "
    "empfaenger_email, versendet_at, versendet_von, created_at, updated_at"
)


def create_angebot(mandant_id: str, vorgang_id: str, version: int,
                   vorgaenger_angebot_id: str | None, angebot_nummer: str) -> dict:
    aid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO angebot (id, mandant_id, vorgang_id, angebot_nummer, version, "
        "vorgaenger_angebot_id, status) VALUES (%s, %s, %s, %s, %s, %s, 'entwurf')",
        (aid, mandant_id, vorgang_id, angebot_nummer, version, vorgaenger_angebot_id),
        mandant_id=mandant_id,
    )
    return get_angebot(mandant_id, aid)


def get_angebot(mandant_id: str, angebot_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {ANGEBOT_COLS} FROM angebot WHERE mandant_id = %s AND id = %s",
        (mandant_id, angebot_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_angebote(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {ANGEBOT_COLS} FROM angebot WHERE mandant_id = %s AND vorgang_id = %s "
        "ORDER BY created_at DESC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


def update_angebot(mandant_id: str, angebot_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_angebot(mandant_id, angebot_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, angebot_id]
    db.engine.command(
        f"UPDATE angebot SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_angebot(mandant_id, angebot_id)


def mark_versendet(mandant_id: str, angebot_id: str, empfaenger_email: str, versendet_von: str,
                   netto_summe: float, steuer_summe: float, brutto_summe: float) -> dict | None:
    db.engine.command(
        "UPDATE angebot SET status = 'versendet', empfaenger_email = %s, versendet_von = %s, "
        "versendet_at = %s, netto_summe = %s, steuer_summe = %s, brutto_summe = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (empfaenger_email, versendet_von, _now(), netto_summe, steuer_summe, brutto_summe, _now(),
         mandant_id, angebot_id),
        mandant_id=mandant_id,
    )
    return get_angebot(mandant_id, angebot_id)


# --- Positionen ---------------------------------------------------------

POSITION_COLS = (
    "id, mandant_id, angebot_id, bezeichnung, menge, einheit, einzelpreis, steuersatz, "
    "rabatt_typ, rabatt_wert, sortierung, kalkulierter_einzelpreis, "
    "preis_override_begruendung, created_at, updated_at"
)


def list_positionen(mandant_id: str, angebot_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {POSITION_COLS} FROM angebot_position WHERE mandant_id = %s AND angebot_id = %s "
        "ORDER BY sortierung ASC, created_at ASC",
        (mandant_id, angebot_id), mandant_id=mandant_id,
    )


def get_position(mandant_id: str, angebot_id: str, position_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {POSITION_COLS} FROM angebot_position WHERE mandant_id = %s "
        f"AND angebot_id = %s AND id = %s",
        (mandant_id, angebot_id, position_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_position(mandant_id: str, angebot_id: str, bezeichnung: str, menge: float, einheit: str,
                    einzelpreis: float, steuersatz: float, rabatt_typ: str, rabatt_wert: float,
                    sortierung: int, kalkulierter_einzelpreis: float | None = None) -> dict:
    pid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO angebot_position (id, mandant_id, angebot_id, bezeichnung, menge, einheit, "
        "einzelpreis, steuersatz, rabatt_typ, rabatt_wert, sortierung, kalkulierter_einzelpreis) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (pid, mandant_id, angebot_id, bezeichnung, menge, einheit, einzelpreis, steuersatz,
         rabatt_typ, rabatt_wert, sortierung, kalkulierter_einzelpreis),
        mandant_id=mandant_id,
    )
    return get_position(mandant_id, angebot_id, pid)


def update_position(mandant_id: str, angebot_id: str, position_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_position(mandant_id, angebot_id, position_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, angebot_id, position_id]
    db.engine.command(
        f"UPDATE angebot_position SET {', '.join(sets)} "
        "WHERE mandant_id = %s AND angebot_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_position(mandant_id, angebot_id, position_id)


def delete_position(mandant_id: str, angebot_id: str, position_id: str) -> None:
    db.engine.command(
        "DELETE FROM angebot_position WHERE mandant_id = %s AND angebot_id = %s AND id = %s",
        (mandant_id, angebot_id, position_id), mandant_id=mandant_id,
    )


# --- Stammdaten für die PDF-Vorlage -----------------------------------------

def get_mandant_name(mandant_id: str) -> str:
    rows = db.engine.query("SELECT name FROM mandanten WHERE id = %s", (mandant_id,),
                           mandant_id=mandant_id)
    return rows[0]["name"] if rows else ""
