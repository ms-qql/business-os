from datetime import datetime, timezone

from app.features.kunden.schemas import KundeCreateRead
from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_kunde_response_accepts_postgres_timestamps():
    now = datetime.now(timezone.utc)
    kunde = KundeCreateRead(id="id", name="Kunde", created_at=now, updated_at=now)
    assert kunde.created_at == now


def test_buero_creates_and_lists_kunde(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.post("/kunden", headers=_auth(tok), json={"name": "Anna Muster", "email": "anna@kunde.de"})
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Anna Muster"
    assert r.json()["moegliche_duplikate"] == []

    r2 = client.get("/kunden", headers=_auth(tok))
    assert r2.status_code == 200
    assert r2.json()["total"] == 1
    assert r2.json()["items"][0]["name"] == "Anna Muster"


def test_monteur_cannot_list_kunden(client, mandant):
    tok = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.get("/kunden", headers=_auth(tok))
    assert r.status_code == 403


def test_tenant_isolation_kunden(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"})
    tok_b = _login(client, b, "b@shk.de", "Buero")
    client.post("/kunden", headers=_auth(tok_b), json={"name": "Kunde B"})

    r = client.get("/kunden", headers=_auth(tok_a))
    names = {k["name"] for k in r.json()["items"]}
    assert names == {"Kunde A"}


def test_duplicate_email_hint_without_merge(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    client.post("/kunden", headers=_auth(tok), json={"name": "Erst", "email": "dup@kunde.de"})
    r = client.post("/kunden", headers=_auth(tok), json={"name": "Zweit", "email": "dup@kunde.de"})
    assert r.status_code == 201
    assert len(r.json()["moegliche_duplikate"]) == 1
    # keine automatische Zusammenführung: zwei getrennte Kunden bleiben bestehen
    r2 = client.get("/kunden", headers=_auth(tok))
    assert r2.json()["total"] == 2


def test_pagination_limit_offset(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    for i in range(3):
        client.post("/kunden", headers=_auth(tok), json={"name": f"Kunde {i}"})
    r = client.get("/kunden?limit=2&offset=1", headers=_auth(tok))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 1


def test_delete_kunde_blocked_with_vorgang(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = client.post("/kunden", headers=_auth(tok), json={"name": "Kunde"}).json()["id"]
    client.post("/vorgaenge", headers=_auth(tok),
               json={"kunde_id": kid, "anliegen": "Heizung defekt"})
    r = client.delete(f"/kunden/{kid}", headers=_auth(tok))
    assert r.status_code == 409


def test_delete_kunde_allowed_without_vorgang(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = client.post("/kunden", headers=_auth(tok), json={"name": "Kunde"}).json()["id"]
    r = client.delete(f"/kunden/{kid}", headers=_auth(tok))
    assert r.status_code == 204
    r2 = client.get(f"/kunden/{kid}", headers=_auth(tok))
    assert r2.status_code == 404


def test_create_and_list_objekt(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = client.post("/kunden", headers=_auth(tok), json={"name": "Kunde"}).json()["id"]
    r = client.post(f"/kunden/{kid}/objekte", headers=_auth(tok),
                    json={"adresse": "Musterstr. 1, 12345 Musterstadt"})
    assert r.status_code == 201, r.text
    r2 = client.get(f"/kunden/{kid}/objekte", headers=_auth(tok))
    assert r2.status_code == 200
    assert len(r2.json()) == 1
    assert r2.json()[0]["adresse"] == "Musterstr. 1, 12345 Musterstadt"
