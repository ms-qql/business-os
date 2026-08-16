#!/usr/bin/env python3
"""Wendet die Raw-SQL-Migrationen in sql/ auf die in DATABASE_URL konfigurierte
PostgreSQL-Instanz an. Idempotent dank IF NOT EXISTS / CREATE OR REPLACE."""
from __future__ import annotations

import pathlib

import psycopg
from app.config import settings

SQL_DIR = pathlib.Path(__file__).resolve().parent / "sql"


def main() -> None:
    with psycopg.connect(settings.database_url) as conn:
        conn.execute("BEGIN")
        for path in sorted(SQL_DIR.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            conn.execute(sql)
        conn.commit()
    print("Migrationen angewendet.")


if __name__ == "__main__":
    main()
