from datetime import datetime, timezone
from urllib.parse import quote

from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from conftest import make_mandant, make_user

# Zeitfenster für die Kalenderabfrage (UTC-ISO). Für die GET-Query werden die
# Werte prozent-kodiert übergeben (so wie es ein echter HTTP-Client tut — ein
# unkodiertes '+' im Query-String würde sonst zu einem Leerzeichen).
VON = "2026-08-17T22:00:00+00:00"   # Mo 00:00 Berlin
BIS = "2026-08-23T22:00:00+00:00"   # So 24:00 Berlin


def _q(s: str) -> str:
    return quote(s, safe="")


def _iso(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc).isoformat()


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _setup_vorgang(mandant_id, anliegen="Heizung defekt", status="Neu"):
    kunde = kunden_repo.create_kunde(mandant_id, "Kunde X", "kunde@extern.de", None, None)
    vorgang = vorgaenge_repo.create_vorgang(
        mandant_id, kunde["id"], None, status, "Sonstiges", anliegen, None)
    return kunde, vorgang


def _setup_monteur(mandant_id, email="monteur@shk.de", status="active"):
    return make_user(mandant_id, email, "Monteur", status=status)


def _create_termin(client, tok, vorgang_id, monteure, beginn, ende, adresse=None):
    payload = {
        "vorgang_id": vorgang_id, "beginn": beginn, "ende": ende,
        "adresse": adresse, "monteure": monteure,
    }
    return client.post("/termine", headers=_auth(tok), json=payload)


# --- AC-1: Anlage ---------------------------------------------------------


def test_create_termin_sets_vorgang_status_and_history(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant, status="Neu")
    m = _setup_monteur(mandant)
    r = _create_termin(client, tok, vorgang["id"], [m], _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["termin"]["id"]
    assert body["termin"]["anliegen"] == "Heizung defekt"
    assert body["termin"]["monteure"][0]["nutzer_id"] == m
    assert body["konflikt"] is False
    # Vorgang auf "Termin geplant"
    updated = vorgaenge_repo.get_vorgang(mandant, vorgang["id"])
    assert updated["status"] == "Termin geplant"


def test_create_termin_ohne_monteur_erlaubt(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    r = _create_termin(client, tok, vorgang["id"], [], _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    assert r.status_code == 201, r.text
    assert r.json()["termin"]["monteure"] == []


# --- AC-3: Vorgangsbezug (422 bei fremdem/ungültigem Vorgang) ------------


def test_create_termin_fremder_vorgang_422(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    mandant_b = make_mandant("B")
    _, vorgang_b = _setup_vorgang(mandant_b)
    r = _create_termin(client, tok, vorgang_b["id"], [],
                       _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    assert r.status_code == 422, r.text


def test_create_termin_unknown_vorgang_422(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    r = _create_termin(client, tok, "00000000-0000-0000-0000-000000000000", [],
                       _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    assert r.status_code == 422, r.text


# --- AC-7: Validierung ende > beginn -------------------------------------


def test_create_termin_ende_vor_beginn_422(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    r = _create_termin(client, tok, vorgang["id"], [],
                       _iso(2026, 8, 18, 11), _iso(2026, 8, 18, 9))
    assert r.status_code == 422, r.text


def test_create_termin_gleiche_zeit_422(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    r = _create_termin(client, tok, vorgang["id"], [],
                       _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 9))
    assert r.status_code == 422, r.text


# --- AC-4: Konfliktwarnung nicht-blockierend -----------------------------


def test_konflikt_erkannt_aber_gespeichert(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    # Erster Termin
    r1 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    assert r1.status_code == 201, r1.text
    # Überlappender zweiter Termin (9:30–10:30) für denselben Monteur
    r2 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 18, 9, 30), _iso(2026, 8, 18, 10, 30))
    assert r2.status_code == 201, r2.text  # trotzdem gespeichert
    body = r2.json()
    assert body["konflikt"] is True
    assert m in body["konflikt_monteure"]


def test_kein_konflikt_bei_verschiedenen_monteuren(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m1 = _setup_monteur(mandant, "m1@shk.de")
    m2 = _setup_monteur(mandant, "m2@shk.de")
    _create_termin(client, tok, vorgang["id"], [m1],
                   _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    r2 = _create_termin(client, tok, vorgang["id"], [m2],
                        _iso(2026, 8, 18, 9, 30), _iso(2026, 8, 18, 10, 30))
    assert r2.json()["konflikt"] is False


def test_abgesagter_termin_erzeugt_keinen_konflikt(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    r1 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    tid1 = r1.json()["termin"]["id"]
    client.post(f"/termine/{tid1}/absagen", headers=_auth(tok))
    r2 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 18, 9, 30), _iso(2026, 8, 18, 10, 30))
    assert r2.json()["konflikt"] is False


# --- AC-5: Monteursicht (nur eigene, Schreibzugriff 403) -----------------


def test_monteur_sieht_nur_eigene_termine(client, mandant):
    buero = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m1 = _setup_monteur(mandant, "m1@shk.de")
    m2 = _setup_monteur(mandant, "m2@shk.de")
    _create_termin(client, buero, vorgang["id"], [m1],
                   _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    _create_termin(client, buero, vorgang["id"], [m2],
                   _iso(2026, 8, 19, 9), _iso(2026, 8, 19, 11))
    tok_m1 = _login(client, mandant, "m1@shk.de", "Monteur")
    r = client.get(f"/termine?von={_q(VON)}&bis={_q(BIS)}", headers=_auth(tok_m1))
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["monteure"][0]["nutzer_id"] == m1


def test_monteur_forbidden_write(client, mandant):
    buero = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    created = _create_termin(client, buero, vorgang["id"], [m],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    tok_m = _login(client, mandant, "m@shk.de", "Monteur")
    r = client.post("/termine", headers=_auth(tok_m), json={
        "vorgang_id": vorgang["id"], "beginn": _iso(2026, 8, 20, 9),
        "ende": _iso(2026, 8, 20, 11), "monteure": [m]})
    assert r.status_code == 403
    # Auch PATCH/DELETE blockiert
    assert client.patch(f"/termine/{tid}", headers=_auth(tok_m),
                        json={"notiz": "x"}).status_code == 403
    assert client.post(f"/termine/{tid}/absagen", headers=_auth(tok_m)).status_code == 403


def test_monteur_detail_fremder_termin_403(client, mandant):
    buero = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m1 = _setup_monteur(mandant, "m1@shk.de")
    m2 = _setup_monteur(mandant, "m2@shk.de")
    created = _create_termin(client, buero, vorgang["id"], [m1],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    tok_m2 = _login(client, mandant, "m2@shk.de", "Monteur")
    r = client.get(f"/termine/{tid}", headers=_auth(tok_m2))
    assert r.status_code == 403


def test_monteur_detail_eigener_termin_hat_kontakt(client, mandant):
    buero = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m1 = _setup_monteur(mandant, "m1@shk.de")
    created = _create_termin(client, buero, vorgang["id"], [m1],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    tok_m1 = _login(client, mandant, "m1@shk.de", "Monteur")
    r = client.get(f"/termine/{tid}", headers=_auth(tok_m1))
    assert r.status_code == 200, r.text
    detail = r.json()
    assert detail["kontakt"]["name"] == "Kunde X"
    assert detail["kontakt"]["email"] == "kunde@extern.de"
    assert detail["ist_eigen"] is True


# --- AC-6: Statuswechsel bei Absage --------------------------------------


def test_absage_letzter_offener_termin_setzt_status_zurueck(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant, status="Neu")
    m = _setup_monteur(mandant)
    created = _create_termin(client, tok, vorgang["id"], [m],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    assert vorgaenge_repo.get_vorgang(mandant, vorgang["id"])["status"] == "Termin geplant"
    r = client.post(f"/termine/{tid}/absagen", headers=_auth(tok))
    assert r.status_code == 200, r.text
    assert r.json()["termin"]["abgesagt_at"]
    # Status zurück auf "Neu" + Historie
    updated = vorgaenge_repo.get_vorgang(mandant, vorgang["id"])
    assert updated["status"] == "Neu"
    hist = vorgaenge_repo.list_historie(mandant, vorgang["id"])
    events = [h["ereignis"] for h in hist]
    assert "termin_status_zurueckgesetzt" in events


def test_absage_nicht_letzter_termin_behaelt_status(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant, status="Neu")
    m = _setup_monteur(mandant)
    t1 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()["termin"]["id"]
    t2 = _create_termin(client, tok, vorgang["id"], [m],
                        _iso(2026, 8, 19, 9), _iso(2026, 8, 19, 11)).json()["termin"]["id"]
    client.post(f"/termine/{t1}/absagen", headers=_auth(tok))
    # t2 bleibt offen -> Status "Termin geplant"
    assert vorgaenge_repo.get_vorgang(mandant, vorgang["id"])["status"] == "Termin geplant"
    client.post(f"/termine/{t2}/absagen", headers=_auth(tok))
    assert vorgaenge_repo.get_vorgang(mandant, vorgang["id"])["status"] == "Neu"


# --- Zuweisungen ----------------------------------------------------------


def test_zuweisung_hinzufuegen_entziehen(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    created = _create_termin(client, tok, vorgang["id"], [],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    r = client.post(f"/termine/{tid}/zuweisungen", headers=_auth(tok),
                    json={"nutzer_id": m})
    assert r.status_code == 201, r.text
    assert r.json()["termin"]["monteure"][0]["nutzer_id"] == m
    r2 = client.delete(f"/termine/{tid}/zuweisungen/{m}", headers=_auth(tok))
    assert r2.status_code == 200, r2.text
    assert r2.json()["termin"]["monteure"] == []


def test_zuweisung_nicht_monteur_422(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    # Inhaber anlegen; dessen echte Nutzer-ID als "nicht-Monteur"-Zuweisung nutzen.
    inhaber_id = make_user(mandant, "inhaber@shk.de", "Inhaber")
    created = _create_termin(client, tok, vorgang["id"], [],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]
    r = client.post(f"/termine/{tid}/zuweisungen", headers=_auth(tok),
                    json={"nutzer_id": inhaber_id})
    assert r.status_code == 422, r.text


# --- Nested-Route /vorgaenge/{id}/termine --------------------------------


def test_nested_vorgang_termine(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    _create_termin(client, tok, vorgang["id"], [m],
                   _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11))
    r = client.get(f"/vorgaenge/{vorgang['id']}/termine", headers=_auth(tok))
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
    r2 = client.post(f"/vorgaenge/{vorgang['id']}/termine", headers=_auth(tok), json={
        "beginn": _iso(2026, 8, 18, 13), "ende": _iso(2026, 8, 18, 15),
        "monteure": [m]})
    assert r2.status_code == 201, r2.text


# --- GET /nutzer/monteure ------------------------------------------------


def test_list_monteure_endpoint(client, mandant):
    _login(client, mandant, "buero@shk.de")
    _setup_monteur(mandant, "aktiv@shk.de", "active")
    _setup_monteur(mandant, "inaktiv@shk.de", "disabled")
    make_user(mandant, "inhaber@shk.de", "Inhaber")
    r = client.get("/nutzer/monteure", headers=_auth(_login(client, mandant, "b2@shk.de")))
    assert r.status_code == 200, r.text
    optionen = r.json()
    emails = {o["name"] for o in optionen}
    assert "aktiv@shk.de" not in emails  # Name, nicht E-Mail; prüfe aktiv-Flag
    assert all(o["aktiv"] is True for o in optionen)
    assert len(optionen) == 1  # nur aktiver Monteur


# --- Tenant-Isolation (AC-5 serverseitig) --------------------------------


def test_cross_tenant_termin_nicht_sichtbar(client, mandant):
    tok_a = _login(client, mandant, "buero-a@shk.de")
    _, vorgang_a = _setup_vorgang(mandant)
    m = _setup_monteur(mandant)
    created = _create_termin(client, tok_a, vorgang_a["id"], [m],
                             _iso(2026, 8, 18, 9), _iso(2026, 8, 18, 11)).json()
    tid = created["termin"]["id"]

    mandant_b = make_mandant("B")
    tok_b = _login(client, mandant_b, "buero-b@shk.de")
    # B darf A's Termin weder lesen noch auflisten
    assert client.get(f"/termine/{tid}", headers=_auth(tok_b)).status_code == 404
    liste = client.get(f"/termine?von={_q(VON)}&bis={_q(BIS)}", headers=_auth(tok_b)).json()
    assert liste["total"] == 0


# --- Status=alle (Vorgangsauswahl im Dialog) -----------------------------


def test_list_vorgaenge_status_alle(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _setup_vorgang(mandant, status="Neu")
    _setup_vorgang(mandant, status="Erledigt")
    r = client.get("/vorgaenge?limit=100&status=alle", headers=_auth(tok))
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 2
