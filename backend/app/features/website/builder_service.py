from __future__ import annotations

import io
import json
import uuid

from PIL import Image, ImageOps

from app.errors import ConflictError, NotFoundError, StorageError, ValidationError
from app.features.website import builder_repository as repo
from app.features.website import repository as website_repo
from app.features.website import builder_schemas as sch
from app.features.website.builder_schemas import (
    BildRead,
    BuilderSectionRead,
    BuilderStateRead,
)
from app import storage as storage_mod

# Bildprüfung analog Logo/Anfragebild (Format/Magic Bytes, Größenlimit).
MAX_SECTION_BILD_BYTES = 8 * 1024 * 1024
BILD_ALLOWED_TYPEN = {"hero", "text_mit_bild"}

# Feste Zielformate je Sektion (cover-crop, kein Verzerren) und WebP-Qualität.
SECTION_BILD_ZIELFORMAT: dict[str, tuple[int, int]] = {
    "hero": (1920, 1080),
    "text_mit_bild": (1200, 900),
}
WEBP_QUALITY = 82
SEKTIONS_LABEL: dict[str, str] = {
    "hero": "Hero",
    "text_mit_bild": "Text mit Bild",
}

# Die in den Akzeptanzkriterien genannten acht Defaultsektionen mit neutralen
# Defaulttexten und sichtbarem Status (ein gelöschtes/ausgeblendetes Hero ist
# zulässig; mindestens eine sichtbare Sektion wird nicht erzwungen).
DEFAULT_SEKTIONEN: list[sch.SectionInhalt] = [
    sch.HeroInhalt(titel="Willkommen", text="", cta_typ="anfrage", cta_text="Anfrage starten"),
    sch.TextMitBildInhalt(titel="Über uns", text=""),
    sch.LeistungenInhalt(titel="Unsere Leistungen", einleitung="", cta_typ="leistungen",
                         cta_text="Leistungen ansehen"),
    sch.KennzahlenInhalt(titel="Kennzahlen", kennzahlen=[]),
    sch.AblaufInhalt(titel="So läuft es ab", schritte=[]),
    sch.FaqInhalt(titel="Häufige Fragen", fragen=[]),
    sch.KontaktInhalt(titel="Kontakt", einleitung="", cta_typ="kontakt", cta_text="Kontakt aufnehmen"),
    sch.CtaInhalt(titel="Bereit für Ihr Projekt?", text="", cta_typ="anfrage",
                  cta_text="Jetzt anfragen"),
]


def _version_conflict() -> None:
    raise ConflictError(
        "Ihr Builder-Stand war veraltet. Bitte laden Sie die Seite neu, "
        "bevor Sie die Änderung erneut speichern."
    )


def _ensure_landingpage(mandant_id: str) -> dict:
    lp = repo.get_landingpage(mandant_id)
    if lp is None:
        lp = repo.create_landingpage(mandant_id)
    return lp


def _public_bild(mandant_id: str, section: dict) -> BildRead | None:
    bild = repo.get_bild(mandant_id, section["id"])
    if not bild:
        return None
    domain = website_repo.get_domain(mandant_id)
    # Der Editor läuft auf der Betriebszentrale, nicht auf der öffentlichen
    # Mandantendomain. Ein relativer Pfad würde dort den falschen Host auflösen.
    url = f"/public/sections/{section['id']}/bild"
    if domain and domain["status"] == "aktiv":
        url = f"https://{domain['hostname']}{url}"
    return BildRead(
        url=url,
        alt_text=bild["alt_text"] or "",
        anzeigename=bild.get("anzeigename"),
    )


def _to_builder_section(mandant_id: str, section: dict) -> BuilderSectionRead:
    return BuilderSectionRead(
        id=section["id"],
        typ=section["typ"],
        visible=bool(section["visible"]),
        position=int(section["position"]),
        inhalt=json.loads(section["inhalt"]) if isinstance(section["inhalt"], str)
        else section["inhalt"],
        bild=_public_bild(mandant_id, section),
    )


def get_builder_state(mandant_id: str) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    sections = repo.list_sections(mandant_id, lp["id"])
    return BuilderStateRead(
        landingpage_id=lp["id"],
        version=int(lp["version"]),
        sections=[_to_builder_section(mandant_id, s) for s in sections],
    )


def initialize_landingpage(mandant_id: str) -> BuilderStateRead:
    lp = repo.get_landingpage(mandant_id)
    if lp is not None:
        # Idempotent: wiederholter Aufruf liefert den bestehenden Zustand.
        return get_builder_state(mandant_id)
    lp = repo.create_landingpage(mandant_id)
    for pos, inhalt in enumerate(DEFAULT_SEKTIONEN, start=1):
        repo.create_section(
            mandant_id, lp["id"], inhalt.typ, pos,
            json.loads(inhalt.model_dump_json()),
        )
    repo.bump_version(mandant_id, lp["id"], 1)
    return get_builder_state(mandant_id)


def add_section(mandant_id: str, typ: str, version: int) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    inhalt_cls = {
        "hero": sch.HeroInhalt, "text_mit_bild": sch.TextMitBildInhalt,
        "leistungen": sch.LeistungenInhalt, "kennzahlen": sch.KennzahlenInhalt,
        "ablauf": sch.AblaufInhalt, "faq": sch.FaqInhalt,
        "kontakt": sch.KontaktInhalt, "cta": sch.CtaInhalt,
    }[typ]
    position = repo.next_position(mandant_id, lp["id"])
    repo.create_section(mandant_id, lp["id"], typ, position,
                        json.loads(inhalt_cls().model_dump_json()))
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def patch_section(mandant_id: str, section_id: str, version: int,
                  visible: bool | None, inhalt: sch.SectionInhalt) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    section = repo.get_section(mandant_id, section_id)
    if not section:
        raise NotFoundError("Sektion nicht gefunden.")
    if section["typ"] != inhalt.typ:
        raise ValidationError("Der Sektionstyp darf nicht geändert werden.")
    repo.update_section(mandant_id, section_id, inhalt.typ, visible,
                        json.loads(inhalt.model_dump_json()))
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def set_reihenfolge(mandant_id: str, version: int,
                    ordered_ids: list[str]) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    vorhanden = repo.list_sections(mandant_id, lp["id"])
    vorhandene_ids = {s["id"] for s in vorhanden}
    # Vollständige, duplikatfreie Liste der vorhandenen IDs erwartet.
    if set(ordered_ids) != vorhandene_ids or len(ordered_ids) != len(vorhandene_ids):
        raise ValidationError(
            "Die Reihenfolge muss alle vorhandenen Sektionen genau einmal enthalten."
        )
    id_to_pos = {sid: i + 1 for i, sid in enumerate(ordered_ids)}
    repo.set_positions(mandant_id, lp["id"], id_to_pos)
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def delete_section(mandant_id: str, section_id: str, version: int) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    section = repo.get_section(mandant_id, section_id)
    if not section:
        raise NotFoundError("Sektion nicht gefunden.")
    # MinIO-Objekt mitlöschen, falls vorhanden.
    bild = repo.get_bild(mandant_id, section_id)
    if bild:
        _delete_object(bild)
    repo.delete_bild(mandant_id, section_id)
    repo.delete_section(mandant_id, section_id)
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def upload_section_bild(mandant_id: str, section_id: str, version: int,
                        dateiname: str, data: bytes, alt_text: str) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    section = repo.get_section(mandant_id, section_id)
    if not section:
        raise NotFoundError("Sektion nicht gefunden.")
    if section["typ"] not in BILD_ALLOWED_TYPEN:
        raise ValidationError(
            "Bilder sind nur für die Sektionstypen Hero und Text mit Bild erlaubt."
        )
    if _sniff_image_ext(data) is None:
        raise ValidationError("Nur Bilddateien (JPEG, PNG, GIF, WEBP) sind erlaubt.")
    if len(data) > MAX_SECTION_BILD_BYTES:
        raise ValidationError("Die Datei ist zu groß (maximal 8 MB).")

    # Konvertierung/Zuschnitt vor jeder Schreiboperation — schlägt sie fehl,
    # bleibt weder DB noch Speicher verändert (BUG-1).
    webp_data = _to_webp(data, section["typ"])

    inhalt = json.loads(section["inhalt"]) if isinstance(section["inhalt"], str) else section["inhalt"]
    anzeigename = _eindeutiger_anzeigename(
        mandant_id, _anzeigename_basis(section["typ"], inhalt), section_id
    )

    # Altes Bild erst nach erfolgreichem Schreiben des neuen ersetzen.
    old = repo.get_bild(mandant_id, section_id)
    objektpfad = f"website-sections/{mandant_id}/{section_id}/{uuid.uuid4()}.webp"
    try:
        storage_mod.image_storage.put_object(objektpfad, webp_data, "image/webp")
    except Exception as exc:
        raise StorageError() from exc
    if int(repo.get_landingpage(mandant_id)["version"]) != version:
        _delete_object_from(storage_mod.image_storage, objektpfad)
        _version_conflict()
    try:
        repo.upsert_bild(mandant_id, section_id, objektpfad, alt_text or "",
                         speicher_backend="website_images", content_type="image/webp",
                         anzeigename=anzeigename)
    except Exception:
        # Objekt bereits geschrieben, Metadaten aber nicht gespeichert: neues
        # Objekt best-effort wieder entfernen, damit nichts Unreferenziertes
        # ausgeliefert wird; alter Verweis bleibt unverändert bestehen.
        _delete_object_from(storage_mod.image_storage, objektpfad)
        raise
    if old:
        _delete_object(old)
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def delete_section_bild(mandant_id: str, section_id: str, version: int) -> BuilderStateRead:
    lp = _ensure_landingpage(mandant_id)
    if int(lp["version"]) != version:
        _version_conflict()
    section = repo.get_section(mandant_id, section_id)
    if not section:
        raise NotFoundError("Sektion nicht gefunden.")
    bild = repo.get_bild(mandant_id, section_id)
    if not bild:
        raise NotFoundError("Diese Sektion hat kein Bild.")
    _delete_object(bild)
    repo.delete_bild(mandant_id, section_id)
    # Bildentfernung lässt die Textvariante intakt; Landingpage-Version erhöhen.
    repo.bump_version(mandant_id, lp["id"], version)
    return get_builder_state(mandant_id)


def _delete_object(bild: dict) -> None:
    store = (storage_mod.image_storage if bild.get("speicher_backend") == "website_images"
             else storage_mod.storage)
    _delete_object_from(store, bild["objektpfad"])


def _delete_object_from(store, objektpfad: str) -> None:
    try:
        store.delete_object(objektpfad)
    except Exception:
        # Best-Effort: ein nicht löschbares Objekt blockiert nicht den Verweis-Delete.
        pass


def _sniff_image_ext(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _to_webp(data: bytes, typ: str) -> bytes:
    """Dekodiert, verwirft Animationen, schneidet unverzerrt (`cover`) auf das
    feste Sektionsformat zu und kodiert als einzelnes WebP (Qualität 82).
    Kleinere Quellbilder werden nicht künstlich hochskaliert (BUG-1)."""
    target_w, target_h = SECTION_BILD_ZIELFORMAT[typ]
    target_ratio = target_w / target_h
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise ValidationError(
            "Die Datei konnte nicht als Bild gelesen werden. Bitte ein gültiges "
            "JPEG-, PNG-, GIF- oder WebP-Bild hochladen."
        ) from exc
    if getattr(img, "is_animated", False):
        raise ValidationError(
            "Animierte Bilder werden nicht unterstützt. Bitte ein Standbild hochladen."
        )
    img = ImageOps.exif_transpose(img) or img

    src_w, src_h = img.size
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = max(1, round(src_h * target_ratio))
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    elif src_ratio < target_ratio:
        new_h = max(1, round(src_w / target_ratio))
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    if img.width > target_w:
        img = img.resize((target_w, target_h), Image.LANCZOS)

    if img.mode == "P":
        img = img.convert("RGBA" if "transparency" in img.info else "RGB")
    elif img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")

    try:
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=WEBP_QUALITY)
    except Exception as exc:
        raise ValidationError(
            "Das Bild konnte nicht verarbeitet werden. Bitte ein anderes Bild wählen."
        ) from exc
    return buf.getvalue()


def _anzeigename_basis(typ: str, inhalt: dict) -> str:
    label = SEKTIONS_LABEL.get(typ, typ)
    titel = (inhalt.get("titel") or "").strip() if isinstance(inhalt, dict) else ""
    if not titel:
        return f"{label}-Bild"
    return f"{label} – {titel}"


def _eindeutiger_anzeigename(mandant_id: str, basis: str, section_id: str) -> str:
    name = basis
    n = 2
    while repo.anzeigename_vergeben(mandant_id, name, section_id):
        name = f"{basis} ({n})"
        n += 1
    return name


# --- Öffentlich (kein Mandantenkontext bekannt) ---------------------------

def public_sections(mandant_id: str) -> list[dict]:
    """Liefert ausschließlich sichtbare Sektionen in sortierter Renderer-Form.
    Keine unsichtbare Sektion, kein Objektpfad, keine fremde/inaktive Leistung."""
    lp = repo.get_landingpage(mandant_id)
    if lp is None:
        return []
    sections = repo.list_sections(mandant_id, lp["id"])
    out = []
    for s in sections:
        if not s["visible"]:
            continue
        inhalt = json.loads(s["inhalt"]) if isinstance(s["inhalt"], str) else s["inhalt"]
        if s["typ"] in BILD_ALLOWED_TYPEN:
            bild = repo.get_bild(mandant_id, s["id"])
            if bild:
                inhalt = {
                    **inhalt,
                    "bild": {
                        "url": f"/public/sections/{s['id']}/bild",
                        "alt_text": bild["alt_text"] or "",
                    },
                }
        out.append(inhalt)
    return out
