from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_tenant_sees_only_own_users(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Inhaber")
    make_user(a, "a2@shk.de", "Buero")
    make_user(b, "b@shk.de", "Buero")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok_a}"})
    emails = {u["email"] for u in r.json()}
    assert emails == {"a@shk.de", "a2@shk.de"}


def test_tenant_cannot_patch_other_tenant_user(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Inhaber")
    uid_b = make_user(b, "b@shk.de", "Buero")
    r = client.patch(f"/users/{uid_b}", headers={"Authorization": f"Bearer {tok_a}"},
                     json={"status": "disabled"})
    assert r.status_code == 404  # nicht gefunden, nicht 403 — verrät nichts


def test_operator_token_rejected_on_business_endpoint(client, betreiber):
    r = client.post("/operator/auth/login",
                    json={"email": "op@plattform.de", "password": "op-passwort-123"})
    op_token = r.json()["access_token"]
    r2 = client.get("/users", headers={"Authorization": f"Bearer {op_token}"})
    assert r2.status_code == 401
