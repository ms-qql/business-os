from __future__ import annotations

import datetime as _dt
from typing import Optional

from app.deps import CurrentUser
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.features.termine import repository as repo
from app.features.vorgaenge import repository as vorgaenge_repo

TERMIN_STATUS_OFFEN = "Termin geplant"


def _to_utc(dt: _dt.datetime) -> str:
    """Normalisiert einen datetime-Wert auf einen UTC-ISO-String (AC-7).
    Naive Eingaben (Browser liefert lokale Zeit) werden als UTC interpretiert,
    damit alle Zeitvergleiche (inkl. Konfliktprüfung) in derselben Zeitzone laufen."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.astimezone(_dt.timezone.utc).isoformat()


def _require_vorgang(mandant_id: str, vorgang_id: str) -> dict:
    # AC-3: ein Termin ohne gültigen, dem Mandanten gehörenden Vorgang wird
    # mit 422 abgelehnt (Validierungsfehler, nicht 404).
    vorgang = vorgaenge_repo.get_vorgang(mandant_id, vorgang_id)
    if not vorgang:
        raise ValidationError("Der gewählte Vorgang gehört nicht zu diesem Mandanten.")
    return vorgang


def _require_termin(mandant_id: str, termin_id: str) -> dict:
    termin = repo.get_termin_row(mandant_id, termin_id)
    if not termin:
        raise NotFoundError("Termin nicht gefunden.")
    return termin


def _require_monteur(mandant_id: str, nutzer_id: str) -> dict:
    nutzer = vorgaenge_repo.get_nutzer(mandant_id, nutzer_id)
    if not nutzer:
        raise NotFoundError("Nutzer nicht gefunden.")
    if nutzer["role"] != "Monteur":
        raise ValidationError("Ein Termin kann nur einem Monteur zugewiesen werden.")
    if nutzer["status"] != "active":
        # BUG-1 (QA): deaktivierte Nutzer können einem Termin nicht neu
        # zugewiesen werden (Spec-Edge-Case). Bestehende Zuweisungen bleiben
        # unangetastet — diese Prüfung greift nur bei Neuzuweisung.
        raise ValidationError("Ein deaktivierter Monteur kann nicht neu zugewiesen werden.")
    return nutzer


def _monteure_read(mandant_id: str, termin_id: str) -> list[dict]:
    return repo.list_zuweisungen(mandant_id, termin_id)


def _build_monteure(mandant_id: str, termin_id: str) -> list[dict]:
    return [
        {"nutzer_id": z["nutzer_id"], "name": z["name"], "aktiv": bool(z["aktiv"])}
        for z in _monteure_read(mandant_id, termin_id)
    ]


def _with_monteure(mandant_id: str, termin: dict) -> dict:
    termin = dict(termin)
    termin["monteure"] = _build_monteure(mandant_id, termin["id"])
    termin["konflikt"] = False
    termin["konflikt_monteure"] = []
    return termin


def _to_list_item(mandant_id: str, termin: dict) -> dict:
    t = _with_monteure(mandant_id, termin)
    t.pop("vorheriger_vorgang_status", None)
    return t


def _detail(mandant_id: str, termin_id: str, nutzer: Optional[CurrentUser] = None) -> dict:
    termin = _require_termin(mandant_id, termin_id)
    termin = _with_monteure(mandant_id, termin)
    kontakt = repo.get_kontakt_for_vorgang(mandant_id, termin["vorgang_id"])
    termin["kontakt"] = (
        {"name": kontakt["name"], "telefon": kontakt.get("telefon"),
         "email": kontakt.get("email")} if kontakt else None
    )
    if nutzer is not None and nutzer.role == "Monteur":
        termin["ist_eigen"] = repo.termin_gehoert_zu_nutzer(
            mandant_id, termin_id, nutzer.id)
    return termin


# --- Statuswechsel (AC-6) -------------------------------------------------


def _setze_status_geplant(user, vorgang: dict) -> None:
    if vorgang["status"] == TERMIN_STATUS_OFFEN:
        return
    vorgaenge_repo.update_vorgang(
        user.mandant_id, vorgang["id"], {"status": TERMIN_STATUS_OFFEN})
    vorgaenge_repo.add_historie(
        user.mandant_id, vorgang["id"], "termin_geplant", vorgang["anliegen"], user.id)


def _pruefe_ruecksetzung(user, vorgang: dict, vorheriger_status: str | None) -> None:
    """Bei Absage des letzten offenen Termins: Status zurücksetzen + historisieren."""
    if repo.count_open_termine(user.mandant_id, vorgang["id"]) > 0:
        return
    ziel = vorheriger_status or "Neu"
    vorgaenge_repo.update_vorgang(user.mandant_id, vorgang["id"], {"status": ziel})
    vorgaenge_repo.add_historie(
        user.mandant_id, vorgang["id"], "termin_status_zurueckgesetzt",
        f"-> {ziel}", user.id)


# --- Anlage / Änderung / Absage ------------------------------------------


def _validate_zeitraum(beginn: _dt.datetime, ende: _dt.datetime) -> None:
    if ende <= beginn:
        raise ValidationError("Das Ende muss nach dem Beginn liegen.")


def create_termin(user, payload, vorgang_id_override: str | None = None) -> dict:
    vorgang_id = vorgang_id_override or payload.vorgang_id
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)
    _validate_zeitraum(payload.beginn, payload.ende)

    beginn = _to_utc(payload.beginn)
    ende = _to_utc(payload.ende)

    konflikt_ids = repo.find_konflikt_monteure(user.mandant_id, payload.monteure, beginn, ende)

    vorheriger = (vorgang["status"] if vorgang["status"] != TERMIN_STATUS_OFFEN
                  else vorgang.get("vorheriger_vorgang_status") or "Neu")

    termin = repo.create_termin(
        user.mandant_id, vorgang["id"], beginn, ende, payload.adresse, payload.notiz,
        vorheriger_vorgang_status=vorheriger)

    for nutzer_id in payload.monteure:
        _require_monteur(user.mandant_id, nutzer_id)
        repo.add_zuweisung(user.mandant_id, termin["id"], nutzer_id)

    _setze_status_geplant(user, vorgang)
    vorgaenge_repo.add_historie(
        user.mandant_id, vorgang["id"], "termin_angelegt", vorgang["anliegen"], user.id)

    detail = _detail(user.mandant_id, termin["id"], user)
    return {
        "termin": detail,
        "konflikt": bool(konflikt_ids),
        "konflikt_monteure": konflikt_ids,
    }


def update_termin(user, termin_id: str, payload) -> dict:
    termin = _require_termin(user.mandant_id, termin_id)

    beginn_dt = payload.beginn if payload.beginn is not None else _parse(termin["beginn"])
    ende_dt = payload.ende if payload.ende is not None else _parse(termin["ende"])
    _validate_zeitraum(beginn_dt, ende_dt)

    if payload.vorgang_id is not None and payload.vorgang_id != termin["vorgang_id"]:
        _require_vorgang(user.mandant_id, payload.vorgang_id)
        new_vorgang_id = payload.vorgang_id
    else:
        new_vorgang_id = termin["vorgang_id"]

    beginn = _to_utc(beginn_dt)
    ende = _to_utc(ende_dt)

    monteure = payload.monteure if payload.monteure is not None else (
        [z["nutzer_id"] for z in _monteure_read(user.mandant_id, termin_id)]
    )
    konflikt_ids = repo.find_konflikt_monteure(
        user.mandant_id, monteure, beginn, ende, exclude_termin_id=termin_id)

    fields: dict = {}
    if payload.adresse is not None:
        fields["adresse"] = payload.adresse
    if payload.notiz is not None:
        fields["notiz"] = payload.notiz
    if beginn != termin["beginn"] or ende != termin["ende"]:
        fields["beginn"] = beginn
        fields["ende"] = ende
    if new_vorgang_id != termin["vorgang_id"]:
        fields["vorgang_id"] = new_vorgang_id
    repo.update_termin(user.mandant_id, termin_id, fields)

    if payload.monteure is not None:
        existing = [z["nutzer_id"] for z in _monteure_read(user.mandant_id, termin_id)]
        for nutzer_id in payload.monteure:
            _require_monteur(user.mandant_id, nutzer_id)
            if nutzer_id not in existing:
                repo.add_zuweisung(user.mandant_id, termin_id, nutzer_id)
        for nutzer_id in existing:
            if nutzer_id not in payload.monteure:
                repo.remove_zuweisung(user.mandant_id, termin_id, nutzer_id)

    vorgaenge_repo.add_historie(
        user.mandant_id, new_vorgang_id, "termin_geaendert", termin["anliegen"], user.id)

    detail = _detail(user.mandant_id, termin_id, user)
    return {
        "termin": detail,
        "konflikt": bool(konflikt_ids),
        "konflikt_monteure": konflikt_ids,
    }


def absagen(user, termin_id: str) -> dict:
    termin = _require_termin(user.mandant_id, termin_id)
    if termin["abgesagt_at"]:
        # Idempotent: bereits abgesagt -> nur Konflikt neu berechnen
        konflikt_ids = repo.find_konflikt_monteure(
            user.mandant_id,
            [z["nutzer_id"] for z in _monteure_read(user.mandant_id, termin_id)],
            termin["beginn"], termin["ende"], exclude_termin_id=termin_id)
        detail = _detail(user.mandant_id, termin_id, user)
        return {"termin": detail, "konflikt": bool(konflikt_ids),
                "konflikt_monteure": konflikt_ids}

    abgesagt_at = _to_utc(_dt.datetime.now(_dt.timezone.utc))
    repo.cancel_termin(user.mandant_id, termin_id, abgesagt_at)

    vorgang = _require_vorgang(user.mandant_id, termin["vorgang_id"])
    # Snapshot des Vorherstatus merken, falls der Termin der letzte offene ist
    if repo.count_open_termine(user.mandant_id, vorgang["id"],
                               exclude_termin_id=termin_id) == 0:
        if termin.get("vorheriger_vorgang_status"):
            repo.update_termin(
                user.mandant_id, termin_id,
                {"vorheriger_vorgang_status": termin["vorheriger_vorgang_status"]})

    vorgaenge_repo.add_historie(
        user.mandant_id, vorgang["id"], "termin_abgesagt", termin["anliegen"], user.id)
    _pruefe_ruecksetzung(user, vorgang, termin.get("vorheriger_vorgang_status"))

    detail = _detail(user.mandant_id, termin_id, user)
    return {"termin": detail, "konflikt": False, "konflikt_monteure": []}


# --- Zuweisungen ---------------------------------------------------------


def zuweisen(user, termin_id: str, nutzer_id: str) -> dict:
    termin = _require_termin(user.mandant_id, termin_id)
    _require_monteur(user.mandant_id, nutzer_id)
    repo.add_zuweisung(user.mandant_id, termin_id, nutzer_id)
    konflikt_ids = repo.find_konflikt_monteure(
        user.mandant_id, [nutzer_id], termin["beginn"], termin["ende"],
        exclude_termin_id=termin_id)
    vorgaenge_repo.add_historie(
        user.mandant_id, termin["vorgang_id"], "termin_zugewiesen",
        nutzer_id, user.id)
    detail = _detail(user.mandant_id, termin_id, user)
    return {"termin": detail, "konflikt": bool(konflikt_ids),
            "konflikt_monteure": konflikt_ids}


def entziehen(user, termin_id: str, nutzer_id: str) -> dict:
    termin = _require_termin(user.mandant_id, termin_id)
    repo.remove_zuweisung(user.mandant_id, termin_id, nutzer_id)
    vorgaenge_repo.add_historie(
        user.mandant_id, termin["vorgang_id"], "termin_entzogen",
        nutzer_id, user.id)
    detail = _detail(user.mandant_id, termin_id, user)
    return {"termin": detail, "konflikt": False, "konflikt_monteure": []}


# --- Listen / Lesen ------------------------------------------------------


def _parse(value: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(value)


def _parse_filter(von: str | None, bis: str | None) -> tuple[str, str]:
    if not von or not bis:
        raise ValidationError("Die Parameter 'von' und 'bis' sind erforderlich.")
    try:
        v = _parse(von)
        b = _parse(bis)
    except ValueError:
        raise ValidationError("Ungültiges Zeitfenster (ISO erwartet).")
    if b <= v:
        raise ValidationError("'bis' muss nach 'von' liegen.")
    return _to_utc(v), _to_utc(b)


def list_termine(user, von: str | None, bis: str | None,
                 nutzer_ids: list[str] | None = None) -> dict:
    if user.role == "Monteur":
        # AC-5: Monteure sehen serverseitig nur die eigenen Termine.
        eigene = repo.list_eigene_termin_ids(user.mandant_id, user.id)
        nutzer_ids = [user.id]
        rows = [r for r in repo.list_termine_rows(
            user.mandant_id, *(_parse_filter(von, bis)),
            nutzer_ids=[user.id]) if r["id"] in set(eigene)]
    else:
        v, b = _parse_filter(von, bis)
        rows = repo.list_termine_rows(user.mandant_id, v, b, nutzer_ids)

    items = [_to_list_item(user.mandant_id, r) for r in rows]
    konflikte = set()
    for r in rows:
        if r["abgesagt_at"]:
            continue
        kids = repo.find_konflikt_monteure(
            user.mandant_id,
            [z["nutzer_id"] for z in _monteure_read(user.mandant_id, r["id"])],
            r["beginn"], r["ende"], exclude_termin_id=r["id"])
        if kids:
            for it in items:
                if it["id"] == r["id"]:
                    it["konflikt"] = True
                    it["konflikt_monteure"] = kids
            konflikte.update(kids)
    total = len(items)
    return {
        "items": items,
        "konflikt_monteure": sorted(konflikte),
        "total": total,
    }


def get_termin_detail(user, termin_id: str) -> dict:
    termin = _require_termin(user.mandant_id, termin_id)
    if user.role == "Monteur":
        if not repo.termin_gehoert_zu_nutzer(user.mandant_id, termin_id, user.id):
            raise ForbiddenError("Sie können nur Ihnen zugewiesene Termine einsehen.")
    return _detail(user.mandant_id, termin_id, user)


def list_vorgang_termine(user, vorgang_id: str) -> list[dict]:
    _require_vorgang(user.mandant_id, vorgang_id)
    if user.role == "Monteur":
        allowed = repo.list_eigene_termin_ids(user.mandant_id, user.id)
        alle = repo.list_termine_by_vorgang(user.mandant_id, vorgang_id)
        rows = [r for r in alle if r["id"] in set(allowed)]
    else:
        rows = repo.list_termine_by_vorgang(user.mandant_id, vorgang_id)
    return [_to_list_item(user.mandant_id, r) for r in rows]


def list_monteure(user) -> list[dict]:
    # Aktive Monteure des Mandanten für die Auswahl im Termin-Dialog.
    rows = vorgaenge_repo.list_nutzer_by_role(user.mandant_id, "Monteur", "active")
    return [{"id": r["id"], "name": r["name"], "aktiv": r["status"] == "active"}
            for r in rows]
