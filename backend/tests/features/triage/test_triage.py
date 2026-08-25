from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from conftest import make_domain, make_mandant, make_user

from app import db


def _auth(client, mandant_id, email, role):
    make_user(mandant_id, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_shk(client, headers):
    r = client.post("/formulare", json={"vorlage": "shk"}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _publish(client, headers, formular_id, draft_revision):
    r = client.post(f"/formulare/{formular_id}/veroeffentlichen",
                    json={"draft_revision": draft_revision}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _add_schritt(client, headers, fid, titel, rev):
    r = client.post(f"/formulare/{fid}/schritte",
                    json={"titel": titel, "draft_revision": rev}, headers=headers)
    assert r.status_code == 200
    return r


def _add_dropdown(client, headers, fid, sid, rev):
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder",
                    json={"typ": "dropdown", "draft_revision": rev}, headers=headers)
    assert r.status_code == 200
    return r


def _add_date(client, headers, fid, sid, rev):
    r = client.post(f"/formulare/{fid}/schritte/{sid}/felder",
                    json={"typ": "datum", "draft_revision": rev}, headers=headers)
    assert r.status_code == 200
    return r


def _patch_feld(client, headers, fid, sid, feld_id, body):
    r = client.patch(f"/formulare/{fid}/schritte/{sid}/felder/{feld_id}", json=body,
                     headers=headers)
    assert r.status_code == 200, r.text
    return r


def _publish_with_leistung_und_termin(client, headers):
    """Baut ein veröffentlichtes Formular mit Dropdown-Leistung + Datums-Wunschtermin
    und liefert (formular_id, public_id, snapshot_felder_by_label)."""
    f = _create_shk(client, headers)
    fid = f["id"]
    # Schritt + Dropdown 'Leistung'.
    r = _add_schritt(client, headers, fid, "Leistung", f["draft_revision"])
    rev = r.json()["draft_revision"]
    sid = r.json()["schritte"][-1]["id"]
    r = _add_dropdown(client, headers, fid, sid, rev)
    rev = r.json()["draft_revision"]
    leistung_f = r.json()["schritte"][-1]["felder"][-1]["id"]
    r = _patch_feld(client, headers, fid, sid, leistung_f, {
        "label": "Leistung", "pflichtfeld": True, "optional_in_einfach": False,
        "uebernahme": None,
        "optionen": [{"label": "Heizung", "wert": "heizung"},
                     {"label": "Sanitaer", "wert": "sanitaer"},
                     {"label": "Sonstiges", "wert": "sonstiges"}],
        "draft_revision": rev})
    rev = r.json()["draft_revision"]
    # Datumsfeld 'Wunschtermin'.
    r = _add_date(client, headers, fid, sid, rev)
    rev = r.json()["draft_revision"]
    termin_f = r.json()["schritte"][-1]["felder"][-1]["id"]
    r = _patch_feld(client, headers, fid, sid, termin_f, {
        "label": "Wunschtermin", "pflichtfeld": False, "optional_in_einfach": False,
        "uebernahme": None, "draft_revision": rev})
    rev = r.json()["draft_revision"]
    pub = _publish(client, headers, fid, rev)
    public_id = pub["public_id"]
    snap = client.get(f"/formulare/{fid}/veroeffentlichte-version", headers=headers).json()
    felder = {fld["label"]: fld for s in snap["schritte"] for fld in s["felder"]}
    return fid, public_id, felder


def _submit(client, public_id, hostname, werte, kennung=None):
    if kennung is None:
        kennung = f"kenn-{public_id[:8]}-{uuid.uuid4().hex[:8]}"
    payload = {
        "uebermittlungskennung": kennung,
        "client_start": (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        "honeypot": "", "werte": werte,
    }
    r = client.post(f"/public/formulare/{public_id}/einsendungen",
                    json=payload, headers={"Host": hostname})
    assert r.status_code == 201, r.text
    return kennung


def _vorgang_id_for_kennung(client, mandant_id, kennung):
    return db.engine.query(
        "SELECT vorgang_id FROM formular_einsendung WHERE mandant_id = %s "
        "AND uebermittlungskennung = %s",
        (mandant_id, kennung), mandant_id=mandant_id)[0]["vorgang_id"]


# --- Einstellungen (GET / PUT / PATCH) ------------------------------------


def test_einstellung_leer_ohne_zeile(client):
    m = make_mandant()
    h = _auth(client, m, "buero@t.de", "Buero")
    r = client.get("/triage/einstellung", headers=h)
    assert r.status_code == 200
    assert r.json() == {"leistungs_formular_id": None, "leistungs_feld_id": None,
                        "wunschtermin_feld_id": None, "naechster_freier_termin": None,
                        "werte": []}


def test_put_einstellung_als_buero_403(client):
    m = make_mandant()
    h = _auth(client, m, "buero@t.de", "Buero")
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": "x", "leistungs_feld_id": "y", "werte": []}, headers=h)
    assert r.status_code == 403


def test_put_und_patch_kapazitaet(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h_inh = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h_inh)
    leistung_f = felder["Leistung"]["id"]
    termin_f = felder["Wunschtermin"]["id"]

    # Leistungsfeld referenziert nicht veröffentlichtes Formular -> 404.
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": "00000000-0000-0000-0000-000000000000",
        "leistungs_feld_id": leistung_f, "werte": []}, headers=h_inh)
    assert r.status_code == 404

    # Gültige Konfiguration.
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "wunschtermin_feld_id": termin_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"},
                  {"wert": "sanitaer", "klassifikation": "unpassend"}]}, headers=h_inh)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["leistungs_feld_id"] == leistung_f
    assert body["wunschtermin_feld_id"] == termin_f
    assert {w["wert"]: w["klassifikation"] for w in body["werte"]} == {
        "heizung": "passend", "sanitaer": "unpassend"}

    # Wert, der keine Option des Feldes ist -> 422.
    r = client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "nicht_existent", "klassifikation": "passend"}]}, headers=h_inh)
    assert r.status_code == 422

    # Kapazität setzen.
    r = client.patch("/triage/einstellung/kapazitaet",
                     json={"naechster_freier_termin": "2026-09-12"}, headers=h_inh)
    assert r.status_code == 200
    assert r.json()["naechster_freier_termin"] == "2026-09-12"
    # Büro darf Kapazität nicht setzen.
    h_buero = _auth(client, m, "buero@t.de", "Buero")
    r = client.patch("/triage/einstellung/kapazitaet",
                     json={"naechster_freier_termin": "2026-10-01"}, headers=h_buero)
    assert r.status_code == 403
    # Aber lesen.
    r = client.get("/triage/einstellung", headers=h_buero)
    assert r.status_code == 200
    assert r.json()["naechster_freier_termin"] == "2026-09-12"
    # Kapazität entfernen (null).
    r = client.patch("/triage/einstellung/kapazitaet",
                     json={"naechster_freier_termin": None}, headers=h_inh)
    assert r.status_code == 200
    assert r.json()["naechster_freier_termin"] is None


# --- Veröffentlichte Version (GET) ----------------------------------------


def test_veroeffentlichte_version_404_unpublished(client):
    m = make_mandant()
    h = _auth(client, m, "inhaber@t.de", "Inhaber")
    f = _create_shk(client, h)
    r = client.get(f"/formulare/{f['id']}/veroeffentlichte-version", headers=h)
    assert r.status_code == 404


def test_veroeffentlichte_version_liefert_snapshot(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h)
    r = client.get(f"/formulare/{fid}/veroeffentlichte-version", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["modus"] in ("einfach", "erweitert")
    labels = [fld["label"] for s in body["schritte"] for fld in s["felder"]]
    assert "Leistung" in labels


# --- Triage-Berechnung in Vorgangslisten/-detail --------------------------


def test_triage_gruen_gelb_rot_nicht_bewertet(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h)
    leistung_f = felder["Leistung"]["id"]
    termin_f = felder["Wunschtermin"]["id"]

    # Konfiguration: heizung=passend, sanitaer=unpassend; Kapazität 2026-09-12.
    client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "wunschtermin_feld_id": termin_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"},
                  {"wert": "sanitaer", "klassifikation": "unpassend"}]}, headers=h)
    client.patch("/triage/einstellung/kapazitaet",
                 json={"naechster_freier_termin": "2026-09-12"}, headers=h)

    def submit(leistung, wunsch=None, dringlich=False):
        werte = [
            {"feld_id": felder["Ihr Name"]["id"], "wert": "Max"},
            {"feld_id": felder["E-Mail"]["id"], "wert": "max@x.de"},
            {"feld_id": felder["Telefon"]["id"], "wert": ""},
            {"feld_id": felder["Adresse"]["id"], "wert": ""},
            {"feld_id": felder["Ihr Anliegen"]["id"], "wert": "Termin"},
            {"feld_id": felder["Datenschutz"]["id"], "wert": "true"},
            {"feld_id": leistung_f, "werte": [leistung]},
        ]
        if wunsch:
            werte.append({"feld_id": termin_f, "datum": wunsch})
        kennung = _submit(client, public_id, "a.de", werte)
        # Dringlichkeit ggf. setzen.
        if dringlich:
            aid = db.engine.query(
                "SELECT a.id FROM anfrage a JOIN formular_einsendung fe ON fe.anfrage_id = a.id "
                "WHERE fe.mandant_id = %s AND fe.uebermittlungskennung = %s",
                (m, kennung), mandant_id=m)[0]["id"]
            db.engine.command("UPDATE anfrage SET dringlichkeit = 'Dringend' WHERE id = %s",
                              (aid,), mandant_id=m)
        return _vorgang_id_for_kennung(client, m, kennung)

    v_gruen = submit("heizung", wunsch="2026-10-01")
    v_rot = submit("sanitaer")
    v_gelb_datum = submit("heizung", wunsch="2026-09-01")
    v_gelb_dringend = submit("heizung", dringlich=True)

    r = client.get("/vorgaenge", headers=h)
    assert r.status_code == 200
    items = {it["id"]: it["triage"]["status"] for it in r.json()["items"]}
    assert items[v_gruen] == "gruen"
    assert items[v_rot] == "rot"
    assert items[v_gelb_datum] == "gelb"
    assert items[v_gelb_dringend] == "gelb"

    # Detail liefert Gründe.
    r = client.get(f"/vorgaenge/{v_rot}", headers=h)
    assert r.status_code == 200
    assert r.json()["triage"]["status"] == "rot"
    assert any("nicht passend" in g for g in r.json()["triage"]["gruende"])

    r = client.get(f"/vorgaenge/{v_gelb_datum}", headers=h)
    assert "vor 12.09.2026" in "".join(r.json()["triage"]["gruende"])


def test_triage_nicht_bewertet_ohne_grundlage(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h)
    leistung_f = felder["Leistung"]["id"]

    # Vorgang direkt angelegt (keine Formular-Einsendung) -> nicht_bewertet.
    kunde_r = client.post("/kunden", json={"name": "Direkt", "email": "d@x.de"}, headers=h)
    assert kunde_r.status_code == 201, kunde_r.text
    kid = kunde_r.json()["id"]
    v_r = client.post("/vorgaenge", json={"kunde_id": kid, "anliegen": "Direkt"},
                      headers=h)
    assert v_r.status_code == 201
    vid = v_r.json()["id"]
    r = client.get(f"/vorgaenge/{vid}", headers=h)
    assert r.status_code == 200
    assert r.json()["triage"]["status"] == "nicht_bewertet"

    # Einsendung mit Leistungswert, der NICHT konfiguriert ist -> nicht_bewertet.
    client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"}]}, headers=h)
    werte = [
        {"feld_id": felder["Ihr Name"]["id"], "wert": "Max"},
        {"feld_id": felder["E-Mail"]["id"], "wert": "max@x.de"},
        {"feld_id": felder["Telefon"]["id"], "wert": ""},
        {"feld_id": felder["Adresse"]["id"], "wert": ""},
        {"feld_id": felder["Ihr Anliegen"]["id"], "wert": "Termin"},
        {"feld_id": felder["Datenschutz"]["id"], "wert": "true"},
        {"feld_id": leistung_f, "werte": ["sonstiges"]},  # gültige Option, aber nicht konfiguriert
    ]
    kennung = _submit(client, public_id, "a.de", werte)
    vid2 = _vorgang_id_for_kennung(client, m, kennung)
    r = client.get(f"/vorgaenge/{vid2}", headers=h)
    assert r.json()["triage"]["status"] == "nicht_bewertet"
    assert any("nicht konfiguriert" in g for g in r.json()["triage"]["gruende"])


def test_triage_filter_und_sort(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h)
    leistung_f = felder["Leistung"]["id"]
    client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"},
                  {"wert": "sanitaer", "klassifikation": "unpassend"}]}, headers=h)
    client.patch("/triage/einstellung/kapazitaet",
                 json={"naechster_freier_termin": "2026-09-12"}, headers=h)

    def submit(leistung):
        werte = [
            {"feld_id": felder["Ihr Name"]["id"], "wert": "Max"},
            {"feld_id": felder["E-Mail"]["id"], "wert": "max@x.de"},
            {"feld_id": felder["Telefon"]["id"], "wert": ""},
            {"feld_id": felder["Adresse"]["id"], "wert": ""},
            {"feld_id": felder["Ihr Anliegen"]["id"], "wert": "Termin"},
            {"feld_id": felder["Datenschutz"]["id"], "wert": "true"},
            {"feld_id": leistung_f, "werte": [leistung]},
        ]
        kennung = _submit(client, public_id, "a.de", werte)
        return _vorgang_id_for_kennung(client, m, kennung)

    submit("heizung")  # grün
    submit("sanitaer")  # rot
    submit("sanitaer")  # rot

    # Filter rot.
    r = client.get("/vorgaenge?triage=rot", headers=h)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 2
    assert all(it["triage"]["status"] == "rot" for it in items)
    # Ungültiger Filter -> 422.
    r = client.get("/vorgaenge?triage=blau", headers=h)
    assert r.status_code == 422
    # Sortierung ampel: rot zuerst.
    r = client.get("/vorgaenge?sort=ampel", headers=h)
    assert r.status_code == 200
    stats = [it["triage"]["status"] for it in r.json()["items"]]
    assert stats.index("rot") < stats.index("gruen") or "gruen" not in stats


def test_triage_unsichtbar_fuer_monteur(client):
    m = make_mandant()
    make_domain(m, "a.de")
    h_inh = _auth(client, m, "inhaber@t.de", "Inhaber")
    fid, public_id, felder = _publish_with_leistung_und_termin(client, h_inh)
    leistung_f = felder["Leistung"]["id"]
    client.put("/triage/einstellung", json={
        "leistungs_formular_id": fid, "leistungs_feld_id": leistung_f,
        "werte": [{"wert": "heizung", "klassifikation": "passend"},
                  {"wert": "sanitaer", "klassifikation": "unpassend"}]}, headers=h_inh)
    werte = [
        {"feld_id": felder["Ihr Name"]["id"], "wert": "Max"},
        {"feld_id": felder["E-Mail"]["id"], "wert": "max@x.de"},
        {"feld_id": felder["Telefon"]["id"], "wert": ""},
        {"feld_id": felder["Adresse"]["id"], "wert": ""},
        {"feld_id": felder["Ihr Anliegen"]["id"], "wert": "Termin"},
        {"feld_id": felder["Datenschutz"]["id"], "wert": "true"},
        {"feld_id": leistung_f, "werte": ["heizung"]},
    ]
    kennung = _submit(client, public_id, "a.de", werte)
    vid = _vorgang_id_for_kennung(client, m, kennung)
    # Vorgang dem Monteur zuweisen.
    h_mont = _auth(client, m, "mont@t.de", "Monteur")
    mid = db.engine.query("SELECT id FROM nutzer WHERE mandant_id = %s AND email = %s",
                          (m, "mont@t.de"), mandant_id=m)[0]["id"]
    db.engine.command("UPDATE vorgang SET zugewiesener_nutzer_id = %s WHERE id = %s",
                      (mid, vid), mandant_id=m)
    r = client.get(f"/vorgaenge/{vid}", headers=h_mont)
    assert r.status_code == 200
    assert r.json().get("triage") is None
    r = client.get("/vorgaenge", headers=h_mont)
    assert r.status_code == 200
    assert all(it.get("triage") is None for it in r.json()["items"])
    # Monteur darf Triage-Endpunkte nicht nutzen.
    r = client.get("/triage/einstellung", headers=h_mont)
    assert r.status_code == 403
