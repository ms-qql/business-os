from __future__ import annotations

import json

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.deps import CurrentUser, require_role
from app.config import settings
from app.features.formulare import builder_service as b_service
from app.features.formulare import public_service as p_service
from app.features.formulare.schemas import (
    EinsendungCreate, EinsendungResult, EinsendungUploadRead, FeldWrite, FormularCreate,
    FormularDraftRead, FormularEinbindung, FormularEinsendungListeResponse,
    FormularEinsendungRead, FormularListeItem,
    FormularListeResponse, PublishRequest, PublicFormular, WithdrawRequest,
)

formular_router = APIRouter(prefix="/formulare", tags=["formulare"])
public_formular_router = APIRouter(prefix="/public/formulare", tags=["public-formulare"])

_owner = require_role("Inhaber", "Buero")


def _to_dict(val):
    """JSONB-Spalten kommen je nach Treiber als dict oder str an."""
    if val is None:
        return {}
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return {}
    return val


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


# === Angemeldet (Inhaber) =====================================================


@formular_router.get("", response_model=FormularListeResponse)
def list_formulare(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(_owner),
):
    items, total = b_service.list_formulare(user.mandant_id, limit, offset)
    return FormularListeResponse(
        items=[
            FormularListeItem(
                id=r["id"], name=r["name"],
                komplexitaet=r["komplexitaetsstufe"], draft_revision=int(r["draft_revision"]),
                veroeffentlicht=bool(r["published_version_id"]), public_id=r.get("public_id"),
                updated_at=r["updated_at"],
            )
            for r in items
        ],
        total=total, limit=limit, offset=offset,
    )


# === Spam-Einsendungen (Inhaber/Büro) ====================================
# Eigener Prefix "/formular-einsendungen" (laut Tech Design API-Contract
# Zeile 202), damit kein Kollisionsrisiko mit /formulare/{id} besteht.


einsendungen_router = APIRouter(prefix="/formular-einsendungen", tags=["formulare"])


@einsendungen_router.get("", response_model=FormularEinsendungListeResponse)
def list_formular_einsendungen(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(_owner),
):
    items, total = p_service.list_spam_einsendungen(user.mandant_id, limit, offset)
    return FormularEinsendungListeResponse(
        items=[
            FormularEinsendungRead(
                id=r["id"], formular_id=r["formular_id"],
                formular_name=r.get("formular_name") or "",
                uebermittlungskennung=r["uebermittlungskennung"],
                werte=_to_dict(r.get("werte")),
                consent_nachweis=_to_dict(r.get("consent_nachweis")),
                spam_status=r["spam_status"], eingegangen_am=r["eingegangen_am"],
                anfrage_id=r.get("anfrage_id"), vorgang_id=r.get("vorgang_id"),
            )
            for r in items
        ],
        total=total, limit=limit, offset=offset,
    )


@formular_router.post("", response_model=FormularDraftRead, status_code=200)
def create_formular(payload: FormularCreate, user: CurrentUser = Depends(_owner)):
    return b_service.create_formular(user.mandant_id, payload.vorlage)


@formular_router.get("/{formular_id}", response_model=FormularDraftRead)
def get_formular(formular_id: str, user: CurrentUser = Depends(_owner)):
    return b_service.get_draft(user.mandant_id, formular_id)


@formular_router.patch("/{formular_id}", response_model=FormularDraftRead)
def patch_formular(
    formular_id: str,
    payload: dict,
    user: CurrentUser = Depends(_owner),
):
    # Flache Felder name/komplexitaet aus dem Request-Body.
    name = payload.get("name")
    komplexitaet = payload.get("komplexitaet")
    return b_service.patch_formular(user.mandant_id, formular_id, name, komplexitaet)


@formular_router.delete("/{formular_id}")
def delete_formular(formular_id: str, user: CurrentUser = Depends(_owner)):
    b_service.delete_formular(user.mandant_id, formular_id)
    return {"ok": True}


# --- Schritte ---


@formular_router.post("/{formular_id}/schritte", response_model=FormularDraftRead)
def add_schritt(formular_id: str, payload: dict, user: CurrentUser = Depends(_owner)):
    return b_service.add_schritt(
        user.mandant_id, formular_id, int(payload.get("draft_revision", 0)))


@formular_router.patch("/{formular_id}/schritte/{schritt_id}", response_model=FormularDraftRead)
def patch_schritt(formular_id: str, schritt_id: str, payload: dict,
                  user: CurrentUser = Depends(_owner)):
    return b_service.patch_schritt(
        user.mandant_id, formular_id, schritt_id,
        int(payload.get("draft_revision", 0)), payload.get("titel", ""))


@formular_router.delete("/{formular_id}/schritte/{schritt_id}")
def delete_schritt(
    formular_id: str, schritt_id: str,
    draft_revision: Annotated[int, Query()],
    user: CurrentUser = Depends(_owner),
):
    return b_service.delete_schritt(
        user.mandant_id, formular_id, schritt_id, draft_revision)


@formular_router.put("/{formular_id}/schritte/reihenfolge", response_model=FormularDraftRead)
def reorder_schritte(formular_id: str, payload: dict, user: CurrentUser = Depends(_owner)):
    return b_service.set_schritt_reihenfolge(
        user.mandant_id, formular_id, int(payload.get("draft_revision", 0)),
        payload.get("ordered_ids", []))


# --- Felder ---


@formular_router.post("/{formular_id}/schritte/{schritt_id}/felder",
                      response_model=FormularDraftRead)
def add_feld(formular_id: str, schritt_id: str, payload: dict,
             user: CurrentUser = Depends(_owner)):
    feld = FeldWrite(**payload)
    return b_service.add_feld(
        user.mandant_id, formular_id, schritt_id,
        int(payload.get("draft_revision", 0)), feld)


@formular_router.patch("/{formular_id}/schritte/{schritt_id}/felder/{feld_id}",
                       response_model=FormularDraftRead)
def patch_feld(formular_id: str, schritt_id: str, feld_id: str, payload: dict,
               user: CurrentUser = Depends(_owner)):
    feld = FeldWrite(**payload)
    return b_service.patch_feld(
        user.mandant_id, formular_id, schritt_id, feld_id,
        int(payload.get("draft_revision", 0)), feld)


@formular_router.delete("/{formular_id}/schritte/{schritt_id}/felder/{feld_id}")
def delete_feld(
    formular_id: str, schritt_id: str, feld_id: str,
    draft_revision: Annotated[int, Query()],
    user: CurrentUser = Depends(_owner),
):
    return b_service.delete_feld(
        user.mandant_id, formular_id, schritt_id, feld_id, draft_revision)


@formular_router.put("/{formular_id}/schritte/{schritt_id}/felder/reihenfolge",
                     response_model=FormularDraftRead)
def reorder_felder(formular_id: str, schritt_id: str, payload: dict,
                   user: CurrentUser = Depends(_owner)):
    return b_service.set_feld_reihenfolge(
        user.mandant_id, formular_id, schritt_id,
        int(payload.get("draft_revision", 0)), payload.get("ordered_ids", []))


# --- Publish / Einbindung ---


@formular_router.post("/{formular_id}/veroeffentlichen", response_model=FormularDraftRead)
def publish(formular_id: str, payload: PublishRequest, user: CurrentUser = Depends(_owner)):
    return b_service.publish(
        user.mandant_id, formular_id, payload.draft_revision, user.id)


@formular_router.post("/{formular_id}/veroeffentlichung-zuruecknehmen",
                      response_model=FormularDraftRead)
def withdraw(formular_id: str, payload: WithdrawRequest, user: CurrentUser = Depends(_owner)):
    return b_service.withdraw(user.mandant_id, formular_id, payload.draft_revision)


@formular_router.get("/{formular_id}/einbindung", response_model=FormularEinbindung)
def einbindung(formular_id: str, request: Request, user: CurrentUser = Depends(_owner)):
    from app.features.website import repository as web_repo
    dom = web_repo.get_domain(user.mandant_id)
    domain = dom["hostname"] if dom else None
    if not domain:
        # Fallback auf den Host des Requests (für lokale Entwicklung).
        domain = _hostname(request) or None
    return b_service.get_einbindung(user.mandant_id, formular_id, domain)


# === Öffentlich (ohne Token) ==================================================


@public_formular_router.get("/{public_id}", response_model=PublicFormular)
def public_snapshot(public_id: str, request: Request):
    hostname = _hostname(request)
    mandant_id = p_service._find_mandant(hostname)
    return p_service.get_public_snapshot(mandant_id, public_id)


@public_formular_router.post("/{public_id}/uploads", response_model=EinsendungUploadRead,
                             status_code=201)
async def public_upload(
    public_id: str,
    uebermittlungskennung: str = Form(...),
    feld_id: str = Form(...),
    datei: UploadFile = File(...),
    request: Request = None,
):
    data = await datei.read()
    hostname = _hostname(request)
    mandant_id = p_service._find_mandant(hostname)
    upload_id = p_service.upload_datei(
        mandant_id, hostname, _client_ip(request),
        uebermittlungskennung, public_id, feld_id, datei.filename or "datei", data,
    )
    return EinsendungUploadRead(upload_id=upload_id)


@public_formular_router.post("/{public_id}/einsendungen", response_model=EinsendungResult,
                             status_code=201)
def public_submit(public_id: str, payload: EinsendungCreate, request: Request):
    hostname = _hostname(request)
    mandant_id = p_service._find_mandant(hostname)
    return p_service.submit_einsendung(
        mandant_id, hostname, _client_ip(request), public_id, payload)
