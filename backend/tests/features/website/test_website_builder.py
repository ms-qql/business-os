from app import db
from conftest import make_domain, make_mandant, make_user


def _tiny_png() -> bytes:
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077"
        "53de0000000c4944415408d763f8cfc0000003010109dc7bfa0000000049454e44ae426082"
    )


def _login(client, mandant, email, role="Inhaber"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


# --- Auth & Rollen -------------------------------------------------------

def test_builder_requires_auth(client):
    r = client.get("/website-builder/startseite")
    assert r.status_code == 401


def test_builder_forbids_non_owner(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.get("/website-builder/startseite", headers=_auth(tok))
    assert r.status_code == 403


# --- Initialisierung -----------------------------------------------------

def test_initialisieren_erstellt_defaultsektionen(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    r = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    # Acht Defaultsektionen, sichtbar, sortiert.
    assert len(body["sections"]) == 8
    assert body["version"] == 2  # Erstellung (1;_init) -> bump auf 2
    positions = [s["position"] for s in body["sections"]]
    assert positions == sorted(positions)
    assert all(s["visible"] for s in body["sections"])
    assert body["sections"][0]["typ"] == "hero"


def test_initialisieren_idempotent(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    r1 = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok))
    r2 = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok))
    assert r2.status_code == 200
    assert r1.json()["landingpage_id"] == r2.json()["landingpage_id"]
    assert len(r2.json()["sections"]) == 8


def test_get_startseite_lazy_creates(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    r = client.get("/website-builder/startseite", headers=_auth(tok))
    assert r.status_code == 200
    assert r.json()["version"] == 1
    assert r.json()["sections"] == []


# --- Sektion hinzufügen / bearbeiten --------------------------------------

def test_add_section_at_end(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    r = client.post(
        "/website-builder/sections",
        headers=_auth(tok),
        json={"type": "faq", "version": init["version"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["sections"]) == 9
    assert body["sections"][-1]["typ"] == "faq"
    assert body["version"] == init["version"] + 1


def test_add_section_wrong_version_is_409(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    client.post("/website-builder/startseite/initialisieren", headers=_auth(tok))
    r = client.post(
        "/website-builder/sections",
        headers=_auth(tok),
        json={"type": "faq", "version": 999},
    )
    assert r.status_code == 409, r.text


def test_patch_section_updates_inhalt_and_visibility(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    sec = init["sections"][0]  # hero
    r = client.patch(
        f"/website-builder/sections/{sec['id']}",
        headers=_auth(tok),
        json={
            "version": init["version"],
            "visible": False,
            "inhalt": {
                "typ": "hero", "titel": "Neuer Titel", "text": "Text",
                "cta_typ": "anfrage", "cta_text": "Los",
            },
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    hero = next(s for s in body["sections"] if s["id"] == sec["id"])
    assert hero["visible"] is False
    assert hero["inhalt"]["titel"] == "Neuer Titel"
    assert body["version"] == init["version"] + 1


def test_patch_section_rejects_type_change(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    sec = init["sections"][0]
    r = client.patch(
        f"/website-builder/sections/{sec['id']}",
        headers=_auth(tok),
        json={
            "version": init["version"], "visible": True,
            "inhalt": {"typ": "cta", "titel": "x", "text": "", "cta_typ": "anfrage",
                       "cta_text": "x"},
        },
    )
    assert r.status_code == 422, r.text  # Typ-Wechsel verletzt Sektions-Validierung


def test_patch_section_invalid_cta_target_rejected(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    sec = init["sections"][0]
    r = client.patch(
        f"/website-builder/sections/{sec['id']}",
        headers=_auth(tok),
        json={
            "version": init["version"], "visible": True,
            "inhalt": {"typ": "hero", "titel": "x", "text": "", "cta_typ": "evil",
                       "cta_text": "x"},
        },
    )
    assert r.status_code == 422, r.text


# --- Reihenfolge ---------------------------------------------------------

def test_reihenfolge_reorders(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    ids = [s["id"] for s in init["sections"]]
    reverse = list(reversed(ids))
    r = client.put(
        "/website-builder/sections/reihenfolge",
        headers=_auth(tok),
        json={"version": init["version"], "ordered_ids": reverse},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert [s["id"] for s in body["sections"]] == reverse
    assert body["version"] == init["version"] + 1


def test_reihenfolge_requires_complete_set(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    ids = [s["id"] for s in init["sections"]]
    r = client.put(
        "/website-builder/sections/reihenfolge",
        headers=_auth(tok),
        json={"version": init["version"], "ordered_ids": ids[:3]},
    )
    assert r.status_code == 422, r.text


def test_reihenfolge_duplicate_ids_rejected(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    ids = [s["id"] for s in init["sections"]]
    dup = ids + [ids[0]]
    r = client.put(
        "/website-builder/sections/reihenfolge",
        headers=_auth(tok),
        json={"version": init["version"], "ordered_ids": dup},
    )
    assert r.status_code == 422, r.text


# --- Löschen -------------------------------------------------------------

def test_delete_section(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    sec = init["sections"][2]
    r = client.delete(
        f"/website-builder/sections/{sec['id']}?version={init['version']}",
        headers=_auth(tok),
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["sections"]) == 7
    assert all(s["id"] != sec["id"] for s in r.json()["sections"])


# --- Bilder --------------------------------------------------------------

def test_upload_and_delete_section_bild(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        data={"alt_text": "Hintergrund"},
        files={"datei": ("hero.png", _tiny_png(), "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    hero_after = next(s for s in body["sections"] if s["id"] == hero["id"])
    assert hero_after["bild"]
    assert hero_after["bild"]["alt_text"] == "Hintergrund"
    assert hero_after["bild"]["url"].startswith("memory://")

    # Bild wieder entfernen -> Textvariante bleibt, Bildverweis weg.
    r2 = client.delete(
        f"/website-builder/sections/{hero['id']}/bild?version={body['version']}",
        headers=_auth(tok),
    )
    assert r2.status_code == 200, r2.text
    hero2 = next(s for s in r2.json()["sections"] if s["id"] == hero["id"])
    assert hero2["bild"] is None


def test_public_section_bild_uses_same_origin_url(client, mandant):
    make_domain(mandant, "shk-mueller.de")
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    uploaded = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        files={"datei": ("hero.png", _tiny_png(), "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text

    site = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    public_hero = next(s for s in site.json()["sections"] if s["typ"] == "hero")
    assert public_hero["bild"]["url"] == f"/public/sections/{hero['id']}/bild"

    image = client.get(public_hero["bild"]["url"], headers={"Host": "shk-mueller.de"})
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content == _tiny_png()


def test_upload_bild_rejects_non_image(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        data={"alt_text": "x"},
        files={"datei": ("hero.png", b"not-an-image", "image/png")},
    )
    assert r.status_code == 422, r.text


def test_upload_bild_forbidden_for_non_image_section(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    faq = next(s for s in init["sections"] if s["typ"] == "faq")
    r = client.post(
        f"/website-builder/sections/{faq['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        data={"alt_text": "x"},
        files={"datei": ("x.png", _tiny_png(), "image/png")},
    )
    assert r.status_code == 422, r.text


# --- Mandantenisolation (RLS via App-Layer) -------------------------------

def test_owner_cannot_see_other_tenant_sections(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de")
    tok_b = _login(client, b, "b@shk.de")
    client.post("/website-builder/startseite/initialisieren", headers=_auth(tok_a))
    # B hat noch keine Landingpage; GET liefert leeren (eigenen) Zustand.
    rb = client.get("/website-builder/startseite", headers=_auth(tok_b))
    assert rb.status_code == 200
    assert rb.json()["sections"] == []


# --- Öffentlich: GET /public/site liefert nur sichtbare Sections ---------

def test_public_site_includes_visible_sections_only(client, mandant):
    make_domain(mandant, "shk-mueller.de")
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()

    # Erste Sektion (hero) ausblenden.
    hero = init["sections"][0]
    client.patch(
        f"/website-builder/sections/{hero['id']}",
        headers=_auth(tok),
        json={"version": init["version"], "visible": False,
              "inhalt": {"typ": "hero", "titel": "x", "text": "", "cta_typ": "anfrage",
                         "cta_text": "x"}},
    )
    r = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    assert r.status_code == 200, r.text
    types = [s["typ"] for s in r.json()["sections"]]
    assert "hero" not in types  # ausgeblendet
    assert len(types) == 7
    # Kein Objektpfad/verstecktes Feld in der öffentlichen Antwort.
    for s in r.json()["sections"]:
        assert "objektpfad" not in s


def test_public_site_sections_backward_compatible_when_no_landingpage(client, mandant):
    make_domain(mandant, "shk-mueller.de")
    r = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    assert r.status_code == 200, r.text
    assert r.json()["sections"] == []  # kein Builder -> leer, nicht broken
