from __future__ import annotations

import datetime
import json
import uuid

from app import db

TEMPLATE_SHK: dict = {
    "name": "SHK-Kontaktformular",
    "komplexitaet": "einfach",
    "schritte": [
        {
            "titel": "Ihre Angaben",
            "felder": [
                {"typ": "text", "label": "Ihr Name", "pflichtfeld": True,
                 "uebernahme": "kontaktname", "maxlaenge": 120},
                {"typ": "text", "label": "E-Mail", "pflichtfeld": True,
                 "uebernahme": "email", "maxlaenge": 160, "reg_exp": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
                {"typ": "text", "label": "Telefon", "pflichtfeld": False,
                 "uebernahme": "telefon", "maxlaenge": 60},
                {"typ": "adresse", "label": "Adresse", "pflichtfeld": False,
                 "uebernahme": "adresse"},
                {"typ": "mehrzeilig", "label": "Ihr Anliegen", "pflichtfeld": True,
                 "uebernahme": "anliegen", "maxlaenge": 2000},
                {"typ": "consent", "label": "Datenschutz", "pflichtfeld": True,
                 "hilfetext": "Ich willige in die Verarbeitung meiner Daten ein."},
            ],
        }
    ],
}

TEMPLATE_ENTRUEMPELUNG: dict = {
    "name": "Entrümpelung Anfrage",
    "komplexitaet": "einfach",
    "schritte": [
        {
            "titel": "Objekt & Umfang",
            "felder": [
                {"typ": "text", "label": "Ansprechpartner", "pflichtfeld": True,
                 "uebernahme": "kontaktname", "maxlaenge": 120},
                {"typ": "text", "label": "E-Mail", "pflichtfeld": True,
                 "uebernahme": "email", "maxlaenge": 160, "reg_exp": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
                {"typ": "text", "label": "Telefon", "pflichtfeld": False,
                 "uebernahme": "telefon", "maxlaenge": 60},
                {"typ": "adresse", "label": "Objektadresse", "pflichtfeld": True,
                 "uebernahme": "adresse"},
                {"typ": "dropdown", "label": "Art der Maßnahme", "pflichtfeld": True,
                 "optionen": [
                     {"label": "Komplette Wohnungsräumung", "wert": "wohnung"},
                     {"label": "Teilräumung / Keller", "wert": "teil"},
                     {"label": "Haushaltsauflösung", "wert": "haushalt"},
                 ]},
                {"typ": "mehrzeilig", "label": "Beschreibung", "pflichtfeld": True,
                 "uebernahme": "anliegen", "maxlaenge": 2000},
                {"typ": "consent", "label": "Datenschutz", "pflichtfeld": True,
                 "hilfetext": "Ich willige in die Verarbeitung meiner Daten ein."},
            ],
        }
    ],
}

TEMPLATES = {"shk": TEMPLATE_SHK, "entruempelung": TEMPLATE_ENTRUEMPELUNG}


def _next_position(mandant_id: str, formular_id: str, tabelle: str,
                   schritt_id: str | None = None, tx=None) -> int:
    eng = tx if tx is not None else db.engine
    if tabelle == "formular_feld" and schritt_id:
        if tx is None:
            rows = db.engine.query(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_feld "
                "WHERE mandant_id = %s AND schritt_id = %s",
                (mandant_id, schritt_id), mandant_id=mandant_id,
            )
        else:
            rows = tx.query(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_feld "
                "WHERE mandant_id = %s AND schritt_id = %s",
                (mandant_id, schritt_id),
            )
    else:
        if tx is None:
            rows = db.engine.query(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_schritt "
                "WHERE mandant_id = %s AND formular_id = %s",
                (mandant_id, formular_id), mandant_id=mandant_id,
            )
        else:
            rows = tx.query(
                "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_schritt "
                "WHERE mandant_id = %s AND formular_id = %s",
                (mandant_id, formular_id),
            )
    return int(rows[0]["next"])


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_formular(mandant_id: str, formular_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, name, komplexitaet, draft_revision, veroeffentlicht, "
        "aktuelle_version_id, created_at, updated_at "
        "FROM formular WHERE mandant_id = %s AND id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_formulare(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    total_rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formulare WHERE mandant_id = %s".replace("formulare", "formular"),
        (mandant_id,), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0
    rows = db.engine.query(
        "SELECT id, name, komplexitaet, draft_revision, veroeffentlicht, "
        "aktuelle_version_id, updated_at "
        "FROM formular WHERE mandant_id = %s ORDER BY updated_at DESC LIMIT %s OFFSET %s",
        (mandant_id, limit, offset), mandant_id=mandant_id,
    )
    return rows, total


def create_formular(mandant_id: str, name: str, komplexitaet: str, tx=None) -> str:
    fid = str(uuid.uuid4())
    if tx is None:
        db.engine.command(
            "INSERT INTO formular (id, mandant_id, name, komplexitaet, draft_revision) "
            "VALUES (%s, %s, %s, %s, 1)",
            (fid, mandant_id, name, komplexitaet), mandant_id=mandant_id,
        )
    else:
        tx.command(
            "INSERT INTO formular (id, mandant_id, name, komplexitaet, draft_revision) "
            "VALUES (%s, %s, %s, %s, 1)",
            (fid, mandant_id, name, komplexitaet),
        )
    return fid


def delete_formular(mandant_id: str, formular_id: str) -> None:
    db.engine.command(
        "DELETE FROM formular WHERE mandant_id = %s AND id = %s "
        "AND veroeffentlicht = FALSE AND aktuelle_version_id IS NULL",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )


def count_formulare(mandant_id: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def seed_template_tx(mandant_id: str, formular_id: str, tpl: dict, tx) -> None:
    """Transaktions-gebundenes Seeding einer Formularvorlage (analog zum
    öffentlichen create_formular-Pfad, aber läuft innerhalb von ``tx`` statt
    über die globale Engine — für die atomare Paketübernahme)."""
    for s in tpl["schritte"]:
        spos = _next_position(mandant_id, formular_id, "formular_schritt", tx=tx)
        sid = str(uuid.uuid4())
        tx.command(
            "INSERT INTO formular_schritt (id, mandant_id, formular_id, position, titel) "
            "VALUES (%s, %s, %s, %s, %s)",
            (sid, mandant_id, formular_id, spos, s["titel"]),
        )
        for f in s["felder"]:
            fpos = _next_position(mandant_id, formular_id, "formular_feld",
                                  schritt_id=sid, tx=tx)
            fid = str(uuid.uuid4())
            tx.command(
                "INSERT INTO formular_feld (id, mandant_id, formular_id, schritt_id, "
                "position, typ, label, hilfetext, pflichtfeld, optional_in_einfach, "
                "uebernahme) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (fid, mandant_id, formular_id, sid, fpos, f["typ"], f["label"],
                 f.get("hilfetext"), f.get("pflichtfeld", False),
                 f.get("optional_in_einfach", False), f.get("uebernahme")),
            )
            for i, opt in enumerate(f.get("optionen", []), start=1):
                oid = str(uuid.uuid4())
                tx.command(
                    "INSERT INTO formular_option (id, mandant_id, formular_id, feld_id, "
                    "position, label, wert) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (oid, mandant_id, formular_id, fid, i, opt["label"], opt["wert"]),
                )
def _bump_revision(mandant_id: str, formular_id: str, erwartet: int) -> dict:
    """Erhöht draft_revision atomar, wenn sie dem erwarteten Wert entspricht.

    Gibt das aktualisierte Formular zurück — oder None, wenn die Revision
    nicht stimmt (Optimistic-Concurrency-Konflikt -> 409 im Service).
    """
    if db.engine.is_postgres:
        rows = db.engine.query(
            "UPDATE formular SET draft_revision = draft_revision + 1, "
            "updated_at = NOW() "
            "WHERE mandant_id = %s AND id = %s AND draft_revision = %s "
            "RETURNING id, mandant_id, name, komplexitaet, draft_revision, "
            "veroeffentlicht, aktuelle_version_id, created_at, updated_at",
            (mandant_id, formular_id, erwartet), mandant_id=mandant_id,
        )
    else:
        cur = db.engine.query(
            "SELECT id FROM formular WHERE mandant_id = %s AND id = %s AND draft_revision = %s",
            (mandant_id, formular_id, erwartet), mandant_id=mandant_id,
        )
        if not cur:
            return None
        db.engine.command(
            "UPDATE formular SET draft_revision = draft_revision + 1, "
            "updated_at = %s WHERE mandant_id = %s AND id = %s",
            (_now_iso(), mandant_id, formular_id), mandant_id=mandant_id,
        )
        rows = db.engine.query(
            "SELECT id, mandant_id, name, komplexitaet, draft_revision, "
            "veroeffentlicht, aktuelle_version_id, created_at, updated_at "
            "FROM formular WHERE mandant_id = %s AND id = %s",
            (mandant_id, formular_id), mandant_id=mandant_id,
        )
    return rows[0] if rows else None


def patch_formular(mandant_id: str, formular_id: str, erwartet: int,
                   name: str | None, komplexitaet: str | None) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    sets = []
    params: list = []
    if name is not None:
        sets.append("name = %s")
        params.append(name)
    if komplexitaet is not None:
        sets.append("komplexitaet = %s")
        params.append(komplexitaet)
    if sets:
        params.extend([mandant_id, formular_id])
        db.engine.command(
            f"UPDATE formular SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
            tuple(params), mandant_id=mandant_id,
        )
        updated = get_formular(mandant_id, formular_id)
    return updated


# --- Schritte --------------------------------------------------------------


def list_schritte(mandant_id: str, formular_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, formular_id, position, titel FROM formular_schritt "
        "WHERE mandant_id = %s AND formular_id = %s ORDER BY position",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )


def add_schritt(mandant_id: str, formular_id: str, titel: str, erwartet: int) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    # Nächste Position = max(position)+1 bzw. 1.
    pos_rows = db.engine.query(
        "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_schritt "
        "WHERE mandant_id = %s AND formular_id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    pos = int(pos_rows[0]["next"])
    sid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_schritt (id, mandant_id, formular_id, position, titel) "
        "VALUES (%s, %s, %s, %s, %s)",
        (sid, mandant_id, formular_id, pos, titel), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def update_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                   erwartet: int, titel: str) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    db.engine.command(
        "UPDATE formular_schritt SET titel = %s WHERE mandant_id = %s AND id = %s",
        (titel, mandant_id, schritt_id), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def delete_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                   erwartet: int) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    db.engine.command(
        "DELETE FROM formular_schritt WHERE mandant_id = %s AND id = %s",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def reorder_schritte(mandant_id: str, formular_id: str, erwartet: int,
                     ordered_ids: list[str]) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    # Kollisionsfreie Neunummerierung: zuerst auf negative Platzhalter, dann
    # auf die Zielreihenfolge (vermeidet UNIQUE(position)-Konflikt bei SQLite).
    for i, sid in enumerate(ordered_ids, start=1):
        db.engine.command(
            "UPDATE formular_schritt SET position = %s WHERE mandant_id = %s AND id = %s",
            (-1000 - i, mandant_id, sid), mandant_id=mandant_id,
        )
    for i, sid in enumerate(ordered_ids, start=1):
        db.engine.command(
            "UPDATE formular_schritt SET position = %s WHERE mandant_id = %s AND id = %s",
            (i, mandant_id, sid), mandant_id=mandant_id,
        )
    return get_formular(mandant_id, formular_id)


# --- Felder ----------------------------------------------------------------


def list_felder(mandant_id: str, schritt_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, formular_id, schritt_id, position, typ, label, hilfetext, "
        "pflichtfeld, optional_in_einfach, uebernahme, min_val, max_val, ganzzahl, "
        "reg_exp, maxlaenge, datum_min, datum_max, max_anzahl "
        "FROM formular_feld WHERE mandant_id = %s AND schritt_id = %s ORDER BY position",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )


def list_optionen(mandant_id: str, feld_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, feld_id, position, label, wert FROM formular_option "
        "WHERE mandant_id = %s AND feld_id = %s ORDER BY position",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )


def add_feld(mandant_id: str, formular_id: str, schritt_id: str,
             erwartet: int, typ: str) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    pos_rows = db.engine.query(
        "SELECT COALESCE(MAX(position), 0) + 1 AS next FROM formular_feld "
        "WHERE mandant_id = %s AND schritt_id = %s",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )
    pos = int(pos_rows[0]["next"])
    fid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_feld (id, mandant_id, formular_id, schritt_id, "
        "position, typ, label, pflichtfeld) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (fid, mandant_id, formular_id, schritt_id, pos, typ, "", True), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def update_feld(mandant_id: str, formular_id: str, feld_id: str,
                erwartet: int, felddaten: dict) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    # Feld-Stammdaten.
    sets: list[str] = []
    params: list = []
    for col, key in (
        ("label", "label"), ("hilfetext", "hilfetext"),
        ("pflichtfeld", "pflichtfeld"), ("optional_in_einfach", "optional_in_einfach"),
        ("uebernahme", "uebernahme"), ("min_val", "min"), ("max_val", "max"),
        ("ganzzahl", "ganzzahl"), ("reg_exp", "reg_exp"),
        ("maxlaenge", "maxlaenge"), ("datum_min", "datum_min"),
        ("datum_max", "datum_max"), ("max_anzahl", "max_anzahl"),
    ):
        if key in felddaten:
            sets.append(f"{col} = %s")
            params.append(felddaten[key])
    if sets:
        params.extend([mandant_id, feld_id])
        db.engine.command(
            f"UPDATE formular_feld SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
            tuple(params), mandant_id=mandant_id,
        )
    # Optionen (Vollersatz, falls übergeben).
    optionen = felddaten.get("optionen")
    if optionen is not None:
        db.engine.command(
            "DELETE FROM formular_option WHERE mandant_id = %s AND feld_id = %s",
            (mandant_id, feld_id), mandant_id=mandant_id,
        )
        for i, opt in enumerate(optionen, start=1):
            oid = str(uuid.uuid4())
            db.engine.command(
                "INSERT INTO formular_option (id, mandant_id, formular_id, feld_id, "
                "position, label, wert) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (oid, mandant_id, formular_id, feld_id, i, opt["label"], opt["wert"]),
                mandant_id=mandant_id,
            )
    return get_formular(mandant_id, formular_id)


def delete_feld(mandant_id: str, formular_id: str, feld_id: str,
                erwartet: int) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    db.engine.command(
        "DELETE FROM formular_feld WHERE mandant_id = %s AND id = %s",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def reorder_felder(mandant_id: str, formular_id: str, schritt_id: str,
                   erwartet: int, ordered_ids: list[str]) -> dict | None:
    updated = _bump_revision(mandant_id, formular_id, erwartet)
    if not updated:
        return None
    for i, fid in enumerate(ordered_ids, start=1):
        db.engine.command(
            "UPDATE formular_feld SET position = %s WHERE mandant_id = %s AND id = %s",
            (-1000 - i, mandant_id, fid), mandant_id=mandant_id,
        )
    for i, fid in enumerate(ordered_ids, start=1):
        db.engine.command(
            "UPDATE formular_feld SET position = %s WHERE mandant_id = %s AND id = %s",
            (i, mandant_id, fid), mandant_id=mandant_id,
        )
    return get_formular(mandant_id, formular_id)


# --- Publish / Version -----------------------------------------------------


def get_published_version_by_public_id(public_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, formular_id, nummer, public_id, inhalt, "
        "veroeffentlicht_am FROM formular_version WHERE public_id = %s",
        (public_id,),
    )
    return rows[0] if rows else None


def list_versionen(mandant_id: str, formular_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, nummer, public_id, veroeffentlicht_am FROM formular_version "
        "WHERE mandant_id = %s AND formular_id = %s ORDER BY nummer",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )


def next_version_nummer(mandant_id: str, formular_id: str) -> int:
    rows = db.engine.query(
        "SELECT COALESCE(MAX(nummer), 0) + 1 AS next FROM formular_version "
        "WHERE mandant_id = %s AND formular_id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return int(rows[0]["next"])


def create_version(mandant_id: str, formular_id: str, nummer: int,
                   public_id: str, inhalt: dict) -> str:
    vid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_version (id, mandant_id, formular_id, nummer, "
        "public_id, inhalt, veroeffentlicht_von) VALUES (%s, %s, %s, %s, %s, %s, NULL)",
        (vid, mandant_id, formular_id, nummer, public_id, json.dumps(inhalt)),
        mandant_id=mandant_id,
    )
    return vid


def publish_version_link(mandant_id: str, formular_id: str, version_id: str) -> dict:
    db.engine.command(
        "UPDATE formular SET aktuelle_version_id = %s, veroeffentlicht = TRUE "
        "WHERE mandant_id = %s AND id = %s",
        (version_id, mandant_id, formular_id), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def unpublish_version_link(mandant_id: str, formular_id: str) -> dict:
    db.engine.command(
        "UPDATE formular SET aktuelle_version_id = NULL, veroeffentlicht = FALSE "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


# --- Einsendungen & Uploads (öffentlich) -----------------------------------


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


def get_formular_id_for_version(public_id: str) -> str | None:
    v = get_published_version_by_public_id(public_id)
    return v["formular_id"] if v else None


def count_uploads_for_kennung(mandant_id: str, uebermittlungskennung: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular_upload WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant_id, uebermittlungskennung), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def create_upload(mandant_id: str, formular_id: str, feld_id: str | None,
                  uebermittlungskennung: str, objektpfad: str, originalname: str,
                  mime_typ: str, groesse_bytes: int) -> str:
    uid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_upload (id, mandant_id, formular_id, feld_id, "
        "uebermittlungskennung, objektpfad, originalname, mime_typ, groesse_bytes) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (uid, mandant_id, formular_id, feld_id, uebermittlungskennung, objektpfad,
         originalname, mime_typ, groesse_bytes), mandant_id=mandant_id,
    )
    return uid


def get_uploads_by_kennung(mandant_id: str, formular_id: str,
                           uebermittlungskennung: str, upload_ids: list[str]) -> list[dict]:
    if not upload_ids:
        return []
    placeholders = ", ".join(["%s"] * len(upload_ids))
    rows = db.engine.query(
        f"SELECT id, feld_id, objektpfad, originalname, mime_typ, groesse_bytes "
        f"FROM formular_upload WHERE mandant_id = %s AND formular_id = %s "
        f"AND uebermittlungskennung = %s AND einsendung_id IS NULL "
        f"AND id IN ({placeholders})",
        (mandant_id, formular_id, uebermittlungskennung, *upload_ids),
        mandant_id=mandant_id,
    )
    return rows


def get_einsendung_by_kennung(mandant_id: str, uebermittlungskennung: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, spam_status, anfrage_id, vorgang_id "
        "FROM formular_einsendung WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant_id, uebermittlungskennung), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_einsendung(mandant_id: str, formular_id: str, version_id: str,
                      uebermittlungskennung: str, werte: dict,
                      consent_nachweis: dict | None, spam_status: str,
                      anfrage_id: str | None, vorgang_id: str | None) -> str:
    eid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_einsendung (id, mandant_id, formular_id, version_id, "
        "uebermittlungskennung, werte, consent_nachweis, spam_status, anfrage_id, "
        "vorgang_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (eid, mandant_id, formular_id, version_id, uebermittlungskennung,
         json.dumps(werte), json.dumps(consent_nachweis) if consent_nachweis else None,
         spam_status, anfrage_id, vorgang_id), mandant_id=mandant_id,
    )
    return eid


def link_uploads_to_einsendung(mandant_id: str, einsendung_id: str,
                               upload_ids: list[str]) -> None:
    if not upload_ids:
        return
    placeholders = ", ".join(["%s"] * len(upload_ids))
    db.engine.command(
        f"UPDATE formular_upload SET einsendung_id = %s WHERE mandant_id = %s "
        f"AND einsendung_id IS NULL AND id IN ({placeholders})",
        (einsendung_id, mandant_id, *upload_ids), mandant_id=mandant_id,
    )


def mark_anfrage_formular_einsendung(mandant_id: str, anfrage_id: str,
                                     einsendung_id: str) -> None:
    db.engine.command(
        "UPDATE anfrage SET formular_einsendung_id = %s WHERE mandant_id = %s AND id = %s",
        (einsendung_id, mandant_id, anfrage_id), mandant_id=mandant_id,
    )


# --- Listenansicht markierter Einsendungen --------------------------------


def list_einsendungen(mandant_id: str, nur_spam: bool, limit: int, offset: int
                      ) -> tuple[list[dict], int]:
    where = "WHERE e.mandant_id = %s"
    params: list = [mandant_id]
    if nur_spam:
        where += " AND e.spam_status = 'spam'"
    else:
        where += " AND e.spam_status = 'normal'"
    total_rows = db.engine.query(
        f"SELECT COUNT(*) AS c FROM formular_einsendung e {where}",
        tuple(params), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0
    rows = db.engine.query(
        "SELECT e.id, e.formular_id, f.name AS formular_name, e.version_id, "
        "e.uebermittlungskennung, e.spam_status, e.anfrage_id, e.vorgang_id, "
        "e.erstellt_am, e.werte "
        "FROM formular_einsendung e JOIN formular f ON f.id = e.formular_id "
        f"{where} ORDER BY e.erstellt_am DESC LIMIT %s OFFSET %s",
        tuple(params) + (limit, offset), mandant_id=mandant_id,
    )
    return rows, total


# --- Anfrage-Detail-Anreicherung ------------------------------------------


def get_einsendung_for_anfrage(mandant_id: str, anfrage_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT e.id, e.mandant_id, e.version_id, e.werte, e.consent_nachweis, "
        "e.spam_status, e.erstellt_am, f.name AS formular_name "
        "FROM formular_einsendung e JOIN formular f ON f.id = e.formular_id "
        "WHERE e.mandant_id = %s AND e.anfrage_id = %s",
        (mandant_id, anfrage_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


# --- Rate-Limit ------------------------------------------------------------


def count_recent_versuche(ip: str | None, tabelle: str, window_minutes: int) -> int:
    since = (_now_iso_dt() - datetime.timedelta(minutes=window_minutes)).isoformat()
    if ip:
        rows = db.engine.query(
            f"SELECT COUNT(*) AS c FROM {tabelle} WHERE ip = %s AND created_at >= %s",
            (ip, since),
        )
    else:
        rows = db.engine.query(
            f"SELECT COUNT(*) AS c FROM {tabelle} WHERE created_at >= %s",
            (since,),
        )
    return int(rows[0]["c"]) if rows else 0


def record_versuch(ip: str | None, tabelle: str) -> None:
    db.engine.command(
        f"INSERT INTO {tabelle} (id, ip, created_at) VALUES (%s, %s, %s)",
        (str(uuid.uuid4()), ip, _now_iso()),
    )


def _now_iso_dt() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)
