from __future__ import annotations

import uuid

from app.config import settings
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.features.auth import repository as auth_repo
from app.features.users import repository as repo
from app.security import hash_password


VALID_ROLES = ("Inhaber", "Buero", "Monteur")


def list_users(mandant_id: str, limit: int) -> list[dict]:
    limit = min(max(limit, 1), 200)
    return repo.list_users(mandant_id, limit)


def invite_user(mandant_id: str, name: str, email: str, role: str, ip: str | None) -> str:
    if role not in VALID_ROLES:
        raise ValidationError("Ungültige Rolle.")
    if repo.email_exists(mandant_id, email):
        raise ConflictError("E-Mail-Adresse bereits vergeben.")
    user = repo.create_user(mandant_id, name, email, role)
    token = str(uuid.uuid4())
    auth_repo.create_invitation(mandant_id, user["id"], token, settings.invitation_ttl_hours)
    auth_repo.audit(mandant_id, user["id"], "nutzer_eingeladen", True, f"Rolle={role}", ip)
    return token


def change_user(mandant_id: str, user_id: str, role: str | None,
                status: str | None) -> dict:
    user = repo.get_user(mandant_id, user_id)
    if not user:
        raise NotFoundError("Nutzer nicht gefunden.")

    # Letzten aktiven Inhaber schützen.
    if user["role"] == "Inhaber" and user["status"] == "active":
        if status == "disabled" and repo.count_active_owners(mandant_id) <= 1:
            raise ForbiddenError("Der letzte aktive Inhaber kann nicht deaktiviert werden.")
        if role is not None and role != "Inhaber":
            raise ForbiddenError("Die Rolle des letzten Inhabers kann nicht geändert werden.")

    updated = repo.update_user(mandant_id, user_id, role, status)
    auth_repo.audit(mandant_id, user_id, "nutzer_geaendert",
                    True, f"role={role}, status={status}", None)
    return updated
