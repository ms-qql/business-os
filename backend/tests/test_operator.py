from app import db
from app.features.operator import service as op_service
from conftest import make_betreiber


def _op_token(client):
    make_betreiber()
    r = client.post("/operator/auth/login",
                    json={"email": "op@plattform.de", "password": "op-passwort-123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_operator_creates_mandant_with_owner(client):
    tok = _op_token(client)
    r = client.post("/admin/mandanten", headers={"Authorization": f"Bearer {tok}"},
                    json={"name": "SHK Müller", "owner_name": "Herr Müller",
                          "owner_email": "mueller@shk.de"})
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    # Eigentümer existiert als eingeladener Inhaber
    owners = db.engine.query(
        "SELECT id, email, role, status FROM nutzer WHERE mandant_id = %s", (mid,),
        mandant_id=mid)
    assert len(owners) == 1
    assert owners[0]["role"] == "Inhaber"
    assert owners[0]["status"] == "invited"


def test_business_token_rejected_on_operator_endpoint(client, mandant):
    from conftest import make_user
    make_user(mandant, "x@shk.de", "Inhaber")
    r = client.post("/auth/login", json={"email": "x@shk.de", "password": "startpasswort123"})
    tok = r.json()["access_token"]
    r2 = client.post("/admin/mandanten", headers={"Authorization": f"Bearer {tok}"},
                     json={"name": "X", "owner_name": "Y", "owner_email": "y@shk.de"})
    assert r2.status_code == 401
