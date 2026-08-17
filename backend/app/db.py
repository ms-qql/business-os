from __future__ import annotations

import os
import re
import sqlite3
import uuid
from typing import Any

from .config import settings


class BaseEngine:
    """Abstraction over the SQL backend. Repositories only ever call
    ``query`` / ``command``; all raw SQL lives in the repository layer."""

    def query(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> list[dict]:
        raise NotImplementedError

    def command(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> int:
        raise NotImplementedError


class PostgresEngine(BaseEngine):
    """Production engine. Sets the RLS mandant context per transaction so the
    database enforces tenant isolation even if an application filter is missed."""
    is_postgres = True

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _conn(self):
        import psycopg

        return psycopg.connect(self._dsn, autocommit=False)

    def query(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> list[dict]:
        conn = self._conn()
        try:
            conn.execute("BEGIN")
            if mandant_id:
                conn.execute("SELECT set_config('app.current_mandant_id', %s::text, true)", (mandant_id,))
            cur = conn.execute(sql, params)
            cols = [c.name for c in cur.description]
            rows = [
                dict(zip(cols, (str(value) if isinstance(value, uuid.UUID) else value for value in row)))
                for row in cur.fetchall()
            ]
            conn.commit()
            return rows
        except Exception:
            conn.rollback()
            conn.close()
            raise
        else:
            conn.close()

    def command(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> int:
        conn = self._conn()
        try:
            conn.execute("BEGIN")
            if mandant_id:
                conn.execute("SELECT set_config('app.current_mandant_id', %s::text, true)", (mandant_id,))
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount
        except Exception:
            conn.rollback()
            conn.close()
            raise
        else:
            conn.close()


class SqliteEngine(BaseEngine):
    """Test engine: in-memory SQLite. RLS is not available in SQLite, so tenant
    isolation is provided by the application-layer WHERE clauses in the
    repositories (which is what we actually exercise here)."""
    is_postgres = False

    def __init__(self, shared: bool = True) -> None:
        self._conn = sqlite3.connect(":memory:" if shared else f"/tmp/bos_test_{uuid.uuid4().hex}.db",
                                     check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init_schema(self, sql: str) -> None:
        # Strip Postgres-only bits the test schema does not need.
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in statements:
            if stmt.upper().startswith(("ALTER TABLE", "CREATE POLICY", "CREATE INDEX")):
                continue
            self._conn.execute(stmt)
        self._conn.commit()

    @staticmethod
    def _to_qmark(sql: str) -> str:
        return re.sub(r"%s", "?", sql)

    def query(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> list[dict]:
        cur = self._conn.execute(self._to_qmark(sql), params)
        rows = [dict(r) for r in cur.fetchall()]
        self._conn.commit()
        return rows

    def command(self, sql: str, params: tuple = (), mandant_id: str | None = None) -> int:
        cur = self._conn.execute(self._to_qmark(sql), params)
        self._conn.commit()
        return cur.rowcount


engine: BaseEngine = PostgresEngine(settings.database_url)


def set_engine(e: BaseEngine) -> None:
    global engine
    engine = e
