from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_role
from app.features.gewerke import schemas
from app.features.gewerke import service as gewerk_service

# Tech Design PROJ-22: Katalogpflege nur für Inhaber/Büro (wie Angebote).
_write_roles = require_role("Buero", "Inhaber")

router = APIRouter(prefix="/gewerke", tags=["gewerke"])


# --- Kategorien ----------------------------------------------------------

@router.get("/kategorien", response_model=list[schemas.KategorieRead])
def list_kategorien(user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.list_kategorien(user)


@router.post("/kategorien", response_model=schemas.KategorieRead, status_code=201)
def create_kategorie(payload: schemas.KategorieCreate,
                     user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.create_kategorie(user, payload)


@router.patch("/kategorien/{kategorie_id}", response_model=schemas.KategorieRead)
def rename_kategorie(kategorie_id: str, payload: schemas.KategorieCreate,
                    user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.rename_kategorie(user, kategorie_id, payload)


@router.delete("/kategorien/{kategorie_id}", status_code=204)
def delete_kategorie(kategorie_id: str, user: CurrentUser = Depends(_write_roles)):
    gewerk_service.delete_kategorie(user, kategorie_id)
    return None


# --- Gewerke -------------------------------------------------------------

@router.get("", response_model=schemas.GewerkListe)
def list_gewerke(suchbegriff: Optional[str] = None, kategorie_id: Optional[str] = None,
                 user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.list_gewerke(user, suchbegriff, kategorie_id)


@router.post("", response_model=schemas.GewerkRead, status_code=201)
def create_gewerk(payload: schemas.GewerkCreate,
                  user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.create_gewerk(user, payload)


@router.get("/{gewerk_id}", response_model=schemas.GewerkRead)
def get_gewerk(gewerk_id: str, user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.get_gewerk(user, gewerk_id)


@router.patch("/{gewerk_id}", response_model=schemas.GewerkRead)
def update_gewerk(gewerk_id: str, payload: schemas.GewerkUpdate,
                  user: CurrentUser = Depends(_write_roles)):
    return gewerk_service.update_gewerk(user, gewerk_id, payload)


@router.delete("/{gewerk_id}", status_code=204)
def delete_gewerk(gewerk_id: str, user: CurrentUser = Depends(_write_roles)):
    gewerk_service.delete_gewerk(user, gewerk_id)
    return None


# --- Angebot-Position aus Gewerk + Preis-Override -------------------------
#
# Diese Endpunkte liegen bewusst unter /angebote (siehe
# app/features/angebote/routes.py): PositionAusGewerk und PreisOverride sind
# dort als Request-Schemas definiert und rufen gewerk_service auf. Hier nur der
# reine Gewerk-Katalog (Kategorien, Gewerke, Kostenzeilen).
