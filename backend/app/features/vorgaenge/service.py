from __future__ import annotations

import uuid

from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as repo
from app.features.vorgaenge.schemas import VALID_STATUS
from app import storage as storage_mod

MAX_DOKUMENT_BYTES = 15 * 1024 * 1024


def _sniff_ext(data: bytes) -> tuple[str, str] | None:
    """(extension, content_type) anhand der Magic-Bytes — gleiches Muster wie
    website/service.py::_sniff_image_ext, um Foto UND PDF-Uploads am Vorgang
    zu erlauben."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif", "image/gif"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data.startswith(b"%PDF-"):
        return "pdf", "application/pdf"
    return None


def _guard_monteur_read(user, vorgang: dict) -> None:
    if user.role == "Monteur" and vorgang["zugewiesener_nutzer_id"] != user.id:
        raise ForbiddenError("Sie können nur Ihnen zugewiesene Vorgänge einsehen.")


def _require_vorgang(mandant_id: str, vorgang_id: str) -> dict:
    vorgang = repo.get_vorgang(mandant_id, vorgang_id)
    if not vorgang:
        raise NotFoundError("Vorgang nicht gefunden.")
    return vorgang


# --- Liste / Detail -----------------------------------------------------

def list_vorgaenge(user, status: str | None, q: str | None, kunde_id: str | None,
                   limit: int, offset: int) -> tuple[list[dict], int]:
    if status is not None and status not in VALID_STATUS:
        raise ValidationError("Ungültiger Status.")
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    zugewiesener_nutzer_id = user.id if user.role == "Monteur" else None
    return repo.list_vorgaenge(user.mandant_id, status, q, kunde_id, zugewiesener_nutzer_id,
                               limit, offset)


def get_vorgang_detail(user, vorgang_id: str) -> dict:
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)
    _guard_monteur_read(user, vorgang)
    historie = repo.list_historie(user.mandant_id, vorgang_id)
    dokumente = repo.list_dokumente(user.mandant_id, vorgang_id)
    return {**vorgang, "historie": historie, "dokumente": dokumente}


# --- Schreiben (Büro/Inhaber) -------------------------------------------

def create_vorgang(user, kunde_id: str, objekt_id: str | None, anliegen: str, quelle: str,
                   notizen: str | None, status: str) -> dict:
    if not kunden_repo.get_kunde(user.mandant_id, kunde_id):
        raise NotFoundError("Kunde nicht gefunden.")
    if objekt_id:
        objekt = kunden_repo.get_objekt(user.mandant_id, objekt_id)
        if not objekt or objekt["kunde_id"] != kunde_id:
            raise ValidationError("Objekt gehört nicht zu diesem Kunden.")
    vorgang = repo.create_vorgang(user.mandant_id, kunde_id, objekt_id, status, quelle,
                                  anliegen, notizen)
    repo.add_historie(user.mandant_id, vorgang["id"], "angelegt", f"Status={status}", user.id)
    return repo.get_vorgang_list_item(user.mandant_id, vorgang["id"])


def update_vorgang(user, vorgang_id: str, status: str | None, anliegen: str | None,
                   notizen: str | None, objekt_id: str | None) -> dict:
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)

    fields: dict = {}
    if status is not None:
        fields["status"] = status
    if anliegen is not None:
        fields["anliegen"] = anliegen
    if notizen is not None:
        fields["notizen"] = notizen
    if objekt_id is not None:
        objekt = kunden_repo.get_objekt(user.mandant_id, objekt_id)
        if not objekt or objekt["kunde_id"] != vorgang["kunde_id"]:
            raise ValidationError("Objekt gehört nicht zu diesem Kunden.")
        fields["objekt_id"] = objekt_id

    if not fields:
        return vorgang

    updated = repo.update_vorgang(user.mandant_id, vorgang_id, fields)
    if status is not None and status != vorgang["status"]:
        repo.add_historie(user.mandant_id, vorgang_id, "status_geaendert",
                          f"{vorgang['status']} -> {status}", user.id)
    for feld in ("anliegen", "notizen", "objekt_id"):
        if feld in fields:
            repo.add_historie(user.mandant_id, vorgang_id, "feld_geaendert", feld, user.id)
    return updated


def assign_vorgang(user, vorgang_id: str, nutzer_id: str) -> dict:
    _require_vorgang(user.mandant_id, vorgang_id)
    nutzer = repo.get_nutzer(user.mandant_id, nutzer_id)
    if not nutzer:
        raise NotFoundError("Nutzer nicht gefunden.")
    if nutzer["role"] != "Monteur":
        raise ValidationError("Ein Vorgang kann nur einem Monteur zugewiesen werden.")
    updated = repo.assign_vorgang(user.mandant_id, vorgang_id, nutzer_id)
    repo.add_historie(user.mandant_id, vorgang_id, "zugewiesen", nutzer["name"], user.id)
    return updated


# --- Dokumente ------------------------------------------------------------

def upload_dokument(user, vorgang_id: str, dateiname: str, data: bytes) -> dict:
    _require_vorgang(user.mandant_id, vorgang_id)
    if len(data) > MAX_DOKUMENT_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 15 MB).")
    sniffed = _sniff_ext(data)
    if sniffed is None:
        raise ValidationError("Nur Bilddateien (JPEG, PNG, GIF, WEBP) oder PDF sind erlaubt.")
    ext, content_type = sniffed
    objektpfad = f"vorgaenge/{user.mandant_id}/{vorgang_id}/{uuid.uuid4()}.{ext}"
    storage_mod.storage.put_object(objektpfad, data, content_type)
    dokument = repo.create_dokument(user.mandant_id, vorgang_id, dateiname, objektpfad,
                                    content_type, len(data), user.id)
    repo.add_historie(user.mandant_id, vorgang_id, "dokument_hochgeladen", dateiname, user.id)
    return dokument


def get_dokument_download_url(user, vorgang_id: str, dokument_id: str) -> str:
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)
    _guard_monteur_read(user, vorgang)
    dokument = repo.get_dokument(user.mandant_id, vorgang_id, dokument_id)
    if not dokument:
        raise NotFoundError("Dokument nicht gefunden.")
    return storage_mod.storage.presigned_get_url(dokument["objektpfad"])


def delete_dokument(user, vorgang_id: str, dokument_id: str) -> None:
    _require_vorgang(user.mandant_id, vorgang_id)
    dokument = repo.get_dokument(user.mandant_id, vorgang_id, dokument_id)
    if not dokument:
        raise NotFoundError("Dokument nicht gefunden.")
    repo.delete_dokument(user.mandant_id, vorgang_id, dokument_id)
    repo.add_historie(user.mandant_id, vorgang_id, "dokument_geloescht", dokument["dateiname"],
                      user.id)


# --- Anfragen-Übernahme --------------------------------------------------

def _ext_content_type(dateiname: str) -> str:
    lower = dateiname.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"


def uebernehme_anfrage(mandant_id: str, anfrage_id: str, kunde_id: str | None = None,
                       nutzer_id: str | None = None) -> dict:
    anfrage = repo.get_anfrage(mandant_id, anfrage_id)
    if not anfrage:
        raise NotFoundError("Anfrage nicht gefunden.")
    if anfrage["vorgang_id"]:
        raise ValidationError("Diese Anfrage wurde bereits übernommen.")

    if kunde_id:
        kunde = kunden_repo.get_kunde(mandant_id, kunde_id)
        if not kunde:
            raise NotFoundError("Kunde nicht gefunden.")
    else:
        kunde = kunden_repo.create_kunde(
            mandant_id, anfrage["name"], anfrage["email"], anfrage["telefon"], None,
        )
        kunde_id = kunde["id"]

    objekt_id = None
    if anfrage["adresse"]:
        objekt = kunden_repo.create_objekt(mandant_id, kunde_id, anfrage["adresse"], None)
        objekt_id = objekt["id"]

    notizen_teile = [f"Dringlichkeit: {anfrage['dringlichkeit']}"]
    if anfrage["zeitfenster"]:
        notizen_teile.append(f"Zeitfenster: {anfrage['zeitfenster']}")
    vorgang = repo.create_vorgang(
        mandant_id, kunde_id, objekt_id, "Neu", anfrage["quelle"] or "Website",
        anfrage["anliegen"], " | ".join(notizen_teile),
    )
    repo.add_historie(mandant_id, vorgang["id"], "angelegt",
                      f"Aus Anfrage übernommen ({anfrage_id})", nutzer_id)

    for bild in repo.list_anfragebilder(mandant_id, anfrage_id):
        dokument = repo.create_dokument(
            mandant_id, vorgang["id"], bild["dateiname"], bild["objektpfad"],
            _ext_content_type(bild["dateiname"]), 0, None,
        )
        repo.add_historie(mandant_id, vorgang["id"], "dokument_hochgeladen",
                          f"Aus Anfrage übernommen: {dokument['dateiname']}", None)

    repo.mark_anfrage_uebernommen(mandant_id, anfrage_id, vorgang["id"])
    return {"vorgang_id": vorgang["id"], "kunde_id": kunde_id, "objekt_id": objekt_id}
