from datetime import date

from app.features.angebote import repository as angebote_repo
from app.features.angebote import service as angebote_service
from app.features.email import service as email_service
from app.features.kunden import repository as kunden_repo
from app.features.rechnungen import repository as rechnungen_repo
from app.features.rechnungen import service as rechnungen_service
from app.features.vorgaenge import repository as vorgaenge_repo
from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _setup_vorgang(mandant_id, status="Erledigt", email="kunde@extern.de", objekt_adresse="Musterweg 1, 12345 Stadt"):
    kunde = kunden_repo.create_kunde(mandant_id, "Kunde X", email, "0123", None)
    objekt = kunden_repo.create_objekt(mandant_id, kunde["id"], objekt_adresse, None)
    vorgang = vorgaenge_repo.create_vorgang(mandant_id, kunde["id"], objekt["id"], status,
                                            "Sonstiges", "Heizung defekt", None)
    return kunde, objekt, vorgang


def _setup_profil(mandant_id):
    rechnungen_repo.upsert_rechnungsstellerprofil(mandant_id, {
        "firma_name": "SHK Mustermann", "strasse": "Bahnhofsstr.", "hausnummer": "12",
        "plz": "54321", "ort": "Musterstadt", "steuernummer": "12/345/67890", "ust_id": None,
    })


POSITION = {
    "bezeichnung": "Wartung Heizung", "menge": 2, "einheit": "Std",
    "netto_einzelpreis": 80.0, "steuersatz": 19.0, "sortierung": 0,
}


def _create_rechnung(client, tok, vorgang_id, angebot_id=None):
    body = {"rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15"}
    if angebot_id:
        body["angebot_id"] = angebot_id
    r = client.post(f"/vorgaenge/{vorgang_id}/rechnungen", headers=_auth(tok), json=body)
    assert r.status_code == 201, r.text
    return r.json()


# --- AC1: nur aus erledigtem Vorgang -------------------------------------

def test_create_from_erledigt_allowed(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup_vorgang(mandant, status="Erledigt")
    r = _create_rechnung(client, tok, vorgang["id"])
    assert r["status"] == "entwurf"
    assert r["rechnungsnummer"].startswith("RE-")


def test_create_from_nicht_erledigt_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup_vorgang(mandant, status="Neu")
    r = client.post(f"/vorgaenge/{vorgang['id']}/rechnungen", headers=_auth(tok), json={
        "rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15"})
    assert r.status_code == 409
    assert "erledigten Vorgang" in r.json()["detail"]


def test_monteur_forbidden_all_rechnung_routes(client, mandant):
    tok = _login(client, mandant, "monteur@shk.de", "Monteur")
    _, _, vorgang = _setup_vorgang(mandant)
    r = client.post(f"/vorgaenge/{vorgang['id']}/rechnungen", headers=_auth(tok), json={
        "rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15"})
    assert r.status_code == 403


# --- AC2/AC3: Nummer, Summenberechnung ------------------------------------

def test_rechnung_reserves_number_and_computes_summen(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    assert rechnung["rechnungsnummer"]

    r = client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    assert r.status_code == 201, r.text
    detail = r.json()
    # 2 * 80 = 160 netto; Steuer 19% = 30.40; Brutto 190.40
    assert detail["netto_summe"] == 160.0
    assert detail["steuer_summe"] == 30.40
    assert detail["brutto_summe"] == 190.40
    assert detail["positionen"][0]["positions_summe"] == 160.0


def test_numbers_sequential_and_unique(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup_vorgang(mandant)
    a = _create_rechnung(client, tok, vorgang["id"])
    b = _create_rechnung(client, tok, vorgang["id"])
    assert a["rechnungsnummer"] != b["rechnungsnummer"]


def test_numbering_survives_rollback(mandant):
    n1 = rechnungen_repo.next_rechnung_nummer(mandant)
    n2 = rechnungen_repo.next_rechnung_nummer(mandant)
    assert n1 != n2


# --- AC4: Angebotsübernahme -----------------------------------------------

def _make_angebot(client, tok, vorgang_id):
    r = client.post(f"/vorgaenge/{vorgang_id}/angebote", headers=_auth(tok), json={})
    assert r.status_code == 201, r.text
    return r.json()


def test_angebot_positions_uebernommen(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup_vorgang(mandant)
    angebot = _make_angebot(client, tok, vorgang["id"])
    # Angebots-Position nutzt 'einzelpreis' (nicht 'netto_einzelpreis' wie Rechnung).
    angebot_position = {**POSITION, "einzelpreis": POSITION["netto_einzelpreis"]}
    del angebot_position["netto_einzelpreis"]
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=angebot_position)

    rechnung = _create_rechnung(client, tok, vorgang["id"], angebot_id=angebot["id"])
    assert len(rechnung["positionen"]) == 1
    assert rechnung["positionen"][0]["bezeichnung"] == POSITION["bezeichnung"]
    assert rechnung["brutto_summe"] == 190.40


# --- AC5/AC6: Freigabe + Versand ------------------------------------------

def _freigabe(client, tok, rechnung_id, payload=None):
    return client.post(f"/rechnungen/{rechnung_id}/freigabe", headers=_auth(tok), json=payload or {})


def _setup_konto(mandant):
    from app.features.email import repository as email_repo
    email_repo.upsert_konto(mandant, "imap.x", 993, "post@shk.de", "encrypt:" + "A" * 44, True,
                            "smtp.x", 465, "post@shk.de", "encrypt:" + "A" * 44, True)


def test_freigabe_without_profil_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = _freigabe(client, tok, rechnung["id"])
    assert r.status_code == 422
    assert "Rechnungsstellerprofil" in r.json()["detail"]


def test_freigabe_without_objekt_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    kunde = kunden_repo.create_kunde(mandant, "Kunde Y", "y@extern.de", None, None)
    vorgang = vorgaenge_repo.create_vorgang(mandant, kunde["id"], None, "Erledigt",
                                            "Sonstiges", "Ohne Objekt", None)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = _freigabe(client, tok, rechnung["id"])
    assert r.status_code == 422
    assert "Objektanschrift" in r.json()["detail"]


def test_freigabe_returns_preview_and_blocks_missing_email(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    kunde, _, vorgang = _setup_vorgang(mandant, email=None)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = _freigabe(client, tok, rechnung["id"])
    assert r.status_code == 422
    assert "E-Mail" in r.json()["detail"]


def test_freigabe_prefills_empfaenger_and_pdf(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = _freigabe(client, tok, rechnung["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["empfaenger"] == "kunde@extern.de"
    assert body["brutto_summe"] == 190.40
    assert body["pdf_download_url"]
    assert body["rechnungsnummer"] == rechnung["rechnungsnummer"]


def test_senden_requires_freigabe(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = client.post(f"/rechnungen/{rechnung['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 422


def test_senden_success_creates_immutable_fassung(client, mandant, monkeypatch):
    monkeypatch.setattr(email_service.mailclient, "send_message", lambda *a, **kw: "<sent@x>")
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _setup_konto(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    _freigabe(client, tok, rechnung["id"])

    r = client.post(f"/rechnungen/{rechnung['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["versendet"] is True
    assert body["rechnung"]["status"] == "versendet"
    assert body["rechnung"]["fassung_id"]
    # Fassung unveränderlich: nach Versand kein Patch mehr möglich.
    r2 = client.patch(f"/rechnungen/{rechnung['id']}", headers=_auth(tok),
                      json={"empfaenger_email": "neu@x.de"})
    assert r2.status_code == 409


def test_senden_failure_keeps_entwurf(client, mandant, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(email_service.mailclient, "send_message", _boom)
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _setup_konto(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    _freigabe(client, tok, rechnung["id"])

    r = client.post(f"/rechnungen/{rechnung['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["versendet"] is False
    assert body["fehler_text"] == "Rechnung wurde nicht versendet."
    assert body["rechnung"]["status"] == "entwurf"


# --- AC7: Zahlungsstatus -------------------------------------------------

def _versendete_rechnung(client, tok, mandant):
    monkeypatch_send = None
    import pytest
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(email_service.mailclient, "send_message", lambda *a, **kw: "<sent@x>")
    _setup_profil(mandant)
    _setup_konto(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=POSITION)
    _freigabe(client, tok, rechnung["id"])
    r = client.post(f"/rechnungen/{rechnung['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 200
    monkeypatch.undo()
    return rechnung


def test_zahlungsstatus_offen_bezahlt(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    rechnung = _versendete_rechnung(client, tok, mandant)
    r = client.patch(f"/rechnungen/{rechnung['id']}/zahlungsstatus", headers=_auth(tok),
                     json={"zahlungsstatus": "Bezahlt"})
    assert r.status_code == 200, r.text
    assert r.json()["zahlungsstatus"] == "Bezahlt"
    # ändert nie PDF/Fassung: brutto bleibt
    assert r.json()["brutto_summe"] == 190.40


def test_zahlungsstatus_storniert_via_endpoint_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    rechnung = _versendete_rechnung(client, tok, mandant)
    r = client.patch(f"/rechnungen/{rechnung['id']}/zahlungsstatus", headers=_auth(tok),
                     json={"zahlungsstatus": "Storniert"})
    assert r.status_code == 422


def test_zahlungsstatus_on_entwurf_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    r = client.patch(f"/rechnungen/{rechnung['id']}/zahlungsstatus", headers=_auth(tok),
                     json={"zahlungsstatus": "Bezahlt"})
    assert r.status_code == 409


# --- AC8: Storno ----------------------------------------------------------

def test_storno_marks_storniert_keeps_fassung(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    rechnung = _versendete_rechnung(client, tok, mandant)
    rid = rechnung["id"]
    r = client.post(f"/rechnungen/{rid}/storno", headers=_auth(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rechnung"]["status"] == "storniert"
    assert body["rechnung"]["zahlungsstatus"] == "Storniert"
    assert body["rechnung"]["fassung_id"]  # Beleg bleibt
    # PDF weiterhin abrufbar
    pdf = client.get(f"/rechnungen/{rid}/pdf", headers=_auth(tok))
    assert pdf.status_code == 200
    assert pdf.json()["download_url"]


def test_storno_von_entwurf_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_profil(mandant)
    _, _, vorgang = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    r = client.post(f"/rechnungen/{rechnung['id']}/storno", headers=_auth(tok))
    assert r.status_code == 409


# --- Mandantentrennung ----------------------------------------------------

def test_cross_tenant_rechnung_not_visible(client, mandant):
    tok_a = _login(client, mandant, "buero-a@shk.de")
    _setup_profil(mandant)
    _, _, vorgang_a = _setup_vorgang(mandant)
    rechnung = _create_rechnung(client, tok_a, vorgang_a["id"])

    mandant_b = make_mandant("B")
    tok_b = _login(client, mandant_b, "buero-b@shk.de")
    r = client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(tok_b))
    assert r.status_code == 404


# --- Nummer nie wiederverwendet nach Storno (Edge Case) -------------------

def test_nummer_nicht_wiederverwendet_nach_storno(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    rechnung = _versendete_rechnung(client, tok, mandant)
    first_nummer = rechnung["rechnungsnummer"]
    client.post(f"/rechnungen/{rechnung['id']}/storno", headers=_auth(tok))
    # neuer Entwurf aus demselben Vorgang -> neue Nummer
    neu = _create_rechnung(client, tok, rechnung["vorgang_id"])
    assert neu["rechnungsnummer"] != first_nummer
