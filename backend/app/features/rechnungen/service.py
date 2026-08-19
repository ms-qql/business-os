from __future__ import annotations

from app import storage as storage_mod
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.features.email import schemas as email_schemas
from app.features.email import service as email_service
from app.features.kunden import repository as kunden_repo
from app.features.rechnungen import pdf as pdf_mod
from app.features.rechnungen import repository as repo
from app.features.vorgaenge import repository as vorgaenge_repo

# Zahlungsstatus-Wechsel über den dedizierten Endpunkt erlaubt; Storniert wird
# ausschließlich durch den Storno-Endpunkt gesetzt (Tech Design C / ADR-8-5).
ZULAESSIGE_ZAHLUNGSSTATUS = ("Offen", "Bezahlt")


# --- Helper ---------------------------------------------------------------

def _require_vorgang(mandant_id: str, vorgang_id: str) -> dict:
    vorgang = vorgaenge_repo.get_vorgang(mandant_id, vorgang_id)
    if not vorgang:
        raise NotFoundError("Vorgang nicht gefunden.")
    return vorgang


def _require_rechnung(mandant_id: str, rechnung_id: str) -> dict:
    rechnung = repo.get_rechnung(mandant_id, rechnung_id)
    if not rechnung:
        raise NotFoundError("Rechnung nicht gefunden.")
    return rechnung


def _require_entwurf(rechnung: dict) -> None:
    if rechnung["status"] != "entwurf":
        raise ConflictError(
            "Eine versendete oder stornierte Rechnung kann nicht mehr geändert werden.",
        )
    if rechnung.get("freigabe_vorbereitet_at"):
        raise ConflictError(
            "Bitte die Freigabe erneut aufrufen, um Änderungen nach der Vorschau zu übernehmen.",
        )


def _position_netto_steuer(p: dict) -> tuple[float, float]:
    # rechnung_position kennt keinen Rabatt (V1): Summe = Menge * Netto-Einzelpreis.
    menge = float(p["menge"])
    einzelpreis = float(p["netto_einzelpreis"])
    steuersatz = float(p["steuersatz"])
    netto = round(menge * einzelpreis, 2)
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


def _recalc_and_store(mandant_id: str, rechnung_id: str) -> None:
    positionen = repo.list_positionen(mandant_id, rechnung_id)
    netto, steuer, brutto = _totals(positionen)
    repo.update_rechnung(mandant_id, rechnung_id,
                         {"netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto})


def _position_read(p: dict) -> dict:
    netto, _ = _position_netto_steuer(p)
    return {**p, "positions_summe": netto}


def _detail(mandant_id: str, rechnung_id: str) -> dict:
    rechnung = repo.get_rechnung(mandant_id, rechnung_id)
    positionen = [_position_read(p) for p in repo.list_positionen(mandant_id, rechnung_id)]
    return {**rechnung, "positionen": positionen}


def _snapshot_dicts(mandant_id: str, rechnung: dict, vorgang: dict):
    """Sammelt die unveränderlichen Belegdaten aus serverseitig gespeicherten
    Stammdaten (ADR-8-2). Liefert (profil, kunde, objekt, positionen_read, summen)."""
    profil = repo.get_rechnungsstellerprofil(mandant_id) or {}
    kunde = kunden_repo.get_kunde(mandant_id, vorgang["kunde_id"]) or {}
    objekt = {}
    if vorgang.get("objekt_id"):
        o = kunden_repo.get_objekt(mandant_id, vorgang["objekt_id"])
        objekt = o or {}
    positionen = [_position_read(p) for p in repo.list_positionen(mandant_id, rechnung["id"])]
    netto, steuer, brutto = _totals(positionen)
    summen = {"netto_summe": netto, "steuer_summe": steuer, "brutto_summe": brutto}
    return profil, kunde, objekt, positionen, summen


def _build_pdf_bytes(rechnung: dict, profil: dict, kunde: dict, objekt: dict,
                     positionen: list[dict], netto: float, steuer: float, brutto: float) -> bytes:
    return pdf_mod.render_rechnung_pdf(
        rechnungsnummer=rechnung["rechnungsnummer"],
        rechnungsdatum=str(rechnung["rechnungsdatum"]),
        leistungsdatum=str(rechnung["leistungsdatum"]),
        betrieb_name=repo.get_mandant_name(rechnung["mandant_id"]),
        rechnungssteller=profil, kunde=kunde, objekt=objekt,
        positionen=positionen, netto_summe=netto, steuer_summe=steuer, brutto_summe=brutto,
        storniert=rechnung["status"] == "storniert",
    )


# --- Rechnungsstellerprofil (Einstellungen) ------------------------------

def get_rechnungsstellerprofil(user) -> dict | None:
    return repo.get_rechnungsstellerprofil(user.mandant_id)


def save_rechnungsstellerprofil(user, payload) -> dict:
    profil = {
        "firma_name": payload.firma_name, "strasse": payload.strasse,
        "hausnummer": payload.hausnummer, "plz": payload.plz, "ort": payload.ort,
        "steuernummer": payload.steuernummer, "ust_id": payload.ust_id,
    }
    return repo.upsert_rechnungsstellerprofil(user.mandant_id, profil)


# --- Liste / Detail -------------------------------------------------------

def list_rechnungen(user, vorgang_id: str) -> list[dict]:
    _require_vorgang(user.mandant_id, vorgang_id)
    return repo.list_rechnungen(user.mandant_id, vorgang_id)


def get_rechnung_detail(user, rechnung_id: str) -> dict:
    _require_rechnung(user.mandant_id, rechnung_id)
    return _detail(user.mandant_id, rechnung_id)


# --- Anlegen (Entwurf + reservierte Nummer) ------------------------------

def create_rechnung(user, vorgang_id: str, payload) -> dict:
    vorgang = _require_vorgang(user.mandant_id, vorgang_id)
    # AC1: nur aus einem erledigten Vorgang; sonst 409 mit deutscher Hinweismeldung.
    if vorgang["status"] != "Erledigt":
        raise ConflictError(
            "Eine Rechnung kann nur aus einem erledigten Vorgang erstellt werden.",
        )

    nummer = repo.next_rechnung_nummer(user.mandant_id)
    rechnung = repo.create_rechnung(
        user.mandant_id, vorgang["id"], nummer,
        payload.rechnungsdatum.isoformat(), payload.leistungsdatum.isoformat(),
    )

    if payload.angebot_id:
        _uebernehme_angebot_positionen(user.mandant_id, rechnung["id"], payload.angebot_id,
                                       vorgang["id"])
        _recalc_and_store(user.mandant_id, rechnung["id"])

    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "rechnung_angelegt",
                                nummer, user.id)
    return _detail(user.mandant_id, rechnung["id"])


def _uebernehme_angebot_positionen(mandant_id: str, rechnung_id: str, angebot_id: str,
                                   vorgang_id: str) -> None:
    from app.features.angebote import repository as angebote_repo

    angebot = angebote_repo.get_angebot(mandant_id, angebot_id)
    if not angebot or angebot["vorgang_id"] != vorgang_id:
        raise ValidationError("Das Angebot gehört nicht zu diesem Vorgang.")
    for i, p in enumerate(angebote_repo.list_positionen(mandant_id, angebot_id)):
        # Keine Rabattlogik übernehmen (V1): nur die erbrachte Leistung als Preise.
        repo.create_position(mandant_id, rechnung_id, p["bezeichnung"], float(p["menge"]),
                             p["einheit"], float(p["einzelpreis"]), float(p["steuersatz"]),
                             i)


# --- Kopf / Positionen (nur Entwurf) -------------------------------------

def update_rechnung_kopf(user, rechnung_id: str, payload) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    _require_entwurf(rechnung)
    fields: dict = {}
    if payload.rechnungsdatum is not None:
        fields["rechnungsdatum"] = payload.rechnungsdatum.isoformat()
    if payload.leistungsdatum is not None:
        fields["leistungsdatum"] = payload.leistungsdatum.isoformat()
    if payload.empfaenger_email is not None:
        fields["empfaenger_email"] = payload.empfaenger_email
    if fields:
        repo.update_rechnung(user.mandant_id, rechnung_id, fields)
        vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"],
                                    "rechnung_geaendert", rechnung["rechnungsnummer"], user.id)
    return _detail(user.mandant_id, rechnung_id)


def add_position(user, rechnung_id: str, payload) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    _require_entwurf(rechnung)
    repo.create_position(user.mandant_id, rechnung_id, payload.bezeichnung, payload.menge,
                         payload.einheit, payload.netto_einzelpreis, payload.steuersatz,
                         payload.sortierung)
    _recalc_and_store(user.mandant_id, rechnung_id)
    vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"],
                                "rechnung_position_hinzugefuegt", payload.bezeichnung, user.id)
    return _detail(user.mandant_id, rechnung_id)


def update_position(user, rechnung_id: str, position_id: str, payload) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    _require_entwurf(rechnung)
    if not repo.get_position(user.mandant_id, rechnung_id, position_id):
        raise NotFoundError("Position nicht gefunden.")
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        repo.update_position(user.mandant_id, rechnung_id, position_id, updates)
        _recalc_and_store(user.mandant_id, rechnung_id)
        vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"],
                                    "rechnung_position_geaendert", payload.bezeichnung
                                    if payload.bezeichnung else rechnung["rechnungsnummer"],
                                    user.id)
    return _detail(user.mandant_id, rechnung_id)


def delete_position(user, rechnung_id: str, position_id: str) -> None:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    _require_entwurf(rechnung)
    if not repo.get_position(user.mandant_id, rechnung_id, position_id):
        raise NotFoundError("Position nicht gefunden.")
    repo.delete_position(user.mandant_id, rechnung_id, position_id)
    _recalc_and_store(user.mandant_id, rechnung_id)
    vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"],
                                "rechnung_position_entfernt", rechnung["rechnungsnummer"], user.id)


# --- Freigabe (Vorschau, kein Versand) -----------------------------------

def freigabe(user, rechnung_id: str, payload=None) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    _require_entwurf(rechnung)

    positionen = repo.list_positionen(user.mandant_id, rechnung_id)
    if not positionen:
        raise ValidationError("Eine Rechnung ohne Position kann nicht freigegeben werden.")

    vorgang = _require_vorgang(user.mandant_id, rechnung["vorgang_id"])

    # Snapshot-Vollständigkeit prüfen (Tech Design F): kein stiller Fallback.
    profil = repo.get_rechnungsstellerprofil(user.mandant_id)
    if not profil:
        raise ValidationError("Es ist noch kein vollständiges Rechnungsstellerprofil hinterlegt.")
    kunde = kunden_repo.get_kunde(user.mandant_id, vorgang["kunde_id"])
    if not kunde or not kunde.get("name"):
        raise ValidationError("Dem Vorgang fehlen vollständige Kundendaten.")
    objekt_adresse = None
    if vorgang.get("objekt_id"):
        objekt = kunden_repo.get_objekt(user.mandant_id, vorgang["objekt_id"])
        objekt_adresse = objekt.get("adresse") if objekt else None
    if not objekt_adresse:
        raise ValidationError(
            "Dem Vorgang fehlt eine Objektanschrift — die Rechnung kann nicht freigegeben werden.",
        )

    empfaenger = (payload.empfaenger if payload and payload.empfaenger else None) \
        or (rechnung.get("empfaenger_email")) or (kunde.get("email") if kunde else None)
    if not empfaenger:
        raise ValidationError(
            "Der Rechnungsempfänger hat keine E-Mail-Adresse — die Freigabe ist nicht möglich.",
        )

    netto, steuer, brutto = _totals(positionen)
    pdf_bytes = _build_pdf_bytes(rechnung, profil, kunde, objekt or {},
                                [_position_read(p) for p in positionen], netto, steuer, brutto)
    objektpfad = f"rechnungen/{user.mandant_id}/{rechnung['id']}/{rechnung['rechnungsnummer']}.pdf"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"],
                                              f"{rechnung['rechnungsnummer']}.pdf", objektpfad,
                                              "application/pdf", len(pdf_bytes), user.id)

    repo.set_freigabe_vorbereitet(user.mandant_id, rechnung_id, empfaenger, netto, steuer, brutto)
    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "rechnung_freigabe_vorbereitet",
                                rechnung["rechnungsnummer"], user.id)

    betreff = (payload.betreff if payload and payload.betreff else None) \
        or f"Rechnung {rechnung['rechnungsnummer']}"
    return {
        "rechnung_id": rechnung_id, "empfaenger": empfaenger, "betreff": betreff,
        "rechnungsnummer": rechnung["rechnungsnummer"], "netto_summe": netto,
        "steuer_summe": steuer, "brutto_summe": brutto,
        "pdf_download_url": storage_mod.storage.presigned_get_url(dokument["objektpfad"]),
    }


# --- Senden (einziger Versandpfad) ---------------------------------------

def senden(user, rechnung_id: str, payload) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    if rechnung["status"] != "entwurf":
        raise ConflictError("Diese Rechnung wurde bereits versendet oder storniert.")
    if not rechnung.get("freigabe_vorbereitet_at"):
        raise ValidationError(
            "Bitte zuerst die Freigabeansicht aufrufen (POST /rechnungen/{id}/freigabe), "
            "bevor gesendet wird.",
        )

    vorgang = _require_vorgang(user.mandant_id, rechnung["vorgang_id"])
    positionen = repo.list_positionen(user.mandant_id, rechnung_id)
    if not positionen:
        raise ValidationError("Eine Rechnung ohne Position kann nicht versendet werden.")

    profil, kunde, objekt, positionen_read, summen = _snapshot_dicts(
        user.mandant_id, rechnung, vorgang)
    empfaenger = payload.empfaenger or rechnung.get("empfaenger_email") \
        or (kunde.get("email") if kunde else None)
    if not empfaenger:
        raise ValidationError("Der Rechnungsempfänger hat keine E-Mail-Adresse.")
    betreff = payload.betreff or f"Rechnung {rechnung['rechnungsnummer']}"
    text = payload.text or f"Anbei erhalten Sie Ihre Rechnung {rechnung['rechnungsnummer']}."

    pdf_bytes = _build_pdf_bytes(rechnung, profil, kunde, objekt or {}, positionen_read,
                                summen["netto_summe"], summen["steuer_summe"],
                                summen["brutto_summe"])
    dateiname = f"{rechnung['rechnungsnummer']}.pdf"

    compose = email_schemas.EmailCompose(empfaenger=empfaenger, betreff=betreff, text=text)
    try:
        email_service.send_vorgang_email(user, vorgang["id"], compose,
                                         attachment=(dateiname, pdf_bytes, "application/pdf"))
    except Exception:
        # Edge Case: Versand fehlgeschlagen -> Entwurf und Zahlungsstatus unverändert.
        return {"rechnung": _detail(user.mandant_id, rechnung_id), "versendet": False,
                "fehler_text": "Rechnung wurde nicht versendet."}

    # Atomar: unveränderliche Fassung + versandtes PDF + Versandmetadaten.
    objektpfad = f"rechnungen/{user.mandant_id}/{rechnung['id']}/{dateiname}"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"], dateiname,
                                              objektpfad, "application/pdf", len(pdf_bytes),
                                              user.id)
    fassung = repo.create_fassung(
        user.mandant_id, rechnung["id"], rechnung["rechnungsnummer"],
        kopf={"rechnungsdatum": str(rechnung["rechnungsdatum"]),
              "leistungsdatum": str(rechnung["leistungsdatum"])},
        rechnungssteller=profil, kunde=kunde, objekt=objekt,
        positionen=positionen_read, summen=summen, dokument_id=dokument["id"],
    )
    repo.mark_versendet(user.mandant_id, rechnung_id, fassung["id"], empfaenger, user.id,
                        summen["netto_summe"], summen["steuer_summe"], summen["brutto_summe"])
    vorgaenge_repo.add_historie(user.mandant_id, vorgang["id"], "rechnung_versendet",
                                f"{rechnung['rechnungsnummer']} an {empfaenger}", user.id)

    return {"rechnung": _detail(user.mandant_id, rechnung_id), "versendet": True,
            "fehler_text": None}


# --- PDF-Download ---------------------------------------------------------

def get_pdf_download_url(user, rechnung_id: str) -> str:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    # Versendet/storniert: unveränderliches Versand-PDF aus der Fassung.
    if rechnung.get("fassung_id"):
        fassung = repo.get_fassung(user.mandant_id, rechnung["fassung_id"])
        if fassung and fassung.get("dokument_id"):
            dok = vorgaenge_repo.get_dokument(user.mandant_id, rechnung["vorgang_id"],
                                              fassung["dokument_id"])
            if dok:
                return storage_mod.storage.presigned_get_url(dok["objektpfad"])
    # Entwurf: on-demand Vorschau aus gespeicherten Daten rendern.
    positionen = repo.list_positionen(user.mandant_id, rechnung_id)
    if not positionen:
        raise ValidationError("Rechnung hat noch keine Position — es kann noch kein PDF erzeugt werden.")
    vorgang = _require_vorgang(user.mandant_id, rechnung["vorgang_id"])
    profil, kunde, objekt, positionen_read, summen = _snapshot_dicts(
        user.mandant_id, rechnung, vorgang)
    pdf_bytes = _build_pdf_bytes(rechnung, profil, kunde, objekt or {}, positionen_read,
                                summen["netto_summe"], summen["steuer_summe"],
                                summen["brutto_summe"])
    objektpfad = f"rechnungen/{user.mandant_id}/{rechnung['id']}/{rechnung['rechnungsnummer']}.pdf"
    storage_mod.storage.put_object(objektpfad, pdf_bytes, "application/pdf")
    dokument = vorgaenge_repo.create_dokument(user.mandant_id, vorgang["id"],
                                              f"{rechnung['rechnungsnummer']}.pdf", objektpfad,
                                              "application/pdf", len(pdf_bytes), user.id)
    return storage_mod.storage.presigned_get_url(dokument["objektpfad"])


# --- Zahlungsstatus (nur versendet) --------------------------------------

def set_zahlungsstatus(user, rechnung_id: str, payload) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    if rechnung["status"] != "versendet":
        raise ConflictError("Der Zahlungsstatus kann nur für versendete Rechnungen geändert werden.")
    if payload.zahlungsstatus == "Storniert":
        raise ValidationError(
            "Der Zahlungsstatus 'Storniert' wird ausschließlich über den Storno-Endpunkt gesetzt.",
        )
    if payload.zahlungsstatus not in ZULAESSIGE_ZAHLUNGSSTATUS:
        raise ValidationError("Der Zahlungsstatus muss 'Offen' oder 'Bezahlt' sein.")
    if rechnung["zahlungsstatus"] == payload.zahlungsstatus:
        return _detail(user.mandant_id, rechnung_id)
    repo.set_zahlungsstatus(user.mandant_id, rechnung_id, payload.zahlungsstatus)
    vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"],
                                "rechnung_zahlungsstatus",
                                f"{rechnung['rechnungsnummer']}: {payload.zahlungsstatus}",
                                user.id)
    return _detail(user.mandant_id, rechnung_id)


# --- Storno (nur versendet; Beleg bleibt) --------------------------------

def storno(user, rechnung_id: str) -> dict:
    rechnung = _require_rechnung(user.mandant_id, rechnung_id)
    if rechnung["status"] != "versendet":
        raise ConflictError("Nur eine versendete Rechnung kann storniert werden.")
    repo.mark_storniert(user.mandant_id, rechnung_id, user.id)
    vorgaenge_repo.add_historie(user.mandant_id, rechnung["vorgang_id"], "rechnung_storniert",
                                rechnung["rechnungsnummer"], user.id)
    return _detail(user.mandant_id, rechnung_id)
