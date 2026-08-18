from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_role
from app.features.angebote import schemas
from app.features.angebote import service as angebote_service

# Tech Design PROJ-5: "Alle Endpunkte: JWT Pflicht, mandant_id aus Token,
# require_role('Buero','Inhaber')" — auch die Lesepfade, anders als bei
# vorgaenge (dort dürfen Monteure lesen).
_write_roles = require_role("Buero", "Inhaber")

router = APIRouter(tags=["angebote"])


def _to_list_item(a: dict) -> schemas.AngebotListItem:
    return schemas.AngebotListItem(**a)


def _to_detail(a: dict) -> schemas.AngebotDetail:
    return schemas.AngebotDetail(
        **{k: v for k, v in a.items() if k != "positionen"},
        positionen=[schemas.PositionRead(**p) for p in a["positionen"]],
    )


@router.get("/vorgaenge/{vorgang_id}/angebote", response_model=list[schemas.AngebotListItem])
def list_angebote(vorgang_id: str, user: CurrentUser = Depends(_write_roles)):
    return [_to_list_item(a) for a in angebote_service.list_angebote(user, vorgang_id)]


@router.post("/vorgaenge/{vorgang_id}/angebote", response_model=schemas.AngebotDetail, status_code=201)
def create_angebot(vorgang_id: str, payload: schemas.AngebotCreate,
                   user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.create_angebot(user, vorgang_id, payload))


@router.get("/angebote/{angebot_id}", response_model=schemas.AngebotDetail)
def get_angebot(angebot_id: str, user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.get_angebot_detail(user, angebot_id))


@router.patch("/angebote/{angebot_id}", response_model=schemas.AngebotDetail)
def update_angebot(angebot_id: str, payload: schemas.AngebotUpdate,
                   user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.update_angebot_kopf(user, angebot_id, payload))


@router.post("/angebote/{angebot_id}/positionen", response_model=schemas.AngebotDetail, status_code=201)
def add_position(angebot_id: str, payload: schemas.PositionCreate,
                 user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.add_position(user, angebot_id, payload))


@router.patch("/angebote/{angebot_id}/positionen/{position_id}", response_model=schemas.AngebotDetail)
def update_position(angebot_id: str, position_id: str, payload: schemas.PositionUpdate,
                    user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.update_position(user, angebot_id, position_id, payload))


@router.delete("/angebote/{angebot_id}/positionen/{position_id}", response_model=schemas.AngebotDetail)
def delete_position(angebot_id: str, position_id: str, user: CurrentUser = Depends(_write_roles)):
    angebote_service.delete_position(user, angebot_id, position_id)
    return _to_detail(angebote_service.get_angebot_detail(user, angebot_id))


@router.get("/angebote/{angebot_id}/pdf", response_model=schemas.DownloadRead)
def get_pdf(angebot_id: str, user: CurrentUser = Depends(_write_roles)):
    return schemas.DownloadRead(download_url=angebote_service.get_pdf_download_url(user, angebot_id))


@router.post("/angebote/{angebot_id}/freigabe", response_model=schemas.FreigabeResult)
def freigabe(angebot_id: str, payload: schemas.FreigabeRequest | None = None,
             user: CurrentUser = Depends(_write_roles)):
    return schemas.FreigabeResult(**angebote_service.freigabe(user, angebot_id, payload))


@router.post("/angebote/{angebot_id}/senden", response_model=schemas.SendenResult)
def senden(angebot_id: str, payload: schemas.SendenRequest, user: CurrentUser = Depends(_write_roles)):
    result = angebote_service.senden(user, angebot_id, payload)
    return schemas.SendenResult(angebot=_to_detail(result["angebot"]), versendet=result["versendet"],
                                fehler_text=result["fehler_text"])


@router.post("/angebote/{angebot_id}/neue-version", response_model=schemas.AngebotDetail, status_code=201)
def neue_version(angebot_id: str, user: CurrentUser = Depends(_write_roles)):
    return _to_detail(angebote_service.neue_version(user, angebot_id))
