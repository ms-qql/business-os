from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.deps import CurrentUser, require_role
from app.features.website import builder_schemas as sch
from app.features.website import builder_service as wb_service

builder_router = APIRouter(prefix="/website-builder", tags=["website-builder"])

_owner = require_role("Inhaber")


# --- Startseite / Landingpage --------------------------------------------

@builder_router.get("/startseite", response_model=sch.BuilderStateRead)
def get_startseite(user: CurrentUser = Depends(_owner)):
    return wb_service.get_builder_state(user.mandant_id)


@builder_router.post("/startseite/initialisieren", response_model=sch.BuilderStateRead,
                     status_code=200)
def initialisieren(user: CurrentUser = Depends(_owner)):
    return wb_service.initialize_landingpage(user.mandant_id)


# --- Sektionen -----------------------------------------------------------

@builder_router.post("/sections", response_model=sch.BuilderStateRead, status_code=200)
def add_section(payload: sch.SectionAddRequest, user: CurrentUser = Depends(_owner)):
    return wb_service.add_section(user.mandant_id, payload.type, payload.version)


@builder_router.patch("/sections/{section_id}", response_model=sch.BuilderStateRead)
def patch_section(section_id: str, payload: sch.SectionPatchRequest,
                  user: CurrentUser = Depends(_owner)):
    return wb_service.patch_section(
        user.mandant_id, section_id, payload.version, payload.visible, payload.inhalt)


@builder_router.put("/sections/reihenfolge", response_model=sch.BuilderStateRead)
def reihenfolge(payload: sch.ReihenfolgeRequest, user: CurrentUser = Depends(_owner)):
    return wb_service.set_reihenfolge(user.mandant_id, payload.version, payload.ordered_ids)


@builder_router.delete("/sections/{section_id}", response_model=sch.BuilderStateRead)
def delete_section(section_id: str,
                   version: Annotated[int, Query()],
                   user: CurrentUser = Depends(_owner)):
    return wb_service.delete_section(user.mandant_id, section_id, version)


# --- Bilder --------------------------------------------------------------

@builder_router.post("/sections/{section_id}/bild", response_model=sch.BuilderStateRead)
async def upload_bild(section_id: str,
                      version: Annotated[int, Query()],
                      alt_text: Annotated[str, Form()] = "",
                      datei: UploadFile = File(...),
                      user: CurrentUser = Depends(_owner)):
    data = await datei.read()
    return wb_service.upload_section_bild(
        user.mandant_id, section_id, version, datei.filename or "bild", data, alt_text)


@builder_router.delete("/sections/{section_id}/bild", response_model=sch.BuilderStateRead)
def delete_bild(section_id: str,
                version: Annotated[int, Query()],
                user: CurrentUser = Depends(_owner)):
    return wb_service.delete_section_bild(user.mandant_id, section_id, version)
