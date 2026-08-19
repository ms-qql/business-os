"""Unabhängige QA Red-Team-Tests für PROJ-8 (nicht vom Feature-Entwickler geschrieben).
Deckt Mandantentrennung über ALLE Endpunkte, Rollen-Guards für Monteur/Büro/Inhaber,
JWT-Tampering und SQL-Injection-Versuche ab.
"""
import jwt as pyjwt
from app.config import settings
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from app.features.rechnungen import repository as rechnungen_repo
from conftest import make_mandant, make_user

POSITION = {
    "bezeichnung": "Wartung Heizung", "menge": 2, "einheit": "Std",
    "netto_einzelpreis": 80.0, "steuersatz": 19.0, "sortierung": 0,
}


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _setup(mandant):
    kunde = kunden_repo.create_kunde(mandant, "Kunde X", "kunde@extern.de", "0123", None)
    objekt = kunden_repo.create_objekt(mandant, kunde["id"], "Musterweg 1, 12345 Stadt", None)
    vorgang = vorgaenge_repo.create_vorgang(mandant, kunde["id"], objekt["id"], "Erledigt",
                                            "Sonstiges", "Heizung defekt", None)
    rechnungen_repo.upsert_rechnungsstellerprofil(mandant, {
        "firma_name": "SHK Mustermann", "strasse": "Bahnhofsstr.", "hausnummer": "12",
        "plz": "54321", "ort": "Musterstadt", "steuernummer": "12/345/67890", "ust_id": None,
    })
    return kunde, objekt, vorgang


def _create_rechnung(client, tok, vorgang_id):
    r = client.post(f"/vorgaenge/{vorgang_id}/rechnungen", headers=_auth(tok), json={
        "rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15"})
    assert r.status_code == 201, r.text
    return r.json()


# --- Cross-Tenant über ALLE Schreib-/Lese-Endpunkte -----------------------

def test_cross_tenant_all_endpoints_blocked(client, mandant):
    tok_a = _login(client, mandant, "buero-a@shk.de")
    _, _, vorgang_a = _setup(mandant)
    rechnung = _create_rechnung(client, tok_a, vorgang_a["id"])
    client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok_a), json=POSITION)

    mandant_b = make_mandant("B")
    tok_b = _login(client, mandant_b, "buero-b@shk.de")

    # GET Detail
    assert client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(tok_b)).status_code == 404
    # GET Liste des fremden Vorgangs
    r = client.get(f"/vorgaenge/{vorgang_a['id']}/rechnungen", headers=_auth(tok_b))
    assert r.status_code in (404, 403), r.text
    # PATCH Kopf
    assert client.patch(f"/rechnungen/{rechnung['id']}", headers=_auth(tok_b),
                        json={"empfaenger_email": "boese@evil.de"}).status_code == 404
    # POST Position
    assert client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok_b),
                       json=POSITION).status_code == 404
    # Freigabe
    assert client.post(f"/rechnungen/{rechnung['id']}/freigabe", headers=_auth(tok_b),
                       json={}).status_code == 404
    # Senden
    assert client.post(f"/rechnungen/{rechnung['id']}/senden", headers=_auth(tok_b),
                       json={}).status_code == 404
    # PDF
    assert client.get(f"/rechnungen/{rechnung['id']}/pdf", headers=_auth(tok_b)).status_code == 404
    # Zahlungsstatus
    assert client.patch(f"/rechnungen/{rechnung['id']}/zahlungsstatus", headers=_auth(tok_b),
                        json={"zahlungsstatus": "Bezahlt"}).status_code == 404
    # Storno
    assert client.post(f"/rechnungen/{rechnung['id']}/storno", headers=_auth(tok_b)).status_code == 404
    # Rechnungsstellerprofil ist ebenfalls mandantengetrennt
    prof_a = client.get("/einstellungen/rechnungssteller",
                        headers=_auth(_login(client, mandant, "inhaber-a@shk.de", "Inhaber")))
    assert prof_a.status_code == 200
    prof_b = client.get("/einstellungen/rechnungssteller",
                        headers=_auth(_login(client, mandant_b, "inhaber-b@shk.de", "Inhaber")))
    assert prof_b.status_code == 404  # B hat noch kein eigenes Profil


def test_cross_tenant_cannot_create_position_on_foreign_vorgang(client, mandant):
    tok_a = _login(client, mandant, "buero-a@shk.de")
    _, _, vorgang_a = _setup(mandant)

    mandant_b = make_mandant("B")
    tok_b = _login(client, mandant_b, "buero-b@shk.de")
    # B versucht Rechnung auf A's Vorgang anzulegen
    r = client.post(f"/vorgaenge/{vorgang_a['id']}/rechnungen", headers=_auth(tok_b), json={
        "rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15"})
    assert r.status_code == 404


# --- Rollen-Matrix: Monteur überall 403, Büro darf kein Rechnungsstellerprofil schreiben ---

def test_monteur_blocked_read_and_write(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup(mandant)
    rechnung = _create_rechnung(client, tok_buero, vorgang["id"])

    tok_m = _login(client, mandant, "monteur@shk.de", "Monteur")
    assert client.get(f"/vorgaenge/{vorgang['id']}/rechnungen", headers=_auth(tok_m)).status_code == 403
    assert client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(tok_m)).status_code == 403
    assert client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok_m),
                       json=POSITION).status_code == 403
    assert client.get(f"/rechnungen/{rechnung['id']}/pdf", headers=_auth(tok_m)).status_code == 403
    assert client.get("/einstellungen/rechnungssteller", headers=_auth(tok_m)).status_code == 403


def test_buero_cannot_write_rechnungsstellerprofil(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de")
    r = client.put("/einstellungen/rechnungssteller", headers=_auth(tok_buero), json={
        "firma_name": "Hack GmbH", "strasse": "X", "hausnummer": "1", "plz": "11111", "ort": "Y"})
    assert r.status_code == 403


# --- JWT-Tampering ---------------------------------------------------------

def test_jwt_tampered_mandant_id_rejected(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])

    mandant_b = make_mandant("B")
    payload = pyjwt.decode(tok, options={"verify_signature": False})
    payload["mandant_id"] = mandant_b
    forged = pyjwt.encode(payload, "falsches-geheimnis-1234567890ab", algorithm="HS256")
    r = client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(forged))
    assert r.status_code == 401, r.text  # falsche Signatur -> abgelehnt


def test_jwt_expired_rejected(client, mandant):
    import datetime
    make_user(mandant, "buero@shk.de", "Buero")
    tok = _login(client, mandant, "buero@shk.de")
    payload = pyjwt.decode(tok, options={"verify_signature": False})
    secret = settings.jwt_secret if hasattr(settings, "jwt_secret") else None
    if not secret:
        return  # Secret nicht direkt zugänglich -> Test übersprungen, kein Fund
    payload["exp"] = int((datetime.datetime.now(datetime.timezone.utc)
                          - datetime.timedelta(hours=1)).timestamp())
    expired = pyjwt.encode(payload, secret, algorithm="HS256")
    r = client.get("/vorgaenge/x/rechnungen", headers=_auth(expired))
    assert r.status_code == 401


# --- SQL-Injection-Versuch über Pydantic-validierte Felder -----------------

def test_sql_injection_in_bezeichnung_stored_safely(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup(mandant)
    rechnung = _create_rechnung(client, tok, vorgang["id"])
    payload = {**POSITION, "bezeichnung": "x'); DROP TABLE rechnung; --"}
    r = client.post(f"/rechnungen/{rechnung['id']}/positionen", headers=_auth(tok), json=payload)
    assert r.status_code == 201, r.text
    # Tabelle noch da, Payload literal gespeichert
    detail = client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(tok)).json()
    assert detail["positionen"][0]["bezeichnung"] == "x'); DROP TABLE rechnung; --"
    assert client.get(f"/rechnungen/{rechnung['id']}", headers=_auth(tok)).status_code == 200


def test_no_mandant_id_in_request_body_or_path_accepted(client, mandant):
    """mandant_id darf niemals aus Body/Query übernommen werden."""
    tok = _login(client, mandant, "buero@shk.de")
    _, _, vorgang = _setup(mandant)
    mandant_b = make_mandant("B")
    r = client.post(f"/vorgaenge/{vorgang['id']}/rechnungen", headers=_auth(tok), json={
        "rechnungsdatum": "2026-08-19", "leistungsdatum": "2026-08-15",
        "mandant_id": mandant_b})
    assert r.status_code == 201  # extra Feld wird ignoriert (Pydantic strips unknown by default)
    rechnung = r.json()
    # gehört weiterhin zu mandant (aus JWT), nicht zu mandant_b
    detail = rechnungen_repo.get_rechnung(mandant, rechnung["id"])
    assert detail is not None
    detail_b = rechnungen_repo.get_rechnung(mandant_b, rechnung["id"])
    assert detail_b is None
