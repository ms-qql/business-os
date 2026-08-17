from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


_fernet = Fernet(settings.email_credentials_key)


def encrypt_secret(plain: str) -> str:
    """Verschlüsselt ein Klartext-Geheimnis (z. B. Postfach-Passwort) für die DB."""
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Entschlüsselt ein in der DB gespeichertes Geheimnis zurück in Klartext."""
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        # Altlast ohne/mit falschem Key — als leer melden statt zu crashen.
        return ""
