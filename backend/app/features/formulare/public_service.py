from __future__ import annotations

import json
import time
import uuid

from app.config import settings
from app.errors import ConflictError, NotFoundError, TooManyRequestsError, ValidationError
from app.features.formulare import repository as repo
from app.features.formulare.schemas import (
    EinsendungCreate, EinsendungResult, FeldOptionRead, OPTION_TYPEN,
    PublicFeld, PublicFormular, PublicSchritt,
)
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgang_repo
from app import storage as storage_mod

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
# Spam-Heuristik: Einsendung schneller als diese Sekunden gilt als verdächtig.
MIN_ABSENDE_SEKUNDEN = 3
UPLOAD_MIME = {
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
}
WEBP_MAGIC = (b"RIFF", b"WEBP")
PDF_MAGIC = b"%PDF-"
UPLOAD_ALLOWED_EXT = {"jpg", "png", "gif", "webp", "pdf"}


def _sniff_upload(data: bytes) -> tuple[str, str] | None:
    for magic, (ext, ct) in UPLOAD_MIME.items():
        if data.startswith(magic):
            return ext, ct
    if len(data) >= 12 and data[0:4] == WEBP_MAGIC[0] and data[8:12] == WEBP_MAGIC[1]:
        return "webp", "image/webp"
    if data.startswith(PDF_MAGIC):
        return "pdf", "application/pdf"
    return None


def _find_mandant(hostname: str) -> str:
    # Domain-Auflösung übernimmt das bestehende Website-Repository
    # (SECURITY DEFINER für öffentliche Hosts), um RLS zu umgehen.
    from app.features.website import repository as web_repo
    mid = web_repo.find_mandant_id_by_hostname(hostname)
    if not mid:
        raise NotFoundError("Formular nicht gefunden.")
    return mid


def get_public_snapshot(mandant_id: str, public_id: str) -> PublicFormular:
    version = repo.get_version_by_public_id(public_id)
    if not version or version["mandant_id"] != mandant_id or version["zurueckgezogen"]:
        raise NotFoundError("Formular nicht gefunden.")
    snapshot = version["snapshot"]
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    komplex = snapshot.get("komplexitaetsstufe", "einfach")
    schritte = []
    for s in snapshot.get("schritte", []):
        felder = []
        for f in s.get("felder", []):
            cfg = f.get("konfiguration") or {}
            optionen = [
                FeldOptionRead(id="", label=o["label"], wert=o["wert"])
                for o in f.get("optionen", [])
            ]
            felder.append(PublicFeld(
                id=f["id"], typ=f["typ"], label=f["label"], hilfetext=f["hilfetext"],
                pflichtfeld=bool(f["pflichtfeld"]), optionen=optionen,
                min=cfg.get("min"), max=cfg.get("max"),
                ganzzahl=bool(cfg.get("ganzzahl", False)), reg_exp=cfg.get("reg_exp"),
                maxlaenge=cfg.get("max_length"), datum_min=cfg.get("datum_min"),
                datum_max=cfg.get("datum_max"),
                max_anzahl=int(cfg.get("max_anzahl", 1)),
            ))
        schritte.append(PublicSchritt(id=s["id"], titel=s.get("titel", ""), felder=felder))
    return PublicFormular(
        name=snapshot.get("name", ""),
        modus=komplex,
        schritte=schritte,
    )


# --- Upload ---------------------------------------------------------------


def upload_datei(mandant_id: str, hostname: str, ip: str | None,
                 uebermittlungskennung: str, public_id: str, feld_id: str,
                 dateiname: str, data: bytes) -> str:
    # Mandant aus Hostname bestätigen (öffentlicher Pfad ohne Token).
    resolved = _find_mandant(hostname)
    if resolved != mandant_id:
        raise NotFoundError("Formular nicht gefunden.")

    # Rate-Limit (gleiches Muster wie PROJ-2-Anfrage).
    attempts = _count_attempts(ip)
    if attempts >= settings.anfrage_rate_limit_max:
        raise TooManyRequestsError()
    _record_attempt(ip)

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 15 MB).")
    sniffed = _sniff_upload(data)
    if sniffed is None:
        raise ValidationError("Nur Bilder (JPEG, PNG, GIF, WEBP) und PDF sind erlaubt.")
    ext, content_type = sniffed

    # Feld muss ein Upload-Feld der veröffentlichten Version sein.
    feld = _find_upload_feld(mandant_id, public_id, feld_id)
    if not feld:
        raise ValidationError("Ungültiges Upload-Feld.")
    max_anzahl = int((feld["konfiguration"] or {}).get("max_anzahl", 1))
    if repo.count_uploads_for_kennung(mandant_id, uebermittlungskennung) >= max_anzahl * 8:
        # Puffer gegen Missbrauch (mehrere Felder möglich); hartes Limit je Feld
        # wird beim Submit erneut geprüft.
        raise ValidationError("Zu viele Uploads für diese Übermittlung.")

    objektpfad = f"formulare/{mandant_id}/{uebermittlungskennung}/{uuid.uuid4()}.{ext}"
    storage_mod.storage.put_object(objektpfad, data, content_type)
    return repo.create_upload(
        mandant_id, uebermittlungskennung, feld_id, objektpfad, dateiname,
        content_type, len(data),
    )


def _find_upload_feld(mandant_id: str, public_id: str, feld_id: str) -> dict | None:
    version = repo.get_version_by_public_id(public_id)
    if not version or version["mandant_id"] != mandant_id:
        return None
    snapshot = version["snapshot"]
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    for s in snapshot.get("schritte", []):
        for f in s.get("felder", []):
            if f["id"] == feld_id and f["typ"] == "upload":
                cfg = f.get("konfiguration") or {}
                return {"konfiguration": cfg}
    return None


def _count_attempts(ip: str | None) -> int:
    from app.features.website import repository as web_repo
    return web_repo.count_recent_anfrage_attempts(ip, settings.anfrage_rate_limit_window_minutes)


def _record_attempt(ip: str | None) -> None:
    from app.features.website import repository as web_repo
    web_repo.record_anfrage_attempt(ip)


# --- Einsendung (atomare Übernahme) --------------------------------------


def submit_einsendung(mandant_id: str, hostname: str, ip: str | None,
                      public_id: str, payload: EinsendungCreate) -> EinsendungResult:
    resolved = _find_mandant(hostname)
    if resolved != mandant_id:
        raise NotFoundError("Formular nicht gefunden.")
    version = repo.get_version_by_public_id(public_id)
    if not version or version["mandant_id"] != mandant_id or version["zurueckgezogen"]:
        raise NotFoundError("Formular nicht gefunden.")

    # Idempotenz: dieselbe Übermittlungskennung liefert das erste Ergebnis.
    existing = repo.get_einsendung_by_kennung(mandant_id, payload.uebermittlungskennung)
    if existing:
        e = repo.get_einsendung(mandant_id, existing["id"])
        if not e:
            e = existing
        status = "spam" if e.get("spam_status") == "spam" else "erfolgreich"
        return EinsendungResult(status=status)  # type: ignore

    # Spam-Schutz: Honeypot gefüllt oder zu schnell abgesendet.
    spam = False
    if payload.honeypot.strip():
        spam = True
    if payload.client_start is not None:
        try:
            start = time.mktime(time.strptime(payload.client_start, "%Y-%m-%dT%H:%M:%S.%fZ"))
        except ValueError:
            try:
                start = time.mktime(time.strptime(payload.client_start, "%Y-%m-%dT%H:%M:%SZ"))
            except ValueError:
                start = 0.0
        if time.time() - start < MIN_ABSENDE_SEKUNDEN:
            spam = True

    snapshot = version["snapshot"]
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    komplex = snapshot.get("komplexitaetsstufe", "einfach")

    # Pflichtfeld-/Typprüfung (serverseitig). Spam wird trotzdem gespeichert,
    # aber ohne Anfrage/Vorgang.
    werte, upload_links = _validate_werte(
        mandant_id, payload.uebermittlungskennung, snapshot, komplex, payload.werte,
    )

    if spam:
        e = repo.create_einsendung(
            mandant_id, version["id"], payload.uebermittlungskennung,
            werte, _consent_nachweis(snapshot, werte), "spam",
        )
        if upload_links:
            repo.link_uploads_to_einsendung(mandant_id, e["id"], upload_links)
        return EinsendungResult(status="spam")  # type: ignore

    # Rate-Limit zählt erst nach Spam-Check (Spam soll nicht das Limit verbrauchen).
    attempts = _count_attempts(ip)
    if attempts >= settings.anfrage_rate_limit_max:
        raise TooManyRequestsError()
    _record_attempt(ip)

    # Atomare Übernahme als Anfrage + Kundenentwurf + Vorgang + Dokumente.
    einsendung = repo.create_einsendung(
        mandant_id, version["id"], payload.uebermittlungskennung, werte,
        _consent_nachweis(snapshot, werte), "normal",
    )
    uebernahme = _build_uebernahme_map(snapshot, werte)
    name = uebernahme.get("kontaktname") or "Interessent"
    email = uebernahme.get("email")
    telefon = uebernahme.get("telefon")
    adresse = uebernahme.get("adresse")
    anliegen = uebernahme.get("anliegen") or ""
    kontaktweg = "E-Mail" if email else "Telefon"

    # Anfrage mit Verweis auf die Einsendung anlegen.
    anfrage_id = repo.create_formular_anfrage(
        mandant_id, einsendung["id"], name, kontaktweg, telefon, email,
        adresse, anliegen, payload.uebermittlungskennung,
    )

    # Bestandskunde bei E-Mail-Treffer, sonst Kundenentwurf.
    kunde = kunden_repo.get_kunde_by_email(mandant_id, email) if email else None
    if not kunde:
        kunde = kunden_repo.create_kunde_status(
            mandant_id, name, email, telefon, None, "entwurf",
        )

    vorgang = vorgang_repo.create_vorgang(
        mandant_id, kunde["id"], None, "Neu", "Formular", anliegen,
        f"Formular-Einsendung ({version['nummer']})",
    )
    vorgang_repo.add_historie(
        mandant_id, vorgang["id"], "angelegt",
        f"Aus Formular-Einsendung übernommen ({einsendung['id']})", None,
    )
    # Uploads als Vorgangsdokumente referenzieren.
    if upload_links:
        for up in repo.get_unlinked_uploads(
                mandant_id, payload.uebermittlungskennung, "", upload_links):
            vorgang_repo.create_dokument(
                mandant_id, vorgang["id"], up["originalname"], up["objektpfad"],
                up["mime_typ"], up["groesse_bytes"], None,
            )
        repo.link_uploads_to_einsendung(mandant_id, einsendung["id"], upload_links)

    repo.link_einsendung_to_vorgang(mandant_id, einsendung["id"], anfrage_id, vorgang["id"])
    return EinsendungResult(status="erfolgreich")  # type: ignore


def _consent_nachweis(snapshot: dict, werte: dict) -> dict:
    nachweis = {"zeitpunkt": _now_iso(), "felder": {}}
    for s in snapshot.get("schritte", []):
        for f in s.get("felder", []):
            if f["typ"] == "consent":
                nachweis["felder"][f["id"]] = bool(werte.get(f["id"]))
    return nachweis


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _build_uebernahme_map(snapshot: dict, werte: dict) -> dict:
    mapping: dict = {}
    for s in snapshot.get("schritte", []):
        for f in s.get("felder", []):
            ziel = f.get("uebernahme")
            if ziel:
                val = werte.get(f["id"])
                if val is not None and str(val).strip():
                    mapping[ziel] = str(val)
    return mapping


def _validate_werte(mandant_id: str, kennung: str, snapshot: dict, komplex: str,
                    werte: list) -> tuple[dict, list[str]]:
    """Eingabe ist eine Liste von FeldWert-Objekten. Rückgabe ist ein
    flaches werte-Dict (feld_id -> skalarer Wert) für die DB plus die
    verknüpften Upload-IDs."""
    # Index nach feld_id für schnellen Zugriff.
    by_id: dict[str, object] = {w.feld_id: w for w in werte}
    flat: dict[str, object] = {}
    upload_links: list[str] = []

    for s in snapshot.get("schritte", []):
        for f in s.get("felder", []):
            feld_id = f["id"]
            typ = f["typ"]
            w = by_id.get(feld_id)
            # Pflicht/Optional-Logik: im Einfach-Modus sind option_in_einfach-
            # Felder unsichtbar und werden nicht geprüft.
            if komplex == "einfach" and f.get("optional_in_einfach"):
                continue
            if f["pflichtfeld"]:
                present = w is not None and _wert_vorhanden(w, typ)
                if not present:
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' ist erforderlich.")
            if w is None:
                continue
            val = _extract_wert(w, typ)
            flat[feld_id] = val
            cfg = f.get("konfiguration") or {}
            if typ in ("text", "mehrzeilig", "adresse"):
                if not isinstance(val, str):
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' muss ein Text sein.")
                if cfg.get("max_length") and len(val) > cfg["max_length"]:
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' ist zu lang.")
                if cfg.get("min_length") and len(val) < cfg["min_length"]:
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' ist zu kurz.")
            elif typ == "zahl":
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' muss eine Zahl sein.")
                num = float(val)
                if cfg.get("ganzzahl") and num != int(num):
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' muss ganzzahlig sein.")
                if cfg.get("min") is not None and num < cfg["min"]:
                    raise ValidationError(f"Der Wert von '{f['label'] or typ}' ist zu klein.")
                if cfg.get("max") is not None and num > cfg["max"]:
                    raise ValidationError(f"Der Wert von '{f['label'] or typ}' ist zu groß.")
            elif typ == "datum":
                if not isinstance(val, str) or not val:
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' braucht ein Datum.")
            elif typ in OPTION_TYPEN:
                opt_werte = {o["wert"] for o in f.get("optionen", [])}
                if val not in opt_werte:
                    raise ValidationError(f"Ungültige Auswahl bei '{f['label'] or typ}'.")
            elif typ == "consent":
                if not bool(val):
                    raise ValidationError(
                        f"Bitte bestätigen Sie: {f['label'] or 'Einverständnis'}.")
            elif typ == "upload":
                if not isinstance(val, list):
                    raise ValidationError(f"Das Feld '{f['label'] or typ}' erwartet Dateien.")
                max_anzahl = int(cfg.get("max_anzahl", 1))
                if len(val) > max_anzahl:
                    raise ValidationError(
                        f"Höchstens {max_anzahl} Datei(en) bei '{f['label'] or typ}'.")
                ups = repo.get_unlinked_uploads(mandant_id, kennung, feld_id, val)
                if len(ups) != len(val):
                    raise ValidationError("Eine oder mehrere Dateien sind ungültig.")
                upload_links.extend(u["id"] for u in ups)
    return flat, upload_links


def _wert_vorhanden(w, typ: str) -> bool:
    if typ == "consent":
        return bool(getattr(w, "wert", None))
    if typ in OPTION_TYPEN:
        return bool(getattr(w, "werte", None))
    if typ == "upload":
        return bool(getattr(w, "upload_ids", None))
    if typ == "zahl":
        return getattr(w, "zahl", None) is not None
    if typ == "datum":
        return bool(getattr(w, "datum", None))
    return bool(getattr(w, "wert", None))


def _extract_wert(w, typ: str):
    if typ == "consent":
        return bool(getattr(w, "wert", None))
    if typ in OPTION_TYPEN:
        vals = getattr(w, "werte", None) or []
        return vals[0] if vals else None
    if typ == "upload":
        return getattr(w, "upload_ids", None) or []
    if typ == "zahl":
        return getattr(w, "zahl", None)
    if typ == "datum":
        return getattr(w, "datum", None)
    return getattr(w, "wert", None)


# --- Spam-Liste (Inhaber/Büro) -------------------------------------------


def list_spam_einsendungen(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    return repo.list_einsendungen_spam(mandant_id, limit, offset)
