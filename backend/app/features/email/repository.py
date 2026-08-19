from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Postfach-Konto --------------------------------------------------------

def get_konto(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, imap_host, imap_port, imap_user, imap_passwort, imap_tls, "
        "smtp_host, smtp_port, smtp_user, smtp_passwort, smtp_tls, "
        "letzter_abruf_status, letzter_abruf_fehler_text, letzter_abruf_at, "
        "konfiguration_version "
        "FROM email_konto WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def upsert_konto(mandant_id: str, imap_host: str, imap_port: int, imap_user: str,
                 imap_passwort: str, imap_tls: bool, smtp_host: str, smtp_port: int,
                 smtp_user: str | None, smtp_passwort: str | None, smtp_tls: bool) -> dict:
    existing = get_konto(mandant_id)
    if existing:
        db.engine.command(
            "UPDATE email_konto SET imap_host=%s, imap_port=%s, imap_user=%s, imap_passwort=%s, "
            "imap_tls=%s, smtp_host=%s, smtp_port=%s, smtp_user=%s, smtp_passwort=%s, "
            "smtp_tls=%s, updated_at=%s, konfiguration_version = konfiguration_version + 1 "
            "WHERE mandant_id=%s",
            (imap_host, imap_port, imap_user, imap_passwort, imap_tls, smtp_host, smtp_port,
             smtp_user, smtp_passwort, smtp_tls, _now(), mandant_id),
            mandant_id=mandant_id,
        )
    else:
        db.engine.command(
            "INSERT INTO email_konto (id, mandant_id, imap_host, imap_port, imap_user, "
            "imap_passwort, imap_tls, smtp_host, smtp_port, smtp_user, smtp_passwort, smtp_tls) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), mandant_id, imap_host, imap_port, imap_user, imap_passwort,
             imap_tls, smtp_host, smtp_port, smtp_user, smtp_passwort, smtp_tls),
            mandant_id=mandant_id,
        )
    return get_konto(mandant_id)


def update_abruf_status(mandant_id: str, status: str | None, fehler_text: str | None) -> None:
    db.engine.command(
        "UPDATE email_konto SET letzter_abruf_status=%s, letzter_abruf_fehler_text=%s, "
        "letzter_abruf_at=%s WHERE mandant_id=%s",
        (status, fehler_text, _now() if status else None, mandant_id),
        mandant_id=mandant_id,
    )


# --- Threads / Nachrichten -------------------------------------------------

def message_exists(mandant_id: str, kennung: str) -> bool:
    if not kennung:
        return False
    rows = db.engine.query(
        "SELECT 1 FROM email_nachricht WHERE mandant_id=%s AND stabile_mail_kennung=%s",
        (mandant_id, kennung), mandant_id=mandant_id,
    )
    return bool(rows)


def find_message_by_message_id(mandant_id: str, message_ids: list[str]) -> dict | None:
    ids = [i for i in message_ids if i]
    if not ids:
        return None
    placeholders = ", ".join(["%s"] * len(ids))
    rows = db.engine.query(
        f"SELECT id, thread_id, message_id FROM email_nachricht "
        f"WHERE mandant_id=%s AND message_id IN ({placeholders})",
        (mandant_id, *ids), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_thread(mandant_id: str, vorgang_id: str | None, kunde_id: str | None,
                  betreff: str | None) -> str:
    tid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO email_thread (id, mandant_id, vorgang_id, kunde_id, betreff) "
        "VALUES (%s, %s, %s, %s, %s)",
        (tid, mandant_id, vorgang_id, kunde_id, betreff), mandant_id=mandant_id,
    )
    return tid


def get_thread(mandant_id: str, thread_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, vorgang_id, kunde_id, betreff FROM email_thread "
        "WHERE mandant_id=%s AND id=%s",
        (mandant_id, thread_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def find_thread_for_vorgang(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, vorgang_id, kunde_id, betreff FROM email_thread "
        "WHERE mandant_id=%s AND vorgang_id=%s ORDER BY created_at ASC LIMIT 1",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_mandanten_mit_konto() -> list[str]:
    rows = db.engine.query(
        "SELECT DISTINCT mandant_id FROM email_konto", (), mandant_id=None,
    )
    return [r["mandant_id"] for r in rows]


def assign_thread(mandant_id: str, thread_id: str, vorgang_id: str) -> None:
    db.engine.command(
        "UPDATE email_thread SET vorgang_id=%s WHERE mandant_id=%s AND id=%s",
        (vorgang_id, mandant_id, thread_id), mandant_id=mandant_id,
    )


def create_nachricht(mandant_id: str, thread_id: str, richtung: str, absender: str,
                     empfaenger: str, betreff: str | None, text_html: str | None,
                     text_plain: str | None, message_id: str | None, in_reply_to: str | None,
                     references: str | None, stabile_mail_kennung: str | None,
                     gesendet_von_nutzer_id: str | None, empfangen_at: str | None) -> dict:
    nid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO email_nachricht (id, mandant_id, thread_id, richtung, absender, empfaenger, "
        "betreff, text_html, text_plain, message_id, in_reply_to, referenzen, "
        "stabile_mail_kennung, gesendet_von_nutzer_id, empfangen_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (nid, mandant_id, thread_id, richtung, absender, empfaenger, betreff, text_html,
         text_plain, message_id, in_reply_to, references, stabile_mail_kennung,
         gesendet_von_nutzer_id, empfangen_at or _now()),
        mandant_id=mandant_id,
    )
    return get_nachricht(mandant_id, nid)


def get_nachricht(mandant_id: str, nachricht_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, thread_id, richtung, absender, empfaenger, betreff, text_html, text_plain, "
        "message_id, in_reply_to, referenzen, stabile_mail_kennung, gesendet_von_nutzer_id, "
        "empfangen_at, created_at FROM email_nachricht "
        "WHERE mandant_id=%s AND id=%s",
        (mandant_id, nachricht_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_thread_messages(mandant_id: str, thread_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, thread_id, richtung, absender, empfaenger, betreff, text_html, text_plain, "
        "message_id, in_reply_to, referenzen, stabile_mail_kennung, gesendet_von_nutzer_id, "
        "empfangen_at, created_at FROM email_nachricht "
        "WHERE mandant_id=%s AND thread_id=%s ORDER BY created_at ASC",
        (mandant_id, thread_id), mandant_id=mandant_id,
    )


def create_anhang(mandant_id: str, nachricht_id: str, dateiname: str, objektpfad: str,
                  content_type: str, groesse_bytes: int, verarbeitet: bool,
                  fehler_text: str | None) -> dict:
    aid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO email_anhang (id, mandant_id, nachricht_id, dateiname, objektpfad, "
        "content_type, groesse_bytes, verarbeitet, fehler_text) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (aid, mandant_id, nachricht_id, dateiname, objektpfad, content_type, groesse_bytes,
         verarbeitet, fehler_text),
        mandant_id=mandant_id,
    )
    return get_anhang(mandant_id, nachricht_id, aid)


def get_anhang(mandant_id: str, nachricht_id: str, anhang_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, nachricht_id, dateiname, objektpfad, content_type, groesse_bytes, "
        "verarbeitet, fehler_text FROM email_anhang "
        "WHERE mandant_id=%s AND nachricht_id=%s AND id=%s",
        (mandant_id, nachricht_id, anhang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_anhang(mandant_id: str, nachricht_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, nachricht_id, dateiname, objektpfad, content_type, groesse_bytes, "
        "verarbeitet, fehler_text FROM email_anhang "
        "WHERE mandant_id=%s AND nachricht_id=%s ORDER BY created_at ASC",
        (mandant_id, nachricht_id), mandant_id=mandant_id,
    )


def list_inbox(mandant_id: str, zugeordnet: bool | None) -> list[dict]:
    where = ["t.mandant_id = %s"]
    params: list = [mandant_id]
    if zugeordnet is True:
        where.append("t.vorgang_id IS NOT NULL")
    elif zugeordnet is False:
        where.append("t.vorgang_id IS NULL")
    where_sql = " AND ".join(where)
    return db.engine.query(
        "SELECT t.id AS thread_id, t.betreff, t.vorgang_id, t.kunde_id, "
        "m.absender AS absender, m.empfaenger AS empfaenger, m.id AS letzte_nachricht_id, "
        "m.created_at AS letzte_nachricht_am "
        "FROM email_thread t "
        "JOIN email_nachricht m ON m.id = ("
        "  SELECT id FROM email_nachricht WHERE thread_id = t.id ORDER BY created_at DESC LIMIT 1"
        ") "
        f"WHERE {where_sql} ORDER BY m.created_at DESC LIMIT 200",
        tuple(params), mandant_id=mandant_id,
    )


def list_threads_for_vorgang(mandant_id: str, vorgang_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, mandant_id, vorgang_id, kunde_id, betreff FROM email_thread "
        "WHERE mandant_id=%s AND vorgang_id=%s ORDER BY created_at ASC",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
