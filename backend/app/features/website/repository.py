from __future__ import annotations

import datetime
import uuid

from app import db

MAX_UPLOADS_PER_ANFRAGE = 5


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# --- Domainauflösung (öffentlich, kein Mandantenkontext bekannt) -----------

def find_mandant_id_by_hostname(hostname: str) -> str | None:
    if db.engine.is_postgres:
        rows = db.engine.query(
            "SELECT mandant_id FROM website_find_mandant_by_hostname(%s)",
            (hostname,),
        )
    else:
        rows = db.engine.query(
            "SELECT wd.mandant_id AS mandant_id FROM website_domains wd "
            "JOIN mandanten m ON m.id = wd.mandant_id "
            "WHERE wd.hostname = %s AND wd.status = 'aktiv' AND m.status = 'active'",
            (hostname,),
        )
    return rows[0]["mandant_id"] if rows else None


def get_domain(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT hostname, status FROM website_domains WHERE mandant_id = %s "
        "ORDER BY created_at ASC LIMIT 1",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def upsert_domain(mandant_id: str, hostname: str) -> None:
    """Setzt die (einzige) öffentliche Domain des Mandanten. Kollisions-Check
    gegen fremde Mandanten übernimmt der Service via find_mandant_id_by_hostname
    (SECURITY DEFINER, umgeht RLS gezielt). Race zwischen Check und Insert ist
    hier bewusst nicht abgesichert (ponytail: seltenes Wettrennen bei
    gleichzeitiger Erstanmeldung zweier Mandanten auf denselben Hostnamen —
    DB-UNIQUE auf hostname verhindert Dubletten, würde dann als 500 statt 409
    auffallen; Vorab-Lock/Retry nachrüsten, falls das in der Praxis auftritt)."""
    existing = get_domain(mandant_id)
    if existing:
        db.engine.command(
            "UPDATE website_domains SET hostname = %s, status = 'aktiv' WHERE mandant_id = %s",
            (hostname, mandant_id), mandant_id=mandant_id,
        )
    else:
        db.engine.command(
            "INSERT INTO website_domains (id, mandant_id, hostname, status) "
            "VALUES (%s, %s, %s, 'aktiv')",
            (str(uuid.uuid4()), mandant_id, hostname), mandant_id=mandant_id,
        )


# --- Website-Einstellungen ---------------------------------------------

def get_settings(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, firmenname, logo_objektpfad, marken_farbe, telefon, "
        "email, adresse, oeffnungszeiten, ueber_uns FROM website_settings "
        "WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_default_settings(mandant_id: str) -> dict:
    sid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO website_settings (id, mandant_id, firmenname) VALUES (%s, %s, %s)",
        (sid, mandant_id, ""), mandant_id=mandant_id,
    )
    return get_settings(mandant_id)


def update_settings(mandant_id: str, fields: dict) -> dict:
    if not fields:
        return get_settings(mandant_id)
    sets = [f"{col} = %s" for col in fields]
    params = list(fields.values()) + [mandant_id]
    db.engine.command(
        f"UPDATE website_settings SET {', '.join(sets)} WHERE mandant_id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_settings(mandant_id)


def set_logo(mandant_id: str, objektpfad: str) -> None:
    db.engine.command(
        "UPDATE website_settings SET logo_objektpfad = %s WHERE mandant_id = %s",
        (objektpfad, mandant_id), mandant_id=mandant_id,
    )


# --- Leistungsseiten ------------------------------------------------------

def list_leistungen(mandant_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT slug, titel, aktiv, kurzbeschreibung, inhalt FROM leistungsseite "
        "WHERE mandant_id = %s ORDER BY titel",
        (mandant_id,), mandant_id=mandant_id,
    )


def list_active_leistungen(mandant_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT slug, titel, kurzbeschreibung, inhalt FROM leistungsseite "
        "WHERE mandant_id = %s AND aktiv = TRUE ORDER BY titel",
        (mandant_id,), mandant_id=mandant_id,
    )


def get_active_leistung(mandant_id: str, slug: str) -> dict | None:
    rows = db.engine.query(
        "SELECT slug, titel, kurzbeschreibung, inhalt FROM leistungsseite "
        "WHERE mandant_id = %s AND slug = %s AND aktiv = TRUE",
        (mandant_id, slug), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def seed_leistungen(mandant_id: str, katalog: list[tuple[str, str]], tx=None) -> None:
    if tx is None:
        existing = {row["slug"] for row in db.engine.query(
            "SELECT slug FROM leistungsseite WHERE mandant_id = %s",
            (mandant_id,), mandant_id=mandant_id,
        )}
    else:
        existing = {row["slug"] for row in tx.query(
            "SELECT slug FROM leistungsseite WHERE mandant_id = %s",
            (mandant_id,),
        )}
    for slug, titel in katalog:
        if slug in existing:
            continue
        if tx is None:
            db.engine.command(
                "INSERT INTO leistungsseite (id, mandant_id, slug, titel) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), mandant_id, slug, titel), mandant_id=mandant_id,
            )
        else:
            tx.command(
                "INSERT INTO leistungsseite (id, mandant_id, slug, titel) VALUES (%s, %s, %s, %s)",
                (str(uuid.uuid4()), mandant_id, slug, titel),
            )


def patch_leistung(mandant_id: str, slug: str, aktiv: bool | None,
                   kurzbeschreibung: str | None, inhalt: str | None) -> None:
    sets = []
    params: list = []
    if aktiv is not None:
        sets.append("aktiv = %s")
        params.append(aktiv)
    if kurzbeschreibung is not None:
        sets.append("kurzbeschreibung = %s")
        params.append(kurzbeschreibung)
    if inhalt is not None:
        sets.append("inhalt = %s")
        params.append(inhalt)
    if not sets:
        return
    params.extend([mandant_id, slug])
    db.engine.command(
        f"UPDATE leistungsseite SET {', '.join(sets)} WHERE mandant_id = %s AND slug = %s",
        tuple(params), mandant_id=mandant_id,
    )


# --- Anfragen und Bilder ---------------------------------------------------

def get_anfrage_by_kennung(mandant_id: str, uebermittlungskennung: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id FROM anfrage WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (mandant_id, uebermittlungskennung), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_anfrage(mandant_id: str, name: str, kontaktweg: str, telefon: str | None,
                   email: str | None, adresse: str, anliegen: str, dringlichkeit: str,
                   zeitfenster: str | None, uebermittlungskennung: str) -> str:
    aid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO anfrage (id, mandant_id, name, kontaktweg, telefon, email, adresse, "
        "anliegen, dringlichkeit, zeitfenster, quelle, uebermittlungskennung) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Website', %s)",
        (aid, mandant_id, name, kontaktweg, telefon, email, adresse, anliegen,
         dringlichkeit, zeitfenster, uebermittlungskennung),
        mandant_id=mandant_id,
    )
    return aid


def count_uploads_for_kennung(mandant_id: str, uebermittlungskennung: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM anfragebild WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant_id, uebermittlungskennung), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def create_anfragebild(mandant_id: str, uebermittlungskennung: str, objektpfad: str,
                       dateiname: str) -> str:
    bid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO anfragebild (id, mandant_id, uebermittlungskennung, objektpfad, dateiname) "
        "VALUES (%s, %s, %s, %s, %s)",
        (bid, mandant_id, uebermittlungskennung, objektpfad, dateiname),
        mandant_id=mandant_id,
    )
    return bid


def get_unlinked_bilder(mandant_id: str, uebermittlungskennung: str,
                        upload_ids: list[str]) -> list[dict]:
    if not upload_ids:
        return []
    placeholders = ", ".join(["%s"] * len(upload_ids))
    rows = db.engine.query(
        f"SELECT id, objektpfad FROM anfragebild WHERE mandant_id = %s "
        f"AND uebermittlungskennung = %s AND anfrage_id IS NULL AND id IN ({placeholders})",
        (mandant_id, uebermittlungskennung, *upload_ids), mandant_id=mandant_id,
    )
    return rows


def link_bilder_to_anfrage(mandant_id: str, anfrage_id: str, bild_ids: list[str]) -> None:
    if not bild_ids:
        return
    placeholders = ", ".join(["%s"] * len(bild_ids))
    db.engine.command(
        f"UPDATE anfragebild SET anfrage_id = %s WHERE mandant_id = %s AND id IN ({placeholders})",
        (anfrage_id, mandant_id, *bild_ids), mandant_id=mandant_id,
    )


# --- Rate-Limit (Muster: login_versuche, backend/sql/001_init.sql) --------

def count_recent_anfrage_attempts(ip: str | None, window_minutes: int) -> int:
    since = (_now() - datetime.timedelta(minutes=window_minutes)).isoformat()
    if ip:
        rows = db.engine.query(
            "SELECT COUNT(*) AS c FROM website_anfrage_versuche "
            "WHERE ip = %s AND created_at >= %s",
            (ip, since),
        )
    else:
        rows = db.engine.query(
            "SELECT COUNT(*) AS c FROM website_anfrage_versuche WHERE created_at >= %s",
            (since,),
        )
    return int(rows[0]["c"]) if rows else 0


def record_anfrage_attempt(ip: str | None) -> None:
    db.engine.command(
        "INSERT INTO website_anfrage_versuche (id, ip, created_at) VALUES (%s, %s, %s)",
        (str(uuid.uuid4()), ip, _now().isoformat()),
    )
