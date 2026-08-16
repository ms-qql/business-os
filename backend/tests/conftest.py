from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app import db  # noqa: E402
from app.db import SqliteEngine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password  # noqa: E402

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
"""


@pytest.fixture(autouse=True)
def engine():
    eng = SqliteEngine()
    eng.init_schema(SQLITE_SCHEMA)
    db.set_engine(eng)
    yield eng
    db.set_engine(db.PostgresEngine(__import__("app.config", fromlist=["settings"]).settings.database_url))


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
