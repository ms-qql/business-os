from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError

# deps vorab vollständig laden, damit die Feature-Router (die deps importieren)
# beim include_router keine leeren Pfade durch einen Rest-Zyklus erben.
import app.deps  # noqa: F401

app = FastAPI(title="business_os API", version="0.1.5")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def register_routes() -> None:
    # Router werden hier (lazy) importiert, damit alle Module vollständig
    # geladen sind, bevor include_router aufgerufen wird. Das vermeidet
    # zirkuläre-Import-Artefakte (Router mit leeren Pfaden), die beim
    # modulebene-Import in main.py auftreten können.
    from app.features.auth import auth_router
    from app.features.email import email_router, internal_router
    from app.features.kunden import kunden_router
    from app.features.operator import admin_router, operator_router
    from app.features.users import users_router
    from app.features.users.routes import nutzer_router
    from app.features.vorgaenge import anfragen_router, vorgaenge_router
    from app.features.website import public_router, settings_router
    from app.features.angebote import angebote_router
    from app.features.termine import termine_router
    from app.features.onboarding import routes as onboarding_routes

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(nutzer_router)
    app.include_router(operator_router)
    app.include_router(admin_router)
    app.include_router(public_router)
    app.include_router(settings_router)
    app.include_router(kunden_router)
    app.include_router(vorgaenge_router)
    app.include_router(anfragen_router)
    app.include_router(email_router)
    app.include_router(internal_router)
    app.include_router(angebote_router)
    app.include_router(termine_router)
    app.include_router(onboarding_routes.router)
    app.include_router(onboarding_routes.katalog_router)


register_routes()
