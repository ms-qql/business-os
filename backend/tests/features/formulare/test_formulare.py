from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from starlette.requests import Request

from conftest import make_domain, make_mandant, make_user
from app import db
from app.config import settings
from app.features.formulare.routes import _client_ip


def _request(headers: list[tuple[bytes, bytes]], client_ip: str) -> Request:
    return Request({"type": "http", "headers": headers, "client": (client_ip, 1234)})


def test_rate_limit_ip_ignores_untrusted_forwarded_for(monkeypatch):
    monkeypatch.setattr(settings, "internal_proxy_secret", "proxy-secret")
    request = _request([(b"x-forwarded-for", b"203.0.113.7")], "198.51.100.9")
    assert _client_ip(request) == "198.51.100.9"

    trusted = _request(
        [(b"x-forwarded-for", b"203.0.113.7"), (b"x-internal-proxy-secret", b"proxy-secret")],
        "198.51.100.9",
    )
    assert _client_ip(trusted) == "203.0.113.7"


def _auth_headers(client, mandant_id, email="buero@test.de", role="Buero"):
    make_user(mandant_id, email, role)
    # Login ueber bestehenden Auth-Flow.
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_shk(client, headers):
    r = client.post("/formulare", json={"vorlage": "shk"}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _publish(client, headers, formular_id, draft_revision):
    r = client.post(f"/formulare/{formular_id}/veroeffentlichen",
                    json={"draft_revision": draft_revision}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# --- Liste / Anlage --------------------------------------------------------


def test_create_leer_und_vorlage(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    r = client.post("/formulare", json={}, headers=h)
    assert r.status_code == 201
    assert r.json()["name"] == "Neues Formular"
    assert r.json()["schritte"] == []

    r2 = client.post("/formulare", json={"vorlage": "shk"}, headers=h)
    assert r2.status_code == 201
    body = r2.json()
    assert body["name"] == "SHK-Kontaktformular"
    assert len(body["schritte"]) == 1
    assert len(body["schritte"][0]["felder"]) >= 5
    # Consent-Pflichtfeld ist enthalten.
    typen = [f["typ"] for f in body["schritte"][0]["felder"]]
    assert "consent" in typen


def test_liste_ohne_formulare_leer(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    r = client.get("/formulare", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] == 0
    assert r.json()["items"] == []


def test_liste_limit_offset(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    for _ in range(3):
        client.post("/formulare", json={}, headers=h)
    r = client.get("/formulare?limit=2&offset=0", headers=h)
    assert r.status_code == 200
    assert r.json()["limit"] == 2
    assert r.json()["total"] == 3
    assert len(r.json()["items"]) == 2


def test_nie_veroeffentlichten_entwurf_loeschen(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    f = client.post("/formulare", json={}, headers=h).json()

    r = client.delete(f"/formulare/{f['id']}", headers=h)
    assert r.status_code == 204
    assert client.get("/formulare", headers=h).json()["total"] == 0

    published = _create_shk(client, h)
    _publish(client, h, published["id"], published["draft_revision"])
    r = client.delete(f"/formulare/{published['id']}", headers=h)
    assert r.status_code == 422


# --- Draft-Mutationen + Revision -------------------------------------------


def test_schritt_feld_lifecycle_und_revision(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    f = _create_shk(client, h)
    fid = f["id"]
    rev = f["draft_revision"]

    # Schritt hinzufügen.
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "Details", "draft_revision": rev}, headers=h)
    assert r.status_code == 200
    rev2 = r.json()["draft_revision"]
    assert rev2 == rev + 1
    schritt_id = r.json()["schritte"][-1]["id"]
    assert r.json()["schritte"][-1]["titel"] == "Details"

    # Feld hinzufügen.
    r = client.post(f"/formulare/{fid}/schritte/{schritt_id}/felder",
                    json={"typ": "text", "draft_revision": rev2}, headers=h)
    assert r.status_code == 200
    feld_id = r.json()["schritte"][-1]["felder"][-1]["id"]
    rev3 = r.json()["draft_revision"]

    # Feld aktualisieren (Optionen nicht erlaubt bei text -> Validierung ok).
    r = client.patch(
        f"/formulare/{fid}/schritte/{schritt_id}/felder/{feld_id}",
        json={"label": "Mein Feld", "pflichtfeld": True, "optional_in_einfach": False,
              "uebernahme": None, "maxlaenge": 50, "draft_revision": rev3}, headers=h)
    assert r.status_code == 200
    assert r.json()["schritte"][-1]["felder"][-1]["label"] == "Mein Feld"

    # Veraltete Revision -> 409.
    r = client.patch(
        f"/formulare/{fid}/schritte/{schritt_id}/felder/{feld_id}",
        json={"label": "X", "pflichtfeld": False, "optional_in_einfach": False,
              "uebernahme": None, "draft_revision": rev3}, headers=h)
    assert r.status_code == 409


def test_feld_optionen_validierung(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    f = _create_shk(client, h)
    fid = f["id"]
    # Neuen Schritt + Dropdown-Feld.
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "Auswahl", "draft_revision": f["draft_revision"]}, headers=h)
    schritt_id = r.json()["schritte"][-1]["id"]
    rev = r.json()["draft_revision"]
    r = client.post(f"/formulare/{fid}/schritte/{schritt_id}/felder",
                    json={"typ": "dropdown", "draft_revision": rev}, headers=h)
    feld_id = r.json()["schritte"][-1]["felder"][-1]["id"]
    rev = r.json()["draft_revision"]
    # Optionen mit doppeltem Wert -> 422.
    r = client.patch(
        f"/formulare/{fid}/schritte/{schritt_id}/felder/{feld_id}",
        json={"label": "Wahl", "pflichtfeld": True, "optional_in_einfach": False,
              "uebernahme": None,
              "optionen": [{"label": "A", "wert": "a"}, {"label": "B", "wert": "a"}],
              "draft_revision": rev}, headers=h)
    assert r.status_code == 422
    # Gueltige Optionen.
    r = client.patch(
        f"/formulare/{fid}/schritte/{schritt_id}/felder/{feld_id}",
        json={"label": "Wahl", "pflichtfeld": True, "optional_in_einfach": False,
              "uebernahme": None,
              "optionen": [{"label": "A", "wert": "a"}, {"label": "B", "wert": "b"}],
              "draft_revision": rev}, headers=h)
    assert r.status_code == 200
    opts = r.json()["schritte"][-1]["felder"][-1]["optionen"]
    assert {o["wert"] for o in opts} == {"a", "b"}


def test_reorder_schritte(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    f = _create_shk(client, h)
    fid = f["id"]
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "Weitere Angaben", "draft_revision": f["draft_revision"]}, headers=h)
    rev = r.json()["draft_revision"]
    ids = [s["id"] for s in r.json()["schritte"]]
    # umdrehen
    r = client.put(f"/formulare/{fid}/schritte/reihenfolge",
                   json={"ordered_ids": list(reversed(ids)), "draft_revision": rev}, headers=h)
    assert r.status_code == 200
    assert [s["id"] for s in r.json()["schritte"]] == list(reversed(ids))


# --- Publish ---------------------------------------------------------------


def test_publish_und_einbindung(client):
    m = make_mandant()
    make_domain(m, "shk-mueller.de")
    h = _auth_headers(client, m)
    f = _create_shk(client, h)
    fid = f["id"]
    # SHK-Vorlage hat >=1 Schritt, >=1 Feld, genau 1 Pflicht-Consent -> publish ok.
    r = _publish(client, h, fid, f["draft_revision"])
    assert r["veroeffentlicht"] is True
    assert r["public_id"] is not None
    public_id = r["public_id"]

    # Einbindung.
    r2 = client.get(f"/formulare/{fid}/einbindung", headers=h)
    assert r2.status_code == 200
    body = r2.json()
    assert public_id in body["direktlink"]
    assert public_id in body["iframe"]
    assert public_id in body["snippet"]
    assert "X-Forwarded-Host" not in body["iframe"]  # kein Mandanten-/API-Param

    # Zuruecknehmen.
    r3 = client.post(f"/formulare/{fid}/veroeffentlichung-zuruecknehmen",
                    json={"draft_revision": r["draft_revision"]}, headers=h)
    assert r3.status_code == 200
    assert r3.json()["veroeffentlicht"] is False
    assert r3.json()["public_id"] is None


def test_publish_ohne_consent_abgelehnt(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    r = client.post("/formulare", json={}, headers=h)
    fid = r.json()["id"]
    rev = r.json()["draft_revision"]
    # Schritt + Feld (text, pflicht) + Schritt + Consent (nicht pflicht).
    r = client.post(f"/formulare/{fid}/schritte", json={"titel": "Zusatz", "draft_revision": rev}, headers=h)
    sid = r.json()["schritte"][-1]["id"]
    rev = r.json()["draft_revision"]
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder",
                    json={"typ": "text", "draft_revision": rev}, headers=h)
    feld_id = r.json()["schritte"][-1]["felder"][-1]["id"]
    rev = r.json()["draft_revision"]
    r = client.patch(f"/formulare/{fid}/schritte/{sid}/felder/{feld_id}",
                     json={"label": "Name", "pflichtfeld": True, "optional_in_einfach": False,
                           "uebernahme": "kontaktname", "draft_revision": rev}, headers=h)
    rev = r.json()["draft_revision"]
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder",
                    json={"typ": "consent", "draft_revision": rev}, headers=h)
    consent_id = r.json()["schritte"][-1]["felder"][-1]["id"]
    rev = r.json()["draft_revision"]
    r = client.patch(f"/formulare/{fid}/schritte/{sid}/felder/{consent_id}",
                     json={"label": "DS", "pflichtfeld": False, "optional_in_einfach": False,
                           "uebernahme": None, "draft_revision": rev}, headers=h)
    rev = r.json()["draft_revision"]
    # Genau 0 Pflicht-Consent -> Publish abgelehnt (422).
    r = client.post(f"/formulare/{fid}/veroeffentlichen",
                    json={"draft_revision": rev}, headers=h)
    assert r.status_code == 422


def test_einbindung_ohne_publish_422(client):
    m = make_mandant()
    h = _auth_headers(client, m)
    f = _create_shk(client, h)
    r = client.get(f"/formulare/{f['id']}/einbindung", headers=h)
    assert r.status_code == 422


# --- Öffentlich: Snapshot / Upload / Einsendung ---------------------------


def _publish_and_public_id(client, h, m):
    f = _create_shk(client, h)
    r = _publish(client, h, f["id"], f["draft_revision"])
    return f["id"], r["public_id"]


def test_public_snapshot_404_unknown(client):
    r = client.get("/public/formulare/nope", headers={"Host": "x.de"})
    assert r.status_code == 404


def test_public_snapshot_domain_treue(client):
    m = make_mandant("A")
    m2 = make_mandant("B")
    make_domain(m, "a.de")
    make_domain(m2, "b.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    # Fremde Domain -> 404 (keine Mandanteninfo geleakt).
    r = client.get(f"/public/formulare/{public_id}", headers={"Host": "b.de"})
    assert r.status_code == 404
    # Eigene Domain -> Snapshot.
    r = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"})
    assert r.status_code == 200
    body = r.json()
    assert body["modus"] == "einfach"
    assert len(body["schritte"]) >= 1


def _tiny_png():
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc0000003010109dc7bfa0000000049454e44ae426082")


def test_public_upload_magicbytes_und_typ(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    # Upload-Feld-ID aus dem Snapshot holen.
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"}).json()
    upload_feld = None
    for s in snap["schritte"]:
        for fld in s["felder"]:
            if fld["typ"] == "upload":
                upload_feld = fld["id"]
    # SHK-Vorlage hat kein Upload-Feld -> eigenes Formular mit Upload bauen.
    if not upload_feld:
        # Neues Formular, Schritt, Uploadfeld, publish.
        r = client.post("/formulare", json={}, headers=h)
        fid2 = r.json()["id"]
        rev = r.json()["draft_revision"]
        r = client.post(f"/formulare/{fid2}/schritte", json={"titel": "Upload", "draft_revision": rev}, headers=h)
        sid = r.json()["schritte"][-1]["id"]
        rev = r.json()["draft_revision"]
        r = client.post(f"/formulare/{fid2}/schritte/{sid}/felder",
                        json={"typ": "upload", "draft_revision": rev}, headers=h)
        ufid = r.json()["schritte"][-1]["felder"][-1]["id"]
        rev = r.json()["draft_revision"]
        r = client.post(f"/formulare/{fid2}/schritte/{sid}/felder",
                        json={"typ": "consent", "draft_revision": rev}, headers=h)
        cid = r.json()["schritte"][-1]["felder"][-1]["id"]
        rev = r.json()["draft_revision"]
        r = client.patch(f"/formulare/{fid2}/schritte/{sid}/felder/{cid}",
                         json={"label": "DS", "pflichtfeld": True, "optional_in_einfach": False,
                               "uebernahme": None, "draft_revision": rev}, headers=h)
        rev = r.json()["draft_revision"]
        r = client.patch(f"/formulare/{fid2}/schritte/{sid}/felder/{ufid}",
                         json={"label": "Datei", "pflichtfeld": True, "optional_in_einfach": False,
                               "uebernahme": None, "max_anzahl": 2, "draft_revision": rev}, headers=h)
        rev = r.json()["draft_revision"]
        r = _publish(client, h, fid2, rev)
        public_id = r["public_id"]
        upload_feld = ufid

    import io
    r = client.post(
        f"/public/formulare/{public_id}/uploads",
        data={"uebermittlungskennung": "kenn-1", "feld_id": upload_feld},
        files={"datei": ("b.png", _tiny_png(), "image/png")},
        headers={"Host": "a.de"})
    assert r.status_code == 201, r.text
    assert "upload_id" in r.json()

    # Falscher Typ (kein Bild) -> 422.
    r = client.post(
        f"/public/formulare/{public_id}/uploads",
        data={"uebermittlungskennung": "kenn-1", "feld_id": upload_feld},
        files={"datei": ("b.txt", b"hello world not an image", "text/plain")},
        headers={"Host": "a.de"})
    assert r.status_code == 422


def _einsendung_payload(kennung="kenn-einsend-1"):
    return {
        "uebermittlungskennung": kennung,
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "",
        "werte": [
            {"feld_id": "irrelevant", "wert": "Max Mustermann"},
        ],
    }


def test_einsendung_erzeugt_anfrage_und_vorgang(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    # Snapshot-Feld-IDs aus SHK-Vorlage.
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"}).json()
    felder = {f["label"]: f for s in snap["schritte"] for f in s["felder"]}
    name_f = felder["Ihr Name"]["id"]
    email_f = felder["E-Mail"]["id"]
    anliegen_f = felder["Ihr Anliegen"]["id"]
    consent_f = felder["Datenschutz"]["id"]
    telefon_f = felder["Telefon"]["id"]
    adresse_f = felder["Adresse"]["id"]

    payload = {
        "uebermittlungskennung": "kenn-abc",
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "",
        "werte": [
            {"feld_id": name_f, "wert": "Max Mustermann"},
            {"feld_id": email_f, "wert": "max@example.de"},
            {"feld_id": telefon_f, "wert": "0123"},
            {"feld_id": adresse_f, "wert": "Hauptstr 1, 12345 Stadt"},
            {"feld_id": anliegen_f, "wert": "Bitte um Termin"},
            {"feld_id": consent_f, "wert": "true"},
        ],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    json=payload, headers={"Host": "a.de"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "erfolgreich"

    # Anfrage + Vorgang + Kundenentwurf angelegt.
    rows = db.engine.query(
        "SELECT id FROM anfrage WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (m, "kenn-abc"), mandant_id=m)
    assert rows
    anfrage_id = rows[0]["id"]
    eins = db.engine.query(
        "SELECT anfrage_id, vorgang_id, spam_status FROM formular_einsendung "
        "WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (m, "kenn-abc"), mandant_id=m)
    assert eins[0]["anfrage_id"] == anfrage_id
    assert eins[0]["vorgang_id"] is not None
    assert eins[0]["spam_status"] == "normal"
    # Kunde als Entwurf.
    k = db.engine.query("SELECT status FROM kunde WHERE mandant_id = %s AND email = %s",
                        (m, "max@example.de"), mandant_id=m)
    assert k[0]["status"] == "entwurf"

    # Idempotenz: zweite Einsendung gleiche Kennung -> kein neuer Vorgang.
    r2 = client.post(f"/public/formulare/{public_id}/einsendungen",
                     json=payload, headers={"Host": "a.de"})
    assert r2.status_code == 201
    rows2 = db.engine.query(
        "SELECT COUNT(*) AS c FROM vorgang v JOIN formular_einsendung fe ON fe.vorgang_id = v.id "
        "WHERE fe.mandant_id = %s AND fe.uebermittlungskennung = %s",
        (m, "kenn-abc"), mandant_id=m)
    assert int(rows2[0]["c"]) == 1


def test_einsendung_honeypot_als_spam(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"}).json()
    felder = {f["label"]: f for s in snap["schritte"] for f in s["felder"]}
    consent_f = felder["Datenschutz"]["id"]
    payload = {
        "uebermittlungskennung": "kenn-spam",
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "bot-fuelled",
        "werte": [{"feld_id": consent_f, "wert": "true"}],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    json=payload, headers={"Host": "a.de"})
    assert r.status_code == 201
    assert r.json()["status"] == "spam"
    # Keine Anfrage/Vorgang.
    rows = db.engine.query(
        "SELECT id, anfrage_id, vorgang_id, spam_status FROM formular_einsendung "
        "WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (m, "kenn-spam"), mandant_id=m)
    assert rows[0]["spam_status"] == "spam"
    assert rows[0]["anfrage_id"] is None
    assert rows[0]["vorgang_id"] is None


def test_einsendung_unvollstaendig_als_spam(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"}).json()
    felder = {f["label"]: f for s in snap["schritte"] for f in s["felder"]}
    consent_f = felder["Datenschutz"]["id"]
    # Consent fehlt -> Servervalidierung schlägt fehl -> spam, keine Anfrage.
    payload = {
        "uebermittlungskennung": "kenn-invalid",
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "",
        "werte": [{"feld_id": felder["Ihr Name"]["id"], "wert": "Max"}],
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    json=payload, headers={"Host": "a.de"})
    assert r.status_code == 201
    assert r.json()["status"] == "spam"


# --- Einsendungsliste (Spam) -----------------------------------------------


def test_einsendungen_liste_nur_spam(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    # Ein Spam-Eintrag erzeugen.
    client.post(f"/public/formulare/{public_id}/einsendungen",
                json={"uebermittlungskennung": "kenn-spam-2",
                      "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
                      "honeypot": "x", "werte": []},
                headers={"Host": "a.de"})
    # Nur Spam.
    r = client.get("/formular-einsendungen?spam=1", headers=h)
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(it["spam_status"] == "spam" for it in items)
    assert any(it["uebermittlungskennung"] == "kenn-spam-2" for it in items)
    # Ohne spam-Filter: leer (nur Spam vorhanden, aber Filter = nur spam).
    r2 = client.get("/formular-einsendungen?spam=0", headers=h)
    assert r2.status_code == 200
    assert all(it["spam_status"] == "normal" for it in r2.json()["items"])


# --- Vorgangdetail-Anreicherung --------------------------------------------


def test_vorgang_detail_mit_formular_einsendung(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth_headers(client, m)
    fid, public_id = _publish_and_public_id(client, h, m)
    snap = client.get(f"/public/formulare/{public_id}", headers={"Host": "a.de"}).json()
    felder = {f["label"]: f for s in snap["schritte"] for f in s["felder"]}
    payload = {
        "uebermittlungskennung": "kenn-detail",
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "",
        "werte": [
            {"feld_id": felder["Ihr Name"]["id"], "wert": "Max"},
            {"feld_id": felder["E-Mail"]["id"], "wert": "max@x.de"},
            {"feld_id": felder["Telefon"]["id"], "wert": ""},
            {"feld_id": felder["Adresse"]["id"], "wert": ""},
            {"feld_id": felder["Ihr Anliegen"]["id"], "wert": "Termin"},
            {"feld_id": felder["Datenschutz"]["id"], "wert": "true"},
        ],
    }
    client.post(f"/public/formulare/{public_id}/einsendungen",
                json=payload, headers={"Host": "a.de"})
    vorgang_id = db.engine.query(
        "SELECT vorgang_id FROM formular_einsendung WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s", (m, "kenn-detail"), mandant_id=m)[0]["vorgang_id"]
    r = client.get(f"/vorgaenge/{vorgang_id}", headers=h)
    assert r.status_code == 200
    assert "formular_einsendung" in r.json()
    neither_field = None
