from __future__ import annotations

import datetime
import json
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Nummernkreis (siehe Tech Design PROJ-8, ADR-8-3) --------------------

def next_rechnung_nummer(mandant_id: str) -> str:
    """Zieht die nächste Rechnungsnummer für den Mandanten, atomar innerhalb
    einer eigenen Transaktion (SELECT ... FOR UPDATE, dann Hochzählen). Die
    Nummer wird schon beim Entwurf reserviert (sichtbar + nach Storno nie
    wiederverwendet); der zusätzliche Unique-Constraint auf
    (mandant_id, rechnungsnummer) verhindert parallele Kollisionen."""
    jahr = datetime.datetime.now(datetime.timezone.utc).year
    with db.engine.transaction(mandant_id=mandant_id) as tx:
        if db.engine.is_postgres:
            rows = tx.query(
                "SELECT letzte_nummer FROM rechnung_nummernkreis WHERE mandant_id = %s FOR UPDATE",
                (mandant_id,),
            )
        else:
            rows = tx.query(
                "SELECT letzte_nummer FROM rechnung_nummernkreis WHERE mandant_id = %s",
                (mandant_id,),
            )
        if rows:
            naechste = int(rows[0]["letzte_nummer"]) + 1
            tx.command(
                "UPDATE rechnung_nummernkreis SET letzte_nummer = %s WHERE mandant_id = %s",
                (naechste, mandant_id),
            )
        else:
            naechste = 1
            tx.command(
                "INSERT INTO rechnung_nummernkreis (mandant_id, letzte_nummer) VALUES (%s, %s)",
                (mandant_id, naechste),
            )
    return f"RE-{jahr}-{naechste:04d}"


# --- Rechnungsstellerprofil ----------------------------------------------

def get_rechnungsstellerprofil(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT firma_name, strasse, hausnummer, plz, ort, steuernummer, ust_id, "
        "updated_at FROM rechnungsstellerprofil WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def upsert_rechnungsstellerprofil(mandant_id: str, profil: dict) -> dict:
    fields = ["firma_name", "strasse", "hausnummer", "plz", "ort",
              "steuernummer", "ust_id", "updated_at"]
    placeholders = ", ".join(["%s"] * len(fields))
    cols = ", ".join(fields)
    values = [profil["firma_name"], profil["strasse"], profil["hausnummer"], profil["plz"],
              profil["ort"], profil.get("steuernummer"), profil.get("ust_id"), _now()]
    db.engine.command(
        f"INSERT INTO rechnungsstellerprofil (mandant_id, {cols}) VALUES (%s, {placeholders}) "
        "ON CONFLICT (mandant_id) DO UPDATE SET "
        f"{', '.join(f'{c} = EXCLUDED.{c}' for c in fields)}",
        (mandant_id, *values), mandant_id=mandant_id,
    )
    return get_rechnungsstellerprofil(mandant_id)


# --- Rechnung ------------------------------------------------------------

RECHNUNG_COLS = (
    "id, mandant_id, vorgang_id, rechnungsnummer, rechnungsdatum, leistungsdatum, "
    "status, zahlungsstatus, netto_summe, steuer_summe, brutto_summe, empfaenger_email, "
    "fassung_id, freigabe_vorbereitet_at, versendet_at, versendet_von, storniert_at, "
    "storniert_von, created_at, updated_at"
)


def create_rechnung(mandant_id: str, vorgang_id: str, rechnungsnummer: str,
                    rechnungsdatum: str, leistungsdatum: str) -> dict:
    rid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO rechnung (id, mandant_id, vorgang_id, rechnungsnummer, "
        "rechnungsdatum, leistungsdatum, status) VALUES (%s, %s, %s, %s, %s, %s, 'entwurf')",
        (rid, mandant_id, vorgang_id, rechnungsnummer, rechnungsdatum, leistungsdatum),
        mandant_id=mandant_id,
    )
    return get_rechnung(mandant_id, rid)


def get_rechnung(mandant_id: str, rechnung_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {RECHNUNG_COLS} FROM rechnung WHERE mandant_id = %s AND id = %s",
        (mandant_id, rechnung_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_rechnungen(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {RECHNUNG_COLS} FROM rechnung WHERE mandant_id = %s AND vorgang_id = %s "
        "ORDER BY created_at DESC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )


def update_rechnung(mandant_id: str, rechnung_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_rechnung(mandant_id, rechnung_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, rechnung_id]
    db.engine.command(
        f"UPDATE rechnung SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_rechnung(mandant_id, rechnung_id)


def set_freigabe_vorbereitet(mandant_id: str, rechnung_id: str, empfaenger_email: str,
                             netto: float, steuer: float, brutto: float) -> dict | None:
    return update_rechnung(mandant_id, rechnung_id, {
        "empfaenger_email": empfaenger_email,
        "netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto,
        "freigabe_vorbereitet_at": _now(),
    })


def mark_versendet(mandant_id: str, rechnung_id: str, fassung_id: str,
                   empfaenger_email: str, versendet_von: str,
                   netto: float, steuer: float, brutto: float) -> dict | None:
    db.engine.command(
        "UPDATE rechnung SET status = 'versendet', fassung_id = %s, empfaenger_email = %s, "
        "versendet_von = %s, versendet_at = %s, netto_summe = %s, steuer_summe = %s, "
        "brutto_summe = %s, updated_at = %s WHERE mandant_id = %s AND id = %s",
        (fassung_id, empfaenger_email, versendet_von, _now(), netto, steuer, brutto, _now(),
         mandant_id, rechnung_id),
        mandant_id=mandant_id,
    )
    return get_rechnung(mandant_id, rechnung_id)


def mark_storniert(mandant_id: str, rechnung_id: str, storniert_von: str) -> dict | None:
    db.engine.command(
        "UPDATE rechnung SET status = 'storniert', zahlungsstatus = 'Storniert', "
        "storniert_at = %s, storniert_von = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (_now(), storniert_von, _now(), mandant_id, rechnung_id),
        mandant_id=mandant_id,
    )
    return get_rechnung(mandant_id, rechnung_id)


def set_zahlungsstatus(mandant_id: str, rechnung_id: str, zahlungsstatus: str) -> dict | None:
    return update_rechnung(mandant_id, rechnung_id, {"zahlungsstatus": zahlungsstatus})


# --- Positionen ---------------------------------------------------------

POSITION_COLS = (
    "id, mandant_id, rechnung_id, bezeichnung, menge, einheit, netto_einzelpreis, "
    "steuersatz, sortierung, created_at, updated_at"
)


def list_positionen(mandant_id: str, rechnung_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {POSITION_COLS} FROM rechnung_position "
        "WHERE mandant_id = %s AND rechnung_id = %s ORDER BY sortierung ASC, created_at ASC",
        (mandant_id, rechnung_id), mandant_id=mandant_id,
    )


def get_position(mandant_id: str, rechnung_id: str, position_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {POSITION_COLS} FROM rechnung_position "
        "WHERE mandant_id = %s AND rechnung_id = %s AND id = %s",
        (mandant_id, rechnung_id, position_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_position(mandant_id: str, rechnung_id: str, bezeichnung: str, menge: float,
                    einheit: str, netto_einzelpreis: float, steuersatz: float,
                    sortierung: int) -> dict:
    pid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO rechnung_position (id, mandant_id, rechnung_id, bezeichnung, menge, "
        "einheit, netto_einzelpreis, steuersatz, sortierung) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (pid, mandant_id, rechnung_id, bezeichnung, menge, einheit, netto_einzelpreis,
         steuersatz, sortierung),
        mandant_id=mandant_id,
    )
    return get_position(mandant_id, rechnung_id, pid)


def update_position(mandant_id: str, rechnung_id: str, position_id: str, fields: dict) -> dict | None:
    if not fields:
        return get_position(mandant_id, rechnung_id, position_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, rechnung_id, position_id]
    db.engine.command(
        f"UPDATE rechnung_position SET {', '.join(sets)} "
        "WHERE mandant_id = %s AND rechnung_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_position(mandant_id, rechnung_id, position_id)


def delete_position(mandant_id: str, rechnung_id: str, position_id: str) -> None:
    db.engine.command(
        "DELETE FROM rechnung_position WHERE mandant_id = %s AND rechnung_id = %s AND id = %s",
        (mandant_id, rechnung_id, position_id), mandant_id=mandant_id,
    )


# --- Fassung (unveränderlicher Beleg) ------------------------------------

def create_fassung(mandant_id: str, rechnung_id: str, rechnungsnummer: str,
                   kopf: dict, rechnungssteller: dict, kunde: dict, objekt: dict,
                   positionen: list[dict], summen: dict, dokument_id: str | None) -> dict:
    fid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO rechnung_fassung (id, mandant_id, rechnung_id, rechnungsnummer, "
        "kopf_json, rechnungssteller_json, kunde_json, objekt_json, positionen_json, "
        "summen_json, dokument_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (fid, mandant_id, rechnung_id, rechnungsnummer, json.dumps(kopf, ensure_ascii=False),
         json.dumps(rechnungssteller, ensure_ascii=False), json.dumps(kunde, ensure_ascii=False),
         json.dumps(objekt, ensure_ascii=False), json.dumps(positionen, ensure_ascii=False),
         json.dumps(summen, ensure_ascii=False), dokument_id),
        mandant_id=mandant_id,
    )
    return get_fassung(mandant_id, fid)


def get_fassung(mandant_id: str, fassung_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, rechnung_id, rechnungsnummer, kopf_json, "
        "rechnungssteller_json, kunde_json, objekt_json, positionen_json, summen_json, "
        "dokument_id, created_at FROM rechnung_fassung WHERE mandant_id = %s AND id = %s",
        (mandant_id, fassung_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


# --- Stammdaten für die PDF-Vorlage --------------------------------------

def get_mandant_name(mandant_id: str) -> str:
    rows = db.engine.query("SELECT name FROM mandanten WHERE id = %s", (mandant_id,),
                           mandant_id=mandant_id)
    return rows[0]["name"] if rows else ""
