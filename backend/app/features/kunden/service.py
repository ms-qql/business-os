from __future__ import annotations

from app.errors import ConflictError, NotFoundError, ValidationError
from app.features.kunden import repository as repo


def list_kunden(mandant_id: str, q: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    return repo.list_kunden(mandant_id, q, limit, offset)


def get_kunde(mandant_id: str, kunde_id: str) -> dict:
    kunde = repo.get_kunde(mandant_id, kunde_id)
    if not kunde:
        raise NotFoundError("Kunde nicht gefunden.")
    return kunde


def create_kunde(mandant_id: str, name: str, email: str | None, telefon: str | None,
                 notiz: str | None) -> dict:
    duplikate = repo.find_moegliche_duplikate(mandant_id, email or None, telefon or None)
    kunde = repo.create_kunde(mandant_id, name, email, telefon, notiz)
    return {**kunde, "moegliche_duplikate": duplikate}


def update_kunde(mandant_id: str, kunde_id: str, name: str | None, email: str | None,
                 telefon: str | None, notiz: str | None) -> dict:
    get_kunde(mandant_id, kunde_id)
    if name is not None and not name.strip():
        raise ValidationError("Name darf nicht leer sein.")
    fields = {}
    for col, value in (("name", name), ("email", email), ("telefon", telefon), ("notiz", notiz)):
        if value is not None:
            fields[col] = value
    return repo.update_kunde(mandant_id, kunde_id, fields)


def delete_kunde(mandant_id: str, kunde_id: str) -> None:
    get_kunde(mandant_id, kunde_id)
    if repo.has_vorgaenge(mandant_id, kunde_id):
        raise ConflictError(
            "Kunde kann nicht gelöscht werden, solange Vorgänge bestehen."
        )
    repo.delete_kunde(mandant_id, kunde_id)


def list_objekte(mandant_id: str, kunde_id: str) -> list[dict]:
    get_kunde(mandant_id, kunde_id)
    return repo.list_objekte(mandant_id, kunde_id)


def create_objekt(mandant_id: str, kunde_id: str, adresse: str, notiz: str | None) -> dict:
    get_kunde(mandant_id, kunde_id)
    return repo.create_objekt(mandant_id, kunde_id, adresse, notiz)
