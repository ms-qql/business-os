from __future__ import annotations

import datetime
import json
from datetime import date
from typing import Optional

from app.errors import NotFoundError, ValidationError
from app.features.triage import repository as repo
from app.features.triage.schemas import (
    TriageEinstellungRead, TriageErgebnis, TriageLeistungswertRead,
)

_WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
               "Samstag", "Sonntag"]


def _datum_format(d: date) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def get_einstellung(mandant_id: str) -> TriageEinstellungRead:
    row = repo.get_einstellung(mandant_id)
    if not row:
        return TriageEinstellungRead()
    werte = [
        TriageLeistungswertRead(wert=w["wert"], klassifikation=w["klassifikation"])
        for w in repo.get_werte(mandant_id, row["id"])
    ]
    return TriageEinstellungRead(
        leistungs_formular_id=row["leistungs_formular_id"],
        leistungs_feld_id=row["leistungs_feld_id"],
        wunschtermin_feld_id=row["wunschtermin_feld_id"],
        naechster_freier_termin=row["naechster_freier_termin"],
        werte=werte,
    )


def _require_formular(mandant_id: str, formular_id: str) -> dict:
    from app.features.formulare import repository as formular_repo
    formular = formular_repo.get_formular(mandant_id, formular_id)
    if not formular:
        raise NotFoundError("Formular nicht gefunden.")
    return formular


def _publish_snapshot(mandant_id: str, formular_id: str) -> dict:
    """Liefert den unveränderlichen Snapshot (formular_version.inhalt) der
    aktuell veröffentlichten Version — nicht den Entwurf."""
    from app.features.formulare import repository as formular_repo
    formular = _require_formular(mandant_id, formular_id)
    if not formular.get("veroeffentlicht") or not formular.get("aktuelle_version_id"):
        raise ValidationError("Das ausgewählte Formular ist nicht veröffentlicht.")
    version = formular_repo.get_version(mandant_id, formular["aktuelle_version_id"])
    if not version:
        raise NotFoundError("Veröffentlichung nicht gefunden.")
    inhalt = version["inhalt"]
    if isinstance(inhalt, str):
        inhalt = json.loads(inhalt)
    return inhalt


def _snapshot_feld(snapshot: dict, feld_id: str) -> Optional[dict]:
    for s in snapshot["schritte"]:
        for f in s["felder"]:
            if f["id"] == feld_id:
                return f
    return None


AUSWAHL_TYPEN = {"dropdown", "kachel", "radio"}


def setze_einstellung(mandant_id: str, formular_id: str, feld_id: str,
                      wunschtermin_feld_id: Optional[str],
                      werte: list[dict]) -> TriageEinstellungRead:
    # Gegen den Snapshot der veröffentlichten Version prüfen, nicht den Entwurf.
    snapshot = _publish_snapshot(mandant_id, formular_id)
    feld = _snapshot_feld(snapshot, feld_id)
    if not feld:
        raise NotFoundError("Leistungsfeld nicht gefunden.")
    if feld["typ"] not in AUSWAHL_TYPEN:
        raise ValidationError("Das Leistungsfeld muss ein Auswahlfeld sein.")
    if wunschtermin_feld_id:
        wf = _snapshot_feld(snapshot, wunschtermin_feld_id)
        if not wf:
            raise NotFoundError("Wunschterminfeld nicht gefunden.")
        if wf["typ"] != "datum":
            raise ValidationError("Das Wunschterminfeld muss ein Datumsfeld sein.")
    # Stabile Optionswerte des ausgewählten Leistungsfeldes.
    erlaubte_werte = {o["wert"] for o in feld.get("optionen", [])}
    for w in werte:
        if w["wert"] not in erlaubte_werte:
            raise ValidationError(
                f"Wert „{w['wert']}“ ist keine gültige Option des Leistungsfeldes.")
    if len({w["wert"] for w in werte}) != len(werte):
        raise ValidationError("Leistungswerte dürfen nicht doppelt sein.")
    row = repo.replace_einstellung(mandant_id, formular_id, feld_id,
                                   wunschtermin_feld_id, werte)
    return get_einstellung(mandant_id)


def setze_kapazitaet(mandant_id: str, datum: Optional[date]) -> TriageEinstellungRead:
    repo.set_kapazitaet(mandant_id, datum)
    return get_einstellung(mandant_id)


# --- Berechnung (nicht persistiert) --------------------------------------

def berechne(mandant_id: str, vorgang: dict, einsendung: Optional[dict]) -> TriageErgebnis:
    einstellung = repo.get_einstellung(mandant_id)
    if not einstellung:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=["Keine Triage-Konfiguration vorhanden."],
        )

    leistungs_feld_id = einstellung["leistungs_feld_id"]
    wunschtermin_feld_id = einstellung["wunschtermin_feld_id"]
    kapazitaet = einstellung["naechster_freier_termin"]

    # 1) Grundlage: verknüpfte Einsendung + konfiguriertes Leistungsfeld + Wert.
    if not einsendung:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=["Keine Formular-Einsendung verknüpft."],
            naechster_freier_termin=kapazitaet,
        )
    werte = einsendung.get("werte") or {}
    if not isinstance(werte, dict):
        werte = {}
    if leistungs_feld_id not in werte:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=["Kein Leistungswert in dieser Einsendung."],
            naechster_freier_termin=kapazitaet,
        )
    wert_eintrag = werte[leistungs_feld_id]
    leistungswert = (wert_eintrag.get("werte") or [None])[0] if isinstance(
        wert_eintrag, dict) else wert_eintrag
    if not leistungswert:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=["Kein Leistungswert in dieser Einsendung."],
            naechster_freier_termin=kapazitaet,
        )

    # Nicht konfigurierter Leistungswert -> nicht bewertet (nicht „rot raten“).
    klassifikationen = {
        w["wert"]: w["klassifikation"] for w in repo.get_werte(mandant_id, einstellung["id"])
    }
    if leistungswert not in klassifikationen:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=[f"Leistungswert „{leistungswert}“ ist nicht konfiguriert."],
            naechster_freier_termin=kapazitaet,
        )

    # 2) Rot: unpassend konfiguriert.
    if klassifikationen[leistungswert] == "unpassend":
        return TriageErgebnis(
            status="rot",
            gruende=[f"Leistung nicht passend ({leistungswert})."],
            naechster_freier_termin=kapazitaet,
        )

    # Ab hier: Leistung passend.
    # 3) Kein nächster freier Termin -> nicht bewertet.
    if not kapazitaet:
        return TriageErgebnis(
            status="nicht_bewertet",
            gruende=["Kein „Nächster freier Termin“ gepflegt."],
        )

    gruende: list[str] = []
    # 4) Gelb: dringend oder Wunschtermin vor Kapazität.
    anfrage = vorgang.get("_anfrage")
    dringend = bool(anfrage and anfrage.get("dringlichkeit") == "Dringend")
    if dringend:
        gruende.append("Dringende Anfrage")

    wunsch_datum = None
    if wunschtermin_feld_id and wunschtermin_feld_id in werte:
        wt = werte[wunschtermin_feld_id]
        ws = (wt.get("datum") if isinstance(wt, dict) else wt) or ""
        try:
            wunsch_datum = datetime.date.fromisoformat(str(ws)[:10])
        except (ValueError, TypeError):
            wunsch_datum = None
    if wunsch_datum and kapazitaet and wunsch_datum < kapazitaet:
        gruende.append(f"Gewünschter Termin vor {_datum_format(kapazitaet)}")

    if gruende:
        return TriageErgebnis(
            status="gelb", gruende=gruende, naechster_freier_termin=kapazitaet,
        )

    # 5) Grün: passend, keine gelben Hinweise (fehlendes Wunschdatum ist ok).
    return TriageErgebnis(
        status="gruen",
        gruende=["Leistung passend."],
        naechster_freier_termin=kapazitaet,
    )
