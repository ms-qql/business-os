from __future__ import annotations

import datetime
import json
import uuid

from app import db

SECTION_COLS = (
    "id, mandant_id, landingpage_id, typ, visible, position, inhalt, created_at, updated_at"
)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Landingpage ---------------------------------------------------------

def get_landingpage(mandant_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, version, created_at, updated_at "
        "FROM website_landingpage WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_landingpage(mandant_id: str) -> dict:
    lid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO website_landingpage (id, mandant_id, version) VALUES (%s, %s, 1)",
        (lid, mandant_id), mandant_id=mandant_id,
    )
    return get_landingpage(mandant_id)


def bump_version(mandant_id: str, landingpage_id: str, current: int) -> int:
    db.engine.command(
        "UPDATE website_landingpage SET version = version + 1, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s AND version = %s",
        (_now(), mandant_id, landingpage_id, current), mandant_id=mandant_id,
    )
    return int(get_landingpage(mandant_id)["version"])


# --- Sektionen -----------------------------------------------------------

def list_sections(mandant_id: str, landingpage_id: str) -> list[dict]:
    return db.engine.query(
        f"SELECT {SECTION_COLS} FROM website_section "
        "WHERE mandant_id = %s AND landingpage_id = %s ORDER BY position ASC, created_at ASC",
        (mandant_id, landingpage_id), mandant_id=mandant_id,
    )


def get_section(mandant_id: str, section_id: str) -> dict | None:
    rows = db.engine.query(
        f"SELECT {SECTION_COLS} FROM website_section "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, section_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def next_position(mandant_id: str, landingpage_id: str) -> int:
    rows = db.engine.query(
        "SELECT COALESCE(MAX(position), 0) AS m FROM website_section "
        "WHERE mandant_id = %s AND landingpage_id = %s",
        (mandant_id, landingpage_id), mandant_id=mandant_id,
    )
    return int(rows[0]["m"]) + 1


def create_section(mandant_id: str, landingpage_id: str, typ: str,
                   position: int, inhalt: dict) -> dict:
    sid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO website_section (id, mandant_id, landingpage_id, typ, visible, "
        "position, inhalt) VALUES (%s, %s, %s, %s, TRUE, %s, %s)",
        (sid, mandant_id, landingpage_id, typ, position, json.dumps(inhalt, ensure_ascii=False)),
        mandant_id=mandant_id,
    )
    return get_section(mandant_id, sid)


def update_section(mandant_id: str, section_id: str, typ: str,
                   visible: bool | None, inhalt: dict) -> dict:
    sets = ["typ = %s"]
    params: list = [typ]
    if visible is not None:
        sets.append("visible = %s")
        params.append(visible)
    sets.append("inhalt = %s")
    params.append(json.dumps(inhalt, ensure_ascii=False))
    sets.append("updated_at = %s")
    params.append(_now())
    params.extend([mandant_id, section_id])
    db.engine.command(
        f"UPDATE website_section SET {', '.join(sets)} "
        "WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_section(mandant_id, section_id)


def set_positions(mandant_id: str, landingpage_id: str, id_to_pos: dict[str, int]) -> None:
    # Zwei Durchläufe, um die UNIQUE(landingpage_id, position)-Kollision beim
    # direkten Neunummerieren zu vermeiden: erst aus dem 1..N-Bereich heraus
    # auf einen kollisionsfreien Offset, dann auf die Zielposition.
    offset = 1_000_000
    for sid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE website_section SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND landingpage_id = %s AND id = %s",
            (offset + pos, _now(), mandant_id, landingpage_id, sid), mandant_id=mandant_id,
        )
    for sid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE website_section SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND landingpage_id = %s AND id = %s",
            (pos, _now(), mandant_id, landingpage_id, sid), mandant_id=mandant_id,
        )


def delete_section(mandant_id: str, section_id: str) -> None:
    db.engine.command(
        "DELETE FROM website_section WHERE mandant_id = %s AND id = %s",
        (mandant_id, section_id), mandant_id=mandant_id,
    )


# --- Bilder --------------------------------------------------------------

def get_bild(mandant_id: str, section_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, section_id, objektpfad, alt_text FROM website_section_bild "
        "WHERE mandant_id = %s AND section_id = %s",
        (mandant_id, section_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def upsert_bild(mandant_id: str, section_id: str, objektpfad: str, alt_text: str) -> dict:
    existing = get_bild(mandant_id, section_id)
    if existing:
        db.engine.command(
            "UPDATE website_section_bild SET objektpfad = %s, alt_text = %s "
            "WHERE mandant_id = %s AND section_id = %s",
            (objektpfad, alt_text, mandant_id, section_id), mandant_id=mandant_id,
        )
        return get_bild(mandant_id, section_id)
    bid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO website_section_bild (id, mandant_id, section_id, objektpfad, alt_text) "
        "VALUES (%s, %s, %s, %s, %s)",
        (bid, mandant_id, section_id, objektpfad, alt_text), mandant_id=mandant_id,
    )
    return get_bild(mandant_id, section_id)


def delete_bild(mandant_id: str, section_id: str) -> None:
    db.engine.command(
        "DELETE FROM website_section_bild WHERE mandant_id = %s AND section_id = %s",
        (mandant_id, section_id), mandant_id=mandant_id,
    )


def find_bild_by_objektpfad(mandant_id: str, objektpfad: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, section_id FROM website_section_bild "
        "WHERE mandant_id = %s AND objektpfad = %s",
        (mandant_id, objektpfad), mandant_id=mandant_id,
    )
    return rows[0] if rows else None
