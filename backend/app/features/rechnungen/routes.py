from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_role
from app.features.rechnungen import schemas
from app.features.rechnungen import service as rechnungen_service

# Tech Design PROJ-8: alle Endpunkte JWT + require_role('Buero','Inhaber').
# mandant_id kommt nie aus Request-Pfad/Body. Monteur erhält 403.
_write_roles = require_role("Buero", "Inhaber")

router = APIRouter(tags=["rechnungen"])


def _to_detail(r: dict) -> schemas.RechnungDetail:
    return schemas.RechnungDetail(
        **{k: v for k, v in r.items() if k != "positionen"},
        positionen=[schemas.PositionRead(**p) for p in r["positionen"]],
    )


# --- Rechnungsstellerprofil (Einstellungen, nur Inhaber) -----------------

@router.get("/einstellungen/rechnungssteller", response_model=schemas.RechnungsstellerProfilRead)
def get_rechnungssteller(user: CurrentUser = Depends(require_role("Inhaber"))):
    profil = rechnungen_service.get_rechnungsstellerprofil(user)
    if not profil:
        from app.errors import NotFoundError
        raise NotFoundError("Es ist noch kein Rechnungsstellerprofil hinterlegt.")
    return schemas.RechnungsstellerProfilRead(**profil)


@router.put("/einstellungen/rechnungssteller", response_model=schemas.RechnungsstellerProfilRead)
def put_rechnungssteller(payload: schemas.RechnungsstellerProfilIn,
                         user: CurrentUser = Depends(require_role("Inhaber"))):
    return schemas.RechnungsstellerProfilRead(
        **rechnungen_service.save_rechnungsstellerprofil(user, payload))


# --- Vorgang-Rechnungen ---------------------------------------------------

@router.get("/vorgaenge/{vorgang_id}/rechnungen", response_model=list[schemas.RechnungListItem])
def list_rechnungen(vorgang_id: str, user: CurrentUser = Depends(_write_roles)):
    return [schemas.RechnungListItem(**r)
            for r in rechnungen_service.list_rechnungen(user, vorgang_id)]


@router.post("/vorgaenge/{vorgang_id}/rechnungen", response_model=schemas.RechnungDetail,
             status_code=201)
def create_rechnung(vorgang_id: str, payload: schemas.RechnungCreate,
                   user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.create_rechnung(user, vorgang_id, payload))


# --- Einzelne Rechnung ----------------------------------------------------

@router.get("/rechnungen/{rechnung_id}", response_model=schemas.RechnungDetail)
def get_rechnung(rechnung_id: str, user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.get_rechnung_detail(user, rechnung_id))


@router.patch("/rechnungen/{rechnung_id}", response_model=schemas.RechnungDetail)
def patch_rechnung(rechnung_id: str, payload: schemas.RechnungKopfUpdate,
                  user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.update_rechnung_kopf(user, rechnung_id, payload))


@router.post("/rechnungen/{rechnung_id}/positionen", response_model=schemas.RechnungDetail,
             status_code=201)
def add_position(rechnung_id: str, payload: schemas.PositionCreate,
                user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.add_position(user, rechnung_id, payload))


@router.patch("/rechnungen/{rechnung_id}/positionen/{position_id}",
              response_model=schemas.RechnungDetail)
def patch_position(rechnung_id: str, position_id: str, payload: schemas.PositionUpdate,
                  user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.update_position(user, rechnung_id, position_id, payload))


@router.delete("/rechnungen/{rechnung_id}/positionen/{position_id}",
               response_model=schemas.RechnungDetail)
def delete_position(rechnung_id: str, position_id: str,
                    user: CurrentUser = Depends(_write_roles)):
    rechnungen_service.delete_position(user, rechnung_id, position_id)
    return _to_detail(rechnungen_service.get_rechnung_detail(user, rechnung_id))


@router.post("/rechnungen/{rechnung_id}/freigabe", response_model=schemas.FreigabeResult)
def freigabe(rechnung_id: str, payload: schemas.FreigabeRequest | None = None,
             user: CurrentUser = Depends(_write_roles)):
    return schemas.FreigabeResult(**rechnungen_service.freigabe(user, rechnung_id, payload))


@router.post("/rechnungen/{rechnung_id}/senden", response_model=schemas.SendenResult)
def senden(rechnung_id: str, payload: schemas.SendenRequest,
           user: CurrentUser = Depends(_write_roles)):
    result = rechnungen_service.senden(user, rechnung_id, payload)
    return schemas.SendenResult(rechnung=_to_detail(result["rechnung"]),
                                versendet=result["versendet"], fehler_text=result["fehler_text"])


@router.get("/rechnungen/{rechnung_id}/pdf", response_model=schemas.DownloadRead)
def get_pdf(rechnung_id: str, user: CurrentUser = Depends(_write_roles)):
    return schemas.DownloadRead(
        download_url=rechnungen_service.get_pdf_download_url(user, rechnung_id))


@router.patch("/rechnungen/{rechnung_id}/zahlungsstatus", response_model=schemas.RechnungDetail)
def zahlungsstatus(rechnung_id: str, payload: schemas.ZahlungsstatusUpdate,
                  user: CurrentUser = Depends(_write_roles)):
    return _to_detail(rechnungen_service.set_zahlungsstatus(user, rechnung_id, payload))


@router.post("/rechnungen/{rechnung_id}/storno", response_model=schemas.StornoResult)
def storno(rechnung_id: str, user: CurrentUser = Depends(_write_roles)):
    result = rechnungen_service.storno(user, rechnung_id)
    return schemas.StornoResult(rechnung=_to_detail(result), storniert=True)
