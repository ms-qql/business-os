from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.deps import CurrentUser, get_current_user, require_role
from app.features.users import schemas
from app.features.users import service as users_service

router = APIRouter(prefix="/users", tags=["users"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("", response_model=list[schemas.UserRead])
def list_users(limit: int = 50, user: CurrentUser = Depends(require_role("Inhaber"))):
    return [schemas.UserRead(**u) for u in users_service.list_users(user.mandant_id, limit)]


@router.post("", response_model=schemas.UserRead, status_code=201)
def invite_user(payload: schemas.UserCreate,
                request: Request,
                user: CurrentUser = Depends(require_role("Inhaber"))):
    token = users_service.invite_user(
        user.mandant_id, payload.name, payload.email, payload.role, _client_ip(request)
    )
    created = users_service.list_users(user.mandant_id, 200)
    created = [u for u in created if u["email"] == payload.email]
    return schemas.UserRead(**created[0])


@router.patch("/{user_id}", response_model=schemas.UserRead)
def change_user(user_id: str, payload: schemas.UserUpdate,
                user: CurrentUser = Depends(require_role("Inhaber"))):
    updated = users_service.change_user(
        user.mandant_id, user_id, payload.role, payload.status
    )
    return schemas.UserRead(**updated)
