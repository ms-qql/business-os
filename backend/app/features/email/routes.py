from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.config import settings
from app.deps import CurrentUser, get_current_user, require_role
from app.errors import ForbiddenError
from app.features.email import schemas
from app.features.email import service as email_service

router = APIRouter(tags=["email"])
internal_router = APIRouter(prefix="/internal/email", tags=["email-internal"])

_schreib_rollen = require_role("Buero", "Inhaber")
_inhaber_rolle = require_role("Inhaber")


def _internal_guard(x_internal_secret: str | None = Header(default=None)) -> None:
    if x_internal_secret != settings.internal_proxy_secret:
        raise ForbiddenError("Kein Zugriff.")


@router.get("/email-konto", response_model=schemas.EmailKontoRead)
def get_konto(user: CurrentUser = Depends(_schreib_rollen)):
    return schemas.EmailKontoRead(**email_service.get_konto_read(user.mandant_id))


@router.put("/email-konto", response_model=schemas.EmailKontoRead)
def put_konto(payload: schemas.EmailKontoConfig, user: CurrentUser = Depends(_inhaber_rolle)):
    return schemas.EmailKontoRead(**email_service.save_konto(user.mandant_id, payload))


@router.post("/email-konto/test", response_model=schemas.EmailKontoTestResult)
def test_konto(payload: schemas.EmailKontoTest, user: CurrentUser = Depends(_inhaber_rolle)):
    result = email_service.test_konto(payload)
    return schemas.EmailKontoTestResult(**result)


@router.get("/email/inbox", response_model=schemas.EmailInboxResponse)
def inbox(zugeordnet: bool | None = None, user: CurrentUser = Depends(_schreib_rollen)):
    data = email_service.get_inbox(user.mandant_id, zugeordnet)
    return schemas.EmailInboxResponse(
        items=[schemas.EmailInboxItem(**i) for i in data["items"]],
        konto_status=data["konto_status"],
        konto_fehler_text=data["konto_fehler_text"],
    )


@router.get("/email/nachrichten/{nachricht_id}", response_model=schemas.EmailNachrichtRead)
def nachricht(nachricht_id: str, user: CurrentUser = Depends(_schreib_rollen)):
    return schemas.EmailNachrichtRead(**email_service.get_nachricht(user.mandant_id, nachricht_id))


@router.post("/email/nachrichten/{nachricht_id}/zuordnen",
             response_model=schemas.EmailThreadRead)
def zuordnen(nachricht_id: str, payload: schemas.EmailZuordnen,
             user: CurrentUser = Depends(_schreib_rollen)):
    thread = email_service.zuordnen(user.mandant_id, nachricht_id, payload.vorgang_id)
    return schemas.EmailThreadRead(**thread)


@router.post("/email/nachrichten/{nachricht_id}/vorgang",
             response_model=schemas.EmailThreadRead)
def nachricht_zu_vorgang(nachricht_id: str, payload: schemas.EmailVorgangAusNachricht,
                         user: CurrentUser = Depends(_schreib_rollen)):
    thread = email_service.nachricht_zu_vorgang(user.mandant_id, nachricht_id, payload)
    return schemas.EmailThreadRead(**thread)


@router.get("/vorgaenge/{vorgang_id}/emails", response_model=list[schemas.EmailThreadRead])
def vorgang_emails(vorgang_id: str, user: CurrentUser = Depends(_schreib_rollen)):
    threads = email_service.list_vorgang_emails(user.mandant_id, vorgang_id)
    return [schemas.EmailThreadRead(**t) for t in threads]


@router.post("/vorgaenge/{vorgang_id}/emails", response_model=schemas.EmailNachrichtRead,
             status_code=201)
def vorgang_email_send(vorgang_id: str, payload: schemas.EmailCompose,
                       user: CurrentUser = Depends(_schreib_rollen)):
    nachricht = email_service.send_vorgang_email(user, vorgang_id, payload)
    return schemas.EmailNachrichtRead(**nachricht)


@router.get("/vorgaenge/{vorgang_id}/emails/{email_id}/anhaenge/{anhang_id}/download")
def vorgang_email_anhang_download(vorgang_id: str, email_id: str, anhang_id: str,
                                  user: CurrentUser = Depends(_schreib_rollen)):
    url = email_service.get_download_url(user, vorgang_id, email_id, anhang_id)
    return schemas.DownloadRead(download_url=url)


@internal_router.post("/poll", status_code=200)
def poll(mandant_id: str | None = None, _: None = Depends(_internal_guard)):
    """Interner E-Mail-Abruf (per Dokploy-Cron getriggert). Pollt alle
    konfigurierten Mandanten oder nur einen, falls mandant_id übergeben wird."""
    from app.features.email import repository as repo

    mandanten = [mandant_id] if mandant_id else repo.list_mandanten_mit_konto()
    ergebnisse = {}
    for mid in mandanten:
        ergebnisse[mid] = email_service.poll_postfach(mid)
    return {"ergebnisse": ergebnisse}
