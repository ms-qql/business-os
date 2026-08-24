"""QA Red-Team PROJ-14: Cross-Tenant + Auth-Bypass für Branchenpaket."""
import uuid

from conftest import make_mandant, make_user

from app import db


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_cross_tenant_paket_isolation(client):
    """Mandant B uebernimmt ein Paket -> Mandant A sieht es nicht in seinem Status."""
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@t.de")
    tok_b = _login(client, b, "b@t.de")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok_b}"}, json={"kennung": "shk"})
    assert r.status_code == 201, r.text
    status_a = client.get("/onboarding", headers={"Authorization": f"Bearer {tok_a}"}).json()
    assert status_a["branchenpaket"]["kennung"] is None
    rows = db.engine.query("SELECT branchenpaket_kennung FROM mandanten WHERE id = %s",
                           (a,), mandant_id=a)
    assert rows[0]["branchenpaket_kennung"] is None


def test_monteur_cannot_uebernehmen(client):
    a = make_mandant("A")
    tok = _login(client, a, "m@t.de", "Monteur")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"}, json={"kennung": "shk"})
    assert r.status_code == 403, r.text


def test_buero_cannot_uebernehmen(client):
    a = make_mandant("A")
    tok = _login(client, a, "b@t.de", "Buero")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"}, json={"kennung": "shk"})
    assert r.status_code == 403, r.text


def test_sql_injection_via_kennung(client, mandant):
    tok = _login(client, mandant, "i@t.de", "Inhaber")
    injection = "shk'); DROP TABLE mandanten; --"
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"}, json={"kennung": injection})
    assert r.status_code == 422, r.text
    # Tabelle noch da.
    rows = db.engine.query("SELECT COUNT(*) AS c FROM mandanten", (), mandant_id=None)
    assert int(rows[0]["c"]) >= 1


def test_client_cannot_inject_mandant_id_or_version(client, mandant):
    """kennung ist das einzig erlaubte Feld; zusaetzliche Felder duerfen keine
    Wirkung haben (mandant_id/version sind serverseitig, nie Client-Input)."""
    tok = _login(client, mandant, "i2@t.de", "Inhaber")
    other = make_mandant("Other")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "shk", "mandant_id": other, "version": 999})
    assert r.status_code == 201, r.text
    rows = db.engine.query("SELECT branchenpaket_version FROM mandanten WHERE id = %s",
                           (mandant,), mandant_id=mandant)
    assert rows[0]["branchenpaket_version"] == 1
    rows_other = db.engine.query("SELECT branchenpaket_kennung FROM mandanten WHERE id = %s",
                                 (other,), mandant_id=other)
    assert rows_other[0]["branchenpaket_kennung"] is None
