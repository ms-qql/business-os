from __future__ import annotations

import json

from app.errors import ConflictError, NotFoundError, ValidationError
from app.features.formulare import repository as repo
from app.features.formulare.schemas import (
    FeldRead, FeldWrite, FormularDraftRead, OPTION_TYPEN, SchrittRead,
)
from app.features.formulare.repository import _pack_config

# Maximale Werte (ponytail) — gegen ungebundene Speicherung.
MAX_SCHRITTE = 50
MAX_FELDER_PRO_SCHRITT = 100
MAX_OPTIONEN_PRO_FELD = 100


def _revision_conflict() -> None:
    raise ConflictError(
        "Ihr Formular-Stand war veraltet. Bitte laden Sie die Seite neu, "
        "bevor Sie die Änderung erneut speichern."
    )


def _config_from_feld(feld: dict) -> dict:
    cfg = feld["konfiguration"]
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    return {
        "min": cfg.get("min"),
        "max": cfg.get("max"),
        "ganzzahl": bool(cfg.get("ganzzahl", False)),
        "reg_exp": cfg.get("reg_exp"),
        "minlaenge": cfg.get("min_length"),
        "maxlaenge": cfg.get("max_length"),
        "datum_min": cfg.get("datum_min"),
        "datum_max": cfg.get("datum_max"),
        "max_anzahl": int(cfg.get("max_anzahl", 1)),
    }


def _feld_to_read(mandant_id: str, feld: dict) -> FeldRead:
    from app.features.formulare.schemas import FeldOptionRead
    optionen = [FeldOptionRead(id=o["id"], label=o["label"], wert=o["wert"])
                for o in repo.list_optionen(mandant_id, feld["id"])]
    return FeldRead(
        id=feld["id"], typ=feld["typ"], label=feld["label"],
        hilfetext=feld["hilfetext"], pflichtfeld=bool(feld["pflichtfeld"]),
        optional_in_einfach=bool(feld["optional_in_einfach"]),
        uebernahme=feld["uebernahme"], optionen=optionen,
        **_config_from_feld(feld),
    )


def _schritt_to_read(mandant_id: str, schritt: dict) -> SchrittRead:
    felder = repo.list_felder(mandant_id, schritt["id"])
    return SchrittRead(
        id=schritt["id"], titel=schritt["titel"], position=int(schritt["position"]),
        felder=[_feld_to_read(mandant_id, f) for f in felder],
    )


def _to_draft_read(mandant_id: str, formular: dict) -> FormularDraftRead:
    schritte = repo.list_schritte(mandant_id, formular["id"])
    return FormularDraftRead(
        id=formular["id"], name=formular["name"],
        komplexitaet=formular["komplexitaetsstufe"],
        draft_revision=int(formular["draft_revision"]),
        veroeffentlicht=bool(formular["published_version_id"]),
        public_id=formular.get("public_id"),
        schritte=[_schritt_to_read(mandant_id, s) for s in schritte],
        created_at=formular["created_at"], updated_at=formular["updated_at"],
    )


# --- Liste / Metadaten --------------------------------------------------


def list_formulare(mandant_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    items, total = repo.list_formulare(mandant_id, limit, offset)
    return items, total


def get_draft(mandant_id: str, formular_id: str) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    return _to_draft_read(mandant_id, formular)


# --- Erstellen (leer / Vorlage) -----------------------------------------


def create_formular(mandant_id: str, vorlage: str) -> FormularDraftRead:
    if vorlage == "leer":
        formular = repo.create_formular(mandant_id, "Neues Formular")
    else:
        tmpl = repo.get_vorlage(vorlage)
        if not tmpl:
            raise ValidationError("Unbekannte Vorlage.")
        formular = repo.create_formular(
            mandant_id, _vorlage_name(vorlage))
        _apply_vorlage(mandant_id, formular["id"], tmpl)
    return _to_draft_read(mandant_id, formular)


def _vorlage_name(vorlage: str) -> str:
    return "SHK-Formular" if vorlage == "shk" else "Entrümpelungs-Formular"


def _apply_vorlage(mandant_id: str, formular_id: str, schritte: list[dict]) -> None:
    for s in schritte:
        if len(s["felder"]) > MAX_FELDER_PRO_SCHRITT:
            raise ValidationError("Die Vorlage überschreitet die Feldbegrenzung.")
        schritt = repo.create_schritt(mandant_id, formular_id, s.get("titel", ""))
        for f in s["felder"]:
            feld = repo.create_feld(mandant_id, schritt["id"], _feld_dict(f))
            if f.get("optionen"):
                repo.replace_optionen(mandant_id, feld["id"], f["optionen"])


def _feld_dict(f: FeldWrite | dict) -> dict:
    if isinstance(f, FeldWrite):
        return {
            "typ": f.typ, "label": f.label, "hilfetext": f.hilfetext,
            "pflichtfeld": f.pflichtfeld, "optional_in_einfach": f.optional_in_einfach,
            "konfiguration": _pack_config(f.model_dump(by_alias=True)),
            "uebernahme": f.uebernahme,
        }
    return {
        "typ": f["typ"], "label": f.get("label", ""), "hilfetext": f.get("hilfetext", ""),
        "pflichtfeld": f.get("pflichtfeld", False),
        "optional_in_einfach": f.get("optional_in_einfach", False),
        "konfiguration": f.get("konfiguration", {}), "uebernahme": f.get("uebernahme"),
    }


# --- Metadaten-Änderungen -----------------------------------------------


def patch_formular(mandant_id: str, formular_id: str, name: str | None,
                   komplexitaet: str | None) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    fields: dict = {}
    if name is not None:
        fields["name"] = name
    if komplexitaet is not None:
        fields["komplexitaetsstufe"] = komplexitaet
    repo.update_formular(mandant_id, formular_id, fields)
    return _to_draft_read(mandant_id, repo.get_formular(mandant_id, formular_id))


def delete_formular(mandant_id: str, formular_id: str) -> None:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    repo.delete_formular(mandant_id, formular_id)


# --- Schritte ------------------------------------------------------------


def add_schritt(mandant_id: str, formular_id: str, draft_revision: int) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    if len(repo.list_schritte(mandant_id, formular_id)) >= MAX_SCHRITTE:
        raise ValidationError(f"Maximal {MAX_SCHRITTE} Schritte erlaubt.")
    repo.create_schritt(mandant_id, formular_id)
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def patch_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                  draft_revision: int, titel: str) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    repo.update_schritt(mandant_id, schritt_id, titel)
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def set_schritt_reihenfolge(mandant_id: str, formular_id: str, draft_revision: int,
                            ordered_ids: list[str]) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    vorhanden = repo.list_schritte(mandant_id, formular_id)
    vorhandene_ids = {s["id"] for s in vorhanden}
    if set(ordered_ids) != vorhandene_ids or len(ordered_ids) != len(vorhandene_ids):
        raise ValidationError(
            "Die Reihenfolge muss alle vorhandenen Schritte genau einmal enthalten."
        )
    repo.set_schritt_position(mandant_id, formular_id,
                              {sid: i + 1 for i, sid in enumerate(ordered_ids)})
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def delete_schritt(mandant_id: str, formular_id: str, schritt_id: str,
                   draft_revision: int) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    repo.delete_schritt(mandant_id, schritt_id)
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


# --- Felder --------------------------------------------------------------


def add_feld(mandant_id: str, formular_id: str, schritt_id: str, draft_revision: int,
             feld: FeldWrite) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    if len(repo.list_felder(mandant_id, schritt_id)) >= MAX_FELDER_PRO_SCHRITT:
        raise ValidationError(f"Maximal {MAX_FELDER_PRO_SCHRITT} Felder je Schritt erlaubt.")
    _validate_feld_config(feld)
    new_feld = repo.create_feld(mandant_id, schritt_id, _feld_dict(feld))
    if feld.typ in OPTION_TYPEN:
        repo.replace_optionen(mandant_id, new_feld["id"],
                              [o.model_dump() for o in feld.optionen])
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def patch_feld(mandant_id: str, formular_id: str, schritt_id: str, feld_id: str,
               draft_revision: int, feld: FeldWrite) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    existing = repo.get_feld(mandant_id, feld_id)
    if not existing or existing["schritt_id"] != schritt_id:
        raise NotFoundError("Feld nicht gefunden.")
    _validate_feld_config(feld)
    repo.update_feld(mandant_id, feld_id, _feld_dict(feld))
    if feld.typ in OPTION_TYPEN:
        repo.replace_optionen(mandant_id, feld_id, [o.model_dump() for o in feld.optionen])
    else:
        repo.replace_optionen(mandant_id, feld_id, [])  # Optionen nur bei Auswahltypen
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def set_feld_reihenfolge(mandant_id: str, formular_id: str, schritt_id: str,
                         draft_revision: int, ordered_ids: list[str]) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    vorhanden = repo.list_felder(mandant_id, schritt_id)
    vorhandene_ids = {f["id"] for f in vorhanden}
    if set(ordered_ids) != vorhandene_ids or len(ordered_ids) != len(vorhandene_ids):
        raise ValidationError(
            "Die Reihenfolge muss alle vorhandenen Felder genau einmal enthalten."
        )
    repo.set_feld_position(mandant_id, schritt_id,
                           {fid: i + 1 for i, fid in enumerate(ordered_ids)})
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def delete_feld(mandant_id: str, formular_id: str, schritt_id: str, feld_id: str,
                draft_revision: int) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    schritt = repo.get_schritt(mandant_id, schritt_id)
    if not schritt or schritt["formular_id"] != formular_id:
        raise NotFoundError("Schritt nicht gefunden.")
    existing = repo.get_feld(mandant_id, feld_id)
    if not existing or existing["schritt_id"] != schritt_id:
        raise NotFoundError("Feld nicht gefunden.")
    repo.delete_feld(mandant_id, feld_id)
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


# --- Publish / Einbindung -----------------------------------------------


def _build_snapshot(mandant_id: str, formular: dict) -> dict:
    snap_schritte = []
    for s in repo.list_schritte(mandant_id, formular["id"]):
        snap_felder = []
        for f in repo.list_felder(mandant_id, s["id"]):
            konfig = f["konfiguration"]
            if isinstance(konfig, str):
                konfig = json.loads(konfig)
            feld_dict = {
                "id": f["id"], "typ": f["typ"], "label": f["label"],
                "hilfetext": f["hilfetext"], "pflichtfeld": bool(f["pflichtfeld"]),
                "optional_in_einfach": bool(f["optional_in_einfach"]),
                "konfiguration": konfig, "uebernahme": f["uebernahme"],
            }
            if f["typ"] in OPTION_TYPEN:
                optionen = repo.list_optionen(mandant_id, f["id"])
                feld_dict["optionen"] = [
                    {"label": o["label"], "wert": o["wert"]} for o in optionen
                ]
            snap_felder.append(feld_dict)
        snap_schritte.append({
            "id": s["id"], "titel": s["titel"],
            "position": int(s["position"]), "felder": snap_felder,
        })
    return {
        "name": formular["name"],
        "komplexitaetsstufe": formular["komplexitaetsstufe"],
        "schritte": snap_schritte,
    }


def _validate_publishable(mandant_id: str, formular: dict) -> dict:
    snapshot = _build_snapshot(mandant_id, formular)
    if not snapshot["schritte"]:
        raise ValidationError("Ein Formular braucht mindestens einen Schritt.")
    total_felder = sum(len(s["felder"]) for s in snapshot["schritte"])
    if total_felder == 0:
        raise ValidationError("Ein Formular braucht mindestens ein Feld.")
    consent_count = 0
    for s in snapshot["schritte"]:
        for f in s["felder"]:
            if f["typ"] in OPTION_TYPEN:
                opts = f.get("optionen", [])
                if not opts:
                    raise ValidationError(
                        f"Das Feld '{f['label'] or f['typ']}' hat keine Auswahloptionen."
                    )
                werte = [o["wert"] for o in opts]
                if len(set(werte)) != len(werte) or any(not w.strip() for w in werte):
                    raise ValidationError(
                        f"Das Feld '{f['label'] or f['typ']}' hat doppelte oder leere Werte."
                    )
            if f["typ"] == "consent" and f["pflichtfeld"]:
                consent_count += 1
    if consent_count == 0:
        raise ValidationError(
            "Ein veröffentlichbares Formular braucht genau ein verpflichtendes "
            "Consent-Feld."
        )
    return snapshot


def publish(mandant_id: str, formular_id: str, draft_revision: int,
            nutzer_id: str | None) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    snapshot = _validate_publishable(mandant_id, formular)
    nummer = repo.next_version_nummer(mandant_id, formular_id)
    version = repo.create_version(mandant_id, formular_id, nummer, snapshot, nutzer_id)
    repo.set_published_version(mandant_id, formular_id, version["id"])
    return _to_draft_read(mandant_id, repo.get_formular(mandant_id, formular_id))


def withdraw(mandant_id: str, formular_id: str, draft_revision: int) -> FormularDraftRead:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if int(formular["draft_revision"]) != draft_revision:
        _revision_conflict()
    if not formular["published_version_id"]:
        raise ValidationError("Dieses Formular ist nicht veröffentlicht.")
    repo.withdraw_version(mandant_id, formular["published_version_id"])
    repo.clear_published_version(mandant_id, formular_id)
    repo.bump_revision(mandant_id, formular_id, draft_revision)
    return get_draft(mandant_id, formular_id)


def get_einbindung(mandant_id: str, formular_id: str, domain: str | None) -> dict:
    formular = repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    if not formular["published_version_id"]:
        raise ValidationError("Nur veröffentlichte Formulare können eingebunden werden.")
    public_id = formular.get("public_id")
    if not public_id:
        raise ValidationError("Für die Einbindung wird die Betriebsdomain benötigt.")
    base = f"https://{domain}"
    path = f"/formulare/{public_id}"
    url = base + path
    iframe = (
        f'<iframe src="{url}" title="{formular["name"]}" width="100%" height="800" '
        f'style="border:0" loading="lazy"></iframe>'
    )
    js = (
        "(function(){var s=document.createElement('script');"
        "s.src='https://bizos.app.msce.info/embed.js';"
        "var f=document.createElement('div');"
        f"f.dataset.formular='{public_id}';"
        "document.currentScript.parentNode.appendChild(f);"
        "document.head.appendChild(s);})();"
    )
    return {"direktlink": url, "iframe": iframe, "snippet": js}


def _validate_feld_config(feld: FeldWrite) -> None:
    if feld.typ in OPTION_TYPEN:
        if len(feld.optionen) > MAX_OPTIONEN_PRO_FELD:
            raise ValidationError(f"Maximal {MAX_OPTIONEN_PRO_FELD} Optionen erlaubt.")
    if feld.typ == "upload":
        if feld.max_anzahl < 1 or feld.max_anzahl > MAX_OPTIONEN_PRO_FELD:
            raise ValidationError("Ungültige maximale Upload-Anzahl.")
    if feld.minlaenge is not None and feld.maxlaenge is not None:
        if feld.minlaenge > feld.maxlaenge:
            raise ValidationError("minlaenge darf nicht größer als maxlaenge sein.")
