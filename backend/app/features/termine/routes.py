from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, get_current_user, require_role
from app.features.termine import schemas
from app.features.termine import service as termine_service

# Schreibende Endpunkte tragen require_role("Buero", "Inhaber") (AC-1, AC-5).
_write_roles = require_role("Buero", "Inhaber")

router = APIRouter(prefix="/termine", tags=["termine"])


def _ergebnis(result: dict) -> dict:
    return schemas.TerminErgebnis(**result).model_dump()


@router.get("", response_model=schemas.TerminListResult)
def list_termine(von: str | None = None, bis: str | None = None,
                 nutzer_ids: str | None = None,
                 user: CurrentUser = Depends(get_current_user)):
    ids = [i for i in (nutzer_ids or "").split(",") if i] if nutzer_ids else None
    return termine_service.list_termine(user, von, bis, ids)


@router.post("", response_model=schemas.TerminErgebnis, status_code=201)
def create_termin(payload: schemas.TerminCreate,
                  user: CurrentUser = Depends(_write_roles)):
    return _ergebnis(termine_service.create_termin(user, payload))


@router.get("/{termin_id}", response_model=schemas.TerminDetail)
def get_termin(termin_id: str, user: CurrentUser = Depends(get_current_user)):
    return termine_service.get_termin_detail(user, termin_id)


@router.patch("/{termin_id}", response_model=schemas.TerminErgebnis)
def update_termin(termin_id: str, payload: schemas.TerminUpdate,
                  user: CurrentUser = Depends(_write_roles)):
    return _ergebnis(termine_service.update_termin(user, termin_id, payload))


@router.post("/{termin_id}/absagen", response_model=schemas.TerminErgebnis)
def absagen(termin_id: str, user: CurrentUser = Depends(_write_roles)):
    return _ergebnis(termine_service.absagen(user, termin_id))


@router.post("/{termin_id}/zuweisungen", response_model=schemas.TerminErgebnis,
             status_code=201)
def zuweisen(termin_id: str, payload: schemas.ZuweisungCreate,
             user: CurrentUser = Depends(_write_roles)):
    return _ergebnis(termine_service.zuweisen(user, termin_id, payload.nutzer_id))


@router.delete("/{termin_id}/zuweisungen/{nutzer_id}",
               response_model=schemas.TerminErgebnis)
def entziehen(termin_id: str, nutzer_id: str,
              user: CurrentUser = Depends(_write_roles)):
    return _ergebnis(termine_service.entziehen(user, termin_id, nutzer_id))
