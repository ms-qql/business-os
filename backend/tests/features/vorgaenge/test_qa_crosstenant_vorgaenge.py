"""QA red-team additions for PROJ-3: direct cross-tenant ID guessing attempts
that the existing suite does not cover (existing tests only check that list
endpoints don't leak; these check that direct-ID access to another mandant's
row is rejected, not just filtered out of a list)."""

from conftest import make_mandant, make_user

PDF_BYTES = b"%PDF-1.4\n%mock pdf content for tests\n%%EOF"


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make_kunde(client, tok, name="Kunde"):
    return client.post("/kunden", headers=_auth(tok), json={"name": name}).json()["id"]


def test_cross_tenant_cannot_read_vorgang_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]
    vid_a = client.post("/vorgaenge", headers=_auth(tok_a),
                        json={"kunde_id": kid_a, "anliegen": "Geheim"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.get(f"/vorgaenge/{vid_a}", headers=_auth(tok_b))
    assert r.status_code == 404, r.text


def test_cross_tenant_cannot_patch_vorgang_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]
    vid_a = client.post("/vorgaenge", headers=_auth(tok_a),
                        json={"kunde_id": kid_a, "anliegen": "Geheim"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.patch(f"/vorgaenge/{vid_a}", headers=_auth(tok_b), json={"status": "Erledigt"})
    assert r.status_code == 404, r.text

    # Verify mandant A's data was not modified.
    r2 = client.get(f"/vorgaenge/{vid_a}", headers=_auth(tok_a))
    assert r2.json()["status"] == "Neu"


def test_cross_tenant_cannot_download_dokument_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]
    vid_a = client.post("/vorgaenge", headers=_auth(tok_a),
                        json={"kunde_id": kid_a, "anliegen": "Geheim"}).json()["id"]
    dok_id = client.post(f"/vorgaenge/{vid_a}/dokumente", headers=_auth(tok_a),
                         files={"datei": ("bericht.pdf", PDF_BYTES, "application/pdf")}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    # Mandant B guesses/knows both the vorgang id and dokument id of mandant A.
    r = client.get(f"/vorgaenge/{vid_a}/dokumente/{dok_id}/download", headers=_auth(tok_b))
    assert r.status_code == 404, r.text


def test_cross_tenant_cannot_delete_dokument_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]
    vid_a = client.post("/vorgaenge", headers=_auth(tok_a),
                        json={"kunde_id": kid_a, "anliegen": "Geheim"}).json()["id"]
    dok_id = client.post(f"/vorgaenge/{vid_a}/dokumente", headers=_auth(tok_a),
                         files={"datei": ("bericht.pdf", PDF_BYTES, "application/pdf")}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.delete(f"/vorgaenge/{vid_a}/dokumente/{dok_id}", headers=_auth(tok_b))
    assert r.status_code == 404, r.text

    # Document must still exist for mandant A.
    r2 = client.get(f"/vorgaenge/{vid_a}", headers=_auth(tok_a))
    assert len(r2.json()["dokumente"]) == 1


def test_cross_tenant_cannot_create_vorgang_against_foreign_kunde(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    # Mandant B tries to attach a new Vorgang to mandant A's Kunde by guessing the id.
    r = client.post("/vorgaenge", headers=_auth(tok_b),
                    json={"kunde_id": kid_a, "anliegen": "Hijack"})
    assert r.status_code == 404, r.text


def test_cross_tenant_cannot_assign_foreign_vorgang(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]
    vid_a = client.post("/vorgaenge", headers=_auth(tok_a),
                        json={"kunde_id": kid_a, "anliegen": "Geheim"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    monteur_b_id = make_user(b, "monteur_b@shk.de", "Monteur")
    r = client.post(f"/vorgaenge/{vid_a}/zuweisungen", headers=_auth(tok_b),
                    json={"nutzer_id": monteur_b_id})
    assert r.status_code == 404, r.text


def test_monteur_can_download_dokument_of_assigned_vorgang(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = _make_kunde(client, tok_buero)
    vid = client.post("/vorgaenge", headers=_auth(tok_buero),
                      json={"kunde_id": kid, "anliegen": "Test"}).json()["id"]
    dok_id = client.post(f"/vorgaenge/{vid}/dokumente", headers=_auth(tok_buero),
                         files={"datei": ("bericht.pdf", PDF_BYTES, "application/pdf")}).json()["id"]

    monteur_id = make_user(mandant, "monteur@shk.de", "Monteur")
    client.post(f"/vorgaenge/{vid}/zuweisungen", headers=_auth(tok_buero),
               json={"nutzer_id": monteur_id})
    tok_monteur = client.post("/auth/login",
                              json={"email": "monteur@shk.de",
                                    "password": "startpasswort123"}).json()["access_token"]

    r = client.get(f"/vorgaenge/{vid}/dokumente/{dok_id}/download", headers=_auth(tok_monteur))
    assert r.status_code == 200, r.text
