import io

from PIL import Image

from app import db, storage
from conftest import make_domain, make_mandant, make_user


def _tiny_png() -> bytes:
    return _png(4, 4)


def _png(width: int, height: int, color=(200, 50, 50)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


def _animated_gif() -> bytes:
    buf = io.BytesIO()
    frames = [Image.new("RGB", (10, 10), c) for c in ((255, 0, 0), (0, 255, 0))]
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=100, loop=0)
    return buf.getvalue()


class _BrokenStorage(storage.BaseStorage):
    def put_object(self, object_key, data, content_type):
        raise RuntimeError("MinIO nicht erreichbar (simuliert)")

    def get_object(self, object_key):
        raise RuntimeError("MinIO nicht erreichbar (simuliert)")

    def delete_object(self, object_key):
        pass


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
    assert hero_after["bild"]["url"] == f"/public/sections/{hero['id']}/bild"

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
    editor_hero = next(s for s in uploaded.json()["sections"] if s["id"] == hero["id"])
    assert editor_hero["bild"]["url"] == f"https://shk-mueller.de/public/sections/{hero['id']}/bild"

    site = client.get("/public/site", headers={"Host": "shk-mueller.de"})
    public_hero = next(s for s in site.json()["sections"] if s["typ"] == "hero")
    assert public_hero["bild"]["url"] == f"/public/sections/{hero['id']}/bild"

    image = client.get(public_hero["bild"]["url"], headers={"Host": "shk-mueller.de"})
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/webp"


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


# --- PROJ-23: WebP-Zuschnitt, Anzeigename, Fehlerbehandlung (BUG-1/2/3) ---

def test_upload_bild_crops_to_fixed_section_ratio(client, mandant):
    """BUG-1: das gespeicherte Bild wird verzerrungsfrei auf das feste
    Seitenverhältnis der Sektion zugeschnitten, nicht nur kantenbegrenzt."""
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        files={"datei": ("breit.png", _png(3000, 2000), "image/png")},
    )
    assert r.status_code == 200, r.text

    make_domain(mandant, "hero-crop.de")
    site = client.get("/public/site", headers={"Host": "hero-crop.de"})
    bild_url = next(s for s in site.json()["sections"] if s["typ"] == "hero")["bild"]["url"]
    image = client.get(bild_url, headers={"Host": "hero-crop.de"})
    assert image.headers["content-type"] == "image/webp"
    img = Image.open(io.BytesIO(image.content))
    assert img.size == (1920, 1080)


def test_upload_bild_does_not_upscale_small_source(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    text_bild = next(s for s in init["sections"] if s["typ"] == "text_mit_bild")
    r = client.post(
        f"/website-builder/sections/{text_bild['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        files={"datei": ("klein.png", _png(80, 80), "image/png")},
    )
    assert r.status_code == 200, r.text

    make_domain(mandant, "small-src.de")
    site = client.get("/public/site", headers={"Host": "small-src.de"})
    bild_url = next(s for s in site.json()["sections"] if s["typ"] == "text_mit_bild")["bild"]["url"]
    image = client.get(bild_url, headers={"Host": "small-src.de"})
    img = Image.open(io.BytesIO(image.content))
    # 4:3-Zuschnitt aus 80x80 ohne Hochskalierung -> 80x60, nicht 1200x900.
    assert img.size == (80, 60)


def test_upload_bild_rejects_animated_gif(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok),
        files={"datei": ("anim.gif", _animated_gif(), "image/gif")},
    )
    assert r.status_code == 422, r.text
    # Kein neuer Verweis: Sektion bleibt ohne Bild.
    state = client.get("/website-builder/startseite", headers=_auth(tok)).json()
    assert next(s for s in state["sections"] if s["id"] == hero["id"])["bild"] is None


def test_upload_bild_assigns_unique_anzeigename(client, mandant):
    """BUG-2: Anzeigename aus Sektionstyp + Überschrift, mandantenweit
    eindeutig mit deterministischer ` (2)`-Deduplizierung."""
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    init = client.patch(
        f"/website-builder/sections/{hero['id']}", headers=_auth(tok),
        json={"version": init["version"], "inhalt": {**hero["inhalt"], "titel": "Dachsanierung"}},
    ).json()
    init = client.post(
        "/website-builder/sections", headers=_auth(tok),
        json={"type": "hero", "version": init["version"]},
    ).json()
    second_hero = init["sections"][-1]
    init = client.patch(
        f"/website-builder/sections/{second_hero['id']}", headers=_auth(tok),
        json={"version": init["version"], "inhalt": {**second_hero["inhalt"], "titel": "Dachsanierung"}},
    ).json()

    r1 = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok), files={"datei": ("a.png", _png(100, 100), "image/png")},
    )
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert next(s for s in body1["sections"] if s["id"] == hero["id"])["bild"]["anzeigename"] \
        == "Hero – Dachsanierung"

    r2 = client.post(
        f"/website-builder/sections/{second_hero['id']}/bild?version={body1['version']}",
        headers=_auth(tok), files={"datei": ("b.png", _png(100, 100), "image/png")},
    )
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert (
        next(s for s in body2["sections"] if s["id"] == second_hero["id"])["bild"]["anzeigename"]
        == "Hero – Dachsanierung (2)"
    )


def test_upload_bild_default_anzeigename_uses_sektionsbezeichnung(client, mandant):
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    # Leere Überschrift -> Anzeigename fällt auf die Sektionsbezeichnung zurück.
    patched = client.patch(
        f"/website-builder/sections/{hero['id']}",
        headers=_auth(tok),
        json={"version": init["version"],
              "inhalt": {**hero["inhalt"], "titel": ""}},
    ).json()
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={patched['version']}",
        headers=_auth(tok), files={"datei": ("a.png", _png(100, 100), "image/png")},
    )
    assert r.status_code == 200, r.text
    bild = next(s for s in r.json()["sections"] if s["id"] == hero["id"])["bild"]
    assert bild["anzeigename"] == "Hero-Bild"


def test_upload_bild_storage_failure_returns_german_error_and_keeps_old_ref(client, mandant):
    """BUG-3: ein Speicherfehler beim Upload darf keinen ungefangenen 500
    erzeugen und darf den bestehenden Bildverweis nicht ändern."""
    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    ok = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok), files={"datei": ("a.png", _png(100, 100), "image/png")},
    )
    assert ok.status_code == 200, ok.text
    old_url = next(s for s in ok.json()["sections"] if s["id"] == hero["id"])["bild"]["url"]

    storage.set_image_storage(_BrokenStorage())
    try:
        r = client.post(
            f"/website-builder/sections/{hero['id']}/bild?version={ok.json()['version']}",
            headers=_auth(tok), files={"datei": ("b.png", _png(100, 100), "image/png")},
        )
    finally:
        from app.storage import InMemoryStorage
        storage.set_image_storage(InMemoryStorage())

    assert r.status_code == 503, r.text
    assert "erreichbar" in r.json()["detail"]

    state = client.get("/website-builder/startseite", headers=_auth(tok)).json()
    assert next(s for s in state["sections"] if s["id"] == hero["id"])["bild"]["url"] == old_url


def test_upload_bild_rejects_version_changed_during_processing(client, mandant, monkeypatch):
    """Ein paralleler Edit während der Bildverarbeitung darf keinen
    veralteten Bildverweis speichern."""
    from app.features.website import builder_repository, builder_service

    tok = _login(client, mandant, "inh@shk.de")
    init = client.post("/website-builder/startseite/initialisieren", headers=_auth(tok)).json()
    hero = next(s for s in init["sections"] if s["typ"] == "hero")
    original_to_webp = builder_service._to_webp

    def change_version_during_processing(data, typ):
        builder_repository.bump_version(mandant, init["landingpage_id"], init["version"])
        return original_to_webp(data, typ)

    monkeypatch.setattr(builder_service, "_to_webp", change_version_during_processing)
    r = client.post(
        f"/website-builder/sections/{hero['id']}/bild?version={init['version']}",
        headers=_auth(tok), files={"datei": ("hero.png", _png(100, 100), "image/png")},
    )

    assert r.status_code == 409, r.text
    state = client.get("/website-builder/startseite", headers=_auth(tok)).json()
    assert next(s for s in state["sections"] if s["id"] == hero["id"])["bild"] is None


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
