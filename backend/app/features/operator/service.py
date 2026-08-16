from __future__ import annotations

import datetime
import uuid

from app import security
from app.errors import AuthError, ConflictError, ValidationError
from app.features.auth import repository as auth_repo
from app.features.operator import repository as repo
from app.config import settings


def _expired(iso: str) -> bool:
    exp = datetime.datetime.fromisoformat(iso)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    return exp < datetime.datetime.now(datetime.timezone.utc)


def operator_login(email: str, password: str) -> tuple[str, dict]:
    op = repo.find_betreiber_by_email(email)
    if not op or not security.verify_password(password, op.get("password_hash")):
        raise AuthError("Betreiber-Anmeldung fehlgeschlagen.")
    session = repo.create_betreiber_session(op["id"])
    return security.make_token(session["id"], "operator", {"username": op["email"]}), op


def operator_logout(session_id: str) -> None:
    repo.revoke_betreiber_session(session_id)


def create_mandant_with_owner(name: str, owner_name: str, owner_email: str) -> tuple[dict, str]:
    if not name.strip():
        raise ValidationError("Betriebsname erforderlich.")
    if repo.find_betreiber_by_email(owner_email):
        raise ConflictError("E-Mail bereits als Betreiber registriert.")
    mandant = repo.create_mandant(name)
    owner = repo.create_owner_user(mandant["id"], owner_name, owner_email)
    token = str(uuid.uuid4())
    auth_repo.create_invitation(mandant["id"], owner["id"], token, settings.invitation_ttl_hours)
    auth_repo.audit(mandant["id"], owner["id"], "mandant_angelegt", True,
                    f"owner={owner_email}", None)
    return mandant, token
