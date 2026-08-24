from __future__ import annotations

import datetime
import json
import uuid

from app import db


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Formular (Metadaten) -----------------------------------------------


def list_formulare(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    total_rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular WHERE mandant_id = %s",
        (mandant_id,), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0
    rows = db.engine.query(
        "SELECT f.id, f.name, f.komplexitaetsstufe, f.draft_revision, "
        "f.published_version_id, f.created_at, f.updated_at, v.public_id "
        "FROM formular f LEFT JOIN formular_version v "
        "ON v.id = f.published_version_id "
        "WHERE f.mandant_id = %s ORDER BY f.updated_at DESC LIMIT %s OFFSET %s",
        (mandant_id, limit, offset), mandant_id=mandant_id,
    )
    return rows, total


def get_formular(mandant_id: str, formular_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT f.id, f.mandant_id, f.name, f.komplexitaetsstufe, f.draft_revision, "
        "f.published_version_id, f.created_at, f.updated_at, v.public_id "
        "FROM formular f LEFT JOIN formular_version v ON v.id = f.published_version_id "
        "WHERE f.mandant_id = %s AND f.id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_formular(mandant_id: str, name: str, komplexitaetsstufe: str = "einfach") -> dict:
    fid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular (id, mandant_id, name, komplexitaetsstufe) "
        "VALUES (%s, %s, %s, %s)",
        (fid, mandant_id, name, komplexitaetsstufe), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, fid)


def update_formular(mandant_id: str, formular_id: str, fields: dict) -> dict:
    if not fields:
        return get_formular(mandant_id, formular_id)
    sets = [f"{col} = %s" for col in fields] + ["updated_at = %s"]
    params = list(fields.values()) + [_now(), mandant_id, formular_id]
    db.engine.command(
        f"UPDATE formular SET {', '.join(sets)} WHERE mandant_id = %s AND id = %s",
        tuple(params), mandant_id=mandant_id,
    )
    return get_formular(mandant_id, formular_id)


def delete_formular(mandant_id: str, formular_id: str) -> None:
    db.engine.command(
        "DELETE FROM formular WHERE mandant_id = %s AND id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )


def bump_revision(mandant_id: str, formular_id: str, current: int) -> int:
    db.engine.command(
        "UPDATE formular SET draft_revision = draft_revision + 1, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s AND draft_revision = %s",
        (_now(), mandant_id, formular_id, current), mandant_id=mandant_id,
    )
    return int(get_formular(mandant_id, formular_id)["draft_revision"])


def set_published_version(mandant_id: str, formular_id: str, version_id: str) -> None:
    db.engine.command(
        "UPDATE formular SET published_version_id = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (version_id, _now(), mandant_id, formular_id), mandant_id=mandant_id,
    )


def clear_published_version(mandant_id: str, formular_id: str) -> None:
    db.engine.command(
        "UPDATE formular SET published_version_id = NULL, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (_now(), mandant_id, formular_id), mandant_id=mandant_id,
    )


# --- Schritte ------------------------------------------------------------


def list_schritte(mandant_id: str, formular_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, formular_id, position, titel FROM formular_schritt "
        "WHERE mandant_id = %s AND formular_id = %s ORDER BY position ASC",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )


def get_schritt(mandant_id: str, schritt_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, formular_id, position, titel FROM formular_schritt "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def next_schritt_position(mandant_id: str, formular_id: str) -> int:
    rows = db.engine.query(
        "SELECT COALESCE(MAX(position), 0) AS m FROM formular_schritt "
        "WHERE mandant_id = %s AND formular_id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return int(rows[0]["m"]) + 1


def create_schritt(mandant_id: str, formular_id: str, titel: str = "") -> dict:
    sid = str(uuid.uuid4())
    pos = next_schritt_position(mandant_id, formular_id)
    db.engine.command(
        "INSERT INTO formular_schritt (id, mandant_id, formular_id, position, titel) "
        "VALUES (%s, %s, %s, %s, %s)",
        (sid, mandant_id, formular_id, pos, titel), mandant_id=mandant_id,
    )
    return get_schritt(mandant_id, sid)


def update_schritt(mandant_id: str, schritt_id: str, titel: str) -> None:
    db.engine.command(
        "UPDATE formular_schritt SET titel = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (titel, _now(), mandant_id, schritt_id), mandant_id=mandant_id,
    )


def set_schritt_position(mandant_id: str, formular_id: str, id_to_pos: dict[str, int]) -> None:
    # Kollisionsfreies Neunummerieren über Offset (wie website_builder).
    offset = 1_000_000
    for sid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE formular_schritt SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND formular_id = %s AND id = %s",
            (offset + pos, _now(), mandant_id, formular_id, sid), mandant_id=mandant_id,
        )
    for sid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE formular_schritt SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND formular_id = %s AND id = %s",
            (pos, _now(), mandant_id, formular_id, sid), mandant_id=mandant_id,
        )


def delete_schritt(mandant_id: str, schritt_id: str) -> None:
    db.engine.command(
        "DELETE FROM formular_schritt WHERE mandant_id = %s AND id = %s",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )


# --- Felder --------------------------------------------------------------


def list_felder(mandant_id: str, schritt_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, schritt_id, position, typ, label, hilfetext, pflichtfeld, "
        "optional_in_einfach, konfiguration, uebernahme "
        "FROM formular_feld WHERE mandant_id = %s AND schritt_id = %s ORDER BY position ASC",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )


def get_feld(mandant_id: str, feld_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, schritt_id, position, typ, label, hilfetext, pflichtfeld, "
        "optional_in_einfach, konfiguration, uebernahme "
        "FROM formular_feld WHERE mandant_id = %s AND id = %s",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def next_feld_position(mandant_id: str, schritt_id: str) -> int:
    rows = db.engine.query(
        "SELECT COALESCE(MAX(position), 0) AS m FROM formular_feld "
        "WHERE mandant_id = %s AND schritt_id = %s",
        (mandant_id, schritt_id), mandant_id=mandant_id,
    )
    return int(rows[0]["m"]) + 1


def create_feld(mandant_id: str, schritt_id: str, feld: dict) -> dict:
    fid = str(uuid.uuid4())
    pos = next_feld_position(mandant_id, schritt_id)
    db.engine.command(
        "INSERT INTO formular_feld (id, mandant_id, schritt_id, position, typ, label, "
        "hilfetext, pflichtfeld, optional_in_einfach, konfiguration, uebernahme) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (fid, mandant_id, schritt_id, pos, feld["typ"], feld["label"], feld["hilfetext"],
         feld["pflichtfeld"], feld["optional_in_einfach"],
         json.dumps(feld["konfiguration"], ensure_ascii=False), feld["uebernahme"]),
        mandant_id=mandant_id,
    )
    return get_feld(mandant_id, fid)


def update_feld(mandant_id: str, feld_id: str, feld: dict) -> None:
    db.engine.command(
        "UPDATE formular_feld SET typ = %s, label = %s, hilfetext = %s, pflichtfeld = %s, "
        "optional_in_einfach = %s, konfiguration = %s, uebernahme = %s, updated_at = %s "
        "WHERE mandant_id = %s AND id = %s",
        (feld["typ"], feld["label"], feld["hilfetext"], feld["pflichtfeld"],
         feld["optional_in_einfach"], json.dumps(feld["konfiguration"], ensure_ascii=False),
         feld["uebernahme"], _now(), mandant_id, feld_id),
        mandant_id=mandant_id,
    )


def set_feld_position(mandant_id: str, schritt_id: str, id_to_pos: dict[str, int]) -> None:
    offset = 2_000_000
    for fid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE formular_feld SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND schritt_id = %s AND id = %s",
            (offset + pos, _now(), mandant_id, schritt_id, fid), mandant_id=mandant_id,
        )
    for fid, pos in id_to_pos.items():
        db.engine.command(
            "UPDATE formular_feld SET position = %s, updated_at = %s "
            "WHERE mandant_id = %s AND schritt_id = %s AND id = %s",
            (pos, _now(), mandant_id, schritt_id, fid), mandant_id=mandant_id,
        )


def delete_feld(mandant_id: str, feld_id: str) -> None:
    db.engine.command(
        "DELETE FROM formular_feld WHERE mandant_id = %s AND id = %s",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )


# --- Optionen ------------------------------------------------------------


def list_optionen(mandant_id: str, feld_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, feld_id, position, label, wert FROM formular_option "
        "WHERE mandant_id = %s AND feld_id = %s ORDER BY position ASC",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )


def replace_optionen(mandant_id: str, feld_id: str, optionen: list[dict]) -> None:
    db.engine.command(
        "DELETE FROM formular_option WHERE mandant_id = %s AND feld_id = %s",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )
    for pos, opt in enumerate(optionen, start=1):
        db.engine.command(
            "INSERT INTO formular_option (id, mandant_id, feld_id, position, label, wert) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), mandant_id, feld_id, pos, opt["label"], opt["wert"]),
            mandant_id=mandant_id,
        )


# --- Versionen (Snapshot) ------------------------------------------------


def get_version_by_public_id(public_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, formular_id, nummer, snapshot, veroeffentlicht_am, "
        "zurueckgezogen FROM formular_version WHERE public_id = %s",
        (public_id,),
    )
    return rows[0] if rows else None


def get_published_version(mandant_id: str, formular_id: str, version_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, mandant_id, formular_id, nummer, snapshot, veroeffentlicht_am, "
        "zurueckgezogen FROM formular_version "
        "WHERE mandant_id = %s AND formular_id = %s AND id = %s",
        (mandant_id, formular_id, version_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def next_version_nummer(mandant_id: str, formular_id: str) -> int:
    rows = db.engine.query(
        "SELECT COALESCE(MAX(nummer), 0) AS m FROM formular_version "
        "WHERE mandant_id = %s AND formular_id = %s",
        (mandant_id, formular_id), mandant_id=mandant_id,
    )
    return int(rows[0]["m"]) + 1


def create_version(mandant_id: str, formular_id: str, nummer: int,
                   snapshot: dict, veroeffentlicht_von: str | None) -> dict:
    vid = str(uuid.uuid4())
    public_id = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_version (id, mandant_id, formular_id, nummer, public_id, "
        "snapshot, veroeffentlicht_von) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (vid, mandant_id, formular_id, nummer, public_id,
         json.dumps(snapshot, ensure_ascii=False), veroeffentlicht_von),
        mandant_id=mandant_id,
    )
    return get_published_version(mandant_id, formular_id, vid)


def withdraw_version(mandant_id: str, version_id: str) -> None:
    db.engine.command(
        "UPDATE formular_version SET zurueckgezogen = TRUE, zurueckgezogen_am = %s "
        "WHERE mandant_id = %s AND id = %s",
        (_now(), mandant_id, version_id), mandant_id=mandant_id,
    )


# --- Einsendungen / Uploads ----------------------------------------------


def get_einsendung_by_kennung(mandant_id: str, kennung: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id FROM formular_einsendung WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (mandant_id, kennung), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def create_einsendung(mandant_id: str, version_id: str, kennung: str,
                      werte: dict, consent: dict, spam_status: str) -> dict:
    eid = str(uuid.uuid4())
    # formular_id aus der Version ermitteln (für Leselisten/Spam-Übersicht).
    vrows = db.engine.query(
        "SELECT formular_id FROM formular_version WHERE mandant_id = %s AND id = %s",
        (mandant_id, version_id), mandant_id=mandant_id,
    )
    formular_id = vrows[0]["formular_id"] if vrows else None
    db.engine.command(
        "INSERT INTO formular_einsendung (id, mandant_id, formular_id, version_id, "
        "uebermittlungskennung, werte, consent_nachweis, spam_status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (eid, mandant_id, formular_id, version_id, kennung,
         json.dumps(werte, ensure_ascii=False),
         json.dumps(consent, ensure_ascii=False), spam_status),
        mandant_id=mandant_id,
    )
    rows = db.engine.query(
        "SELECT id, formular_id, uebermittlungskennung, werte, consent_nachweis, "
        "spam_status, eingegangen_am, anfrage_id, vorgang_id FROM formular_einsendung "
        "WHERE mandant_id = %s AND id = %s",
        (mandant_id, eid), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def mark_einsendung_to_vorgang(mandant_id: str, einsendung_id: str,
                               anfrage_id: str, vorgang_id: str) -> None:
    db.engine.command(
        "UPDATE formular_einsendung SET anfrage_id = %s, vorgang_id = %s "
        "WHERE mandant_id = %s AND id = %s",
        (anfrage_id, vorgang_id, mandant_id, einsendung_id), mandant_id=mandant_id,
    )


def count_uploads_for_kennung(mandant_id: str, kennung: str) -> int:
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular_upload WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant_id, kennung), mandant_id=mandant_id,
    )
    return int(rows[0]["c"]) if rows else 0


def create_upload(mandant_id: str, kennung: str, feld_id: str, objektpfad: str,
                  originalname: str, mime_typ: str, groesse_bytes: int) -> str:
    uid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO formular_upload (id, mandant_id, uebermittlungskennung, feld_id, "
        "objektpfad, originalname, mime_typ, groesse_bytes) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (uid, mandant_id, kennung, feld_id, objektpfad, originalname, mime_typ,
         groesse_bytes), mandant_id=mandant_id,
    )
    return uid


def get_unlinked_uploads(mandant_id: str, kennung: str, feld_id: str,
                         upload_ids: list[str]) -> list[dict]:
    if not upload_ids:
        return []
    placeholders = ", ".join(["%s"] * len(upload_ids))
    params = [mandant_id, kennung]
    if feld_id:
        fcond = "AND feld_id = %s "
        params.append(feld_id)
    else:
        fcond = ""
    rows = db.engine.query(
        f"SELECT id, objektpfad, originalname, mime_typ, groesse_bytes FROM formular_upload "
        f"WHERE mandant_id = %s AND uebermittlungskennung = %s {fcond}"
        f"AND einsendung_id IS NULL AND id IN ({placeholders})",
        (*params, *upload_ids), mandant_id=mandant_id,
    )
    return rows


def list_uploads_for_einsendung(mandant_id: str, einsendung_id: str) -> list[dict]:
    return db.engine.query(
        "SELECT id, originalname, mime_typ, groesse_bytes FROM formular_upload "
        "WHERE mandant_id = %s AND einsendung_id = %s ORDER BY created_at ASC",
        (mandant_id, einsendung_id), mandant_id=mandant_id,
    )


def link_uploads_to_einsendung(mandant_id: str, einsendung_id: str,
                               upload_ids: list[str]) -> None:
    if not upload_ids:
        return
    placeholders = ", ".join(["%s"] * len(upload_ids))
    db.engine.command(
        f"UPDATE formular_upload SET einsendung_id = %s "
        f"WHERE mandant_id = %s AND id IN ({placeholders})",
        (einsendung_id, mandant_id, *upload_ids), mandant_id=mandant_id,
    )


def get_einsendung(mandant_id: str, einsendung_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, formular_id, uebermittlungskennung, werte, consent_nachweis, "
        "spam_status, eingegangen_am, anfrage_id, vorgang_id "
        "FROM formular_einsendung WHERE mandant_id = %s AND id = %s",
        (mandant_id, einsendung_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def get_einsendung_by_vorgang(mandant_id: str, vorgang_id: str) -> dict | None:
    rows = db.engine.query(
        "SELECT id, formular_id, uebermittlungskennung, werte, consent_nachweis, "
        "spam_status, eingegangen_am, anfrage_id, vorgang_id "
        "FROM formular_einsendung WHERE mandant_id = %s AND vorgang_id = %s",
        (mandant_id, vorgang_id), mandant_id=mandant_id,
    )
    return rows[0] if rows else None


def list_einsendungen_spam(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    total_rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular_einsendung "
        "WHERE mandant_id = %s AND spam_status = 'spam'",
        (mandant_id,), mandant_id=mandant_id,
    )
    total = int(total_rows[0]["c"]) if total_rows else 0
    rows = db.engine.query(
        "SELECT e.id, e.formular_id, f.name AS formular_name, e.uebermittlungskennung, "
        "e.werte, e.consent_nachweis, e.spam_status, e.eingegangen_am, "
        "e.anfrage_id, e.vorgang_id "
        "FROM formular_einsendung e JOIN formular f ON f.id = e.formular_id "
        "WHERE e.mandant_id = %s AND e.spam_status = 'spam' "
        "ORDER BY e.eingegangen_am DESC LIMIT %s OFFSET %s",
        (mandant_id, limit, offset), mandant_id=mandant_id,
    )
    return rows, total


# --- Anfrage (formular_einsendung_id) ------------------------------------


def create_formular_anfrage(mandant_id: str, einsendung_id: str, name: str,
                            kontaktweg: str, telefon: str | None, email: str | None,
                            adresse: str | None, anliegen: str,
                            uebermittlungskennung: str) -> str:
    aid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO anfrage (id, mandant_id, name, kontaktweg, telefon, email, "
        "adresse, anliegen, dringlichkeit, quelle, uebermittlungskennung, "
        "formular_einsendung_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Normal', 'Formular', %s, %s)",
        (aid, mandant_id, name, kontaktweg, telefon, email, adresse or "",
         anliegen, uebermittlungskennung, einsendung_id),
        mandant_id=mandant_id,
    )
    return aid


def link_einsendung_to_vorgang(mandant_id: str, einsendung_id: str,
                               anfrage_id: str, vorgang_id: str) -> None:
    db.engine.command(
        "UPDATE formular_einsendung SET anfrage_id = %s, vorgang_id = %s "
        "WHERE mandant_id = %s AND id = %s",
        (anfrage_id, vorgang_id, mandant_id, einsendung_id), mandant_id=mandant_id,
    )


# --- Vorlagen (Release-Inhalt, kein Mandanten-Write) ---------------------


def get_vorlage(name: str) -> dict | None:
    return VORLAGEN.get(name)


def _pack_config(f: dict) -> dict:
    """Flache Editor-Konfiguration in die verschachtelte DB-Struktur."""
    return {
        "min_length": f.get("minlaenge"),
        "max_length": f.get("maxlaenge"),
        "min": f.get("min"),
        "max": f.get("max"),
        "ganzzahl": bool(f.get("ganzzahl", False)),
        "max_anzahl": f.get("max_anzahl", 1),
    }


# Jede Vorlage liefert Schritte mit Feldern + Optionen im selben Shape wie
# der Editor schreibt. uebernahme-Zuordnungen sind bereits gesetzt.
VORLAGEN: dict[str, list[dict]] = {
    "shk": [
        {
            "titel": "Ihre Kontaktdaten",
            "felder": [
                {"typ": "text", "label": "Ihr Name", "pflichtfeld": True,
                 "uebernahme": "kontaktname"},
                {"typ": "text", "label": "E-Mail", "pflichtfeld": True,
                 "konfiguration": {"max_length": 200}, "uebernahme": "email"},
                {"typ": "text", "label": "Telefon", "pflichtfeld": False,
                 "uebernahme": "telefon"},
                {"typ": "adresse", "label": "Adresse", "pflichtfeld": False,
                 "uebernahme": "adresse"},
            ],
        },
        {
            "titel": "Ihr Anliegen",
            "felder": [
                {"typ": "dropdown", "label": "Art der Anfrage", "pflichtfeld": True,
                 "optionen": [
                     {"label": "Heizung", "wert": "heizung"},
                     {"label": "Sanitär", "wert": "sanitaer"},
                     {"label": "Bad", "wert": "bad"},
                     {"label": "Notdienst", "wert": "notdienst"},
                 ]},
                {"typ": "mehrzeilig", "label": "Beschreibung", "pflichtfeld": True,
                 "konfiguration": {"max_length": 2000}, "uebernahme": "anliegen"},
                {"typ": "upload", "label": "Fotos / Dokumente", "pflichtfeld": False,
                 "konfiguration": {"max_anzahl": 5}},
            ],
        },
    ],
    "entruempelung": [
        {
            "titel": "Ihre Kontaktdaten",
            "felder": [
                {"typ": "text", "label": "Ihr Name", "pflichtfeld": True,
                 "uebernahme": "kontaktname"},
                {"typ": "text", "label": "E-Mail", "pflichtfeld": True,
                 "konfiguration": {"max_length": 200}, "uebernahme": "email"},
                {"typ": "text", "label": "Telefon", "pflichtfeld": False,
                 "uebernahme": "telefon"},
                {"typ": "adresse", "label": "Adresse der Entrümpelung", "pflichtfeld": True,
                 "uebernahme": "adresse"},
            ],
        },
        {
            "titel": "Umfang",
            "felder": [
                {"typ": "radio", "label": "Objektgröße", "pflichtfeld": True,
                 "optionen": [
                     {"label": "Bis 50 m²", "wert": "klein"},
                     {"label": "50–150 m²", "wert": "mittel"},
                     {"label": "Über 150 m²", "wert": "gross"},
                 ]},
                {"typ": "mehrzeilig", "label": "Besonderheiten", "pflichtfeld": False,
                 "konfiguration": {"max_length": 2000}, "uebernahme": "anliegen"},
                {"typ": "consent", "label": "Einverständnis Datenschutz",
                 "pflichtfeld": True},
            ],
        },
    ],
}
