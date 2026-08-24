from conftest import make_domain, make_mandant, make_user


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_app_registers_formular_routes(client):
    # Stellt sicher, dass die Router sauber importiert/registriert wurden.
    r = client.get("/health")
    assert r.status_code == 200


def test_builder_flow_and_publish(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")

    # Anlegen (leer)
    r = client.post("/formulare", headers=_auth(tok), json={"vorlage": "leer"})
    assert r.status_code == 200, r.text
    body = r.json()
    fid = body["id"]
    assert body["komplexitaet"] == "einfach"
    rev = body["draft_revision"]

    # Schritt hinzufügen
    r = client.post(f"/formulare/{fid}/schritte", headers=_auth(tok),
                    json={"draft_revision": rev})
    assert r.status_code == 200, r.text
    rev = r.json()["draft_revision"]
    schritt_id = r.json()["schritte"][0]["id"]

    # Textfeld (pflicht) + Consent (pflicht) hinzufügen
    r = client.post(f"/formulare/{fid}/schritte/{schritt_id}/felder", headers=_auth(tok),
                    json={"type": "text", "label": "Ihr Name", "pflichtfeld": True,
                          "uebernahme": "kontaktname", "draft_revision": rev})
    assert r.status_code == 200, r.text
    rev = r.json()["draft_revision"]
    name_feld = r.json()["schritte"][0]["felder"][0]["id"]

    r = client.post(f"/formulare/{fid}/schritte/{schritt_id}/felder", headers=_auth(tok),
                    json={"type": "consent", "label": "Datenschutz", "pflichtfeld": True,
                          "draft_revision": rev})
    assert r.status_code == 200, r.text
    rev = r.json()["draft_revision"]

    # Veröffentlichen
    r = client.post(f"/formulare/{fid}/veroeffentlichen", headers=_auth(tok),
                    json={"draft_revision": rev})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["veroeffentlicht"] is True
    public_id = body["public_id"]
    assert public_id

    # Einbindung (benötigt Domain)
    make_domain(mandant, "form.test")
    r = client.get(f"/formulare/{fid}/einbindung", headers=_auth(tok))
    assert r.status_code == 200, r.text
    einb = r.json()
    assert einb["direktlink"].endswith(f"/formulare/{public_id}")
    assert "iframe" in einb["iframe"]

    return fid, public_id, name_feld


def test_public_submit_atomic_takeover(client, mandant):
    fid, public_id, name_feld = test_builder_flow_and_publish(client, mandant)
    make_domain(mandant, "submit.test")

    # Öffentlicher Snapshot
    r = client.get(f"/public/formulare/{public_id}", headers={"Host": "submit.test"})
    assert r.status_code == 200, r.text
    snap = r.json()
    assert snap["modus"] == "einfach"
    assert snap["schritte"]

    # Einsendung (kein Token, Host löst Mandant auf)
    payload = {
        "uebermittlungskennung": "test-kennung-1",
        "client_start": "2000-01-01T00:00:00.000Z",
        "honeypot": "",
        "werte": [
            {"feld_id": name_feld, "wert": "Max Mustermann"},
            {"feld_id": next(f["id"] for s in snap["schritte"] for f in s["felder"]
                             if f["typ"] == "consent"), "wert": "ja"},
        ],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    headers={"Host": "submit.test"}, json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "erfolgreich"

    # Idempotenz: zweite Einsendung mit selber Kennung bleibt erfolgreich
    r2 = client.post(f"/public/formulare/{public_id}/einsendungen",
                     headers={"Host": "submit.test"}, json=payload)
    assert r2.status_code == 201
    assert r2.json()["status"] == "erfolgreich"

    # Übernahme sichtbar: Kunde (entwurf) + Vorgang + Anfrage
    from app import db
    kunden = db.engine.query(
        "SELECT id, name, status FROM kunde WHERE mandant_id = %s AND email IS NULL",
        (mandant,), mandant_id=mandant)
    assert any(k["name"] == "Max Mustermann" for k in kunden)
    anfragen = db.engine.query(
        "SELECT id, name, formular_einsendung_id FROM anfrage WHERE mandant_id = %s",
        (mandant,), mandant_id=mandant)
    assert anfragen, "Anfrage wurde nicht angelegt"
    assert anfragen[0]["name"] == "Max Mustermann"


def test_public_submit_spam(client, mandant):
    fid, public_id, name_feld = test_builder_flow_and_publish(client, mandant)
    make_domain(mandant, "spam.test")
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "spam.test"}).json()
    consent_feld = next(f["id"] for s in snap["schritte"] for f in s["felder"]
                        if f["typ"] == "consent")
    payload = {
        "uebermittlungskennung": "spam-kennung-1",
        "client_start": "2000-01-01T00:00:00.000Z",
        "honeypot": "bot",  # gefüllt -> Spam
        "werte": [
            {"feld_id": name_feld, "wert": "Spammer"},
            {"feld_id": consent_feld, "wert": "ja"},
        ],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    headers={"Host": "spam.test"}, json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "spam"

    from app import db
    spam = db.engine.query(
        "SELECT spam_status FROM formular_einsendung WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant, "spam-kennung-1"), mandant_id=mandant)
    assert spam and spam[0]["spam_status"] == "spam"


def test_buero_can_manage_formulare(client, mandant):
    # BUG-1: Büro-Rolle muss Formulare verwalten dürfen (require_role Inhaber,Buero).
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.post("/formulare", headers=_auth(tok), json={"vorlage": "leer"})
    assert r.status_code == 200, r.text
    assert r.json()["komplexitaet"] == "einfach"


def test_spam_einsendungen_liste_erreichbar(client, mandant):
    # BUG-2: GET /formular-einsendungen?spam=1 muss markierte Spam liefern.
    test_public_submit_spam(client, mandant)
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/formular-einsendungen?spam=1", headers=_auth(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] >= 1
    spam_ids = {e["uebermittlungskennung"] for e in body["items"]}
    assert "spam-kennung-1" in spam_ids


def test_vorgang_detail_enthalt_formularantwort(client, mandant):
    # BUG-3: GET /vorgaenge/{id} muss die verknüpfte Formularantwort liefern.
    fid, public_id, name_feld = test_builder_flow_and_publish(client, mandant)
    make_domain(mandant, "detail.test")
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "detail.test"}).json()
    consent_feld = next(f["id"] for s in snap["schritte"] for f in s["felder"]
                        if f["typ"] == "consent")
    payload = {
        "uebermittlungskennung": "detail-kennung-1",
        "client_start": "2000-01-01T00:00:00.000Z",
        "honeypot": "",
        "werte": [
            {"feld_id": name_feld, "wert": "Antwort Person"},
            {"feld_id": consent_feld, "wert": "ja"},
        ],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    headers={"Host": "detail.test"}, json=payload)
    assert r.status_code == 201, r.text

    from app import db
    vorgang = db.engine.query(
        "SELECT vorgang_id FROM formular_einsendung WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant, "detail-kennung-1"), mandant_id=mandant)
    assert vorgang and vorgang[0]["vorgang_id"]
    vorgang_id = vorgang[0]["vorgang_id"]

    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get(f"/vorgaenge/{vorgang_id}", headers=_auth(tok))
    assert r.status_code == 200, r.text
    fe = r.json()["formular_einsendung"]
    assert fe, "Formularantwort fehlt im Vorgangdetail"
    assert fe["uebermittlungskennung"] == "detail-kennung-1"
    assert fe["werte"].get(name_feld) == "Antwort Person"
    assert fe["consent_nachweis"]

