from __future__ import annotations

from app import storage as storage_mod
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.features.angebote import pdf as pdf_mod
from app.features.angebote import repository as repo
from app.features.email import schemas as email_schemas
from app.features.email import service as email_service
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from app.features.vorgaenge import service as vorgaenge_service


# --- Helper -----------------------------------------------------------------

def _require_vorgang(mandant_id: str, vorgang_id: str) -> dict:
    vorgang = vorgaenge_repo.get_vorgang(mandant_id, vorgang_id)
    if not vorgang:
        raise NotFoundError("Vorgang nicht gefunden.")
    return vorgang


def _require_angebot(mandant_id: str, angebot_id: str) -> dict:
    angebot = repo.get_angebot(mandant_id, angebot_id)
    if not angebot:
        raise NotFoundError("Angebot nicht gefunden.")
    return angebot


def _require_entwurf(angebot: dict) -> None:
    if angebot["status"] != "entwurf":
        raise ConflictError(
            "Ein versendetes Angebot kann nicht mehr geändert werden — erstellen Sie eine neue Version.",
        )


def _validate_rabatt(menge: float, einzelpreis: float, rabatt_typ: str, rabatt_wert: float) -> None:
    if rabatt_typ == "prozent":
        if not (0 <= rabatt_wert <= 100):
            raise ValidationError("Rabatt in Prozent muss zwischen 0 und 100 liegen.")
    else:
        if rabatt_wert < 0:
            raise ValidationError("Rabattbetrag darf nicht negativ sein.")
        if (menge * einzelpreis) - rabatt_wert < 0:
            raise ValidationError("Rabattbetrag darf die Positionssumme nicht unter 0 senken.")


def _position_netto_steuer(p: dict) -> tuple[float, float]:
    # ponytail: DB liefert Decimal für NUMERIC-Spalten -> coerce zu float, sonst float+=Decimal
    menge = float(p["menge"])
    einzelpreis = float(p["einzelpreis"])
    rabatt_wert = float(p["rabatt_wert"])
    steuersatz = float(p["steuersatz"])
    basis = menge * einzelpreis
    if p["rabatt_typ"] == "prozent":
        netto = basis * (1 - rabatt_wert / 100)
    else:
        netto = basis - rabatt_wert
    netto = round(netto, 2)
    steuer = round(netto * steuersatz / 100, 2)
    return netto, steuer


def _totals(positionen: list[dict]) -> tuple[float, float, float]:
    netto_summe = 0.0
    steuer_summe = 0.0
    for p in positionen:
        netto, steuer = _position_netto_steuer(p)
        netto_summe += netto
        steuer_summe += steuer
    netto_summe = round(netto_summe, 2)
    steuer_summe = round(steuer_summe, 2)
    return netto_summe, steuer_summe, round(netto_summe + steuer_summe, 2)


def _recalc_and_store(mandant_id: str, angebot_id: str) -> None:
    positionen = repo.list_positionen(mandant_id, angebot_id)
    netto, steuer, brutto = _totals(positionen)
    repo.update_angebot(mandant_id, angebot_id,
                        {"netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto})


def _position_read(p: dict) -> dict:
    netto, _ = _position_netto_steuer(p)
    kalkuliert = p.get("kalkulierter_einzelpreis")
    angepasst = bool(kalkuliert is not None
                     and abs(float(p["einzelpreis"]) - float(kalkuliert)) >= 0.005)
    return {**p, "positions_summe": netto,
            "kalkulierter_einzelpreis": (float(kalkuliert) if kalkuliert is not None else None),
            "preis_override_begruendung": p.get("preis_override_begruendung"),
            "preis_angepasst": angepasst,
            "aus_gewerk": kalkuliert is not None}


def _detail(mandant_id: str, angebot_id: str) -> dict:
    angebot = repo.get_angebot(mandant_id, angebot_id)
    positionen = [_position_read(p) for p in repo.list_positionen(mandant_id, angebot_id)]
    return {**angebot, "positionen": positionen}


def _build_pdf_bytes(mandant_id: str, angebot: dict, vorgang: dict, positionen: list[dict],
                     netto: float, steuer: float, brutto: float) -> bytes:
    kunde = kunden_repo.get_kunde(mandant_id, vorgang["kunde_id"])
    positionen_read = [_position_read(p) for p in positionen]
    return pdf_mod.render_angebot_pdf(
        angebot_nummer=angebot["angebot_nummer"], version=angebot["version"],
        gueltig_bis=str(angebot["gueltig_bis"]) if angebot.get("gueltig_bis") else None,
        betrieb_name=repo.get_mandant_name(mandant_id),
        kunde_name=kunde["name"] if kunde else "", kunde_email=kunde.get("email") if kunde else None,
        kunde_telefon=kunde.get("telefon") if kunde else None, positionen=positionen_read,
        netto_summe=netto, steuer_summe=steuer, brutto_summe=brutto, freitext=angebot.get("freitext"),
    )


# --- Liste / Detail -----------------------------------------------------

def list_angebote(user, vorgang_id: str) -> list[dict]:
    _require_vorgang(user.mandant_id, vorgang_id)
    return repo.list_angebote(user.mandant_id, vorgang_id)


def get_angebot_detail(user, angebot_id: str) -> dict:
    _require_angebot(user.mandant_id, angebot_id)
    return _detail(user.mandant_id, angebot_id)


# --- Anlegen / Kopf ändern ------------------------------------------------

def create_angebot(user, vorgang_id: str, payload) -> dict:
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)
    # Edge Case: Testvorgänge dürfen nicht weiterbearbeitet werden (Acceptance-Kriterium).
    if vorgang.get("ist_test"):
        raise ForbiddenError(
            "Aus einem Testvorgang kann kein Angebot erstellt werden."
        )
    version = 1
    vorgaenger_id = None
    if payload.vorgaenger_angebot_id:
        vorgaenger = repo.get_angebot(user.mandant_id, payload.vorgaenger_angebot_id)
        if not vorgaenger or vorgaenger["vorgang_id"] != vorgang["id"]:
            raise ValidationError("Vorgänger-Angebot gehört nicht zu diesem Vorgang.")
        version = vorgaenger["version"] + 1
        vorgaenger_id = vorgaenger["id"]

    nummer = repo.next_angebot_nummer(user.mandant_id)
    angebot = repo.create_angebot(user.mandant_id, vorgang["id"], version, vorgaenger_id, nummer)

    fields: dict = {}
    if payload.gueltig_bis is not None:
        fields["gueltig_bis"] = payload.gueltig_bis.isoformat()
    if payload.freitext is not None:
        fields["freitext"] = payload.freitext
    if fields:
        repo.update_angebot(user.mandant_id, angebot["id"], fields)

    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "angebot_angelegt", nummer, user.id)
    return _detail(user.mandant_id, angebot["id"])


def update_angebot_kopf(user, angebot_id: str, payload) -> dict:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    _require_entwurf(angebot)
    fields: dict = {}
    if payload.gueltig_bis is not None:
        fields["gueltig_bis"] = payload.gueltig_bis.isoformat()
    if payload.freitext is not None:
        fields["freitext"] = payload.freitext
    if fields:
        repo.update_angebot(user.mandant_id, angebot_id, fields)
        vorgaenge_repo.add_historie(user.mandant_id, angebot["vorgang_id"], "angebot_geaendert",
                                    angebot["angebot_nummer"], user.id)
    return _detail(user.mandant_id, angebot_id)


# --- Positionen ---------------------------------------------------------

def add_position(user, angebot_id: str, payload) -> dict:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    _require_entwurf(angebot)
    _validate_rabatt(payload.menge, payload.einzelpreis, payload.rabatt_typ, payload.rabatt_wert)
    repo.create_position(user.mandant_id, angebot_id, payload.bezeichnung, payload.menge,
                         payload.einheit, payload.einzelpreis, payload.steuersatz,
                         payload.rabatt_typ, payload.rabatt_wert, payload.sortierung)
    _recalc_and_store(user.mandant_id, angebot_id)
    vorgaenge_repo.add_historie(user.mandant_id, angebot["vorgang_id"], "angebot_position_hinzugefuegt",
                                payload.bezeichnung, user.id)
    return _detail(user.mandant_id, angebot_id)


def update_position(user, angebot_id: str, position_id: str, payload) -> dict:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    _require_entwurf(angebot)
    existing = repo.get_position(user.mandant_id, angebot_id, position_id)
    if not existing:
        raise NotFoundError("Position nicht gefunden.")

    updates = payload.model_dump(exclude_unset=True)
    merged = {**existing, **updates}
    _validate_rabatt(merged["menge"], merged["einzelpreis"], merged["rabatt_typ"], merged["rabatt_wert"])

    if updates:
        repo.update_position(user.mandant_id, angebot_id, position_id, updates)
        _recalc_and_store(user.mandant_id, angebot_id)
        vorgaenge_repo.add_historie(user.mandant_id, angebot["vorgang_id"], "angebot_position_geaendert",
                                    merged["bezeichnung"], user.id)
    return _detail(user.mandant_id, angebot_id)


def delete_position(user, angebot_id: str, position_id: str) -> None:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    _require_entwurf(angebot)
    existing = repo.get_position(user.mandant_id, angebot_id, position_id)
    if not existing:
        raise NotFoundError("Position nicht gefunden.")
    repo.delete_position(user.mandant_id, angebot_id, position_id)
    _recalc_and_store(user.mandant_id, angebot_id)
    vorgaenge_repo.add_historie(user.mandant_id, angebot["vorgang_id"], "angebot_position_entfernt",
                                existing["bezeichnung"], user.id)


# --- PDF ------------------------------------------------------------------

def get_pdf_download_url(user, angebot_id: str) -> str:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    if angebot["dokument_id"]:
        dokument = vorgaenge_repo.get_dokument(user.mandant_id, angebot["vorgang_id"], angebot["dokument_id"])
        if dokument:
            return storage_mod.storage.presigned_get_url(dokument["objektpfad"])
    # Noch keine Vorschau erzeugt (kein freigabe-Aufruf bisher) -> on-demand rendern.
    positionen = repo.list_positionen(user.mandant_id, angebot_id)
    if not positionen:
        raise ValidationError("Angebot hat noch keine Position — es kann noch kein PDF erzeugt werden.")
    vorgang = _require_vorgang(user.mandant_id, angebot["vorgang_id"])
    netto, steuer, brutto = _totals(positionen)
    pdf_bytes = _build_pdf_bytes(user.mandant_id, angebot, vorgang, positionen, netto, steuer, brutto)
    objektpfad = f"angebote/{user.mandant_id}/{angebot_id}/{angebot['angebot_nummer']}.pdf"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"],
                                              f"{angebot['angebot_nummer']}.pdf", objektpfad,
                                              "application/pdf", len(pdf_bytes), user.id)
    repo.update_angebot(user.mandant_id, angebot_id, {"dokument_id": dokument["id"]})
    return storage_mod.storage.presigned_get_url(dokument["objektpfad"])


# --- Freigabe / Senden -----------------------------------------------------

def freigabe(user, angebot_id: str, payload=None) -> dict:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    _require_entwurf(angebot)

    positionen = repo.list_positionen(user.mandant_id, angebot_id)
    if not positionen:
        raise ValidationError("Ein Angebot ohne Position kann nicht freigegeben werden.")

    vorgang = _require_vorgang(user.mandant_id, angebot["vorgang_id"])
    kunde = kunden_repo.get_kunde(user.mandant_id, vorgang["kunde_id"])
    empfaenger = (payload.empfaenger if payload and payload.empfaenger else None) or \
        (kunde.get("email") if kunde else None)
    if not empfaenger:
        raise ValidationError("Ein Angebot ohne Empfänger-E-Mail kann nicht freigegeben werden.")

    netto, steuer, brutto = _totals(positionen)
    pdf_bytes = _build_pdf_bytes(user.mandant_id, angebot, vorgang, positionen, netto, steuer, brutto)
    objektpfad = f"angebote/{user.mandant_id}/{angebot_id}/{angebot['angebot_nummer']}.pdf"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"],
                                              f"{angebot['angebot_nummer']}.pdf", objektpfad,
                                              "application/pdf", len(pdf_bytes), user.id)

    repo.update_angebot(user.mandant_id, angebot_id,
                        {"dokument_id": dokument["id"], "empfaenger_email": empfaenger,
                         "netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto})
    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "angebot_freigabe_vorbereitet",
                                angebot["angebot_nummer"], user.id)

    betreff = (payload.betreff if payload and payload.betreff else None) or f"Angebot {angebot['angebot_nummer']}"
    return {
        "angebot_id": angebot_id, "empfaenger": empfaenger, "betreff": betreff,
        "netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto,
        "pdf_download_url": storage_mod.storage.presigned_get_url(dokument["objektpfad"]),
    }


def senden(user, angebot_id: str, payload) -> dict:
    angebot = _require_angebot(user.mandant_id, angebot_id)
    if angebot["status"] != "entwurf":
        raise ConflictError("Dieses Angebot wurde bereits versendet.")
    if not angebot["dokument_id"] or not angebot["empfaenger_email"]:
        raise ValidationError(
            "Bitte zuerst die Freigabeansicht aufrufen (POST /angebote/{id}/freigabe), bevor gesendet wird.",
        )

    vorgang = _require_vorgang(user.mandant_id, angebot["vorgang_id"])
    positionen = repo.list_positionen(user.mandant_id, angebot_id)
    if not positionen:
        raise ValidationError("Ein Angebot ohne Position kann nicht versendet werden.")

    empfaenger = payload.empfaenger or angebot["empfaenger_email"]
    betreff = payload.betreff or f"Angebot {angebot['angebot_nummer']}"
    text = payload.text or f"Anbei erhalten Sie unser Angebot {angebot['angebot_nummer']}."

    netto, steuer, brutto = _totals(positionen)
    pdf_bytes = _build_pdf_bytes(user.mandant_id, angebot, vorgang, positionen, netto, steuer, brutto)
    dateiname = f"{angebot['angebot_nummer']}.pdf"

    compose = email_schemas.EmailCompose(empfaenger=empfaenger, betreff=betreff, text=text)
    try:
        email_service.send_vorgang_email(user, vorgang["id"], compose,
                                         attachment=(dateiname, pdf_bytes, "application/pdf"))
    except Exception:
        # Edge Case: Versand fehlgeschlagen -> Angebot bleibt Entwurf.
        return {"angebot": _detail(user.mandant_id, angebot_id), "versendet": False,
                "fehler_text": "Angebot wurde nicht versendet."}

    objektpfad = f"angebote/{user.mandant_id}/{angebot_id}/{dateiname}"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"], dateiname, objektpfad,
                                              "application/pdf", len(pdf_bytes), user.id)
    repo.mark_versendet(user.mandant_id, angebot_id, empfaenger, user.id, netto, steuer, brutto)
    repo.update_angebot(user.mandant_id, angebot_id, {"dokument_id": dokument["id"]})
    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "angebot_versendet",
                                f"{angebot['angebot_nummer']} an {empfaenger}", user.id)
    vorgaenge_service.update_vorgang(user, vorgang["id"], status="Angebot offen", anliegen=None,
                                     notizen=None, objekt_id=None)

    return {"angebot": _detail(user.mandant_id, angebot_id), "versendet": True, "fehler_text": None}


def neue_version(user, angebot_id: str) -> dict:
    quelle = _require_angebot(user.mandant_id, angebot_id)
    if quelle["status"] != "versendet":
        raise ConflictError("Nur ein versendetes Angebot kann als neue Version fortgeführt werden.")

    nummer = repo.next_angebot_nummer(user.mandant_id)
    neu = repo.create_angebot(user.mandant_id, quelle["vorgang_id"], quelle["version"] + 1,
                              quelle["id"], nummer)
    kopf_fields: dict = {}
    if quelle.get("gueltig_bis"):
        kopf_fields["gueltig_bis"] = quelle["gueltig_bis"]
    if quelle.get("freitext"):
        kopf_fields["freitext"] = quelle["freitext"]
    if kopf_fields:
        repo.update_angebot(user.mandant_id, neu["id"], kopf_fields)

    for p in repo.list_positionen(user.mandant_id, quelle["id"]):
        repo.create_position(user.mandant_id, neu["id"], p["bezeichnung"], p["menge"], p["einheit"],
                             p["einzelpreis"], p["steuersatz"], p["rabatt_typ"], p["rabatt_wert"],
                             p["sortierung"])
    _recalc_and_store(user.mandant_id, neu["id"])

    vorgaenge_repo.add_historie(user.mandant_id, quelle["vorgang_id"], "angebot_neue_version",
                                f"{quelle['angebot_nummer']} -> {nummer}", user.id)
    return _detail(user.mandant_id, neu["id"])
