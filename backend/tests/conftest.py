from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app import db  # noqa: E402
from app import storage  # noqa: E402
from app.db import SqliteEngine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.storage import InMemoryStorage  # noqa: E402

SQLITE_SCHEMA = """
CREATE TABLE mandanten (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE nutzer (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL,
    password_hash TEXT, role TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'invited',
    created_at TEXT NOT NULL DEFAULT 'now', UNIQUE (mandant_id, email)
);
CREATE TABLE sitzungen (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, nutzer_id TEXT NOT NULL, ip TEXT,
    revoked BOOLEAN NOT NULL DEFAULT 0, expires_at TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE einladungen (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, nutzer_id TEXT NOT NULL, token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL, used BOOLEAN NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE passwort_resets (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, nutzer_id TEXT NOT NULL, token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL, used BOOLEAN NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE login_versuche (
    id TEXT PRIMARY KEY, email TEXT NOT NULL, ip TEXT, erfolg BOOLEAN NOT NULL, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE audit_events (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, nutzer_id TEXT, typ TEXT NOT NULL,
    erfolg BOOLEAN NOT NULL, detail TEXT, ip TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE betreiber (
    id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE betreiber_sitzungen (
    id TEXT PRIMARY KEY, betreiber_id TEXT NOT NULL, revoked BOOLEAN NOT NULL DEFAULT 0,
    expires_at TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE website_settings (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL UNIQUE, firmenname TEXT NOT NULL DEFAULT '',
    logo_objektpfad TEXT, marken_farbe TEXT, telefon TEXT, email TEXT, adresse TEXT,
    oeffnungszeiten TEXT, ueber_uns TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE website_domains (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, hostname TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'aktiv', veröffentlicht_am TEXT,
    created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE leistungsseite (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, slug TEXT NOT NULL, titel TEXT NOT NULL,
    aktiv BOOLEAN NOT NULL DEFAULT 0, kurzbeschreibung TEXT NOT NULL DEFAULT '',
    inhalt TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (mandant_id, slug)
);
CREATE TABLE anfrage (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, name TEXT NOT NULL, kontaktweg TEXT NOT NULL,
    telefon TEXT, email TEXT, adresse TEXT NOT NULL, anliegen TEXT NOT NULL,
    dringlichkeit TEXT NOT NULL, zeitfenster TEXT, quelle TEXT NOT NULL DEFAULT 'Website',
    uebermittlungskennung TEXT NOT NULL, vorgang_id TEXT, formular_einsendung_id TEXT, created_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (mandant_id, uebermittlungskennung)
);
CREATE TABLE anfragebild (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, anfrage_id TEXT, uebermittlungskennung TEXT NOT NULL,
    objektpfad TEXT NOT NULL, dateiname TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE website_anfrage_versuche (
    id TEXT PRIMARY KEY, ip TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE kunde (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT, telefon TEXT,
    notiz TEXT, status TEXT NOT NULL DEFAULT 'aktiv', created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE objekt (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, kunde_id TEXT NOT NULL, adresse TEXT NOT NULL,
    notiz TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE vorgang (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, kunde_id TEXT NOT NULL, objekt_id TEXT,
    status TEXT NOT NULL DEFAULT 'Neu', quelle TEXT NOT NULL DEFAULT 'Sonstiges',
    anliegen TEXT NOT NULL, notizen TEXT, zugewiesener_nutzer_id TEXT,
    ist_test BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE vorgang_historie (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL, ereignis TEXT NOT NULL,
    detail TEXT, nutzer_id TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE vorgang_dokument (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL, dateiname TEXT NOT NULL,
    objektpfad TEXT NOT NULL, content_type TEXT NOT NULL, groesse_bytes INTEGER NOT NULL,
    hochgeladen_von TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE email_konto (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, imap_host TEXT NOT NULL,
    imap_port INTEGER NOT NULL DEFAULT 993, imap_user TEXT NOT NULL, imap_passwort TEXT NOT NULL,
    imap_tls BOOLEAN NOT NULL DEFAULT 1, smtp_host TEXT NOT NULL, smtp_port INTEGER NOT NULL DEFAULT 465,
    smtp_user TEXT, smtp_passwort TEXT, smtp_tls BOOLEAN NOT NULL DEFAULT 1,
    konfiguration_version INTEGER NOT NULL DEFAULT 1,
    letzter_abruf_status TEXT, letzter_abruf_fehler_text TEXT, letzter_abruf_at TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE email_thread (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT, kunde_id TEXT,
    betreff TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE email_nachricht (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, thread_id TEXT NOT NULL, richtung TEXT NOT NULL,
    absender TEXT NOT NULL, empfaenger TEXT NOT NULL, betreff TEXT, text_html TEXT, text_plain TEXT,
    message_id TEXT, in_reply_to TEXT, referenzen TEXT, stabile_mail_kennung TEXT,
    gesendet_von_nutzer_id TEXT, empfangen_at TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE email_anhang (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, nachricht_id TEXT NOT NULL, dateiname TEXT NOT NULL,
    objektpfad TEXT NOT NULL, content_type TEXT NOT NULL, groesse_bytes INTEGER NOT NULL,
    verarbeitet BOOLEAN NOT NULL DEFAULT 1, fehler_text TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE angebot_nummernkreis (
    mandant_id TEXT PRIMARY KEY, letzte_nummer INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE angebot (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL,
    angebot_nummer TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, vorgaenger_angebot_id TEXT,
    status TEXT NOT NULL DEFAULT 'entwurf', gueltig_bis TEXT, freitext TEXT,
    netto_summe REAL NOT NULL DEFAULT 0, steuer_summe REAL NOT NULL DEFAULT 0,
    brutto_summe REAL NOT NULL DEFAULT 0, dokument_id TEXT, empfaenger_email TEXT,
    versendet_at TEXT, versendet_von TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE angebot_position (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, angebot_id TEXT NOT NULL, bezeichnung TEXT NOT NULL,
    menge REAL NOT NULL, einheit TEXT NOT NULL, einzelpreis REAL NOT NULL, steuersatz REAL NOT NULL,
    rabatt_typ TEXT NOT NULL DEFAULT 'prozent', rabatt_wert REAL NOT NULL DEFAULT 0,
    sortierung INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE termin (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL,
    beginn TEXT NOT NULL, ende TEXT NOT NULL, adresse TEXT, notiz TEXT,
    abgesagt_at TEXT, vorheriger_vorgang_status TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE termin_zuweisung (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, termin_id TEXT NOT NULL, nutzer_id TEXT NOT NULL,
    aktiv BOOLEAN NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (termin_id, nutzer_id)
);
CREATE TABLE onboarding_postfach_test (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, email_konto_id TEXT NOT NULL,
    konfiguration_version INTEGER NOT NULL, imap_ok BOOLEAN NOT NULL, smtp_ok BOOLEAN NOT NULL,
    detail TEXT NOT NULL DEFAULT '', getestet_von TEXT,
    created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE onboarding_testvorgang (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL,
    kunde_id TEXT NOT NULL, objekt_id TEXT, anfrage_id TEXT, erstellt_von TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', UNIQUE (vorgang_id)
);
CREATE TABLE preisliste (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, bezeichnung TEXT NOT NULL,
    einheit TEXT NOT NULL DEFAULT 'Stk.', netto_einzelpreis REAL NOT NULL DEFAULT 0,
    steuersatz REAL NOT NULL DEFAULT 19, created_at TEXT NOT NULL DEFAULT 'now',
    updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE rechnung_nummernkreis (
    mandant_id TEXT PRIMARY KEY, letzte_nummer INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE rechnungsstellerprofil (
    mandant_id TEXT PRIMARY KEY, firma_name TEXT NOT NULL, strasse TEXT NOT NULL,
    hausnummer TEXT NOT NULL, plz TEXT NOT NULL, ort TEXT NOT NULL,
    steuernummer TEXT, ust_id TEXT, updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE rechnung (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, vorgang_id TEXT NOT NULL,
    rechnungsnummer TEXT NOT NULL, rechnungsdatum TEXT NOT NULL, leistungsdatum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'entwurf', zahlungsstatus TEXT NOT NULL DEFAULT 'Offen',
    netto_summe REAL NOT NULL DEFAULT 0, steuer_summe REAL NOT NULL DEFAULT 0,
    brutto_summe REAL NOT NULL DEFAULT 0, empfaenger_email TEXT,
    fassung_id TEXT, freigabe_vorbereitet_at TEXT, versendet_at TEXT, versendet_von TEXT,
    storniert_at TEXT, storniert_von TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (mandant_id, rechnungsnummer)
);
CREATE TABLE rechnung_position (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, rechnung_id TEXT NOT NULL,
    bezeichnung TEXT NOT NULL, menge REAL NOT NULL, einheit TEXT NOT NULL,
    netto_einzelpreis REAL NOT NULL, steuersatz REAL NOT NULL, sortierung INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE rechnung_fassung (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, rechnung_id TEXT NOT NULL,
    rechnungsnummer TEXT NOT NULL, kopf_json TEXT NOT NULL, rechnungssteller_json TEXT NOT NULL,
    kunde_json TEXT NOT NULL, objekt_json TEXT NOT NULL, positionen_json TEXT NOT NULL,
    summen_json TEXT NOT NULL, dokument_id TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE website_landingpage (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL UNIQUE, version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE website_section (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, landingpage_id TEXT NOT NULL,
    typ TEXT NOT NULL, visible BOOLEAN NOT NULL DEFAULT 1, position INTEGER NOT NULL,
    inhalt TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT 'now',
    updated_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (mandant_id, landingpage_id, position)
);
CREATE TABLE website_section_bild (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, section_id TEXT NOT NULL UNIQUE,
    objektpfad TEXT NOT NULL, alt_text TEXT NOT NULL DEFAULT '',
    speicher_backend TEXT NOT NULL DEFAULT 'legacy', content_type TEXT, anzeigename TEXT,
    created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE UNIQUE INDEX idx_website_section_bild_anzeigename
    ON website_section_bild (mandant_id, anzeigename) WHERE anzeigename IS NOT NULL;
-- PROJ-13: Formular-Baukasten (Spiegel von sql/011_formular_baukasten.sql).
CREATE TABLE formular (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, name TEXT NOT NULL DEFAULT 'Neues Formular',
    komplexitaet TEXT NOT NULL DEFAULT 'einfach', draft_revision INTEGER NOT NULL DEFAULT 1,
    veroeffentlicht BOOLEAN NOT NULL DEFAULT 0, aktuelle_version_id TEXT,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE formular_schritt (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    position INTEGER NOT NULL, titel TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (formular_id, position)
);
CREATE TABLE formular_feld (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    schritt_id TEXT NOT NULL, position INTEGER NOT NULL, typ TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '', hilfetext TEXT, pflichtfeld BOOLEAN NOT NULL DEFAULT 0,
    optional_in_einfach BOOLEAN NOT NULL DEFAULT 0, uebernahme TEXT,
    min_val NUMERIC, max_val NUMERIC, ganzzahl BOOLEAN, reg_exp TEXT, maxlaenge INTEGER,
    datum_min TEXT, datum_max TEXT, max_anzahl INTEGER,
    created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now',
    UNIQUE (schritt_id, position)
);
CREATE TABLE formular_option (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    feld_id TEXT NOT NULL, position INTEGER NOT NULL, label TEXT NOT NULL, wert TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT 'now', UNIQUE (feld_id, position), UNIQUE (feld_id, wert)
);
CREATE TABLE formular_version (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    nummer INTEGER NOT NULL, public_id TEXT NOT NULL, inhalt TEXT NOT NULL,
    veroeffentlicht_am TEXT NOT NULL DEFAULT 'now', veroeffentlicht_von TEXT,
    UNIQUE (formular_id, nummer), UNIQUE (public_id)
);
CREATE TABLE formular_einsendung (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    version_id TEXT NOT NULL, uebermittlungskennung TEXT NOT NULL, werte TEXT NOT NULL,
    consent_nachweis TEXT, spam_status TEXT NOT NULL DEFAULT 'normal',
    anfrage_id TEXT, vorgang_id TEXT, erstellt_am TEXT NOT NULL DEFAULT 'now',
    UNIQUE (mandant_id, uebermittlungskennung)
);
CREATE TABLE formular_upload (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, formular_id TEXT NOT NULL,
    feld_id TEXT, uebermittlungskennung TEXT NOT NULL, einsendung_id TEXT,
    objektpfad TEXT NOT NULL, originalname TEXT NOT NULL, mime_typ TEXT NOT NULL,
    groesse_bytes INTEGER NOT NULL, erstellt_am TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE formular_einsendung_versuche (
    id TEXT PRIMARY KEY, ip TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE formular_upload_versuche (
    id TEXT PRIMARY KEY, ip TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
"""

import uuid
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def engine():
    eng = SqliteEngine()
    eng.init_schema(SQLITE_SCHEMA)
    db.set_engine(eng)
    yield eng
    db.set_engine(db.PostgresEngine(__import__("app.config", fromlist=["settings"]).settings.database_url))


@pytest.fixture(autouse=True)
def object_storage():
    storage.set_storage(InMemoryStorage())
    storage.set_image_storage(InMemoryStorage())
    yield
    storage.set_storage(storage.MinioStorage())
    storage.set_image_storage(storage.MinioStorage())


def _iso():
    return datetime.now(timezone.utc).isoformat()


def make_mandant(name: str = "SHK Test") -> str:
    mid = str(uuid.uuid4())
    db.engine.command("INSERT INTO mandanten (id, name, status) VALUES (%s, %s, 'active')",
                      (mid, name))
    return mid


def make_user(mandant_id: str, email: str, role: str, password: str | None = "startpasswort123",
              status: str = "active") -> str:
    existing = db.engine.query(
        "SELECT id FROM nutzer WHERE mandant_id = %s AND email = %s",
        (mandant_id, email), mandant_id=mandant_id)
    if existing:
        return existing[0]["id"]
    uid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO nutzer (id, mandant_id, name, email, password_hash, role, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (uid, mandant_id, "Max", email, hash_password(password) if password else None,
         role, status),
    )
    return uid


def make_domain(mandant_id: str, hostname: str, status: str = "aktiv") -> None:
    db.engine.command(
        "INSERT INTO website_domains (id, mandant_id, hostname, status) VALUES (%s, %s, %s, %s)",
        (str(uuid.uuid4()), mandant_id, hostname, status),
    )


def make_betreiber(email: str = "op@plattform.de", password: str = "op-passwort-123") -> None:
    db.engine.command(
        "INSERT INTO betreiber (id, email, password_hash) VALUES (%s, %s, %s)",
        (str(uuid.uuid4()), email, hash_password(password)),
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mandant():
    return make_mandant()


@pytest.fixture
def betreiber():
    make_betreiber()
    return "op@plattform.de"
