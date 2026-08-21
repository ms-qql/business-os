from __future__ import annotations

import re
import uuid

from app.config import settings
from app.errors import ConflictError, NotFoundError, TooManyRequestsError, ValidationError
from app.features.website import repository as repo
from app.features.website.schemas import AnfrageCreate, LeistungPatch
from app.features.vorgaenge import service as vorgaenge_service
from app import storage as storage_mod

# Vordefinierter SHK-Leistungskatalog (fest laut Tech Design — kein Baukasten).
SEED_LEISTUNGEN: list[tuple[str, str]] = [
    ("heizung", "Heizungsinstallation & -wartung"),
    ("sanitaer", "Sanitärinstallation"),
    ("bad", "Badsanierung"),
    ("notdienst", "Notdienst"),
    ("energie", "Energieberatung"),
]

MAX_UPLOADS = repo.MAX_UPLOADS_PER_ANFRAGE
MAX_BILD_BYTES = 8 * 1024 * 1024
MAX_LOGO_BYTES = 5 * 1024 * 1024

HOSTNAME_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$"
)


def _validate_hostname(raw: str) -> str:
    hostname = raw.strip().lower()
    if not HOSTNAME_RE.match(hostname):
        raise ValidationError(
            "Ungültige Domain. Bitte nur den Hostnamen angeben (z. B. beispiel.de), "
            "ohne https:// oder Pfad."
        )
    return hostname


def _sniff_image_ext(data: bytes) -> str | None:
    """Bestimmt den Bildtyp anhand der Datei-Magic-Bytes statt des vom Client
    behaupteten Content-Type — Upload-Prüfung darf sich nicht auf Client-
    Angaben verlassen."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _check_rate_limit(ip: str | None) -> None:
    attempts = repo.count_recent_anfrage_attempts(ip, settings.anfrage_rate_limit_window_minutes)
    if attempts >= settings.anfrage_rate_limit_max:
        raise TooManyRequestsError()
    repo.record_anfrage_attempt(ip)


def _get_or_create_settings(mandant_id: str) -> dict:
    row = repo.get_settings(mandant_id)
    if row is None:
        row = repo.create_default_settings(mandant_id)
    repo.seed_leistungen(mandant_id, SEED_LEISTUNGEN)
    return row


def _logo_url(row: dict) -> str | None:
    if not row.get("logo_objektpfad"):
        return None
    return storage_mod.storage.presigned_get_url(row["logo_objektpfad"])


def _resolve_mandant(hostname: str) -> str:
    mandant_id = repo.find_mandant_id_by_hostname(hostname)
    if not mandant_id:
        raise NotFoundError("Website nicht gefunden.")
    return mandant_id


# --- Öffentlich -------------------------------------------------------

def get_public_site(hostname: str) -> dict:
    mandant_id = _resolve_mandant(hostname)
    row = _get_or_create_settings(mandant_id)
    leistungen = repo.list_active_leistungen(mandant_id)
    from app.features.website import builder_service as builder_service

    sections = builder_service.public_sections(mandant_id)
    return {
        "firmenname": row["firmenname"] or "",
        "logo_url": _logo_url(row),
        "marken_farbe": row["marken_farbe"],
        "telefon": row["telefon"],
        "email": row["email"],
        "adresse": row["adresse"],
        "oeffnungszeiten": row["oeffnungszeiten"],
        "ueber_uns": row["ueber_uns"],
        "leistungen": leistungen,
        "sections": sections,
    }


def get_public_leistung(hostname: str, slug: str) -> dict:
    mandant_id = _resolve_mandant(hostname)
    leistung = repo.get_active_leistung(mandant_id, slug)
    if not leistung:
        raise NotFoundError("Leistung nicht gefunden.")
    return leistung


def upload_anfrage_bild(hostname: str, ip: str | None, uebermittlungskennung: str,
                        dateiname: str, data: bytes) -> str:
    _check_rate_limit(ip)
    mandant_id = _resolve_mandant(hostname)

    if len(data) > MAX_BILD_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 8 MB je Bild).")
    ext = _sniff_image_ext(data)
    if ext is None:
        raise ValidationError("Nur Bilddateien (JPEG, PNG, GIF, WEBP) sind erlaubt.")
    if repo.count_uploads_for_kennung(mandant_id, uebermittlungskennung) >= MAX_UPLOADS:
        raise ValidationError(f"Es sind höchstens {MAX_UPLOADS} Bilder je Anfrage erlaubt.")

    objektpfad = f"anfragen/{mandant_id}/{uebermittlungskennung}/{uuid.uuid4()}.{ext}"
    storage_mod.storage.put_object(objektpfad, data, f"image/{ext if ext != 'jpg' else 'jpeg'}")
    return repo.create_anfragebild(mandant_id, uebermittlungskennung, objektpfad, dateiname)


def submit_anfrage(hostname: str, ip: str | None, payload: AnfrageCreate) -> None:
    _check_rate_limit(ip)
    mandant_id = _resolve_mandant(hostname)

    if payload.kontaktweg == "Telefon" and not (payload.telefon and payload.telefon.strip()):
        raise ValidationError("Bitte geben Sie eine Telefonnummer an.")
    if payload.kontaktweg == "E-Mail" and not (payload.email and payload.email.strip()):
        raise ValidationError("Bitte geben Sie eine E-Mail-Adresse an.")
    if len(payload.upload_ids) > MAX_UPLOADS:
        raise ValidationError(f"Es sind höchstens {MAX_UPLOADS} Bilder je Anfrage erlaubt.")

    # Idempotenz: dieselbe Übermittlungskennung erzeugt höchstens eine Anfrage.
    existing = repo.get_anfrage_by_kennung(mandant_id, payload.uebermittlungskennung)
    if existing:
        return

    anfrage_id = repo.create_anfrage(
        mandant_id, payload.name, payload.kontaktweg, payload.telefon, payload.email,
        payload.adresse, payload.anliegen, payload.dringlichkeit, payload.zeitfenster,
        payload.uebermittlungskennung,
    )
    if payload.upload_ids:
        bilder = repo.get_unlinked_bilder(mandant_id, payload.uebermittlungskennung,
                                          payload.upload_ids)
        repo.link_bilder_to_anfrage(mandant_id, anfrage_id, [b["id"] for b in bilder])
    vorgaenge_service.uebernehme_anfrage(mandant_id, anfrage_id)


# --- Angemeldet (Inhaber) ----------------------------------------------

def get_website_settings(mandant_id: str) -> dict:
    row = _get_or_create_settings(mandant_id)
    domain = repo.get_domain(mandant_id)
    return {
        "firmenname": row["firmenname"] or "",
        "logo_url": _logo_url(row),
        "marken_farbe": row["marken_farbe"],
        "telefon": row["telefon"],
        "email": row["email"],
        "adresse": row["adresse"],
        "oeffnungszeiten": row["oeffnungszeiten"],
        "ueber_uns": row["ueber_uns"],
        "domain": domain["hostname"] if domain else None,
        "domain_status": domain["status"] if domain else None,
        "leistungen": repo.list_leistungen(mandant_id),
    }


def update_website_settings(mandant_id: str, firmenname: str | None, marken_farbe: str | None,
                            telefon: str | None, email: str | None, adresse: str | None,
                            oeffnungszeiten: str | None, ueber_uns: str | None,
                            leistungen: list[LeistungPatch] | None) -> dict:
    _get_or_create_settings(mandant_id)

    if firmenname is not None and not firmenname.strip():
        raise ValidationError("Firmenname darf nicht leer sein.")

    # ADR-7-2: Die Domain-Zuordnung ist kein Schreibpfad mehr. Sie erfolgt
    # ausschließlich über PUT /onboarding/domain (Reservierung, Status 'inaktiv')
    # und POST /onboarding/veroeffentlichen (Aktivierung). Hier wird kein
    # upsert_domain mehr aufgerufen.

    fields = {}
    for name, value in (
        ("firmenname", firmenname), ("marken_farbe", marken_farbe), ("telefon", telefon),
        ("email", email), ("adresse", adresse), ("oeffnungszeiten", oeffnungszeiten),
        ("ueber_uns", ueber_uns),
    ):
        if value is not None:
            fields[name] = value
    if fields:
        repo.update_settings(mandant_id, fields)

    if leistungen:
        for l in leistungen:
            repo.patch_leistung(mandant_id, l.slug, l.aktiv, l.kurzbeschreibung, l.inhalt)

    return get_website_settings(mandant_id)


def upload_logo(mandant_id: str, dateiname: str, data: bytes) -> str:
    _get_or_create_settings(mandant_id)
    if len(data) > MAX_LOGO_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 5 MB).")
    ext = _sniff_image_ext(data)
    if ext is None:
        raise ValidationError("Nur Bilddateien (JPEG, PNG, GIF, WEBP) sind erlaubt.")
    objektpfad = f"logo/{mandant_id}/{uuid.uuid4()}.{ext}"
    storage_mod.storage.put_object(objektpfad, data, f"image/{ext if ext != 'jpg' else 'jpeg'}")
    repo.set_logo(mandant_id, objektpfad)
    return storage_mod.storage.presigned_get_url(objektpfad)
