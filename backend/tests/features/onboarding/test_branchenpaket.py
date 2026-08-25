"""Tests für PROJ-14: Branchenpaket-Übernahme + Website-Seed-Korrektur."""
import uuid

from conftest import make_domain, make_mandant, make_user

from app import db


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


# --- Website-Seed-Korrektur (globaler SHK-Seed entfernt) -----------------

def test_website_settings_seeds_no_leistungen(client, mandant):
    """ADR-14-2: GET /website-settings darf keine globalen Leistungsseiten
    mehr anlegen — ein leerer Betrieb hat keine Leistungen, bis das Paket
    übernommen wurde."""
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    assert r.json()["leistungen"] == []
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM leistungsseite WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(rows[0]["c"]) == 0


def test_public_site_no_global_seed(client):
    """Ein Entrümpelungs-Betrieb darf über den öffentlichen Pfad keine
    SHK-Leistungsseiten erben."""
    mandant = make_mandant()
    make_user(mandant, "i@e.de", "Inhaber")
    make_domain(mandant, "e-firma.de")
    r = client.get("/public/site", headers={"Host": "e-firma.de"})
    assert r.status_code == 200, r.text
    assert r.json()["leistungen"] == []
    rows = db.engine.query(
        "SELECT COUNT(*) AS c FROM leistungsseite WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(rows[0]["c"]) == 0


# --- Katalog-Optionen ---------------------------------------------------

def test_liste_branchenpakete(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/onboarding/branchenpakete",
                   headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    opts = {o["kennung"]: o for o in r.json()}
    assert set(opts) == {"shk", "entruempelung"}
    assert "SHK" in opts["shk"]["name"]
    assert "Entrümpelung" in opts["entruempelung"]["name"]
    for o in opts.values():
        assert "version" not in o
        assert "leistungen" not in o


def test_buero_cannot_list_branchenpakete(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/onboarding/branchenpakete",
                   headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403, r.text


# --- Atomare Übernahme ---------------------------------------------------

def test_uebernehmen_shk_atomar(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "shk"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kennung"] == "shk"
    assert body["name"] == "SHK"
    assert body["version"] == 1
    assert body["uebernommen_am"]

    leist = db.engine.query(
        "SELECT COUNT(*) AS c FROM leistungsseite WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(leist[0]["c"]) == 5
    gewerke = db.engine.query(
        "SELECT COUNT(*) AS c FROM gewerk WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(gewerke[0]["c"]) == 3
    kosten = db.engine.query(
        "SELECT COUNT(*) AS c FROM gewerk_kostenzeile WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(kosten[0]["c"]) == 3
    form = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(form[0]["c"]) == 1
    fs = db.engine.query(
        "SELECT COUNT(*) AS c FROM formular_schritt WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(fs[0]["c"]) == 1

    status = client.get("/onboarding",
                        headers={"Authorization": f"Bearer {tok}"}).json()
    bp = next(s for s in status["schritte"] if s["id"] == "branchenpaket")
    assert bp["status"] == "erledigt"
    assert status["paket_info"]["kennung"] == "shk"
    assert status["paket_info"]["name"] == "SHK"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert me["paket_kennung"] == "shk"
    assert me["paket_name"] == "SHK"


def test_uebernehmen_entruempelung(client, mandant):
    tok = _login(client, mandant, "inh@e.de", "Inhaber")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "entruempelung"})
    assert r.status_code == 201, r.text
    leist = db.engine.query(
        "SELECT slug FROM leistungsseite WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    slugs = {row["slug"] for row in leist}
    assert {"flaeche", "entsorgung", "transport", "wertanrechnung"} <= slugs


def test_uebernehmen_invalid_kennung_422(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "unbekannt"})
    assert r.status_code == 422, r.text
    leist = db.engine.query(
        "SELECT COUNT(*) AS c FROM leistungsseite WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert int(leist[0]["c"]) == 0


def test_uebernehmen_idempotent_409(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r1 = client.post("/onboarding/branchenpaket-uebernehmen",
                     headers={"Authorization": f"Bearer {tok}"},
                     json={"kennung": "shk"})
    assert r1.status_code == 201, r1.text
    r2 = client.post("/onboarding/branchenpaket-uebernehmen",
                     headers={"Authorization": f"Bearer {tok}"},
                     json={"kennung": "entruempelung"})
    assert r2.status_code == 409, r2.text
    rows = db.engine.query(
        "SELECT branchenpaket_kennung FROM mandanten WHERE id = %s",
        (mandant,), mandant_id=mandant,
    )
    assert rows[0]["branchenpaket_kennung"] == "shk"


def test_uebernehmen_rejects_existing_content_409(client, mandant):
    """Invariante: existiert bereits ein Zielinhalt, wird keine Übernahme
    gestartet (Edge Case 'Existieren im Zielmandanten bereits Inhalte')."""
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    db.engine.command(
        "INSERT INTO leistungsseite (id, mandant_id, slug, titel) VALUES (%s, %s, 'x', 'X')",
        (str(uuid.uuid4()), mandant), mandant_id=mandant,
    )
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "shk"})
    assert r.status_code == 409, r.text


def test_veroeffentlichen_gate_requires_branchenpaket(client, mandant):
    """Ohne übernommenes Paket blockiert die Veröffentlichung (Pflicht-Gate)."""
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.post("/onboarding/veroeffentlichen",
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 409, r.text
    assert "Branchenpaket" in r.json()["detail"]


def test_veroeffentlichen_with_package(client, mandant):
    """Mit übernommenem Paket + übrigen Pflichtschritten gelingt die
    Veröffentlichung (Integration des neuen Pflicht-Gates)."""
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    # 1) Paket übernehmen (ganz am Anfang — vor anderen Inhalten).
    r = client.post("/onboarding/branchenpaket-uebernehmen",
                    headers={"Authorization": f"Bearer {tok}"},
                    json={"kennung": "shk"})
    assert r.status_code == 201, r.text
    # 2) Betriebsdaten + Branding.
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok}"},
                  json={"firmenname": "SHK", "telefon": "0123",
                        "email": "f@t.de", "adresse": "S 1",
                        "marken_farbe": "#ff0000"})
    data = open("/tmp/_logo.bin", "wb")
    data.write(b"\xff\xd8\xff\xe0testjpg")
    data.close()
    with open("/tmp/_logo.bin", "rb") as f:
        client.post("/website-settings/logo", headers={"Authorization": f"Bearer {tok}"},
                    files={"datei": ("logo.jpg", f, "image/jpeg")})
    # 3) Leistung aktiv (aus dem Paket geseedet).
    settings = client.get("/website-settings",
                          headers={"Authorization": f"Bearer {tok}"}).json()
    slug = settings["leistungen"][0]["slug"]
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok}"},
                  json={"leistungen": [{"slug": slug, "aktiv": True,
                                       "kurzbeschreibung": "K", "inhalt": "L"}]})
    # 4) Domain + Katalog (Gewerke) + Testvorgang + Postfach.
    client.put("/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
               json={"hostname": "mein-shk.de"})
    client.post("/gewerke", headers={"Authorization": f"Bearer {tok}"},
                json={"bezeichnung": "Wartung", "einheit": "Std",
                      "steuersatz": 19,
                      "kostenzeilen": [{"kostenart": "lohn", "menge": 1.0,
                                        "einheit": "Std", "ek_einzelpreis": 50.0,
                                        "zuschlag_prozent": 0.0}]})
    client.post("/onboarding/testvorgang", headers={"Authorization": f"Bearer {tok}"})
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
    r2 = client.post("/onboarding/veroeffentlichen",
                     headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["ok"] is True
    body = client.get("/onboarding",
                      headers={"Authorization": f"Bearer {tok}"}).json()
    assert body["veroeffentlicht"] is True
