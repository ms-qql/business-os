#!/usr/bin/env python3
"""Wendet die Raw-SQL-Migrationen in sql/ auf die in DATABASE_URL konfigurierte
PostgreSQL-Instanz an. Idempotent dank IF NOT EXISTS / CREATE OR REPLACE."""
from __future__ import annotations

import pathlib
import os
import uuid

import psycopg
from app.config import settings
from app.security import hash_password

SQL_DIR = pathlib.Path(__file__).resolve().parent / "sql"


def bootstrap_admin(conn: psycopg.Connection) -> None:
    email = os.environ.get("INITIAL_ADMIN_EMAIL")
    password = os.environ.get("INITIAL_ADMIN_PASSWORD")
    if not email and not password:
        return
    if not email or not password:
        raise RuntimeError("INITIAL_ADMIN_EMAIL und INITIAL_ADMIN_PASSWORD müssen zusammen gesetzt sein.")
    existing = conn.execute("SELECT 1 FROM nutzer WHERE email = %s", (email,)).fetchone()
    if existing:
        return
    mandant_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO mandanten (id, name, status) VALUES (%s, %s, 'active')",
        (mandant_id, "Mein Betrieb"),
    )
    conn.execute(
        "INSERT INTO nutzer (id, mandant_id, name, email, password_hash, role, status) "
        "VALUES (%s, %s, %s, %s, %s, 'Inhaber', 'active')",
        (str(uuid.uuid4()), mandant_id, "Admin", email, hash_password(password)),
    )


def main() -> None:
    with psycopg.connect(settings.database_url) as conn:
        conn.execute("BEGIN")
        for path in sorted(SQL_DIR.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            conn.execute(sql)
        bootstrap_admin(conn)
        conn.commit()
    print("Migrationen angewendet.")


if __name__ == "__main__":
    main()
