from app.features.users import service as users_service
from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_owner_lists_users(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    make_user(mandant, "b@shk.de", "Buero")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert any(u["email"] == "b@shk.de" for u in r.json())


def test_owner_invites_user(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.post("/users", headers={"Authorization": f"Bearer {tok}"},
                    json={"name": "Eva", "email": "eva@shk.de", "role": "Monteur"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "invited"
    assert r.json()["role"] == "Monteur"


def test_non_owner_cannot_list_users(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_last_active_owner_cannot_be_disabled(client, mandant):
    uid = make_user(mandant, "inh@shk.de", "Inhaber")
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.patch(f"/users/{uid}", headers={"Authorization": f"Bearer {tok}"},
                     json={"status": "disabled"})
    assert r.status_code == 403


def test_owner_can_disable_second_owner(client, mandant):
    make_user(mandant, "inh@shk.de", "Inhaber")
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    uid = make_user(mandant, "inh2@shk.de", "Inhaber")
    r = client.patch(f"/users/{uid}", headers={"Authorization": f"Bearer {tok}"},
                     json={"status": "disabled"})
    # zweiter Inhaber bleibt als einziger aktiver übrig -> erlaubt
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "disabled"
