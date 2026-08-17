from __future__ import annotations

import datetime
import uuid

from app import security
from app.config import settings
from app.errors import AuthError, NotFoundError, ValidationError
from app.features.auth import repository as repo


def _expired(iso: str) -> bool:
    exp = datetime.datetime.fromisoformat(str(iso))
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=datetime.timezone.utc)
    return exp < datetime.datetime.now(datetime.timezone.utc)


def login(email: str, password: str, ip: str | None) -> tuple[str, dict]:
    failures = repo.count_recent_failures(email, ip, settings.throttle_window_minutes)
    if failures >= settings.throttle_max_failures:
        repo.record_login_attempt(email, ip, False)
        raise AuthError("Anmeldung derzeit nicht möglich.")

    user = repo.find_user_by_email(email)
    if not user or not security.verify_password(password, user.get("password_hash")):
        repo.record_login_attempt(email, ip, False)
        # Bestehenden Nutzer für Audit mitführen, sofern bekannt.
        if user:
            repo.audit(user["mandant_id"], user["id"], "login", False, "falsches Passwort", ip)
        raise AuthError("E-Mail oder Passwort falsch.")

    if user["status"] == "disabled":
        repo.record_login_attempt(email, ip, False)
        repo.audit(user["mandant_id"], user["id"], "login", False, "deaktiviert", ip)
        raise AuthError("Konto deaktiviert.")

    if user["status"] == "invited":
        repo.record_login_attempt(email, ip, False)
        repo.audit(user["mandant_id"], user["id"], "login", False, "noch nicht aktiviert", ip)
        raise AuthError("Konto noch nicht aktiviert.")

    session = repo.create_session(user["mandant_id"], user["id"], ip)
    token = security.make_token(session["id"], "business")
    repo.record_login_attempt(email, ip, True)
    repo.audit(user["mandant_id"], user["id"], "login", True, None, ip)
    return token, user


def logout(session_id: str) -> None:
    repo.revoke_session(session_id)


def accept_invitation(token: str, password: str) -> None:
    inv = repo.get_invitation(token)
    if not inv or inv["used"] or _expired(inv["expires_at"]):
        raise ValidationError("Einladung ungültig oder abgelaufen.")
    repo.set_user_password(inv["nutzer_id"], security.hash_password(password))
    repo.mark_invitation_used(token)
    repo.audit(inv["mandant_id"], inv["nutzer_id"], "einladung_angnommen", True, None, None)


def request_password_reset(email: str, ip: str | None) -> None:
    user = repo.find_user_by_email(email)
    if user:
        token = str(uuid.uuid4())
        repo.create_password_reset(user["mandant_id"], user["id"], token,
                                   settings.reset_ttl_minutes)
        repo.audit(user["mandant_id"], user["id"], "passwort_reset_angefordert", True, None, ip)
    # Antwort bewusst identisch — verrät nicht, ob die Adresse existiert.


def confirm_password_reset(token: str, password: str) -> None:
    reset = repo.get_password_reset(token)
    if not reset or reset["used"] or _expired(reset["expires_at"]):
        raise ValidationError("Zurücksetzung ungültig oder abgelaufen.")
    repo.set_user_password(reset["nutzer_id"], security.hash_password(password))
    repo.revoke_user_sessions(reset["nutzer_id"])
    repo.mark_reset_used(token)
    repo.audit(reset["mandant_id"], reset["nutzer_id"], "passwort_reset_gesetzt", True, None, None)
