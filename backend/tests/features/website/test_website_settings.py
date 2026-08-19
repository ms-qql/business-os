from app import db
from conftest import make_domain, make_mandant, make_user


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def test_settings_requires_auth(client):
    r = client.get("/website-settings")
    assert r.status_code == 401


def test_non_owner_cannot_read_settings(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_owner_reads_and_updates_settings(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    assert r.json()["leistungen"]  # Katalog wurde geseedet
    assert r.json()["domain"] is None

    r2 = client.patch(
        "/website-settings", headers={"Authorization": f"Bearer {tok}"},
        json={"firmenname": "SHK Müller GmbH", "telefon": "0221 123456"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["firmenname"] == "SHK Müller GmbH"
    assert r2.json()["telefon"] == "0221 123456"


def test_owner_updates_leistungen(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    settings = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"}).json()
    slug = settings["leistungen"][0]["slug"]

    r = client.patch(
        "/website-settings", headers={"Authorization": f"Bearer {tok}"},
        json={"leistungen": [{"slug": slug, "aktiv": True, "kurzbeschreibung": "Kurz",
                              "inhalt": "Lang"}]},
    )
    assert r.status_code == 200, r.text
    updated = next(l for l in r.json()["leistungen"] if l["slug"] == slug)
    assert updated["aktiv"] is True
    assert updated["kurzbeschreibung"] == "Kurz"


def test_settings_domain_shown_from_website_domains(client, mandant):
    make_domain(mandant, "shk-mueller.de")
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/website-settings", headers={"Authorization": f"Bearer {tok}"})
    assert r.json()["domain"] == "shk-mueller.de"
    assert r.json()["domain_status"] == "aktiv"


def test_owner_domain_not_in_patch_contract(client, mandant):
    # ADR-7-2: domain ist kein Schreibfeld mehr in PATCH /website-settings;
    # es wird bewusst mit 422 abgewiesen (kein stiller No-op).
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.patch(
        "/website-settings", headers={"Authorization": f"Bearer {tok}"},
        json={"domain": "shk-mueller.de"},
    )
    assert r.status_code == 422, r.text
    # Domain-Reservierung läuft ausschließlich über /onboarding/domain.
    r2 = client.put(
        "/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
        json={"hostname": "shk-mueller.de"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "inaktiv"

    # Öffentliche Website ist erst nach Veröffentlichung erreichbar (inaktive
    # Domain ist noch nicht live) — ein expliziter 404 ist hier korrekt.
    site = client.get("/public/site", headers={"host": "shk-mueller.de"})
    assert site.status_code == 404, site.text


def test_domain_collision_with_other_tenant_rejected(client, mandant):
    other = make_mandant("Andere Firma")
    make_domain(other, "shk-mueller.de")
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.put(
        "/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
        json={"hostname": "shk-mueller.de"},
    )
    assert r.status_code == 409, r.text


def test_domain_invalid_format_rejected(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.put(
        "/onboarding/domain", headers={"Authorization": f"Bearer {tok}"},
        json={"hostname": "https://not a hostname/"},
    )
    assert r.status_code == 422, r.text


def test_owner_cannot_see_other_tenant_settings(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Inhaber")
    client.patch("/website-settings", headers={"Authorization": f"Bearer {tok_a}"},
                 json={"firmenname": "Firma A"})
    tok_b = _login(client, b, "b@shk.de", "Inhaber")
    r = client.get("/website-settings", headers={"Authorization": f"Bearer {tok_b}"})
    assert r.json()["firmenname"] != "Firma A"


def test_owner_uploads_logo(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc0000003010109dc7bfa0000000049454e44ae426082"
    )
    r = client.post(
        "/website-settings/logo", headers={"Authorization": f"Bearer {tok}"},
        files={"datei": ("logo.png", png, "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["logo_url"]

    row = db.engine.query(
        "SELECT logo_objektpfad FROM website_settings WHERE mandant_id = %s", (mandant,)
    )[0]
    assert row["logo_objektpfad"]


def test_logo_upload_rejects_non_image(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.post(
        "/website-settings/logo", headers={"Authorization": f"Bearer {tok}"},
        files={"datei": ("logo.png", b"not-a-real-image", "image/png")},
    )
    assert r.status_code == 422
