from app.features.auth import service as auth_service
from app.features.auth import repository as auth_repo
from conftest import make_mandant, make_user


def test_login_success_issues_token(client, mandant):
    make_user(mandant, "max@shk.de", "Inhaber")
    r = client.post("/auth/login", json={"email": "max@shk.de", "password": "startpasswort123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "max@shk.de"
    assert me.json()["role"] == "Inhaber"


def test_login_wrong_password_generic_message(client, mandant):
    make_user(mandant, "max@shk.de", "Inhaber")
    r = client.post("/auth/login", json={"email": "max@shk.de", "password": "falsch"})
    assert r.status_code == 401
    # gleiche Meldung wie bei unbekannter E-Mail (kein Infoleak)
    r2 = client.post("/auth/login", json={"email": "unbekannt@shk.de", "password": "falsch"})
    assert r2.status_code == 401
    assert r.json()["detail"] == r2.json()["detail"]


def test_throttle_blocks_after_five_failures(client, mandant):
    make_user(mandant, "max@shk.de", "Inhaber")
    for _ in range(5):
        client.post("/auth/login", json={"email": "max@shk.de", "password": "falsch"})
    r = client.post("/auth/login", json={"email": "max@shk.de", "password": "startpasswort123"})
    assert r.status_code == 401
    assert "nicht möglich" in r.json()["detail"]


def test_invitation_accept_activates_user(client, mandant):
    uid = make_user(mandant, "neu@shk.de", "Buero", password=None, status="invited")
    token = str(__import__("uuid").uuid4())
    from datetime import datetime, timezone, timedelta
    exp = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    auth_repo.create_invitation(mandant, uid, token, 1)
    r = client.post("/auth/invitations/accept",
                    json={"token": token, "password": "neues-passwort-99"})
    assert r.status_code == 200, r.text
    # danach mit neuem Passwort anmelden
    login = client.post("/auth/login", json={"email": "neu@shk.de", "password": "neues-passwort-99"})
    assert login.status_code == 200


def test_password_reset_confirm_revokes_sessions(client, mandant):
    make_user(mandant, "max@shk.de", "Inhaber")
    login = client.post("/auth/login", json={"email": "max@shk.de", "password": "startpasswort123"})
    token = login.json()["access_token"]
    # Reset anfordern (Antwort immer gleich)
    req = client.post("/auth/password-reset", json={"email": "max@shk.de"})
    assert req.status_code == 200
    # Token aus DB holen (in Produktion per E-Mail)
    from app import db
    reset_rows = db.engine.query("SELECT token FROM passwort_resets WHERE mandant_id = %s",
                                 (mandant,), mandant_id=mandant)
    confirm = client.post("/auth/password-reset/confirm",
                          json={"token": reset_rows[0]["token"], "password": "frisch-99887766"})
    assert confirm.status_code == 200
    # alte Sitzung ungültig
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401
    # neues Passwort funktioniert
    login2 = client.post("/auth/login", json={"email": "max@shk.de", "password": "frisch-99887766"})
    assert login2.status_code == 200
