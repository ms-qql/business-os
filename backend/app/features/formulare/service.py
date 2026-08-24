from __future__ import annotations

import re
import uuid

from app.config import settings
from app.errors import ConflictError, NotFoundError, ValidationError, TooManyRequestsError
from app.features.formulare import repository as repo
from app.features.formulare.schemas import (
    EinsendungCreate, FeldPatch, FormularCreate, FormularPatch, FeldTyp,
    Komplexitaet, SchrittPatch, SchrittReorder, FeldReorder,
)
from app import storage as storage_mod
from app import db
from app.features.kunden import repository as kunden_repo

AUSWAHL_TYPEN = {"dropdown", "kachel", "radio"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_UPLOADS_PRO_FELD = 5  # festes Mengenlimit je Uploadfeld (Tech Design)
UPLOAD_RATE_LIMIT_MAX = getattr(settings, "formular_upload_rate_limit_max", 20)
UPLOAD_RATE_LIMIT_WINDOW = getattr(settings, "formular_upload_rate_limit_window_min", 15)
EINSENDUNG_RATE_LIMIT_MAX = getattr(settings, "formular_einsendung_rate_limit_max", 20)
EINSENDUNG_RATE_LIMIT_WINDOW = getattr(settings, "formular_einsendung_rate_limit_window_min", 15)
# Mindestzeit zwischen client_start und Absenden, um Bot-Tempo zu bremsen.
MIN_ABSEND_INTERVAL_SEK = 1
MAX_ABSEND_INTERVAL_SEK = 4 * 60 * 60  # 4h obere Grenze gegen Uhrzeit-Manipulation


# ===========================================================================
# Angemeldete Routen: Entwurf
# ===========================================================================


def _entwurf_to_dict(mandant_id: str, formular: dict) -> dict:
    schritte = repo.list_schritte(mandant_id, formular["id"])
    out_schritte = []
    for s in schritte:
        felder = repo.list_felder(mandant_id, s["id"])
        out_felder = []
        for f in felder:
            f = dict(f)
            # Typkonfiguration in die Pydantic-freundlichen Feldnamen mappen.
            f["min"] = f.pop("min_val", None)
            f["max"] = f.pop("max_val", None)
            optionen = repo.list_optionen(mandant_id, f["id"])
            f["optionen"] = [
                {"id": o["id"], "label": o["label"], "wert": o["wert"]} for o in optionen
            ]
            out_felder.append(f)
        out_schritte.append({**s, "felder": out_felder})
    public_id = None
    if formular.get("aktuelle_version_id"):
        vrows = repo.list_versionen(mandant_id, formular["id"])
        vid = formular["aktuelle_version_id"]
        public_id = next((v["public_id"] for v in vrows if v["id"] == vid), None)
    return {
        **formular,
        "public_id": public_id,
        "schritte": out_schritte,
    }


def _require_formular(mandant_id: str, formular_id: str) -> dict:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    return formular


def list_formulare(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    items, total = repo.list_formulare(mandant_id, limit, offset)
    return [
        {
            "id": r["id"], "name": r["name"], "komplexitaet": r["komplexitaet"],
            "draft_revision": r["draft_revision"], "veroeffentlicht": r["veroeffentlicht"],
            "public_id": None,  # Liste liefert nicht die Snapshot-ID
            "updated_at": r["updated_at"],
        }
        for r in items
    ], total


def create_formular(mandant_id: str, payload: FormularCreate) -> dict:
    if payload.vorlage:
        tpl = repo.TEMPLATES[payload.vorlage]
        fid = repo.create_formular(mandant_id, tpl["name"], tpl["komplexitaet"])
        _seed_template(mandant_id, fid, tpl)
    else:
        fid = repo.create_formular(mandant_id, "Neues Formular", "einfach")
    formular = repo.get_formular(mandant_id, fid)
    return _entwurf_to_dict(mandant_id, formular)


def _seed_template(mandant_id: str, formular_id: str, tpl: dict) -> None:
    for s in tpl["schritte"]:
        spos = repo._next_position(mandant_id, formular_id, "formular_schritt")
        sid = str(uuid.uuid4())
        db.engine.command(
            "INSERT INTO formular_schritt (id, mandant_id, formular_id, position, titel) "
            "VALUES (%s, %s, %s, %s, %s)",
            (sid, mandant_id, formular_id, spos, s["titel"]), mandant_id=mandant_id,
        )
        for f in s["felder"]:
            fpos = repo._next_position(mandant_id, formular_id, "formular_feld", schritt_id=sid)
            fid = str(uuid.uuid4())
            db.engine.command(
                "INSERT INTO formular_feld (id, mandant_id, formular_id, schritt_id, "
                "position, typ, label, hilfetext, pflichtfeld, optional_in_einfach, "
                "uebernahme) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (fid, mandant_id, formular_id, sid, fpos, f["typ"], f["label"],
                 f.get("hilfetext"), f.get("pflichtfeld", False),
                 f.get("optional_in_einfach", False), f.get("uebernahme")),
                mandant_id=mandant_id,
            )
            for i, opt in enumerate(f.get("optionen", []), start=1):
                oid = str(uuid.uuid4())
                db.engine.command(
                    "INSERT INTO formular_option (id, mandant_id, formular_id, feld_id, "
                    "position, label, wert) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (oid, mandant_id, formular_id, fid, i, opt["label"], opt["wert"]),
                    mandant_id=mandant_id,
                )


def patch_formular(mandant_id: str, formular_id: str, payload: FormularPatch) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.patch_formular(mandant_id, formular_id, payload.draft_revision,
                                  payload.name, payload.komplexitaet)
    if not updated:
        raise ConflictError(
            "Das Formular wurde zwischenzeitlich von jemandem geändert. "
            "Bitte neu laden und erneut speichern."
        )
    return _entwurf_to_dict(mandant_id, updated)


def delete_formular(mandant_id: str, formular_id: str) -> None:
    formular = _require_formular(mandant_id, formular_id)
    if formular["veroeffentlicht"] or formular["aktuelle_version_id"]:
        raise ValidationError("Nur noch nie veröffentlichte Entwürfe können gelöscht werden.")
    repo.delete_formular(mandant_id, formular_id)


def add_schritt(mandant_id: str, formular_id: str, titel: str, draft_revision: int) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.add_schritt(mandant_id, formular_id, titel, draft_revision)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def update_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                   payload: SchrittPatch) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.update_schritt(mandant_id, formular_id, schritt_id,
                                  payload.draft_revision, payload.titel)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def delete_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                   draft_revision: int) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.delete_schritt(mandant_id, formular_id, schritt_id, draft_revision)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def reorder_schritte(mandant_id: str, formular_id: str,
                     payload: SchrittReorder) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.reorder_schritte(mandant_id, formular_id, payload.draft_revision,
                                    payload.ordered_ids)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def add_feld(mandant_id: str, formular_id: str, schritt_id: str,
             typ: FeldTyp, draft_revision: int) -> dict:
    _require_formular(mandant_id, formular_id)
    if typ not in repo.TEMPLATES:  # FeldTyp-Validierung (repo.TEMPLATES nicht relevant, nur Typ-Check)
        pass
    updated = repo.add_feld(mandant_id, formular_id, schritt_id, draft_revision, typ)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def update_feld(mandant_id: str, formular_id: str, feld_id: str,
                payload: FeldPatch) -> dict:
    _require_formular(mandant_id, formular_id)
    # Typcheck auf dem aktuellen Feld.
    feld_rows = repo.db.engine.query(
        "SELECT typ, schritt_id FROM formular_feld WHERE mandant_id = %s AND id = %s",
        (mandant_id, feld_id), mandant_id=mandant_id,
    )
    if not feld_rows:
        raise NotFoundError("Feld nicht gefunden.")
    typ = feld_rows[0]["typ"]
    felddaten = payload.model_dump(exclude_unset=True, exclude={"draft_revision"})
    # Optionen-Validierung serverseitig.
    optionen = felddaten.get("optionen")
    if optionen is not None:
        if typ in AUSWAHL_TYPEN:
            _validate_optionen_input(optionen)
        else:
            raise ValidationError("Dieses Feldtyp unterstützt keine Optionen.")
    felddaten = _clean_felddaten(typ, felddaten)
    updated = repo.update_feld(mandant_id, formular_id, feld_id,
                               payload.draft_revision, felddaten)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def delete_feld(mandant_id: str, formular_id: str, feld_id: str,
                draft_revision: int) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.delete_feld(mandant_id, formular_id, feld_id, draft_revision)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def reorder_felder(mandant_id: str, formular_id: str, schritt_id: str,
                   payload: FeldReorder) -> dict:
    _require_formular(mandant_id, formular_id)
    updated = repo.reorder_felder(mandant_id, formular_id, schritt_id,
                                  payload.draft_revision, payload.ordered_ids)
    if not updated:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    return _entwurf_to_dict(mandant_id, updated)


def _validate_optionen_input(optionen: list[dict]) -> None:
    if len(optionen) == 0:
        raise ValidationError("Auswahlfelder benötigen mindestens eine Option.")
    werte = [o["wert"].strip() for o in optionen]
    if any(w == "" for w in werte):
        raise ValidationError("Optionswerte dürfen nicht leer sein.")
    if len(set(werte)) != len(werte):
        raise ValidationError("Optionswerte müssen eindeutig sein.")


def _clean_felddaten(typ: str, felddaten: dict) -> dict:
    """Nimmt nur typrelevante Konfiguration mit; ignoriert Fremdfelder."""
    cleaned: dict = {"label": felddaten["label"], "hilfetext": felddaten.get("hilfetext"),
                     "pflichtfeld": felddaten.get("pflichtfeld", False),
                     "optional_in_einfach": felddaten.get("optional_in_einfach", False),
                     "uebernahme": felddaten.get("uebernahme")}
    if typ in AUSWAHL_TYPEN:
        cleaned["optionen"] = felddaten.get("optionen")
    if typ == "zahl":
        cleaned["min"] = felddaten.get("min")
        cleaned["max"] = felddaten.get("max")
        cleaned["ganzzahl"] = felddaten.get("ganzzahl")
    if typ == "text" or typ == "mehrzeilig":
        cleaned["maxlaenge"] = felddaten.get("maxlaenge")
        cleaned["reg_exp"] = felddaten.get("reg_exp")
    if typ == "datum":
        cleaned["datum_min"] = felddaten.get("datum_min")
        cleaned["datum_max"] = felddaten.get("datum_max")
    if typ == "upload":
        cleaned["max_anzahl"] = felddaten.get("max_anzahl") or MAX_UPLOADS_PRO_FELD
    return cleaned


# --- Publish / Einbindung --------------------------------------------------


def _build_snapshot(mandant_id: str, formular: dict) -> dict:
    schritte = repo.list_schritte(mandant_id, formular["id"])
    out_schritte = []
    for s in schritte:
        felder = repo.list_felder(mandant_id, s["id"])
        out_felder = []
        for f in felder:
            f = dict(f)
            f["min"] = f.pop("min_val", None)
            f["max"] = f.pop("max_val", None)
            optionen = repo.list_optionen(mandant_id, f["id"])
            f["optionen"] = [
                {"label": o["label"], "wert": o["wert"]} for o in optionen
            ]
            out_felder.append(f)
        out_schritte.append({"id": s["id"], "titel": s["titel"], "felder": out_felder})
    return {"name": formular["name"], "komplexitaet": formular["komplexitaet"],
            "schritte": out_schritte}


def _publish_check(mandant_id: str, formular: dict) -> None:
    snapshot = _build_snapshot(mandant_id, formular)
    if len(snapshot["schritte"]) < 1:
        raise ValidationError("Ein Formular benötigt mindestens einen Schritt.")
    alle_felder = [f for s in snapshot["schritte"] for f in s["felder"]]
    if len(alle_felder) < 1:
        raise ValidationError("Ein Formular benötigt mindestens ein Feld.")
    consent_pflicht = [f for f in alle_felder
                       if f["typ"] == "consent" and f.get("pflichtfeld")]
    if len(consent_pflicht) != 1:
        raise ValidationError(
            "Genau ein verpflichtendes Consent-Feld ist erforderlich.")
    # Auswahloptionen prüfen.
    for f in alle_felder:
        if f["typ"] in AUSWAHL_TYPEN:
            opts = f.get("optionen", [])
            if len(opts) == 0:
                raise ValidationError(
                    f"Das Auswahlfeld „{f['label'] or 'ohne Name'}“ hat keine Optionen.")
            werte = [o["wert"].strip() for o in opts]
            if any(w == "" for w in werte):
                raise ValidationError(
                    f"Das Auswahlfeld „{f['label'] or 'ohne Name'}“ hat leere Optionswerte.")
            if len(set(werte)) != len(werte):
                raise ValidationError(
                    f"Das Auswahlfeld „{f['label'] or 'ohne Name'}“ hat doppelte Optionswerte.")


def publish_formular(mandant_id: str, formular_id: str, draft_revision: int) -> dict:
    formular = _require_formular(mandant_id, formular_id)
    # Bei veralteter Revision -> Conflict (gleichzeitig draft_revision prüfen).
    if formular["draft_revision"] != draft_revision:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    _publish_check(mandant_id, formular)
    snapshot = _build_snapshot(mandant_id, formular)
    nummer = repo.next_version_nummer(mandant_id, formular_id)
    public_id = uuid.uuid4().hex
    version_id = repo.create_version(mandant_id, formular_id, nummer, public_id, snapshot)
    repo.publish_version_link(mandant_id, formular_id, version_id)
    updated = repo.get_formular(mandant_id, formular_id)
    return _entwurf_to_dict(mandant_id, updated)


def unpublish_formular(mandant_id: str, formular_id: str, draft_revision: int) -> dict:
    formular = _require_formular(mandant_id, formular_id)
    if formular["draft_revision"] != draft_revision:
        raise ConflictError("Das Formular wurde zwischenzeitlich geändert. Bitte neu laden.")
    repo.unpublish_version_link(mandant_id, formular_id)
    updated = repo.get_formular(mandant_id, formular_id)
    return _entwurf_to_dict(mandant_id, updated)


def get_einbindung(mandant_id: str, formular_id: str, hostname: str | None) -> dict:
    formular = _require_formular(mandant_id, formular_id)
    if not formular.get("aktuelle_version_id") or not formular["veroeffentlicht"]:
        raise ValidationError("Das Formular ist noch nicht veröffentlicht.")
    vrows = repo.list_versionen(mandant_id, formular_id)
    version = next((v for v in vrows if v["id"] == formular["aktuelle_version_id"]), None)
    if not version:
        raise NotFoundError("Veröffentlichung nicht gefunden.")
    public_id = version["public_id"]
    from app.features.website import repository as website_repo
    domain = website_repo.get_domain(mandant_id)
    public_hostname = domain["hostname"] if domain and domain["status"] == "aktiv" else hostname
    base = f"https://{public_hostname}" if public_hostname else ""
    direktlink = f"{base}/site/formulare/{public_id}" if base else f"/site/formulare/{public_id}"
    iframe = (f'<iframe src="{direktlink}" width="100%" height="800" '
              f'frameborder="0" title="{formular["name"]}"></iframe>')
    snippet = (
        f'<script src="{base}/formular-embed.js" data-formular="{public_id}" '
        f'data-target="formular-container"></script>\n'
        f'<div id="formular-container"></div>'
    )
    return {"direktlink": direktlink, "iframe": iframe, "snippet": snippet}


# ===========================================================================
# Öffentliche Routen
# ===========================================================================


def _resolve_mandant(hostname: str) -> str:
    mandant_id = repo.find_mandant_id_by_hostname(hostname)
    if not mandant_id:
        raise NotFoundError("Formular nicht gefunden.")
    return mandant_id


def get_public_formular(hostname: str, public_id: str) -> dict:
    mandant_id = _resolve_mandant(hostname)
    version = repo.get_published_version_by_public_id(public_id)
    if not version:
        raise NotFoundError("Formular nicht gefunden.")
    # Zugehörigkeit des public_id zum aufgelösten Mandanten (Domain-Treue).
    if version["mandant_id"] != mandant_id:
        raise NotFoundError("Formular nicht gefunden.")
    import json
    inhalt = version["inhalt"]
    if isinstance(inhalt, str):
        inhalt = json.loads(inhalt)
    # Snapshot speichert 'komplexitaet'; öffentliche API erwartet 'modus'.
    inhalt = dict(inhalt)
    inhalt["modus"] = inhalt.pop("komplexitaet", "einfach")
    return inhalt


def _sniff_ext(data: bytes) -> tuple[str, str] | None:
    """(extension, content_type) anhand Magic-Bytes — JPEG/PNG/WebP/PDF."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data.startswith(b"%PDF-"):
        return "pdf", "application/pdf"
    return None


def upload_datei(hostname: str, ip: str | None, public_id: str, feld_id: str,
                 uebermittlungskennung: str, dateiname: str, data: bytes) -> str:
    # Rate-Limit.
    if repo.count_recent_versuche(ip, "formular_upload_versuche",
                                   UPLOAD_RATE_LIMIT_WINDOW) >= UPLOAD_RATE_LIMIT_MAX:
        raise TooManyRequestsError()
    repo.record_versuch(ip, "formular_upload_versuche")

    mandant_id = _resolve_mandant(hostname)
    version = repo.get_published_version_by_public_id(public_id)
    if not version or version["mandant_id"] != mandant_id:
        raise NotFoundError("Formular nicht gefunden.")

    # Feld aus Snapshot ermitteln (Typ prüfen).
    feld = _snapshot_feld_fuer_id(version, feld_id)
    if not feld or feld["typ"] != "upload":
        raise ValidationError("Das Feld akzeptiert keine Uploads.")

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 15 MB je Datei).")
    sniffed = _sniff_ext(data)
    if sniffed is None:
        raise ValidationError("Nur JPEG, PNG, WebP oder PDF sind erlaubt.")
    ext, content_type = sniffed

    # Mengenlimit je Feld.
    max_anzahl = feld.get("max_anzahl") or MAX_UPLOADS_PRO_FELD
    feld_uploads = repo.db.engine.query(
        "SELECT COUNT(*) AS c FROM formular_upload WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s AND feld_id = %s",
        (mandant_id, uebermittlungskennung, feld_id), mandant_id=mandant_id,
    )
    if int(feld_uploads[0]["c"]) >= max_anzahl:
        raise ValidationError(f"Es sind höchstens {max_anzahl} Dateien je Feld erlaubt.")

    objektpfad = f"formular/{mandant_id}/{public_id}/{uebermittlungskennung}/{uuid.uuid4()}.{ext}"
    storage_mod.storage.put_object(objektpfad, data, content_type)
    return repo.create_upload(mandant_id, version["formular_id"], feld_id,
                              uebermittlungskennung, objektpfad, dateiname,
                              content_type, len(data))


def _snapshot_feld_fuer_id(version: dict, feld_id: str) -> dict | None:
    import json
    inhalt = version["inhalt"]
    if isinstance(inhalt, str):
        inhalt = json.loads(inhalt)
    for s in inhalt["schritte"]:
        for f in s["felder"]:
            if f["id"] == feld_id:
                return f
    return None


def submit_einsendung(hostname: str, ip: str | None, public_id: str,
                       payload: EinsendungCreate) -> str:
    # Rate-Limit.
    if repo.count_recent_versuche(ip, "formular_einsendung_versuche",
                                   EINSENDUNG_RATE_LIMIT_WINDOW) >= EINSENDUNG_RATE_LIMIT_MAX:
        raise TooManyRequestsError()
    repo.record_versuch(ip, "formular_einsendung_versuche")

    mandant_id = _resolve_mandant(hostname)
    version = repo.get_published_version_by_public_id(public_id)
    if not version or version["mandant_id"] != mandant_id:
        raise NotFoundError("Formular nicht gefunden.")

    # Honeypot.
    if payload.honeypot.strip():
        # Stille Spam-Markierung ohne Vorgang anlegen.
        _mark_spam(mandant_id, version, payload, ip)
        return "spam"

    # Zeitfenster: client_start darf nicht zu neu (Bot-Tempo) oder zu alt sein.
    if _is_zeitverletzung(payload.client_start):
        _mark_spam(mandant_id, version, payload, ip)
        return "spam"

    # Idempotenz: dieselbe Kennung -> erstes Ergebnis.
    existing = repo.get_einsendung_by_kennung(mandant_id, payload.uebermittlungskennung)
    if existing:
        return "erfolgreich" if existing["spam_status"] == "normal" else "spam"

    # Snapshot validieren (gleiche Regeln wie client, serverseitig maßgebend).
    if not _validate_snapshot_values(version, payload):
        # Ungültige Werte -> kein Vorgang; als spam markieren (nicht eindeutig bot).
        _mark_spam(mandant_id, version, payload, ip)
        return "spam"

    # Uploads verknüpfen (nur eigene, unverknüpfte dieser Kennung).
    upload_ids = _collect_upload_ids(payload)
    uploads = repo.get_uploads_by_kennung(mandant_id, version["formular_id"],
                                          payload.uebermittlungskennung, upload_ids)

    # Atomare Anlage: Einsendung + Anfrage + Kunde/Vorgang + Historie + Upload-Link.
    # Alle Schreiboperationen laufen zwingend im selben ctx (dieselbe Verbindung/
    # Transaktion), damit uncommittete Zeilen sichtbar sind und RLS greift.
    with repo.db.engine.transaction(mandant_id=mandant_id) as ctx:
        anfrage_id, vorgang_id, einsendung_id = _uebernahme(ctx, mandant_id, version, payload)
        _insert_einsendung(ctx, mandant_id, version, payload,
                           anfrage_id, vorgang_id)
        # Anfrage <-> Einsendung beidseitig verknüpfen (innerhalb derselben Tx).
        ctx.command(
            "UPDATE anfrage SET formular_einsendung_id = %s "
            "WHERE mandant_id = %s AND id = %s",
            (einsendung_id, mandant_id, anfrage_id),
        )
        uploads = repo.get_uploads_by_kennung(
            mandant_id, version["formular_id"], payload.uebermittlungskennung, upload_ids)
        for u in uploads:
            ctx.command(
                "UPDATE formular_upload SET einsendung_id = %s "
                "WHERE mandant_id = %s AND einsendung_id IS NULL AND id = %s",
                (einsendung_id, mandant_id, u["id"]),
            )
            # Uploads als Vorgangsdokumente referenzieren (wie Website-Anfrage-Muster).
            ctx.command(
                "INSERT INTO vorgang_dokument (id, mandant_id, vorgang_id, dateiname, "
                "objektpfad, content_type, groesse_bytes, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
                (str(uuid.uuid4()), mandant_id, vorgang_id, u["originalname"],
                 u["objektpfad"], u["mime_typ"], u["groesse_bytes"]),
            )
        ctx.command(
            "INSERT INTO vorgang_historie (id, mandant_id, vorgang_id, ereignis, detail) "
            "VALUES (%s, %s, %s, 'angelegt', %s)",
            (str(uuid.uuid4()), mandant_id, vorgang_id,
             f"Aus Formular-Einsendung übernommen ({einsendung_id})"),
        )
    return "erfolgreich"


def _is_zeitverletzung(client_start: str) -> bool:
    try:
        from datetime import datetime, timezone
        start = datetime.fromisoformat(client_start)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (now - start).total_seconds()
        if delta < MIN_ABSEND_INTERVAL_SEK or delta > MAX_ABSEND_INTERVAL_SEK:
            return True
    except Exception:
        return True
    return False


def _mark_spam(mandant_id: str, version: dict, payload: EinsendungCreate, ip: str | None) -> None:
    werte = _serialize_werte(payload)
    consent = _extract_consent(payload)
    repo.create_einsendung(mandant_id, version["formular_id"], version["id"],
                            payload.uebermittlungskennung, werte, consent,
                            "spam", None, None)


def _serialize_werte(payload: EinsendungCreate) -> dict:
    return {w.feld_id: w.model_dump(exclude_unset=True) for w in payload.werte}


def _extract_consent(payload: EinsendungCreate) -> dict | None:
    # Consent-Nachweis aus den Werten ableiten (Feld-Typ consent, wert='true').
    for w in payload.werte:
        if w.wert and w.wert.lower() in ("true", "1", "ja", "on"):
            return {"feld_id": w.feld_id, "erteilt": True}
    return None


def _collect_upload_ids(payload: EinsendungCreate) -> list[str]:
    ids: list[str] = []
    for w in payload.werte:
        if w.upload_ids:
            ids.extend(w.upload_ids)
    return ids


def _validate_snapshot_values(version: dict, payload: EinsendungCreate) -> bool:
    """Servervalidierung gegen den unveränderlichen Snapshot.

    Prüft Pflichtfelder, Wertebereiche, Auswahlwerte, Zahl/Integer, Länge,
    Regex, max_anzahl und Consent. Bei Verletzung -> False (führt zu Spam-
    Markierung ohne Vorgang, da wir keine Teilanlage wollen).
    """
    import json
    inhalt = version["inhalt"]
    if isinstance(inhalt, str):
        inhalt = json.loads(inhalt)
    werte_map = {w.feld_id: w for w in payload.werte}
    felder = [f for s in inhalt["schritte"] for f in s["felder"]]
    for f in felder:
        w = werte_map.get(f["id"])
        pflicht = f.get("pflichtfeld") or f["typ"] == "consent"
        if f["typ"] == "consent":
            if pflicht and (not w or not w.wert or w.wert.lower() not in ("true", "1", "ja", "on")):
                return False
            continue
        if f["typ"] == "adresse":
            if pflicht and (not w or not w.wert or not w.wert.strip()):
                return False
            continue
        if f["typ"] == "upload":
            ids = w.upload_ids if w else None
            if pflicht and (not ids or len(ids) == 0):
                return False
            max_anzahl = f.get("max_anzahl") or MAX_UPLOADS_PRO_FELD
            if ids and len(ids) > max_anzahl:
                return False
            continue
        if f["typ"] == "zahl":
            if pflicht and (w is None or w.zahl is None):
                return False
            if w and w.zahl is not None:
                if f.get("ganzzahl") and float(w.zahl) != int(w.zahl):
                    return False
                if f.get("min") is not None and w.zahl < f["min"]:
                    return False
                if f.get("max") is not None and w.zahl > f["max"]:
                    return False
            continue
        if f["typ"] == "datum":
            if pflicht and (not w or not w.datum):
                return False
            continue
        if f["typ"] in AUSWAHL_TYPEN:
            gewaehlt = w.werte if (w and w.werte) else None
            if pflicht and (not gewaehlt or len(gewaehlt) == 0):
                return False
            if gewaehlt:
                erlaubt = {o["wert"] for o in f.get("optionen", [])}
                if any(g not in erlaubt for g in gewaehlt):
                    return False
            continue
        # text / mehrzeilig
        text = (w.wert if w else None) or ""
        if pflicht and not text.strip():
            return False
        if f.get("maxlaenge") and len(text) > f["maxlaenge"]:
            return False
        if f.get("reg_exp") and text and not re.search(f["reg_exp"], text):
            return False
    return True


def _insert_einsendung(ctx, mandant_id: str, version: dict,
                       payload: EinsendungCreate,
                       anfrage_id: str | None = None,
                       vorgang_id: str | None = None) -> str:
    werte = _serialize_werte(payload)
    consent = _extract_consent(payload)
    eid = str(uuid.uuid4())
    ctx.command(
        "INSERT INTO formular_einsendung (id, mandant_id, formular_id, version_id, "
        "uebermittlungskennung, werte, consent_nachweis, spam_status, "
        "anfrage_id, vorgang_id) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, 'normal', %s, %s)",
        (eid, mandant_id, version["formular_id"], version["id"],
         payload.uebermittlungskennung, json_dumps(werte),
         json_dumps(consent) if consent else None, anfrage_id, vorgang_id),
    )
    return eid


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj)


def _uebernahme(ctx, mandant_id: str, version: dict, payload: EinsendungCreate,
                ) -> tuple[str, str, str]:
    """Erzeugt Anfrage + (Kunde oder Bestandsreferenz) + Vorgang.

    Folgt dem Muster von vorgaenge/repository.uebernehme_anfrage, hier aber
    aus dem Formular-Snapshot projiziert. Liefert (anfrage_id, vorgang_id,
    einsendung_id) zurück, damit die Einsendung dieselbe ID tragen kann.
    """
    import json
    einsendung_id = str(uuid.uuid4())
    werte_map = {w.feld_id: w for w in payload.werte}
    inhalt = version["inhalt"]
    if isinstance(inhalt, str):
        inhalt = json.loads(inhalt)
    felder = [f for s in inhalt["schritte"] for f in s["felder"]]

    def wert_von(zuordnung: str) -> str | None:
        for f in felder:
            if f.get("uebernahme") == zuordnung:
                w = werte_map.get(f["id"])
                if not w:
                    return None
                if f["typ"] == "zahl":
                    return str(w.zahl) if w.zahl is not None else None
                if f["typ"] in AUSWAHL_TYPEN:
                    return (w.werte or [None])[0]
                return w.wert
        return None

    name = wert_von("kontaktname") or "Unbekannt"
    email = wert_von("email")
    telefon = wert_von("telefon")
    adresse = wert_von("adresse") or ""
    anliegen = wert_von("anliegen") or ""

    # Anfrage anlegen (mit eindeutiger Kennung).
    anfrage_id = str(uuid.uuid4())
    ctx.command(
        "INSERT INTO anfrage (id, mandant_id, name, kontaktweg, telefon, email, adresse, "
        "anliegen, dringlichkeit, zeitfenster, quelle, uebermittlungskennung) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Normal', NULL, 'Formular', %s)",
        (anfrage_id, mandant_id, name, "E-Mail" if email else "Telefon",
         telefon, email, adresse, anliegen, payload.uebermittlungskennung),
    )

    # Kunde: Bestandskunde bei E-Mail-Treffer, sonst Entwurf.
    kunde_id = None
    if email:
        bestand = kunden_repo.get_kunde_by_email(mandant_id, email)
        if bestand:
            kunde_id = bestand["id"]
    if not kunde_id:
        kunde_id = str(uuid.uuid4())
        ctx.command(
            "INSERT INTO kunde (id, mandant_id, name, email, telefon, status) "
            "VALUES (%s, %s, %s, %s, %s, 'entwurf')",
            (kunde_id, mandant_id, name, email, telefon),
        )

    # Objekt (bei Adresse).
    objekt_id = None
    if adresse:
        objekt_id = str(uuid.uuid4())
        ctx.command(
            "INSERT INTO objekt (id, mandant_id, kunde_id, adresse) VALUES (%s, %s, %s, %s)",
            (objekt_id, mandant_id, kunde_id, adresse),
        )

    # Vorgang.
    vorgang_id = str(uuid.uuid4())
    ctx.command(
        "INSERT INTO vorgang (id, mandant_id, kunde_id, objekt_id, status, quelle, "
        "anliegen, notizen) VALUES (%s, %s, %s, %s, 'Neu', 'Formular', %s, %s)",
        (vorgang_id, mandant_id, kunde_id, objekt_id, anliegen,
         f"Formular-Einsendung {einsendung_id}"),
    )
    # Anfrage mit Vorgang verknüpfen.
    ctx.command(
        "UPDATE anfrage SET vorgang_id = %s WHERE id = %s",
        (vorgang_id, anfrage_id),
    )
    return anfrage_id, vorgang_id, einsendung_id


# ===========================================================================
# Listenansicht markierter Einsendungen
# ===========================================================================


def list_einsendungen(mandant_id: str, nur_spam: bool, limit: int, offset: int) -> tuple[list[dict], int]:
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    items, total = repo.list_einsendungen(mandant_id, nur_spam, limit, offset)
    out = []
    for r in items:
        werte = r["werte"]
        if isinstance(werte, str):
            import json
            werte = json.loads(werte)
        out.append({
            "id": r["id"], "formular_id": r["formular_id"],
            "formular_name": r["formular_name"], "version_id": r["version_id"],
            "uebermittlungskennung": r["uebermittlungskennung"],
            "spam_status": r["spam_status"], "anfrage_id": r.get("anfrage_id"),
            "vorgang_id": r.get("vorgang_id"), "erstellt_am": r["erstellt_am"],
            "werte": werte,
        })
    return out, total


def get_einsendung_fuer_anfrage(mandant_id: str, anfrage_id: str) -> dict | None:
    e = repo.get_einsendung_for_anfrage(mandant_id, anfrage_id)
    if not e:
        return None
    werte = e["werte"]
    if isinstance(werte, str):
        import json
        werte = json.loads(werte)
    consent = e.get("consent_nachweis")
    if isinstance(consent, str):
        import json
        consent = json.loads(consent)
    return {**e, "werte": werte, "consent_nachweis": consent}
