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


def test_monteur_cannot_list_users(client, mandant):
    tok = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_buero_can_list_users_but_not_invite_or_change(client, mandant):
    # PROJ-3 BUG-1: Büro braucht GET /users, um Monteure für die Vorgangs-
    # Zuweisung zu laden (POST /vorgaenge/{id}/zuweisungen ist für Büro
    # bereits offen). Schreiboperationen bleiben Inhaber-only.
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    monteur_id = make_user(mandant, "monteur@shk.de", "Monteur")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert any(u["id"] == monteur_id for u in r.json())

    r2 = client.post("/users", headers={"Authorization": f"Bearer {tok}"},
                     json={"name": "Neu", "email": "neu@shk.de", "role": "Monteur"})
    assert r2.status_code == 403

    r3 = client.patch(f"/users/{monteur_id}", headers={"Authorization": f"Bearer {tok}"},
                      json={"status": "disabled"})
    assert r3.status_code == 403


def test_buero_sees_only_own_tenant_users(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "buero-a@shk.de", "Buero")
    make_user(a, "monteur-a@shk.de", "Monteur")
    make_user(b, "monteur-b@shk.de", "Monteur")
    r = client.get("/users", headers={"Authorization": f"Bearer {tok_a}"})
    emails = {u["email"] for u in r.json()}
    assert emails == {"buero-a@shk.de", "monteur-a@shk.de"}


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
