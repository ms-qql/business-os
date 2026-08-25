from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_role
from app.features.triage import schemas
from app.features.triage import service as triage_service

router = APIRouter(prefix="/triage", tags=["triage"])

_lesen = require_role("Inhaber", "Buero")
_inhaber = require_role("Inhaber")


@router.get("/einstellung", response_model=schemas.TriageEinstellungRead)
def get_einstellung(user: CurrentUser = Depends(_lesen)):
    return triage_service.get_einstellung(user.mandant_id)


@router.put("/einstellung", response_model=schemas.TriageEinstellungRead)
def put_einstellung(payload: schemas.TriageEinstellungPut,
                    user: CurrentUser = Depends(_inhaber)):
    return triage_service.setze_einstellung(
        user.mandant_id, payload.leistungs_formular_id, payload.leistungs_feld_id,
        payload.wunschtermin_feld_id, [w.model_dump() for w in payload.werte],
    )


@router.patch("/einstellung/kapazitaet", response_model=schemas.TriageEinstellungRead)
def patch_kapazitaet(payload: schemas.TriageKapazitaetPatch,
                     user: CurrentUser = Depends(_inhaber)):
    return triage_service.setze_kapazitaet(user.mandant_id, payload.naechster_freier_termin)
