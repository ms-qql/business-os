from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request

from app.deps import CurrentUser, get_current_user
from app.features.auth import schemas
from app.features.auth import service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request, authorization: str | None = Header(default=None)) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, request: Request):
    ip = _client_ip(request)
    token, user = auth_service.login(payload.email, payload.password, ip)
    return schemas.TokenResponse(access_token=token)


@router.post("/logout")
def logout(user: CurrentUser = Depends(get_current_user)):
    auth_service.logout(user.session_id)
    return {"ok": True}


@router.post("/invitations/accept")
def accept_invitation(payload: schemas.InvitationAcceptRequest):
    auth_service.accept_invitation(payload.token, payload.password)
    return {"ok": True}


@router.post("/password-reset")
def request_reset(payload: schemas.PasswordResetRequest, request: Request):
    ip = _client_ip(request)
    auth_service.request_password_reset(payload.email, ip)
    # Immer identische Antwort.
    return {"ok": True}


@router.post("/password-reset/confirm")
def confirm_reset(payload: schemas.PasswordResetConfirmRequest):
    auth_service.confirm_password_reset(payload.token, payload.password)
    return {"ok": True}


@router.get("/me", response_model=schemas.MeResponse)
def me(user: CurrentUser = Depends(get_current_user)):
    return schemas.MeResponse(
        id=user.id, mandant_id=user.mandant_id, name=user.name,
        email=user.email, role=user.role, status=user.status,
    )
