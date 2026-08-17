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
    status TEXT NOT NULL DEFAULT 'aktiv', created_at TEXT NOT NULL DEFAULT 'now'
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
    uebermittlungskennung TEXT NOT NULL, vorgang_id TEXT, created_at TEXT NOT NULL DEFAULT 'now',
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
    notiz TEXT, created_at TEXT NOT NULL DEFAULT 'now', updated_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE objekt (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, kunde_id TEXT NOT NULL, adresse TEXT NOT NULL,
    notiz TEXT, created_at TEXT NOT NULL DEFAULT 'now'
);
CREATE TABLE vorgang (
    id TEXT PRIMARY KEY, mandant_id TEXT NOT NULL, kunde_id TEXT NOT NULL, objekt_id TEXT,
    status TEXT NOT NULL DEFAULT 'Neu', quelle TEXT NOT NULL DEFAULT 'Sonstiges',
    anliegen TEXT NOT NULL, notizen TEXT, zugewiesener_nutzer_id TEXT,
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
"""


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
    yield
    storage.set_storage(storage.MinioStorage())


def _iso():
    from datetime import datetime, timezone
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
