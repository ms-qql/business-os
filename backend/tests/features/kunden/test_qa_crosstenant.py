"""QA red-team additions for PROJ-3 (Kunden): direct cross-tenant ID guessing
that the existing suite does not cover (existing tests only check list
filtering, not direct-ID access to another mandant's row)."""

from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_cross_tenant_cannot_read_kunde_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.get(f"/kunden/{kid_a}", headers=_auth(tok_b))
    assert r.status_code == 404, r.text


def test_cross_tenant_cannot_patch_kunde_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.patch(f"/kunden/{kid_a}", headers=_auth(tok_b), json={"name": "Hijacked"})
    assert r.status_code == 404, r.text

    r2 = client.get(f"/kunden/{kid_a}", headers=_auth(tok_a))
    assert r2.json()["name"] == "Kunde A"


def test_cross_tenant_cannot_delete_kunde_by_direct_id(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r = client.delete(f"/kunden/{kid_a}", headers=_auth(tok_b))
    assert r.status_code == 404, r.text

    r2 = client.get(f"/kunden/{kid_a}", headers=_auth(tok_a))
    assert r2.status_code == 200


def test_cross_tenant_cannot_list_or_create_objekte_for_foreign_kunde(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Buero")
    kid_a = client.post("/kunden", headers=_auth(tok_a), json={"name": "Kunde A"}).json()["id"]

    tok_b = _login(client, b, "b@shk.de", "Buero")
    r_list = client.get(f"/kunden/{kid_a}/objekte", headers=_auth(tok_b))
    assert r_list.status_code == 404, r_list.text

    r_create = client.post(f"/kunden/{kid_a}/objekte", headers=_auth(tok_b),
                           json={"adresse": "Hijack-Str. 1"})
    assert r_create.status_code == 404, r_create.text


def test_monteur_cannot_read_kunde_directly(client, mandant):
    tok_buero = _login(client, mandant, "buero@shk.de", "Buero")
    kid = client.post("/kunden", headers=_auth(tok_buero), json={"name": "Kunde"}).json()["id"]
    tok_monteur = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.get(f"/kunden/{kid}", headers=_auth(tok_monteur))
    assert r.status_code == 403, r.text


def test_sql_injection_attempt_in_search_query(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    client.post("/kunden", headers=_auth(tok), json={"name": "Normal Kunde"})
    payload = "'; DROP TABLE kunde; --"
    r = client.get("/kunden", headers=_auth(tok), params={"q": payload})
    assert r.status_code == 200
    # Table must still exist / still be queryable and still contain the row.
    r2 = client.get("/kunden", headers=_auth(tok))
    assert r2.json()["total"] == 1


def test_bug1_retest_buero_lists_users_cross_tenant_blocked(client):
    """Independent QA retest of BUG-1 fix (users/routes.py:20 require_role
    widened to Buero+Inhaber). Buero of mandant A must see only mandant A's
    users, never mandant B's — even though GET /users is now open to Buero."""
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "buero-a@shk.de", "Buero")
    make_user(a, "monteur-a@shk.de", "Monteur")
    inhaber_b_id = make_user(b, "inhaber-b@shk.de", "Inhaber")
    monteur_b_id = make_user(b, "monteur-b@shk.de", "Monteur")

    r = client.get("/users", headers=_auth(tok_a))
    assert r.status_code == 200, r.text
    ids = {u["id"] for u in r.json()}
    assert inhaber_b_id not in ids
    assert monteur_b_id not in ids
    assert {u["email"] for u in r.json()} == {"buero-a@shk.de", "monteur-a@shk.de"}


def test_bug1_retest_monteur_still_blocked_from_users(client, mandant):
    tok = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.get("/users", headers=_auth(tok))
    assert r.status_code == 403, r.text
