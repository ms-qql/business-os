from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.deps import CurrentUser, get_current_user, require_role
from app.features.vorgaenge import schemas
from app.features.vorgaenge import service as vorgaenge_service

router = APIRouter(prefix="/vorgaenge", tags=["vorgaenge"])
anfragen_router = APIRouter(prefix="/anfragen", tags=["vorgaenge"])

_write_roles = require_role("Buero", "Inhaber")


@router.get("", response_model=schemas.VorgangListResponse)
def list_vorgaenge(status: str | None = None, q: str | None = None, kunde_id: str | None = None,
                   limit: int = 50, offset: int = 0,
                   user: CurrentUser = Depends(get_current_user)):
    items, total = vorgaenge_service.list_vorgaenge(user, status, q, kunde_id, limit, offset)
    return schemas.VorgangListResponse(
        items=[schemas.VorgangListItem(**v) for v in items], total=total, limit=limit, offset=offset,
    )


@router.post("", response_model=schemas.VorgangListItem, status_code=201)
def create_vorgang(payload: schemas.VorgangCreate, user: CurrentUser = Depends(_write_roles)):
    vorgang = vorgaenge_service.create_vorgang(
        user, payload.kunde_id, payload.objekt_id, payload.anliegen, payload.quelle,
        payload.notizen, payload.status,
    )
    return schemas.VorgangListItem(**vorgang)


@router.get("/{vorgang_id}", response_model=schemas.VorgangDetail)
def get_vorgang(vorgang_id: str, user: CurrentUser = Depends(get_current_user)):
    return schemas.VorgangDetail(**vorgaenge_service.get_vorgang_detail(user, vorgang_id))


@router.patch("/{vorgang_id}", response_model=schemas.VorgangDetail)
def update_vorgang(vorgang_id: str, payload: schemas.VorgangUpdate,
                   user: CurrentUser = Depends(_write_roles)):
    vorgaenge_service.update_vorgang(
        user, vorgang_id, payload.status, payload.anliegen, payload.notizen, payload.objekt_id,
    )
    return schemas.VorgangDetail(**vorgaenge_service.get_vorgang_detail(user, vorgang_id))


@router.post("/{vorgang_id}/zuweisungen", response_model=schemas.VorgangDetail)
def assign_vorgang(vorgang_id: str, payload: schemas.ZuweisungCreate,
                   user: CurrentUser = Depends(_write_roles)):
    vorgaenge_service.assign_vorgang(user, vorgang_id, payload.nutzer_id)
    return schemas.VorgangDetail(**vorgaenge_service.get_vorgang_detail(user, vorgang_id))


@router.post("/{vorgang_id}/dokumente", response_model=schemas.DokumentRead, status_code=201)
async def upload_dokument(vorgang_id: str, datei: UploadFile = File(...),
                          user: CurrentUser = Depends(_write_roles)):
    data = await datei.read()
    dokument = vorgaenge_service.upload_dokument(user, vorgang_id, datei.filename or "dokument", data)
    return schemas.DokumentRead(**dokument)


@router.get("/{vorgang_id}/dokumente/{dokument_id}/download", response_model=schemas.DownloadRead)
def download_dokument(vorgang_id: str, dokument_id: str,
                      user: CurrentUser = Depends(get_current_user)):
    url = vorgaenge_service.get_dokument_download_url(user, vorgang_id, dokument_id)
    return schemas.DownloadRead(download_url=url)


@router.delete("/{vorgang_id}/dokumente/{dokument_id}", status_code=204)
def delete_dokument(vorgang_id: str, dokument_id: str, user: CurrentUser = Depends(_write_roles)):
    vorgaenge_service.delete_dokument(user, vorgang_id, dokument_id)


@anfragen_router.post("/{anfrage_id}/uebernehmen", response_model=schemas.UebernahmeResult,
                      status_code=201)
def uebernehme_anfrage(anfrage_id: str, payload: schemas.UebernahmeCreate,
                       user: CurrentUser = Depends(_write_roles)):
    result = vorgaenge_service.uebernehme_anfrage(
        user.mandant_id, anfrage_id, payload.kunde_id, user.id,
    )
    return schemas.UebernahmeResult(**result)
