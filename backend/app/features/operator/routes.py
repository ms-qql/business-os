from __future__ import annotations

from fastapi import APIRouter, Depends

from app.errors import AuthError
from app.features.operator import schemas
from app.features.operator import service as op_service
from app.features.operator.deps import CurrentOperator, get_current_operator

router = APIRouter(prefix="/operator", tags=["operator"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/auth/login", response_model=schemas.TokenResponse)
def operator_login(payload: schemas.OperatorLoginRequest):
    try:
        token, op = op_service.operator_login(payload.email, payload.password)
    except AuthError:
        raise AuthError("Betreiber-Anmeldung fehlgeschlagen.")
    return schemas.TokenResponse(access_token=token)


@router.post("/auth/logout")
def operator_logout(op: CurrentOperator = Depends(get_current_operator)):
    op_service.operator_logout(op.session_id)
    return {"ok": True}


@admin_router.post("/mandanten", response_model=schemas.MandantRead, status_code=201)
def create_mandant(payload: schemas.MandantCreateRequest,
                   op: CurrentOperator = Depends(get_current_operator)):
    mandant, _token = op_service.create_mandant_with_owner(
        payload.name, payload.owner_name, payload.owner_email
    )
    return schemas.MandantRead(**mandant)
