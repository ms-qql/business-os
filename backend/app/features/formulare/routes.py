from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.config import settings
from app.deps import CurrentUser, get_current_user, require_role
from app.errors import NotFoundError
from app.features.formulare import schemas
from app.features.formulare import service as formular_service

formulare_router = APIRouter(prefix="/formulare", tags=["formulare"])
public_formulare_router = APIRouter(prefix="/public/formulare", tags=["public-formulare"])
einsendungen_router = APIRouter(prefix="/formular-einsendungen", tags=["formular-einsendungen"])

_write = require_role("Inhaber", "Buero")

# Angemeldete Leser: Inhaber oder Buero (Tech Design: beide Rollen).
_lesen = require_role("Inhaber", "Buero")


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _hostname(request: Request) -> str:
    trusted_proxy = bool(settings.internal_proxy_secret) and (
        request.headers.get("x-internal-proxy-secret") == settings.internal_proxy_secret
    )
    fwd = request.headers.get("x-forwarded-host") if trusted_proxy else None
    host = (fwd or request.headers.get("host") or "").split(",")[0].strip()
    return host.split(":")[0]


def _entwurf(mandant_id: str, formular_id: str) -> schemas.FormularEntwurf:
    formular = formular_service._require_formular(mandant_id, formular_id)
    return schemas.FormularEntwurf(**formular_service._entwurf_to_dict(mandant_id, formular))


# --- Angemeldete Routen: Entwurf ------------------------------------------


@formulare_router.get("", response_model=schemas.FormularListeResult)
def list_formulare(limit: int = 50, offset: int = 0,
                   user: CurrentUser = Depends(_lesen)):
    items, total = formular_service.list_formulare(user.mandant_id, limit, offset)
    return schemas.FormularListeResult(items=items, total=total, limit=limit, offset=offset)


@formulare_router.post("", response_model=schemas.FormularEntwurf, status_code=201)
def create_formular(payload: schemas.FormularCreate,
                     user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.create_formular(user.mandant_id, payload))


@formulare_router.get("/{formular_id}", response_model=schemas.FormularEntwurf)
def get_formular(formular_id: str, user: CurrentUser = Depends(_lesen)):
    return _entwurf(user.mandant_id, formular_id)


@formulare_router.patch("/{formular_id}", response_model=schemas.FormularEntwurf)
def patch_formular(formular_id: str, payload: schemas.FormularPatch,
                   user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.patch_formular(
        user.mandant_id, formular_id, payload))


@formulare_router.post("/{formular_id}/schritte", response_model=schemas.FormularEntwurf)
def add_schritt(formular_id: str, payload: schemas.SchrittCreate,
               user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.add_schritt(
        user.mandant_id, formular_id, payload.draft_revision))


@formulare_router.patch("/{formular_id}/schritte/{schritt_id}", response_model=schemas.FormularEntwurf)
def update_schritt(formular_id: str, schritt_id: str, payload: schemas.SchrittPatch,
                  user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.update_schritt(
        user.mandant_id, formular_id, schritt_id, payload))


@formulare_router.delete("/{formular_id}/schritte/{schritt_id}", response_model=schemas.FormularEntwurf)
def delete_schritt(formular_id: str, schritt_id: str,
                  draft_revision: int, user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.delete_schritt(
        user.mandant_id, formular_id, schritt_id, draft_revision))


@formulare_router.put("/{formular_id}/schritte/reihenfolge", response_model=schemas.FormularEntwurf)
def reorder_schritte(formular_id: str, payload: schemas.SchrittReorder,
                     user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.reorder_schritte(
        user.mandant_id, formular_id, payload))


@formulare_router.post("/{formular_id}/schritte/{schritt_id}/felder",
                       response_model=schemas.FormularEntwurf)
def add_feld(formular_id: str, schritt_id: str, payload: schemas.FeldCreate,
             user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.add_feld(
        user.mandant_id, formular_id, schritt_id, payload.typ, payload.draft_revision))


@formulare_router.patch("/{formular_id}/schritte/{schritt_id}/felder/{feld_id}",
                        response_model=schemas.FormularEntwurf)
def update_feld(formular_id: str, schritt_id: str, feld_id: str,
               payload: schemas.FeldPatch, user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.update_feld(
        user.mandant_id, formular_id, feld_id, payload))


@formulare_router.delete("/{formular_id}/schritte/{schritt_id}/felder/{feld_id}",
                         response_model=schemas.FormularEntwurf)
def delete_feld(formular_id: str, schritt_id: str, feld_id: str,
               draft_revision: int, user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.delete_feld(
        user.mandant_id, formular_id, feld_id, draft_revision))


@formulare_router.put("/{formular_id}/schritte/{schritt_id}/felder/reihenfolge",
                      response_model=schemas.FormularEntwurf)
def reorder_felder(formular_id: str, schritt_id: str, payload: schemas.FeldReorder,
                  user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.reorder_felder(
        user.mandant_id, formular_id, schritt_id, payload))


@formulare_router.post("/{formular_id}/veroeffentlichen", response_model=schemas.FormularEntwurf)
def publish_formular(formular_id: str, payload: schemas.PublishRequest,
                    user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.publish_formular(
        user.mandant_id, formular_id, payload.draft_revision))


@formulare_router.post("/{formular_id}/veroeffentlichung-zuruecknehmen",
                       response_model=schemas.FormularEntwurf)
def unpublish_formular(formular_id: str, payload: schemas.PublishRequest,
                      user: CurrentUser = Depends(_write)):
    return schemas.FormularEntwurf(**formular_service.unpublish_formular(
        user.mandant_id, formular_id, payload.draft_revision))


@formulare_router.get("/{formular_id}/einbindung", response_model=schemas.FormularEinbindung)
def get_einbindung(formular_id: str, request: Request,
                   user: CurrentUser = Depends(_write)):
    return schemas.FormularEinbindung(**formular_service.get_einbindung(
        user.mandant_id, formular_id, _hostname(request) or None))


# --- Öffentliche Routen ----------------------------------------------------


@public_formulare_router.get("/{public_id}", response_model=schemas.PublicFormular)
def get_public_formular(public_id: str, request: Request):
    return schemas.PublicFormular(**formular_service.get_public_formular(
        _hostname(request), public_id))


@public_formulare_router.post("/{public_id}/uploads", response_model=schemas.EinsendungUploadRead,
                              status_code=201)
async def upload_datei(public_id: str, request: Request,
                       uebermittlungskennung: str = Form(...),
                       feld_id: str = Form(...),
                       datei: UploadFile = File(...)):
    data = await datei.read()
    upload_id = formular_service.upload_datei(
        _hostname(request), _client_ip(request), public_id, feld_id,
        uebermittlungskennung, datei.filename or "datei", data)
    return schemas.EinsendungUploadRead(upload_id=upload_id)


@public_formulare_router.post("/{public_id}/einsendungen",
                              response_model=schemas.EinsendungResult, status_code=201)
def submit_einsendung(public_id: str, payload: schemas.EinsendungCreate, request: Request):
    status = formular_service.submit_einsendung(
        _hostname(request), _client_ip(request), public_id, payload)
    return schemas.EinsendungResult(status=status)


# --- Listenansicht markierter Einsendungen --------------------------------


@einsendungen_router.get("", response_model=schemas.EinsendungListResult)
def list_einsendungen(spam: int = 0, limit: int = 50, offset: int = 0,
                      user: CurrentUser = Depends(_write)):
    items, total = formular_service.list_einsendungen(
        user.mandant_id, nur_spam=bool(spam), limit=limit, offset=offset)
    return schemas.EinsendungListResult(items=items, total=total, limit=limit, offset=offset)
