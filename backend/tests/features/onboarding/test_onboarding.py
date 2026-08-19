from conftest import make_domain, make_mandant, make_user

import io
import uuid

from app import db


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _set_settings(client, tok, **fields):
    # Sendet nur die explizit übergebenen Felder (kein implizites Vollprofil),
    # damit Teil-Erfüllungstests (z. B. nur Firmenname) realistisch sind.
    payload = dict(fields)
    return client.patch("/website-settings", headers={"Authorization": f"Bearer {tok}"}, json=payload)


def _put_konto(client, tok, mandant, imap_ok=True, smtp_ok=True):
    """Legt ein gespeichertes Postfach an und mockt den Verbindungstest."""
    from app.features.email import schemas as email_schemas
    cfg = email_schemas.EmailKontoConfig(
        imap_host="imap.example", imap_port=993, imap_user="u", imap_passwort="pw",
        imap_tls=True, smtp_host="smtp.example", smtp_port=465, smtp_user="u",
        smtp_passwort="pw", smtp_tls=True,
    )
    client.put("/email-konto", headers={"Authorization": f"Bearer {tok}"}, json=cfg.model_dump())
    # Konfigurationsversion hochzählen, damit ein anschließender Test passt.
    db.engine.command(
        "UPDATE email_konto SET konfiguration_version = 1 WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    return imap_ok, smtp_ok


# --- Statusberechnung (ADR-7-1: berechnet, nicht abgehakt) ----------------

def test_status_alle_sieben_schritte(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    r = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    body = r.json()
    ids = [s["id"] for s in body["schritte"]]
    assert ids == ["betriebsdaten", "branding", "leistungsseiten", "domain",
                   "postfach", "preisliste", "testanfrage"]
    # Frisch: alles offen bzw. in_bearbeitung, keine erledigt.
    assert all(s["status"] != "erledigt" for s in body["schritte"])
    assert body["veröffentlicht"] is False
    # Jeder offene Schritt nennt konkret die fehlende Eingabe.
    for s in body["schritte"]:
        if s["status"] != "erledigt":
            assert s["fehlende_eingabe"], f"{s['id']} fehlt fehlende_eingabe"


def test_status_betriebsdaten_erledigt_nach_pflege(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    _set_settings(client, tok, firmenname="SHK", telefon="0123", email="f@t.de", adresse="S 1")
    # Branding fehlt noch -> branding offen, betriebsdaten erledigt.
    r = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"})
    body = r.json()
    bd = next(s for s in body["schritte"] if s["id"] == "betriebsdaten")
    assert bd["status"] == "erledigt"


def test_status_konkrete_fehlende_eingabe(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    # Nur Firmenname, Rest fehlt.
    _set_settings(client, tok, firmenname="SHK")
    r = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"})
    bd = next(s for s in r.json()["schritte"] if s["id"] == "betriebsdaten")
    assert "Telefon" in bd["fehlende_eingabe"]
    assert "E-Mail" in bd["fehlende_eingabe"]
    assert "Adresse" in bd["fehlende_eingabe"]


# --- Rollen-Zugriffskontrolle ---------------------------------------------

def test_buero_und_monteur_kein_zugriff(client, mandant):
    tok_b = _login(client, mandant, "buero@t.de", "Buero")
    tok_m = _login(client, mandant, "monteur@t.de", "Monteur")
    for tok in (tok_b, tok_m):
        r = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 403, r.text


def test_onboarding_requires_auth(client):
    r = client.get("/onboarding")
    assert r.status_code == 401


# --- Domain-Reservierung / Veröffentlichungs-Gate -------------------------

def test_domain_reserve_inaktiv(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    r = client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
                   json={"hostname": "mein-shk.de"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "inaktiv"
    # Status zeigt domain als in_bearbeitung (reserviert, nicht veröffentlicht).
    body = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"}).json()
    dom = next(s for s in body["schritte"] if s["id"] == "domain")
    assert dom["status"] == "in_bearbeitung"
    assert dom["domain_status"] == "inaktiv"


def test_veroeffentlichen_gate_alle_schritte(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    # Noch nicht alles erfüllt -> 409 mit konkreten Schritten.
    r = client.post("/onboarding/veroeffentlichen", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 409, r.text
    assert "Betriebsdaten" in r.json()["detail"]

    # Alles erfüllen.
    _set_settings(client, tok, firmenname="SHK", telefon="0123", email="f@t.de", adresse="S 1")
    # Branding
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok}"},
                  json={"marken_farbe": "#ff0000"})
    data = open("/tmp/_logo.bin", "wb")
    data.write(b"\xff\xd8\xff\xe0testjpg")  # minimaler JPEG-Magic
    data.close()
    with open("/tmp/_logo.bin", "rb") as f:
        client.post("/website-settings/logo", headers={"Authorization": f"Bearer {tok}"},
                    files={"datei": ("logo.jpg", f, "image/jpeg")})
    # Leistungsseite aktiv
    settings = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"}).json()
    slug = settings["leistungen"][0]["slug"]
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok}"},
                  json={"leistungen": [{"slug": slug, "aktiv": True,
                                       "kurzbeschreibung": "K", "inhalt": "L"}]})
    # Domain reservieren + publizieren
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
               json={"hostname": "mein-shk.de"})
    # Preisliste + Testvorgang
    client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok}"},
                 json={"bezeichnung": "Wartung", "einheit": "Std", "netto_einzelpreis": 50,
                       "steuersatz": 19})
    client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok}"})

    # Betriebspostfach: Mailbox anlegen + Verbindungstest als bestanden markieren
    # (ohne echtes SMTP/IMAP — der Durchstich nutzt eine lokale Test-Repräsentation).
    from app import db
    db.engine.command(
        "INSERT INTO email_konto (id, mandant_id, imap_host, imap_port, imap_user, "
        "imap_passwort, imap_tls, smtp_host, smtp_port, smtp_user, smtp_passwort, "
        "smtp_tls, konfiguration_version, letzter_abruf_status) VALUES (%s, %s, 'h', 993, "
        "'u', 'p', 1, 'h', 465, 'u', 'p', 1, 1, 'ok')",
        (str(uuid.uuid4()), mandant), mandant_id=mandant,
    )
    db.engine.command(
        "INSERT INTO onboarding_postfach_test (id, mandant_id, email_konto_id, "
        "konfiguration_version, imap_ok, smtp_ok, detail) VALUES (%s, %s, "
        "(SELECT id FROM email_konto WHERE mandant_id = %s LIMIT 1), 1, 1, 1, 'ok')",
        (str(uuid.uuid4()), mandant, mandant), mandant_id=mandant,
    )

    r = client.post("/onboarding/veroeffentlichen", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert r.json()["domain_status"] == "aktiv"
    # Status danach: veröffentlicht.
    body = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"}).json()
    assert body["veröffentlicht"] is True
    assert body["veröffentlicht_am"] is not None


# --- Preisliste CRUD + CSV-Import -----------------------------------------

def test_preisliste_crud(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    # Anlegen
    r = client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok}"},
                    json={"bezeichnung": "Wartung", "einheit": "Std", "netto_einzelpreis": 50,
                          "steuersatz": 19})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    # Liste
    lst = client.get("/katalog", headers={"Authorization": f"Bearer {tok}"}).json()
    assert len(lst["positionen"]) == 1
    # Duplikat -> 409
    r2 = client.post("/katalog/positionen", headers={"Authorization": f"Bearer {tok}"},
                     json={"bezeichnung": "Wartung", "einheit": "Std", "netto_einzelpreis": 60,
                           "steuersatz": 19})
    assert r2.status_code == 409, r2.text
    # Löschen
    d = client.delete(f"/katalog/positionen/{pid}", headers={"Authorization": f"Bearer {tok}"})
    assert d.status_code == 204
    lst2 = client.get("/katalog", headers={"Authorization": f"Bearer {tok}"}).json()
    assert len(lst2["positionen"]) == 0


def test_preisliste_csv_import_zeilenvalidierung(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    csv = "bezeichnung;einheit;netto_einzelpreis;steuersatz\n"
    csv += "Wartung;Std;50,00;19\n"          # Komma statt Punkt -> normalisiert
    csv += "Reparatur;Std;€ 75,50;19\n"       # Währungszeichen -> normalisiert
    csv += "Wartung;Std;10;19\n"              # Duplikat -> Fehler
    csv += "Falsch;Std;nope;19\n"            # ungültiger Preis -> Fehler
    csv += ";Std;10;19\n"                     # leere Bezeichnung -> Fehler
    files = {"datei": ("katalog.csv", csv.encode("utf-8"), "text/csv")}
    r = client.post("/katalog/import", headers={"Authorization": f"Bearer {tok}"}, files=files)
    assert r.status_code == 200, r.text
    res = r.json()
    # 2 korrekte übernommen (Wartung, Reparatur), 3 Fehler.
    assert res["anzahl_uebernommen"] == 2, res
    assert len(res["fehler"]) == 3, res
    fehler_zeilen = {f["zeile"] for f in res["fehler"]}
    assert 4 in fehler_zeilen and 5 in fehler_zeilen and 6 in fehler_zeilen
    # Kein Duplikat angelegt -> nur 2 Positionen.
    lst = client.get("/katalog", headers={"Authorization": f"Bearer {tok}"}).json()
    assert len(lst["positionen"]) == 2


# --- Testvorgang: Erzeugung, Ausschluss, kaskadierendes Löschen ----------

def test_testvorgang_erzeugung_und_ausschluss_aus_liste(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    # Reserviere Domain, damit create_testvorgang den öffentlichen Anfrageweg nimmt.
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
               json={"hostname": "mein-shk.de"})
    r = client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 201, r.text
    vid = r.json()["vorgang_id"]
    assert r.json()["ist_test"] is True

    # Der Testvorgang erscheint NICHT in der regulären Vorgangsliste.
    vorgaenge = client.get("/vorgaenge", headers={"Authorization": f"Bearer {tok}"}).json()
    ids = [v["id"] for v in vorgaenge["items"]]
    assert vid not in ids

    # Aber im Onboarding-Status als Testanfrage erledigt.
    body = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"}).json()
    ta = next(s for s in body["schritte"] if s["id"] == "testanfrage")
    assert ta["status"] == "erledigt"
    assert ta["testvorgang"]["vorgang_id"] == vid


def test_angebot_aus_testvorgang_abgelehnt(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
               json={"hostname": "mein-shk.de"})
    r = client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok}"})
    vid = r.json()["vorgang_id"]
    # Angebot aus Testvorgang -> 403.
    a = client.post(f"/vorgaenge/{vid}/angebote", headers={"Authorization": f"Bearer {tok}"},
                    json={"vorgaenger_angebot_id": None})
    assert a.status_code == 403, a.text


def test_testvorgang_kaskadierend_loeschen(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
               json={"hostname": "mein-shk.de"})
    r = client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok}"})
    vid = r.json()["vorgang_id"]
    d = client.delete(f"/onboarding/testvorgang/{vid}", headers={"Authorization": f"Bearer {tok}"})
    assert d.status_code == 204, d.text
    # Vorgang, Kunde, Objekt, Zuordnung sind weg.
    rows = db.engine.query("SELECT id FROM vorgang WHERE mandant_id = %s AND id = %s",
                           (mandant, vid), mandant_id=mandant)
    assert len(rows) == 0
    rows2 = db.engine.query("SELECT * FROM onboarding_testvorgang WHERE vorgang_id = %s",
                            (vid,), mandant_id=mandant)
    assert len(rows2) == 0
    # Onboarding zeigt Testanfrage wieder als offen.
    body = client.get("/onboarding", headers={"Authorization": f"Bearer {tok}"}).json()
    ta = next(s for s in body["schritte"] if s["id"] == "testanfrage")
    assert ta["status"] == "offen"
    assert ta["testvorgang"] is None


def test_testvorgang_loeschen_fremde_id_404(client, mandant):
    tok = _login(client, mandant, "inh@t.de")
    d = client.delete("/onboarding/testvorgang/nicht-vorhanden",
                      headers={"Authorization": f"Bearer {tok}"})
    assert d.status_code == 404, d.text
