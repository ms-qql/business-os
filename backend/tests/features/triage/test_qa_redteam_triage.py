"""QA Red-Team: unabhängiger Cross-Tenant/Rollen-Angriffstest für PROJ-15 Triage.
Nicht Teil der permanenten Suite des Feature-Devs — eigener QA-Verifikationslauf."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from conftest import make_domain, make_mandant, make_user

from app import db


def _auth(client, mandant_id, email, role):
    make_user(mandant_id, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_shk(client, headers):
    r = client.post("/formulare", json={"vorlage": "shk"}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _publish(client, headers, fid, rev):
    r = client.post(f"/formulare/{fid}/veroeffentlichen", json={"draft_revision": rev},
                    headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_cross_tenant_triage_einstellung_isoliert(client):
    """Mandant A's Triage-Konfiguration darf für Mandant B unsichtbar/unschreibbar sein."""
    m_a = make_mandant()
    m_b = make_mandant()
    make_domain(m_a, "a-tenant.de")
    h_a = _auth(client, m_a, "inhaber@a.de", "Inhaber")
    h_b = _auth(client, m_b, "inhaber@b.de", "Inhaber")

    f = _create_shk(client, h_a)
    fid = f["id"]
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "S", "draft_revision": f["draft_revision"]}, headers=h_a)
    rev = r.json()["draft_revision"]
    sid = r.json()["schritte"][-1]["id"]
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder", json={"typ": "dropdown", "draft_revision": rev}, headers=h_a)
    rev = r.json()["draft_revision"]
    leistung_f = r.json()["schritte"][-1]["felder"][-1]["id"]
    r = client.patch(f"/formulare/{fid}/schritte/{sid}/felder/{leistung_f}", json={
        "label": "Leistung", "pflichtfeld": True, "optional_in_einfach": False, "uebernahme": None,
        "optionen": [{"label": "Heizung", "wert": "heizung"}], "draft_revision": rev}, headers=h_a)
    rev = r.json()["draft_revision"]
    _publish(client, h_a, fid, rev)

    # A konfiguriert Triage.
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"}]}, headers=h_a)
    assert r.status_code == 200, r.text

    # B sieht As Formular nicht (fremde formular_id -> 404, kein Cross-Tenant-Leak).
    r = client.get(f"/formulare/{fid}/veroeffentlichte-version", headers=h_b)
    assert r.status_code == 404, f"LEAK: Mandant B kann Formular von A lesen: {r.status_code}"

    # B versucht, mit As formular_id/feld_id eigene Triage-Einstellung zu setzen -> 404, nicht 200.
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"}]}, headers=h_b)
    assert r.status_code == 404, f"LEAK: Mandant B kann gegen As Formular schreiben: {r.status_code}"

    # B's eigene (leere) Einstellung bleibt unverändert / getrennt von A.
    r = client.get("/triage/einstellung", headers=h_b)
    assert r.status_code == 200
    assert r.json()["leistungs_formular_id"] is None, "LEAK: B sieht As Triage-Konfiguration"

    # A's Einstellung bleibt unverändert unter A.
    r = client.get("/triage/einstellung", headers=h_a)
    assert r.json()["leistungs_formular_id"] == fid


def test_cross_tenant_vorgang_triage_kein_leak(client):
    """Mandant B darf keinen berechneten Triage-Wert für As Vorgang bekommen (404 statt Leak)."""
    m_a = make_mandant()
    m_b = make_mandant()
    h_a = _auth(client, m_a, "inhaber2@a.de", "Inhaber")
    h_b = _auth(client, m_b, "inhaber2@b.de", "Inhaber")

    kunde_r = client.post("/kunden", json={"name": "K", "email": "k@x.de"}, headers=h_a)
    assert kunde_r.status_code == 201
    kid = kunde_r.json()["id"]
    v_r = client.post("/vorgaenge", json={"kunde_id": kid, "anliegen": "X"}, headers=h_a)
    assert v_r.status_code == 201
    vid = v_r.json()["id"]

    r = client.get(f"/vorgaenge/{vid}", headers=h_b)
    assert r.status_code == 404, f"LEAK: Mandant B kann As Vorgang (inkl. Triage) lesen: {r.status_code}"


def test_jwt_ohne_rolle_manipulation_kein_bypass(client):
    """Modifizierter JWT-Payload (role=Inhaber statt Monteur) mit falscher Signatur -> 401."""
    m = make_mandant()
    make_user(m, "mont@t.de", "Monteur")
    r = client.post("/auth/login", json={"email": "mont@t.de", "password": "startpasswort123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Payload-Segment manipulieren (role hochstufen), Signatur bleibt alt -> muss scheitern.
    import base64
    import json as _json
    header_b64, payload_b64, sig_b64 = token.split(".")
    payload = _json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
    payload["role"] = "Inhaber"
    new_payload_b64 = base64.urlsafe_b64encode(_json.dumps(payload).encode()).rstrip(b"=").decode()
    tampered = f"{header_b64}.{new_payload_b64}.{sig_b64}"

    r = client.get("/triage/einstellung", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401, f"AUTH BYPASS: manipuliertes JWT akzeptiert: {r.status_code}"


def test_sql_injection_leistungswert(client):
    """SQL-Injection-Versuch über 'wert'-Feld (Pydantic erlaubt beliebigen String)."""
    m = make_mandant()
    h = _auth(client, m, "inhaber3@t.de", "Inhaber")
    f = _create_shk(client, h)
    fid = f["id"]
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "S", "draft_revision": f["draft_revision"]}, headers=h)
    rev = r.json()["draft_revision"]
    sid = r.json()["schritte"][-1]["id"]
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder", json={"typ": "dropdown", "draft_revision": rev}, headers=h)
    rev = r.json()["draft_revision"]
    leistung_f = r.json()["schritte"][-1]["felder"][-1]["id"]
    payload_injection = "x'; DROP TABLE triage_leistungswert; --"
    r = client.patch(f"/formulare/{fid}/schritte/{sid}/felder/{leistung_f}", json={
        "label": "Leistung", "pflichtfeld": True, "optional_in_einfach": False, "uebernahme": None,
        "optionen": [{"label": "X", "wert": payload_injection}], "draft_revision": rev}, headers=h)
    rev = r.json()["draft_revision"]
    _publish(client, h, fid, rev)

    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": payload_injection, "klassifikation": "passend"}]}, headers=h)
    assert r.status_code == 200, r.text
    # Tabelle muss weiterhin existieren und den Wert unverändert (parametrisiert) enthalten.
    rows = db.engine.query(
        "SELECT wert FROM triage_leistungswert WHERE mandant_id = %s", (m,), mandant_id=m)
    assert any(row["wert"] == payload_injection for row in rows), \
        "Injection-String wurde nicht als Literal gespeichert -> möglicher SQLi-Pfad"
