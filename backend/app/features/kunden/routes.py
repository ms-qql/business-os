from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_role
from app.features.kunden import schemas
from app.features.kunden import service as kunden_service

router = APIRouter(prefix="/kunden", tags=["kunden"])

_write_roles = require_role("Buero", "Inhaber")


@router.get("", response_model=schemas.KundenListResponse)
def list_kunden(q: str | None = None, limit: int = 50, offset: int = 0,
                user: CurrentUser = Depends(_write_roles)):
    items, total = kunden_service.list_kunden(user.mandant_id, q, limit, offset)
    return schemas.KundenListResponse(
        items=[schemas.KundeRead(**k) for k in items], total=total, limit=limit, offset=offset,
    )


@router.post("", response_model=schemas.KundeCreateRead, status_code=201)
def create_kunde(payload: schemas.KundeCreate, user: CurrentUser = Depends(_write_roles)):
    result = kunden_service.create_kunde(
        user.mandant_id, payload.name, payload.email, payload.telefon, payload.notiz,
    )
    return schemas.KundeCreateRead(**result)


@router.get("/{kunde_id}", response_model=schemas.KundeRead)
def get_kunde(kunde_id: str, user: CurrentUser = Depends(_write_roles)):
    return schemas.KundeRead(**kunden_service.get_kunde(user.mandant_id, kunde_id))


@router.patch("/{kunde_id}", response_model=schemas.KundeRead)
def update_kunde(kunde_id: str, payload: schemas.KundeUpdate,
                 user: CurrentUser = Depends(_write_roles)):
    updated = kunden_service.update_kunde(
        user.mandant_id, kunde_id, payload.name, payload.email, payload.telefon, payload.notiz,
    )
    return schemas.KundeRead(**updated)


@router.delete("/{kunde_id}", status_code=204)
def delete_kunde(kunde_id: str, user: CurrentUser = Depends(_write_roles)):
    kunden_service.delete_kunde(user.mandant_id, kunde_id)


@router.get("/{kunde_id}/objekte", response_model=list[schemas.ObjektRead])
def list_objekte(kunde_id: str, user: CurrentUser = Depends(_write_roles)):
    return [schemas.ObjektRead(**o) for o in kunden_service.list_objekte(user.mandant_id, kunde_id)]


@router.post("/{kunde_id}/objekte", response_model=schemas.ObjektRead, status_code=201)
def create_objekt(kunde_id: str, payload: schemas.ObjektCreate,
                  user: CurrentUser = Depends(_write_roles)):
    objekt = kunden_service.create_objekt(user.mandant_id, kunde_id, payload.adresse, payload.notiz)
    return schemas.ObjektRead(**objekt)
