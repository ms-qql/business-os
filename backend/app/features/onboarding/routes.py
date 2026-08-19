from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.deps import CurrentUser, require_role
from app.features.onboarding import schemas
from app.features.onboarding import service as onboarding_service

# Inhaber-only (Tech Design: Betreiber und Inhaber sehen dieselbe Checkliste;
# Büro/Monteur erhalten Zugriffsverweigerung).
_inhaber_rolle = require_role("Inhaber")


router = APIRouter(prefix="/onboarding", tags=["onboarding"])
katalog_router = APIRouter(prefix="/katalog", tags=["katalog"])


# --- Onboarding-Status (Inhaber-only) ------------------------------------

@router.get("", response_model=schemas.OnboardingStatus)
def get_status(user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.get_onboarding_status(user.mandant_id)


@router.put("/domain", response_model=schemas.DomainReserveResponse)
def put_domain(payload: schemas.DomainReserve,
               user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.reserve_domain(user.mandant_id, payload.hostname)


@router.post("/postfach-test", response_model=schemas.PostfachTestResult)
def post_postfach_test(user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.postfach_test(user.mandant_id, user.id)


@router.post("/testvorgang", response_model=schemas.TestvorgangResult, status_code=201)
def post_testvorgang(user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.create_testvorgang(user.mandant_id, user.id)


@router.delete("/testvorgang/{vorgang_id}", status_code=204)
def delete_testvorgang(vorgang_id: str, user: CurrentUser = Depends(_inhaber_rolle)):
    onboarding_service.delete_testvorgang(user.mandant_id, vorgang_id)
    return None


@router.post("/veroeffentlichen", response_model=schemas.VeroeffentlichenResult)
def post_veroeffentlichen(user: CurrentUser = Depends(_inhaber_rolle)):
    result = onboarding_service.veroeffentlichen(user.mandant_id, user.id)
    if not result.ok:
        # 409: Pflichtregeln nicht erfüllt (serverseitige Gate-Logik).
        from app.errors import ConflictError
        raise ConflictError(
            "Veröffentlichung nicht möglich: " + ", ".join(result.fehlende_schritte) + "."
        )
    return result


# --- Preisliste / Leistungskatalog (Inhaber-only) ------------------------

@katalog_router.get("", response_model=schemas.KatalogListe)
def get_katalog(user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.list_preisliste(user.mandant_id)


@katalog_router.post("/positionen", response_model=schemas.PreislistePosition, status_code=201)
def post_katalog_position(payload: schemas.PreislistePositionInput,
                           user: CurrentUser = Depends(_inhaber_rolle)):
    return onboarding_service.create_preisliste_position(user.mandant_id, payload)


@katalog_router.delete("/positionen/{position_id}", status_code=204)
def delete_katalog_position(position_id: str, user: CurrentUser = Depends(_inhaber_rolle)):
    onboarding_service.delete_preisliste_position(user.mandant_id, position_id)
    return None


@katalog_router.post("/import", response_model=schemas.KatalogImportResult)
async def post_katalog_import(datei: UploadFile = File(...),
                              user: CurrentUser = Depends(_inhaber_rolle)):
    inhalt = await datei.read()
    return onboarding_service.import_preisliste_csv(user.mandant_id, inhalt)
