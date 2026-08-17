from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.config import settings
from app.deps import CurrentUser, require_role
from app.features.website import schemas
from app.features.website import service as website_service

public_router = APIRouter(prefix="/public", tags=["public-website"])
settings_router = APIRouter(prefix="/website-settings", tags=["website-settings"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _hostname(request: Request) -> str:
    """Mandant wird ausschließlich über den aufgelösten Hostnamen bestimmt,
    nie über Client-/Formularangaben. `x-forwarded-host` deckt den Fall ab,
    dass Next.js die Anfrage server-seitig weiterreicht (rewrites) — aber nur,
    wenn der Request nachweislich vom internen Next.js-Proxy kommt (Shared
    Secret). Sonst ist der Header client-spoofbar (SEC-1) und wird verworfen."""
    trusted_proxy = bool(settings.internal_proxy_secret) and (
        request.headers.get("x-internal-proxy-secret") == settings.internal_proxy_secret
    )
    fwd = request.headers.get("x-forwarded-host") if trusted_proxy else None
    host = (fwd or request.headers.get("host") or "").split(",")[0].strip()
    return host.split(":")[0]


# --- Öffentliche Website -------------------------------------------------

@public_router.get("/site", response_model=schemas.PublicSite)
def get_site(request: Request):
    return website_service.get_public_site(_hostname(request))


@public_router.get("/leistungen/{slug}", response_model=schemas.PublicLeistungDetail)
def get_leistung(slug: str, request: Request):
    return website_service.get_public_leistung(_hostname(request), slug)


@public_router.post("/anfragen/uploads", response_model=schemas.AnfrageUploadRead, status_code=201)
async def upload_anfrage_bild(
    request: Request,
    uebermittlungskennung: str = Form(...),
    datei: UploadFile = File(...),
):
    data = await datei.read()
    upload_id = website_service.upload_anfrage_bild(
        _hostname(request), _client_ip(request), uebermittlungskennung,
        datei.filename or "bild", data,
    )
    return schemas.AnfrageUploadRead(upload_id=upload_id)


@public_router.post("/anfragen", response_model=schemas.AnfrageResult, status_code=201)
def submit_anfrage(payload: schemas.AnfrageCreate, request: Request):
    website_service.submit_anfrage(_hostname(request), _client_ip(request), payload)
    return schemas.AnfrageResult(ok=True)


# --- Website-Einstellungen (nur Inhaber) ----------------------------------

@settings_router.get("", response_model=schemas.WebsiteSettingsRead)
def get_settings(user: CurrentUser = Depends(require_role("Inhaber"))):
    return website_service.get_website_settings(user.mandant_id)


@settings_router.patch("", response_model=schemas.WebsiteSettingsRead)
def patch_settings(payload: schemas.WebsiteSettingsPatch,
                   user: CurrentUser = Depends(require_role("Inhaber"))):
    return website_service.update_website_settings(
        user.mandant_id, payload.firmenname, payload.marken_farbe, payload.telefon,
        payload.email, payload.adresse, payload.oeffnungszeiten, payload.ueber_uns,
        payload.leistungen, payload.domain,
    )


@settings_router.post("/logo", response_model=schemas.LogoUploadRead)
async def upload_logo(datei: UploadFile = File(...),
                      user: CurrentUser = Depends(require_role("Inhaber"))):
    data = await datei.read()
    logo_url = website_service.upload_logo(user.mandant_id, datei.filename or "logo", data)
    return schemas.LogoUploadRead(logo_url=logo_url)
