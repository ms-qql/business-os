from app import db
from conftest import make_domain, make_mandant


def _tiny_png() -> bytes:
    # 1x1 transparentes PNG — echte Magic-Bytes für die serverseitige Prüfung.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc0000003010109dc7bfa0000000049454e44ae426082"
    )


def test_public_site_unknown_domain_is_404(client):
    r = client.get("/public/site")
    assert r.status_code == 404


def test_public_site_returns_settings_and_active_leistungen(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")

    # Erstzugriff legt Settings + Leistungskatalog automatisch an.
    r = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["leistungen"] == []  # alle Leistungen starten inaktiv

    # Eine Leistung aktivieren -> erscheint öffentlich.
    row = db.engine.query(
        "SELECT slug FROM leistungsseite WHERE mandant_id = %s LIMIT 1", (mandant,)
    )[0]
    db.engine.command(
        "UPDATE leistungsseite SET aktiv = 1 WHERE mandant_id = %s AND slug = %s",
        (mandant, row["slug"]),
    )
    r2 = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    slugs = {l["slug"] for l in r2.json()["leistungen"]}
    assert row["slug"] in slugs


def test_leistung_inactive_or_unknown_is_404(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")
    client.get("/public/site", headers={"Host": "shk-mueller.de"})  # seed
    r = client.get("/public/leistungen/heizung", headers={"Host": "shk-mueller.de"})
    assert r.status_code == 404  # noch nicht aktiviert

    r2 = client.get("/public/leistungen/does-not-exist", headers={"Host": "shk-mueller.de"})
    assert r2.status_code == 404


def test_inactive_domain_returns_404(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de", status="inaktiv")
    r = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    assert r.status_code == 404


def test_domain_never_leaks_other_mandant(client):
    a = make_mandant("A")
    b = make_mandant("B")
    make_domain(a, "a.de")
    make_domain(b, "b.de")
    db.engine.command("INSERT INTO website_settings (id, mandant_id, firmenname) VALUES "
                      "('s-a', %s, 'Firma A')", (a,))
    db.engine.command("INSERT INTO website_settings (id, mandant_id, firmenname) VALUES "
                      "('s-b', %s, 'Firma B')", (b,))
    r = client.get("/public/site", headers={"Host": "a.de"})
    assert r.json()["firmenname"] == "Firma A"
    r2 = client.get("/public/site", headers={"Host": "b.de"})
    assert r2.json()["firmenname"] == "Firma B"


def test_spoofed_forwarded_host_without_proxy_secret_is_ignored(client, monkeypatch):
    """SEC-1: X-Forwarded-Host ist ohne gültiges internes Proxy-Secret nicht
    vertrauenswürdig — sonst könnte ein Angreifer damit fremde Mandantendaten
    auslesen bzw. Anfragen in einen fremden Mandanten einschleusen."""
    from app.config import settings

    monkeypatch.setattr(settings, "internal_proxy_secret", "das-echte-secret")

    a = make_mandant("A")
    make_domain(a, "a-real.de")
    db.engine.command(
        "INSERT INTO website_settings (id, mandant_id, firmenname) VALUES ('s-a', %s, 'Firma A geheim')",
        (a,),
    )

    # Kein Secret-Header mitgeschickt -> gespoofter X-Forwarded-Host wird verworfen,
    # tatsächlicher Host ("irgendwas-beliebiges.de") kennt keinen Mandanten -> 404.
    r = client.get(
        "/public/site",
        headers={"Host": "irgendwas-beliebiges.de", "X-Forwarded-Host": "a-real.de"},
    )
    assert r.status_code == 404

    # Falsches Secret -> ebenfalls verworfen.
    r2 = client.get(
        "/public/site",
        headers={
            "Host": "irgendwas-beliebiges.de",
            "X-Forwarded-Host": "a-real.de",
            "X-Internal-Proxy-Secret": "falsches-secret",
        },
    )
    assert r2.status_code == 404

    # Richtiges Secret (nur der interne Proxy kennt es) -> darf vertraut werden.
    r3 = client.get(
        "/public/site",
        headers={
            "Host": "irgendwas-beliebiges.de",
            "X-Forwarded-Host": "a-real.de",
            "X-Internal-Proxy-Secret": "das-echte-secret",
        },
    )
    assert r3.status_code == 200
    assert r3.json()["firmenname"] == "Firma A geheim"


def test_upload_rejects_non_image(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")
    r = client.post(
        "/public/anfragen/uploads",
        headers={"Host": "shk-mueller.de"},
        data={"uebermittlungskennung": "abc-1"},
        files={"datei": ("bild.png", b"not-a-real-image", "image/png")},
    )
    assert r.status_code == 422


def test_upload_and_submit_links_bild_to_anfrage(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")
    up = client.post(
        "/public/anfragen/uploads",
        headers={"Host": "shk-mueller.de"},
        data={"uebermittlungskennung": "abc-2"},
        files={"datei": ("bild.png", _tiny_png(), "image/png")},
    )
    assert up.status_code == 201, up.text
    upload_id = up.json()["upload_id"]

    r = client.post(
        "/public/anfragen",
        headers={"Host": "shk-mueller.de"},
        json={
            "name": "Max Mustermann", "kontaktweg": "Telefon", "telefon": "0123456789",
            "adresse": "Teststr. 1, 12345 Musterstadt", "anliegen": "Heizung defekt",
            "dringlichkeit": "Dringend", "uebermittlungskennung": "abc-2",
            "upload_ids": [upload_id],
        },
    )
    assert r.status_code == 201, r.text
    rows = db.engine.query(
        "SELECT id FROM anfrage WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (mandant, "abc-2"),
    )
    assert len(rows) == 1
    bild = db.engine.query("SELECT anfrage_id FROM anfragebild WHERE id = %s", (upload_id,))[0]
    assert bild["anfrage_id"] == rows[0]["id"]


def test_anfrage_missing_telefon_for_kontaktweg_telefon_is_422(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")
    r = client.post(
        "/public/anfragen",
        headers={"Host": "shk-mueller.de"},
        json={
            "name": "Max", "kontaktweg": "Telefon", "adresse": "Teststr. 1",
            "anliegen": "Heizung defekt", "dringlichkeit": "Normal",
            "uebermittlungskennung": "abc-3",
        },
    )
    assert r.status_code == 422


def test_anfrage_same_kennung_is_idempotent(client):
    mandant = make_mandant()
    make_domain(mandant, "shk-mueller.de")
    payload = {
        "name": "Max", "kontaktweg": "E-Mail", "email": "max@example.de",
        "adresse": "Teststr. 1", "anliegen": "Bad-Sanierung", "dringlichkeit": "Normal",
        "uebermittlungskennung": "abc-4",
    }
    r1 = client.post("/public/anfragen", headers={"Host": "shk-mueller.de"}, json=payload)
    r2 = client.post("/public/anfragen", headers={"Host": "shk-mueller.de"}, json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    rows = db.engine.query(
        "SELECT id FROM anfrage WHERE mandant_id = %s AND uebermittlungskennung = %s",
        (mandant, "abc-4"),
    )
    assert len(rows) == 1


def test_anfrage_wrong_mandant_domain_creates_in_correct_tenant(client):
    a = make_mandant("A")
    b = make_mandant("B")
    make_domain(a, "a.de")
    make_domain(b, "b.de")
    payload = {
        "name": "Max", "kontaktweg": "E-Mail", "email": "max@example.de",
        "adresse": "Teststr. 1", "anliegen": "Sanitär", "dringlichkeit": "Normal",
        "uebermittlungskennung": "abc-5",
    }
    client.post("/public/anfragen", headers={"Host": "a.de"}, json=payload)
    rows_a = db.engine.query("SELECT id FROM anfrage WHERE mandant_id = %s", (a,))
    rows_b = db.engine.query("SELECT id FROM anfrage WHERE mandant_id = %s", (b,))
    assert len(rows_a) == 1
    assert len(rows_b) == 0
