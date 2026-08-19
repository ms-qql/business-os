from __future__ import annotations

import datetime
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Status-Quellen (read-only, keine Geheimnisse) -----------------------

def get_website_settings(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT firmenname, logo_objektpfad, marken_farbe, telefon, email, adresse "
        "FROM website_settings WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_domain(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT hostname, status, veröffentlicht_am FROM website_domains "
        "WHERE mandant_id = %s ORDER BY created_at ASC LIMIT 1",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def count_active_leistungen(mandant_id: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM leistungsseite "
        "WHERE mandant_id = %s AND aktiv = TRUE AND kurzbeschreibung <> '' AND inhalt <> ''",
        (mandant_id,), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def get_konto_version(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, konfiguration_version FROM email_konto WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_latest_postfach_test(mandant_id: str, email_konto_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, konfiguration_version, imap_ok, smtp_ok, detail, created_at "
        "FROM onboarding_postfach_test WHERE mandant_id = %s AND email_konto_id = %s "
        "ORDER BY created_at DESC LIMIT 1",
        (mandant_id, email_konto_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def count_preisliste(mandant_id: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM preisliste WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def get_testvorgang(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT t.vorgang_id, t.kunde_id, t.objekt_id, t.anfrage_id, t.created_at "
        "FROM onboarding_testvorgang t "
        "WHERE t.mandant_id = %s ORDER BY t.created_at DESC LIMIT 1",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


# --- Domain-Reservierung / Veröffentlichung ------------------------------

def hostname_owner(mandant_id: str, hostname: str) -> str | None:
    """Cross-Tenant-Prüfung (RLS umgangen via SECURITY DEFINER Function).
    Unter SQLite (Tests) gibt es keine SECURITY-DEFINER-Funktion; dort prüfen
    wir direkt gegen website_domains über alle Mandanten hinweg."""
    if db.engine.is_postgres:
        rows = db.engine.query(
            "SELECT mandant_id FROM onboarding_hostname_owner(%s)",
            (hostname,), mandant_id=None,
        )
    else:
        rows = db.engine.query(
            "SELECT mandant_id FROM website_domains WHERE hostname = %s",
            (hostname,), mandant_id=None,
        )
    for r in rows:
        if r["mandant_id"] != mandant_id:
            return r["mandant_id"]
    return None


def reserve_domain(mandant_id: str, hostname: str) -> None:
    existing = get_domain(mandant_id)
    if existing:
        db.engine.command(
            "UPDATE website_domains SET hostname = %s, status = 'inaktiv' "
            "WHERE mandant_id = %s",
            (hostname, mandant_id), mandant_id=mandant_id,
        )
    else:
        db.engine.command(
            "INSERT INTO website_domains (id, mandant_id, hostname, status) "
            "VALUES (%s, %s, %s, 'inaktiv')",
            (str(uuid.uuid4()), mandant_id, hostname), mandant_id=mandant_id,
        )


def publish_domain(mandant_id: str, hostname: str) -> None:
    db.engine.command(
        "UPDATE website_domains SET status = 'aktiv', veröffentlicht_am = %s "
        "WHERE mandant_id = %s AND hostname = %s",
        (_now(), mandant_id, hostname), mandant_id=mandant_id,
    )


# --- Postfach-Test --------------------------------------------------------

def save_postfach_test(mandant_id: str, email_konto_id: str, konfiguration_version: int,
                       imap_ok: bool, smtp_ok: bool, detail: str, getestet_von: str | None) -> None:
    db.engine.command(
        "INSERT INTO onboarding_postfach_test "
        "(id, mandant_id, email_konto_id, konfiguration_version, imap_ok, smtp_ok, detail, getestet_von) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, email_konto_id, konfiguration_version, imap_ok, smtp_ok,
         detail, getestet_von),
        mandant_id=mandant_id,
    )


# --- Testvorgang (atomare Anlage + kaskadierendes Löschen) ---------------

def create_test_kunde(mandant_id: str, name: str, email: str | None) -> str:
    kid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO kunde (id, mandant_id, name, email, telefon, notiz) "
        "VALUES (%s, %s, %s, %s, NULL, 'Onboarding-Test')",
        (kid, mandant_id, name, email), mandant_id=mandant_id,
    )
    return kid


def create_test_objekt(mandant_id: str, kunde_id: str, adresse: str) -> str:
    oid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO objekt (id, mandant_id, kunde_id, adresse, notiz) "
        "VALUES (%s, %s, %s, %s, 'Onboarding-Test')",
        (oid, mandant_id, kunde_id, adresse), mandant_id=mandant_id,
    )
    return oid


def create_test_vorgang(mandant_id: str, kunde_id: str, objekt_id: str | None,
                        anliegen: str, quelle: str) -> str:
    vid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO vorgang (id, mandant_id, kunde_id, objekt_id, status, quelle, "
        "anliegen, notizen, ist_test) "
        "VALUES (%s, %s, %s, %s, 'Neu', %s, %s, 'Onboarding-Test', TRUE)",
        (vid, mandant_id, kunde_id, objekt_id, quelle, anliegen),
        mandant_id=mandant_id,
    )
    return vid


def link_testvorgang(mandant_id: str, vorgang_id: str, kunde_id: str, objekt_id: str | None,
                     anfrage_id: str | None, erstellt_von: str | None) -> None:
    db.engine.command(
        "INSERT INTO onboarding_testvorgang "
        "(id, mandant_id, vorgang_id, kunde_id, objekt_id, anfrage_id, erstellt_von) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, vorgang_id, kunde_id, objekt_id, anfrage_id, erstellt_von),
        mandant_id=mandant_id,
    )


def get_testvorgang_zuordnung(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT vorgang_id, kunde_id, objekt_id FROM onboarding_testvorgang "
        "WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_test_kunde_vorgang_ids(mandant_id: str, kunde_id: str) -> list[str]:
    rows = db.engine.query(
        "SELECT vorgang_id FROM onboarding_testvorgang WHERE mandant_id = %s AND kunde_id = %s",
        (mandant_id, kunde_id), mandant_id=mandant_id,
    )
    return [r["vorgang_id"] for r in rows]


def cascade_delete_testvorgang(tx, mandant_id: str, vorgang_id: str, kunde_id: str,
                               objekt_id: str | None) -> None:
    """Löscht atomar ausschließlich die vom Onboarding erzeugten Testdaten:
    Dokumente + Historie des Vorgangs, E-Mail-Threads/Nachrichten/Anhänge,
    dann Vorgang, Objekt, Kunde und die Zuordnung selbst. Läuft innerhalb von
    ``tx`` (db.engine.transaction), damit alles oder nichts gelöscht wird."""
    # Abhängige E-Mail-Daten (Nachrichten+Anhänge über Threads des Vorgangs).
    tx.command(
        "DELETE FROM email_anhang WHERE nachricht_id IN ("
        "SELECT n.id FROM email_nachricht n "
        "JOIN email_thread t ON t.id = n.thread_id "
        "WHERE t.mandant_id = %s AND t.vorgang_id = %s)",
        (mandant_id, vorgang_id),
    )
    tx.command(
        "DELETE FROM email_nachricht WHERE thread_id IN ("
        "SELECT id FROM email_thread WHERE mandant_id = %s AND vorgang_id = %s)",
        (mandant_id, vorgang_id),
    )
    tx.command(
        "DELETE FROM email_thread WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id),
    )
    # Vorgang-Dokumente + Historie.
    tx.command(
        "DELETE FROM vorgang_dokument WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id),
    )
    tx.command(
        "DELETE FROM vorgang_historie WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id),
    )
    # Vorgang (und ggf. weitere Testvorgänge desselben Test-Kunden).
    vorgang_ids = get_test_kunde_vorgang_ids(mandant_id, kunde_id)
    if vorgang_ids:
        placeholders = ", ".join(["%s"] * len(vorgang_ids))
        tx.command(
            f"DELETE FROM vorgang WHERE mandant_id = %s AND id IN ({placeholders})",
            (mandant_id, *vorgang_ids),
        )
    # Objekt + Kunde (Test-Stammdaten) und Zuordnung.
    if objekt_id:
        tx.command(
            "DELETE FROM objekt WHERE mandant_id = %s AND id = %s",
            (mandant_id, objekt_id),
        )
    tx.command(
        "DELETE FROM kunde WHERE mandant_id = %s AND id = %s",
        (mandant_id, kunde_id),
    )
    tx.command(
        "DELETE FROM onboarding_testvorgang WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id),
    )


# --- Öffentliches Anfrageformular (Testvorgang über echten Prozess) ------
# Die Anfrage wird über das bestehende website_service.submit_anfrage erzeugt;
# diese Hilfen verknüpfen sie anschließend mit dem Testvorgang.

def link_anfrage_to_testvorgang(mandant_id: str, anfrage_id: str, vorgang_id: str) -> None:
    db.engine.command(
        "UPDATE onboarding_testvorgang SET anfrage_id = %s "
        "WHERE mandant_id = %s AND vorgang_id = %s",
        (anfrage_id, mandant_id, vorgang_id),
        mandant_id=mandant_id,
    )


# --- Preisliste / Leistungskatalog (CRUD) --------------------------------

PREISLISTE_COLS = "id, mandant_id, bezeichnung, einheit, netto_einzelpreis, steuersatz, created_at, updated_at"


def list_preisliste(mandant_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {PREISLISTE_COLS} FROM preisliste WHERE mandant_id = %s ORDER BY bezeichnung ASC",
        (mandant_id,), mandant_id=mandant_id,
    )


def get_preisliste_position(mandant_id: str, position_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {PREISLISTE_COLS} FROM preisliste WHERE mandant_id = %s AND id = %s",
        (mandant_id, position_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def find_preisliste_by_bezeichnung(mandant_id: str, bezeichnung: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {PREISLISTE_COLS} FROM preisliste WHERE mandant_id = %s AND bezeichnung = %s",
        (mandant_id, bezeichnung), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_preisliste_position(mandant_id: str, bezeichnung: str, einheit: str,
                               netto_einzelpreis: float, steuersatz: float) -> dict:
    pid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO preisliste (id, mandant_id, bezeichnung, einheit, netto_einzelpreis, steuersatz) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (pid, mandant_id, bezeichnung, einheit, netto_einzelpreis, steuersatz),
        mandant_id=mandant_id,
    )
    return get_preisliste_position(mandant_id, pid)


def delete_preisliste_position(mandant_id: str, position_id: str) -> None:
    db.engine.command(
        "DELETE FROM preisliste WHERE mandant_id = %s AND id = %s",
        (mandant_id, position_id), mandant_id=mandant_id,
    )
