from __future__ import annotations


class AppError(Exception):
    """Base for domain errors that map to HTTP statuses."""

    status: int = 400
    message: str = "Fehler"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class AuthError(AppError):
    status = 401
    message = "Anmeldung fehlgeschlagen."


class NotFoundError(AppError):
    status = 404
    message = "Nicht gefunden."


class ForbiddenError(AppError):
    status = 403
    message = "Zugriff verweigert."


class ConflictError(AppError):
    status = 409
    message = "Konflikt."


class ValidationError(AppError):
    status = 422
    message = "Ungültige Eingabe."
