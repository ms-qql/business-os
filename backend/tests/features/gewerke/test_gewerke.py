"""PROJ-22: Integrationstests für Gewerke-Katalog, Kategorien, Angebot-Snapshot
und Preis-Override. Deckt Rechenregeln, RLS-Isolation (App-Layer), Duplikat-Guard
und die Override-Nachweis-Pflicht ab."""
from conftest import make_mandant, make_user

from app.features.angebote import repository as angebote_repo
from app.features.email import service as email_service  # noqa: F401 (setup)
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _setup_vorgang(mandant_id):
    kunde = kunden_repo.create_kunde(mandant_id, "Kunde X", "k@x.de", None, None)
    vorgang = vorgaenge_repo.create_vorgang(
        mandant_id, kunde["id"], None, "Neu", "Sonstiges", "Anfrage", None)
    return kunde, vorgang


def _create_angebot(client, tok, vorgang_id):
    r = client.post(f"/vorgaenge/{vorgang_id}/angebote", headers=_auth(tok), json={})
    assert r.status_code == 201, r.text
    return r.json()


# --- Kategorien -----------------------------------------------------------

def test_kategorie_crud(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    # Anlegen + Duplikat -> 409
    r = client.post("/gewerke/kategorien", headers=_auth(tok), json={"name": "Heizung"})
    assert r.status_code == 201, r.text
    kid = r.json()["id"]
    r2 = client.post("/gewerke/kategorien", headers=_auth(tok), json={"name": "Heizung"})
    assert r2.status_code == 409, r2.text
    # Umbenennen
    r3 = client.patch(f"/gewerke/kategorien/{kid}", headers=_auth(tok), json={"name": "Sanitär"})
    assert r3.status_code == 200, r3.text
    assert r3.json()["name"] == "Sanitär"
    # Löschen (kein Gewerk zugeordnet)
    d = client.delete(f"/gewerke/kategorien/{kid}", headers=_auth(tok))
    assert d.status_code == 204


def test_kategorie_mit_gewerk_nicht_loeschbar(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    r = client.post("/gewerke/kategorien", headers=_auth(tok), json={"name": "Heizung"})
    kid = r.json()["id"]
    # Gewerk in Kategorie anlegen
    g = client.post("/gewerke", headers=_auth(tok),
                    json={"bezeichnung": "Wartung", "einheit": "Std", "kategorie_id": kid,
                          "steuersatz": 19,
                          "kostenzeilen": [{"kostenart": "lohn", "menge": 1.0, "einheit": "Std",
                                            "ek_einzelpreis": 50.0, "zuschlag_prozent": 0.0}]})
    assert g.status_code == 201, g.text
    # Löschen blockiert
    d = client.delete(f"/gewerke/kategorien/{kid}", headers=_auth(tok))
    assert d.status_code == 409, d.text


# --- Gewerke: Anlage, VK-Berechnung, Duplikat-Guard -----------------------

def _make_gewerk_payload(**over):
    p = {"bezeichnung": "Wartung", "einheit": "Std", "steuersatz": 19,
         "kostenzeilen": [
             {"kostenart": "lohn", "menge": 1.0, "einheit": "Std",
              "ek_einzelpreis": 70.0, "zuschlag_prozent": 27.14},
             {"kostenart": "material", "menge": 2.0, "einheit": "Stk",
              "ek_einzelpreis": 10.0, "zuschlag_prozent": 0.0},
         ]}
    p.update(over)
    return p


def test_gewerk_erstellen_und_vk_berechnung(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    # VK = 70*(1+0.2714) ≈ 89.0 + 2*10 = 20 -> 109.0
    r = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload())
    assert r.status_code == 201, r.text
    body = r.json()
    assert round(body["vk_preis"], 2) == 109.0, body
    assert len(body["kostenzeilen"]) == 2
    # einzelne Zeile: 70 * 1.2714 = 89.0
    lohn = next(z for z in body["kostenzeilen"] if z["kostenart"] == "lohn")
    assert round(lohn["vk_preis"], 2) == 89.0, lohn


def test_gewerk_kostenzeile_beschreibung(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    r = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload(
        kostenzeilen=[{"kostenart": "lohn", "beschreibung": "Meister", "menge": 1,
                        "einheit": "Stunde", "ek_einzelpreis": 70, "zuschlag_prozent": 0}],
    ))
    assert r.status_code == 201, r.text
    assert r.json()["kostenzeilen"][0]["beschreibung"] == "Meister"


def test_gewerk_duplikat_guard(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    assert client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload()).status_code == 201
    # gleiche Bezeichnung + Einheit ohne Bestätigung -> 409
    r2 = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload(steuersatz=7))
    assert r2.status_code == 409, r2.text
    # mit Bestätigung -> 201
    r3 = client.post("/gewerke", headers=_auth(tok),
                     json=_make_gewerk_payload(steuersatz=7, duplikat_bestaetigt=True))
    assert r3.status_code == 201, r3.text


def test_gewerk_update_kostenzeilen_und_vk(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    g = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload())
    gid = g.json()["id"]
    # Kostenzeilen ersetzen -> neue VK
    upd = client.patch(f"/gewerke/{gid}", headers=_auth(tok),
                       json={"kostenzeilen": [
                           {"kostenart": "lohn", "menge": 3.0, "einheit": "Std",
                            "ek_einzelpreis": 40.0, "zuschlag_prozent": 0.0}]})
    assert upd.status_code == 200, upd.text
    assert round(upd.json()["vk_preis"], 2) == 120.0, upd.json()


def test_gewerk_gesamtpreis_art(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    r = client.post("/gewerke", headers=_auth(tok),
                    json={"bezeichnung": "Beratung", "einheit": "Termin",
                          "kalkulationsart": "gesamtpreis", "steuersatz": 19,
                          "kostenzeilen": [{"kostenart": "lohn", "menge": 1.0,
                                            "einheit": "Termin", "ek_einzelpreis": 200.0,
                                            "zuschlag_prozent": 25.0}]})
    assert r.status_code == 201, r.text
    assert round(r.json()["vk_preis"], 2) == 250.0, r.json()


# --- Angebot-Position aus Gewerk (Snapshot, keine Live-Referenz) ----------

def test_position_aus_gewerk_snapshot(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    g = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload())
    gid = g.json()["id"]
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    # Position aus Gewerk mit Menge 3
    r = client.post(f"/angebote/{angebot['id']}/positionen/aus-gewerk",
                    headers=_auth(tok),
                    json={"gewerk_id": gid, "menge": 3, "sortierung": 0})
    assert r.status_code == 201, r.text
    pos = r.json()["positionen"][0]
    # VK des Gewerks = 109.0, kalkulierter Einzelpreis = 109.0 (je_einheit)
    assert round(pos["kalkulierter_einzelpreis"], 2) == 109.0, pos
    assert round(pos["einzelpreis"], 2) == 109.0, pos
    assert pos["menge"] == 3
    # Snapshot: Bezeichnung/Einheit aus Gewerk, nicht mehr live verknüpft.
    assert pos["bezeichnung"] == "Wartung"

    # Gewerk nachträglich ändern -> Position bleibt unverändert (kein Live-Ref).
    client.patch(f"/gewerke/{gid}", headers=_auth(tok),
                 json={"bezeichnung": "Wartung NEU"})
    r2 = client.get(f"/angebote/{angebot['id']}", headers=_auth(tok))
    assert r2.json()["positionen"][0]["bezeichnung"] == "Wartung", r2.json()


def test_position_aus_gewerk_gesamtpreis_menge_eins(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    g = client.post("/gewerke", headers=_auth(tok),
                    json={"bezeichnung": "Beratung", "einheit": "Termin",
                          "kalkulationsart": "gesamtpreis", "steuersatz": 19,
                          "kostenzeilen": [{"kostenart": "lohn", "menge": 1.0,
                                            "einheit": "Termin", "ek_einzelpreis": 200.0,
                                            "zuschlag_prozent": 25.0}]})
    gid = g.json()["id"]
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/positionen/aus-gewerk",
                    headers=_auth(tok), json={"gewerk_id": gid, "menge": 5})
    assert r.status_code == 201, r.text
    pos = r.json()["positionen"][0]
    # gesamtpreis: Menge wird auf 1 gesetzt, VK ist Gesamtpreis.
    assert pos["menge"] == 1, pos
    assert round(pos["einzelpreis"], 2) == 250.0, pos


# --- Preis-Override (Begründungspflicht, Rückstellung) --------------------

def _gewerk_position(client, tok, mandant, gid=None, kalk_art="je_einheit"):
    if gid is None:
        g = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload())
        gid = g.json()["id"]
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/positionen/aus-gewerk",
                    headers=_auth(tok), json={"gewerk_id": gid, "menge": 1})
    return angebot, r.json()["positionen"][0]


def test_override_ohne_begruendung_abgelehnt(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    angebot, pos = _gewerk_position(client, tok, mandant)
    r = client.patch(
        f"/angebote/{angebot['id']}/positionen/{pos['id']}/preis-override",
        headers=_auth(tok), json={"einzelpreis": 120.0})
    assert r.status_code == 422, r.text
    assert "Begründung" in r.text


def test_override_mit_begruendung_und_angepasst_flag(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    angebot, pos = _gewerk_position(client, tok, mandant)
    r = client.patch(
        f"/angebote/{angebot['id']}/positionen/{pos['id']}/preis-override",
        headers=_auth(tok), json={"einzelpreis": 120.0, "begruendung": "Kundenwunsch"})
    assert r.status_code == 200, r.text
    body = r.json()["positionen"][0]
    assert round(body["einzelpreis"], 2) == 120.0, body
    assert body["preis_angepasst"] is True
    assert body["preis_override_begruendung"] == "Kundenwunsch"


def test_override_zurueckstellen_leert_felder(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    angebot, pos = _gewerk_position(client, tok, mandant)
    client.patch(
        f"/angebote/{angebot['id']}/positionen/{pos['id']}/preis-override",
        headers=_auth(tok), json={"einzelpreis": 120.0, "begruendung": "Kundenwunsch"})
    # exakt auf kalkulierten Wert zurückstellen
    r = client.patch(
        f"/angebote/{angebot['id']}/positionen/{pos['id']}/preis-override",
        headers=_auth(tok), json={"einzelpreis": 109.0, "begruendung": "doof"})
    assert r.status_code == 200, r.text
    body = r.json()["positionen"][0]
    assert round(body["einzelpreis"], 2) == 109.0, body
    assert body["preis_angepasst"] is False
    assert body["preis_override_begruendung"] is None


def test_manuelle_position_negative_preise_erlaubt(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok),
                    json={"bezeichnung": "Skonto", "menge": 1, "einheit": "Pauschal",
                          "einzelpreis": -15.0, "steuersatz": 19.0})
    assert r.status_code == 201, r.text
    assert r.json()["positionen"][0]["einzelpreis"] == -15.0


# --- Mandanten-Isolation (App-Layer) --------------------------------------

def test_gewerk_mandanten_isolation(client, mandant):
    m_a = mandant
    m_b = make_mandant("B")
    tok_a = _login(client, m_a, "a@t.de")
    tok_b = _login(client, m_b, "b@t.de")
    client.post("/gewerke", headers=_auth(tok_a), json=_make_gewerk_payload())
    # Mandant B sieht nichts
    lst = client.get("/gewerke", headers=_auth(tok_b)).json()
    assert lst["items"] == []
    # Mandant B darf kein fremdes Gewerk in ein Angebot übernehmen
    _, v_b = _setup_vorgang(m_b)
    ang_b = _create_angebot(client, tok_b, v_b["id"])
    # Gewerk-ID von A ermitteln
    gid_a = client.get("/gewerke", headers=_auth(tok_a)).json()["items"][0]["id"]
    r = client.post(f"/angebote/{ang_b['id']}/positionen/aus-gewerk",
                    headers=_auth(tok_b), json={"gewerk_id": gid_a, "menge": 1})
    assert r.status_code == 404, r.text


# --- Regression: BUG-1 (aus_gewerk fehlt in PositionRead) ---------------

def test_position_aus_gewerk_setzt_aus_gewerk_flag(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    g = client.post("/gewerke", headers=_auth(tok), json=_make_gewerk_payload())
    gid = g.json()["id"]
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/positionen/aus-gewerk",
                    headers=_auth(tok), json={"gewerk_id": gid, "menge": 1})
    assert r.status_code == 201, r.text if hasattr(r, "text") else r
    pos = r.json()["positionen"][0]
    # BUG-1: PositionRead muss aus_gewerk = true liefern (steuert UI Badge/Button).
    assert pos["aus_gewerk"] is True, pos
    assert pos["kalkulierter_einzelpreis"] is not None

    # Manuelle Position darf kein Gewerk-Flag setzen.
    man = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok),
                      json={"bezeichnung": "Skonto", "menge": 1, "einheit": "Pauschal",
                            "einzelpreis": -15.0, "steuersatz": 19.0})
    assert man.json()["positionen"][1]["aus_gewerk"] is False, man.json()


# --- Regression: BUG-3 (anzahl_gewerke fehlt in KategorieRead) ----------

def test_kategorie_liste_liefert_anzahl_gewerke(client, mandant):
    tok = _login(client, mandant, "b@t.de")
    r = client.post("/gewerke/kategorien", headers=_auth(tok), json={"name": "Heizung"})
    assert r.status_code == 201, r.text
    kid = r.json()["id"]

    # Leere Kategorie -> anzahl_gewerke = 0
    lst = client.get("/gewerke/kategorien", headers=_auth(tok)).json()
    heizung = next(k for k in lst if k["id"] == kid)
    assert heizung["anzahl_gewerke"] == 0, heizung

    # Gewerk in Kategorie anlegen -> Zähler steigt
    client.post("/gewerke", headers=_auth(tok),
                json={"bezeichnung": "Wartung", "einheit": "Std", "kategorie_id": kid,
                      "steuersatz": 19,
                      "kostenzeilen": [{"kostenart": "lohn", "menge": 1.0, "einheit": "Std",
                                        "ek_einzelpreis": 50.0, "zuschlag_prozent": 0.0}]})
    lst2 = client.get("/gewerke/kategorien", headers=_auth(tok)).json()
    heizung2 = next(k for k in lst2 if k["id"] == kid)
    assert heizung2["anzahl_gewerke"] == 1, heizung2
