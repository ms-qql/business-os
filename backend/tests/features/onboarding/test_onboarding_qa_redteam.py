"""QA Red-Team ergänzende Tests für PROJ-7 (Begleitetes Onboarding).
Unabhängige Verifikation zusätzlich zu den vom Backend-Worker geschriebenen
Tests: Cross-Tenant-Isolation, Auth-Bypass, Passwort-Leck, SQL-Injection.
"""
import uuid

from conftest import make_mandant, make_user

from app import db


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_cross_tenant_katalog_position_delete_404(client):
    """Mandant B darf eine Katalogposition von Mandant A nicht löschen können."""
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@t.de")
    tok_b = _login(client, b, "b@t.de")
    r = client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok_a}"},
                     json={"bezeichnung": "Geheim", "einheit": "Std",
                           "netto_einzelpreis": 100, "steuersatz": 19})
    pid = r.json()["id"]
    # B versucht As Position zu löschen -> darf nicht klappen (404, nicht 204).
    d = client.delete(f"/katalog/positionen/{pid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert d.status_code == 404, d.text
    # A's Position existiert weiterhin.
    lst = client.get("/katalog", headers={"Authorization": f"Bearer {tok_a}"}).json()
    assert any(p["id"] == pid for p in lst["positionen"])
    # B sieht As Position nicht in der eigenen Liste.
    lst_b = client.get("/katalog", headers={"Authorization": f"Bearer {tok_b}"}).json()
    assert not any(p["id"] == pid for p in lst_b["positionen"])


def test_cross_tenant_testvorgang_delete_404(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@t.de")
    tok_b = _login(client, b, "b@t.de")
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok_a}"},
               json={"hostname": "a-firma.de"})
    r = client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok_a}"})
    vid = r.json()["vorgang_id"]
    d = client.delete(f"/onboarding/testvorgang/{vid}", headers={"Authorization": f"Bearer {tok_b}"})
    assert d.status_code == 404, d.text
    # Vorgang von A besteht weiterhin.
    rows = db.engine.query("SELECT id FROM vorgang WHERE id = %s", (vid,), mandant_id=a)
    assert len(rows) == 1


def test_cross_tenant_onboarding_status_isolated(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@t.de")
    tok_b = _login(client, b, "b@t.de")
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok_a}"},
                json={"firmenname": "Geheimfirma A"})
    body_b = client.get("/onboarding", headers={"Authorization": f"Bearer {tok_b}"}).json()
    # B's Betriebsdaten-Schritt darf keine Daten von A zeigen.
    bd_b = next(s for s in body_b["schritte"] if s["id"] == "betriebsdaten")
    assert bd_b["status"] != "erledigt"


def test_jwt_tampered_signature_rejected(client):
    a = make_mandant("A")
    tok = _login(client, a, "a@t.de")
    # Signatur manipulieren: erstes Zeichen des Signatur-Teils ändern.
    # (Nur das LETZTE Zeichen zu drehen ist unzuverlässig: base64url ignoriert
    # beim Decodieren die untersten Bits des letzten Bytes, wodurch bei manchen
    # Kombinationen zufällig eine byte-identische Signatur entsteht und der
    # Test flaky wird. Ein frühes Zeichen zu ändern verändert zwingend den HMAC.)
    header, payload, sig = tok.split(".")
    tampered_sig = ("A" if sig[0] != "A" else "B") + sig[1:]
    tampered = f"{header}.{payload}.{tampered_sig}"
    r = client.get("/onboarding", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401, r.text


def test_no_token_rejected(client):
    r = client.get("/onboarding")
    assert r.status_code == 401


def test_postfach_password_never_in_response(client):
    a = make_mandant("A")
    tok = _login(client, a, "a@t.de")
    from app.features.email import schemas as email_schemas
    cfg = email_schemas.EmailKontoConfig(
        imap_host="imap.example", imap_port=993, imap_user="u", imap_passwort="supersecret",
        imap_tls=True, smtp_host="smtp.example", smtp_port=465, smtp_user="u",
        smtp_passwort="supersecret2", smtp_tls=True,
    )
    client.put("/email-konto", headers={"Authorization": f"Bearer {tok}"}, json=cfg.model_dump())
    r = client.get("/email-konto", headers={"Authorization": f"Bearer {tok}"})
    assert "supersecret" not in r.text
    assert "supersecret2" not in r.text
    r2 = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"})
    assert "supersecret" not in r2.text
    assert "supersecret2" not in r2.text
    r3 = client.post("/onboarding/postfach-test", headers={"Authorization": f"Bearer {tok}"})
    assert "supersecret" not in r3.text
    assert "supersecret2" not in r3.text


def test_sql_injection_via_bezeichnung(client):
    a = make_mandant("A")
    tok = _login(client, a, "a@t.de")
    injection = "Wartung'); DROP TABLE preisliste; --"
    r = client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok}"},
                     json={"bezeichnung": injection, "einheit": "Std",
                           "netto_einzelpreis": 10, "steuersatz": 19})
    assert r.status_code == 201, r.text
    # Tabelle muss weiterhin existieren und die Zeile lesbar sein (kein Injection-Erfolg).
    lst = client.get("/katalog", headers={"Authorization": f"Bearer {tok}"}).json()
    assert any(p["bezeichnung"] == injection for p in lst["positionen"])


def test_buero_monteur_cannot_write_katalog(client):
    a = make_mandant("A")
    tok_buero = _login(client, a, "buero@t.de", "Buero")
    tok_monteur = _login(client, a, "monteur@t.de", "Monteur")
    for tok in (tok_buero, tok_monteur):
        r = client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok}"},
                        json={"bezeichnung": "X", "einheit": "Std",
                              "netto_einzelpreis": 10, "steuersatz": 19})
        assert r.status_code == 403, r.text


def test_veroeffentlichen_requires_inhaber(client):
    a = make_mandant("A")
    tok_buero = _login(client, a, "buero@t.de", "Buero")
    r = client.post("/onboarding/veroeffentlichen", headers={"Authorization": f"Bearer {tok_buero}"})
    assert r.status_code == 403, r.text


def test_konfiguration_version_erhoeht_sich_bei_kontoaenderung(client):
    """ADR-7-3 / Edge Case: 'Postfach-Zugangsdaten werden nach erfolgreichem Test
    geändert: Schritt 5 fällt auf In Bearbeitung zurück, bis erneut getestet wurde.'
    Das setzt voraus, dass PUT /email-konto die konfiguration_version bei jeder
    erfolgreichen Änderung erhöht."""
    a = make_mandant("A")
    tok = _login(client, a, "a@t.de")
    from app.features.email import schemas as email_schemas
    cfg = email_schemas.EmailKontoConfig(
        imap_host="imap.example", imap_port=993, imap_user="u", imap_passwort="pw1",
        imap_tls=True, smtp_host="smtp.example", smtp_port=465, smtp_user="u",
        smtp_passwort="pw1", smtp_tls=True,
    )
    client.put("/email-konto", headers={"Authorization": f"Bearer {tok}"}, json=cfg.model_dump())
    v1 = db.engine.query("SELECT konfiguration_version FROM email_konto WHERE mandant_id = %s",
                         (a,), mandant_id=a)[0]["konfiguration_version"]
    # Zugangsdaten ändern.
    cfg2 = email_schemas.EmailKontoConfig(
        imap_host="imap.example", imap_port=993, imap_user="u", imap_passwort="pw2-geaendert",
        imap_tls=True, smtp_host="smtp.example", smtp_port=465, smtp_user="u",
        smtp_passwort="pw2-geaendert", smtp_tls=True,
    )
    client.put("/email-konto", headers={"Authorization": f"Bearer {tok}"}, json=cfg2.model_dump())
    v2 = db.engine.query("SELECT konfiguration_version FROM email_konto WHERE mandant_id = %s",
                         (a,), mandant_id=a)[0]["konfiguration_version"]
    assert v2 > v1, (
        "konfiguration_version wurde bei Kontoänderung nicht erhöht "
        f"(v1={v1}, v2={v2}) — verletzt ADR-7-3 und den dokumentierten Edge Case "
        "'Postfach-Zugangsdaten werden nach erfolgreichem Test geändert'."
    )
