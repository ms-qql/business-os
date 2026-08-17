import uuid

from app import db
from conftest import make_mandant, make_user

PDF_BYTES = b"%PDF-1.4\n%mock pdf content for tests\n%%EOF"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make_kunde(client, tok, name="Kunde"):
    return client.post("/kunden", headers=_auth(tok), json={"name": name}).json()["id"]


def test_buero_creates_vorgang_default_status_neu(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    r = client.post("/vorgaenge", headers=_auth(tok),
                    json={"kunde_id": kid, "anliegen": "Heizung defekt"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "Neu"
    assert r.json()["kunde_name"] == "Kunde"


def test_monteur_cannot_create_vorgang(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok_buero)
    tok_monteur = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.post("/vorgaenge", headers=_auth(tok_monteur),
                    json={"kunde_id": kid, "anliegen": "Test"})
    assert r.status_code == 403


def test_status_filter(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    v1 = client.post("/vorgaenge", headers=_auth(tok),
                     json={"kunde_id": kid, "anliegen": "A"}).json()["id"]
    v2 = client.post("/vorgaenge", headers=_auth(tok),
                     json={"kunde_id": kid, "anliegen": "B"}).json()["id"]
    client.patch(f"/vorgaenge/{v2}", headers=_auth(tok), json={"status": "Erledigt"})

    r = client.get("/vorgaenge?status=Erledigt", headers=_auth(tok))
    ids = {v["id"] for v in r.json()["items"]}
    assert ids == {v2}

    r2 = client.get("/vorgaenge?status=Neu", headers=_auth(tok))
    ids2 = {v["id"] for v in r2.json()["items"]}
    assert ids2 == {v1}


def test_invalid_status_filter_rejected(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/vorgaenge?status=Erfunden", headers=_auth(tok))
    assert r.status_code == 422


def test_history_recorded_on_status_change(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    vid = client.post("/vorgaenge", headers=_auth(tok),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    client.patch(f"/vorgaenge/{vid}", headers=_auth(tok), json={"status": "Rückruf"})
    r = client.get(f"/vorgaenge/{vid}", headers=_auth(tok))
    ereignisse = [h["ereignis"] for h in r.json()["historie"]]
    assert "angelegt" in ereignisse
    assert "status_geaendert" in ereignisse


def test_assign_requires_monteur_role(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    vid = client.post("/vorgaenge", headers=_auth(tok),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    buero2_id = make_user(mandant, "buero2@shk.de", "Buero")
    r = client.post(f"/vorgaenge/{vid}/zuweisungen", headers=_auth(tok),
                    json={"nutzer_id": buero2_id})
    assert r.status_code == 422


def test_monteur_sees_only_assigned_vorgang(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok_buero)
    v_assigned = client.post("/vorgaenge", headers=_auth(tok_buero),
                             json={"kunde_id": kid, "anliegen": "Zugewiesen"}).json()["id"]
    v_other = client.post("/vorgaenge", headers=_auth(tok_buero),
                          json={"kunde_id": kid, "anliegen": "Andere"}).json()["id"]

    monteur_id = make_user(mandant, "monteur@shk.de", "Monteur")
    client.post(f"/vorgaenge/{v_assigned}/zuweisungen", headers=_auth(tok_buero),
               json={"nutzer_id": monteur_id})

    tok_monteur = client.post("/auth/login",
                              json={"email": "monteur@shk.de",
                                    "password": "startpasswort123"}).json()["access_token"]

    r = client.get("/vorgaenge", headers=_auth(tok_monteur))
    ids = {v["id"] for v in r.json()["items"]}
    assert ids == {v_assigned}

    r_ok = client.get(f"/vorgaenge/{v_assigned}", headers=_auth(tok_monteur))
    assert r_ok.status_code == 200

    r_forbidden = client.get(f"/vorgaenge/{v_other}", headers=_auth(tok_monteur))
    assert r_forbidden.status_code == 403


def test_monteur_cannot_patch_vorgang(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok_buero)
    vid = client.post("/vorgaenge", headers=_auth(tok_buero),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    monteur_id = make_user(mandant, "monteur@shk.de", "Monteur")
    client.post(f"/vorgaenge/{vid}/zuweisungen", headers=_auth(tok_buero),
               json={"nutzer_id": monteur_id})
    tok_monteur = client.post("/auth/login",
                              json={"email": "monteur@shk.de",
                                    "password": "startpasswort123"}).json()["access_token"]
    r = client.patch(f"/vorgaenge/{vid}", headers=_auth(tok_monteur), json={"status": "Erledigt"})
    assert r.status_code == 403


def test_document_upload_download_delete_roundtrip(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    vid = client.post("/vorgaenge", headers=_auth(tok),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]

    r = client.post(f"/vorgaenge/{vid}/dokumente", headers=_auth(tok),
                    files={"datei": ("bericht.pdf", PDF_BYTES, "application/pdf")})
    assert r.status_code == 201, r.text
    dok_id = r.json()["id"]
    assert r.json()["content_type"] == "application/pdf"

    r2 = client.get(f"/vorgaenge/{vid}", headers=_auth(tok))
    assert len(r2.json()["dokumente"]) == 1

    r3 = client.get(f"/vorgaenge/{vid}/dokumente/{dok_id}/download", headers=_auth(tok))
    assert r3.status_code == 200
    assert r3.json()["download_url"].startswith("memory://")

    r4 = client.delete(f"/vorgaenge/{vid}/dokumente/{dok_id}", headers=_auth(tok))
    assert r4.status_code == 204

    r5 = client.get(f"/vorgaenge/{vid}", headers=_auth(tok))
    assert len(r5.json()["dokumente"]) == 0

    r6 = client.get(f"/vorgaenge/{vid}/dokumente/{dok_id}/download", headers=_auth(tok))
    assert r6.status_code == 404


def test_document_upload_rejects_invalid_filetype(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    vid = client.post("/vorgaenge", headers=_auth(tok),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    r = client.post(f"/vorgaenge/{vid}/dokumente", headers=_auth(tok),
                    files={"datei": ("boese.exe", b"MZ\x90\x00", "application/octet-stream")})
    assert r.status_code == 422


def test_monteur_cannot_upload_dokument(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok_buero)
    vid = client.post("/vorgaenge", headers=_auth(tok_buero),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    monteur_id = make_user(mandant, "monteur@shk.de", "Monteur")
    client.post(f"/vorgaenge/{vid}/zuweisungen", headers=_auth(tok_buero),
               json={"nutzer_id": monteur_id})
    tok_monteur = client.post("/auth/login",
                              json={"email": "monteur@shk.de",
                                    "password": "startpasswort123"}).json()["access_token"]
    r = client.post(f"/vorgaenge/{vid}/dokumente", headers=_auth(tok_monteur),
                    files={"datei": ("foto.png", PNG_BYTES, "image/png")})
    assert r.status_code == 403


def test_tenant_isolation_vorgaenge(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = _make_kunde(client, tok_a, "Kunde A")
    client.post("/vorgaenge", headers=_auth(tok_a), json={"kunde_id": kid_a, "anliegen": "A"})

    tok_b = _login(client, b, "b@shk.de", "Buero")
    kid_b = _make_kunde(client, tok_b, "Kunde B")
    client.post("/vorgaenge", headers=_auth(tok_b), json={"kunde_id": kid_b, "anliegen": "B"})

    r = client.get("/vorgaenge", headers=_auth(tok_a))
    kunden_names = {v["kunde_name"] for v in r.json()["items"]}
    assert kunden_names == {"Kunde A"}


def test_pagination_limit_offset_vorgaenge(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok)
    for i in range(3):
        client.post("/vorgaenge", headers=_auth(tok), json={"kunde_id": kid, "anliegen": f"V{i}"})
    r = client.get("/vorgaenge?limit=2&offset=1", headers=_auth(tok))
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 1


def _make_anfrage(mandant_id: str, adresse: str = "Musterstr. 1") -> str:
    aid = str(uuid.uuid4())
    db.engine.command(
        "INSERT INTO anfrage (id, mandant_id, name, kontaktweg, telefon, email, adresse, "
        "anliegen, dringlichkeit, zeitfenster, quelle, uebermittlungskennung) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (aid, mandant_id, "Interessent", "E-Mail", None, "interessent@kunde.de", adresse,
         "Bad tropft", "Normal", None, "Website", str(uuid.uuid4())),
        mandant_id=mandant_id,
    )
    return aid


def test_uebernehme_anfrage_creates_kunde_objekt_vorgang(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    anfrage_id = _make_anfrage(mandant)
    r = client.post(f"/anfragen/{anfrage_id}/uebernehmen", headers=_auth(tok), json={})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kunde_id"]
    assert body["objekt_id"]
    assert body["vorgang_id"]

    r2 = client.get(f"/vorgaenge/{body['vorgang_id']}", headers=_auth(tok))
    assert r2.json()["anliegen"] == "Bad tropft"

    # Zweite Übernahme derselben Anfrage ist gesperrt.
    r3 = client.post(f"/anfragen/{anfrage_id}/uebernehmen", headers=_auth(tok), json={})
    assert r3.status_code == 422


def test_monteur_cannot_uebernehmen_anfrage(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    anfrage_id = _make_anfrage(mandant)
    tok_monteur = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.post(f"/anfragen/{anfrage_id}/uebernehmen", headers=_auth(tok_monteur), json={})
    assert r.status_code == 403
