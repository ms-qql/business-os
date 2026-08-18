from app.features.angebote import repository as angebote_repo
from app.features.angebote import service as angebote_service
from app.features.email import service as email_service
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from conftest import make_mandant, make_user


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _setup_vorgang(mandant_id, email="kunde@extern.de"):
    kunde = kunden_repo.create_kunde(mandant_id, "Kunde X", email, None, None)
    vorgang = vorgaenge_repo.create_vorgang(mandant_id, kunde["id"], None, "Neu", "Sonstiges",
                                            "Heizung defekt", None)
    return kunde, vorgang


POSITION = {
    "bezeichnung": "Wartung Heizung", "menge": 2, "einheit": "Std",
    "einzelpreis": 80.0, "steuersatz": 19.0, "rabatt_typ": "prozent", "rabatt_wert": 10,
}


def _create_angebot(client, tok, vorgang_id):
    r = client.post(f"/vorgaenge/{vorgang_id}/angebote", headers=_auth(tok), json={})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_angebot_assigns_sequential_nummer(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    a1 = _create_angebot(client, tok, vorgang["id"])
    a2 = _create_angebot(client, tok, vorgang["id"])
    assert a1["angebot_nummer"] != a2["angebot_nummer"]
    assert a1["status"] == "entwurf"
    assert a1["version"] == 1


def test_monteur_forbidden(client, mandant):
    _, vorgang = _setup_vorgang(mandant)
    tok = _login(client, mandant, "monteur@shk.de", "Monteur")
    r = client.post(f"/vorgaenge/{vorgang['id']}/angebote", headers=_auth(tok), json={})
    assert r.status_code == 403


def test_position_prozent_rabatt_computes_summen(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    assert r.status_code == 201, r.text
    detail = r.json()
    # 2 * 80 = 160, -10% = 144.00 netto; Steuer 19% = 27.36; Brutto 171.36
    assert detail["netto_summe"] == 144.0
    assert detail["steuer_summe"] == 27.36
    assert detail["brutto_summe"] == 171.36
    assert detail["positionen"][0]["positions_summe"] == 144.0


def test_position_betrag_rabatt_computes_summen(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    payload = {**POSITION, "rabatt_typ": "betrag", "rabatt_wert": 20}
    r = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=payload)
    assert r.status_code == 201, r.text
    detail = r.json()
    # 160 - 20 = 140 netto; Steuer 19% = 26.60
    assert detail["netto_summe"] == 140.0
    assert detail["steuer_summe"] == 26.60


def test_rabatt_prozent_over_100_rejected(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    payload = {**POSITION, "rabatt_typ": "prozent", "rabatt_wert": 150}
    r = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=payload)
    assert r.status_code == 422


def test_rabatt_betrag_negative_positionssumme_rejected(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    payload = {**POSITION, "rabatt_typ": "betrag", "rabatt_wert": 999}
    r = client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=payload)
    assert r.status_code == 422


def test_freigabe_without_position_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    assert r.status_code == 422


def test_freigabe_without_empfaenger_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant, email=None)
    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    assert r.status_code == 422


def test_freigabe_returns_pdf_url_and_prefills_empfaenger(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["empfaenger"] == "kunde@extern.de"
    assert body["pdf_download_url"]
    assert body["brutto_summe"] == 171.36


def test_freigabe_accepts_empfaenger_betreff_override(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok),
                    json={"empfaenger": "ueberschrieben@extern.de", "betreff": "Individueller Betreff"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["empfaenger"] == "ueberschrieben@extern.de"
    assert body["betreff"] == "Individueller Betreff"


def test_senden_without_freigabe_blocked(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    r = client.post(f"/angebote/{angebot['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 422


def test_senden_success_sets_versendet_and_vorgang_status(client, mandant, monkeypatch):
    monkeypatch.setattr(email_service.mailclient, "send_message", lambda *a, **kw: "<sent@x>")
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    from app.features.email import repository as email_repo
    email_repo.upsert_konto(mandant, "imap.x", 993, "post@shk.de", "encrypt:" + "A" * 44, True,
                            "smtp.x", 465, "post@shk.de", "encrypt:" + "A" * 44, True)

    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    r = client.post(f"/angebote/{angebot['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["versendet"] is True
    assert body["angebot"]["status"] == "versendet"

    updated_vorgang = vorgaenge_repo.get_vorgang(mandant, vorgang["id"])
    assert updated_vorgang["status"] == "Angebot offen"


def test_senden_failure_keeps_entwurf(client, mandant, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(email_service.mailclient, "send_message", _boom)
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    from app.features.email import repository as email_repo
    email_repo.upsert_konto(mandant, "imap.x", 993, "post@shk.de", "encrypt:" + "A" * 44, True,
                            "smtp.x", 465, "post@shk.de", "encrypt:" + "A" * 44, True)

    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    r = client.post(f"/angebote/{angebot['id']}/senden", headers=_auth(tok), json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["versendet"] is False
    assert body["fehler_text"] == "Angebot wurde nicht versendet."
    assert body["angebot"]["status"] == "entwurf"


def test_versendetes_angebot_cannot_be_patched(client, mandant, monkeypatch):
    monkeypatch.setattr(email_service.mailclient, "send_message", lambda *a, **kw: "<sent@x>")
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    from app.features.email import repository as email_repo
    email_repo.upsert_konto(mandant, "imap.x", 993, "post@shk.de", "encrypt:" + "A" * 44, True,
                            "smtp.x", 465, "post@shk.de", "encrypt:" + "A" * 44, True)

    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    client.post(f"/angebote/{angebot['id']}/senden", headers=_auth(tok), json={})

    r = client.patch(f"/angebote/{angebot['id']}", headers=_auth(tok), json={"freitext": "geändert"})
    assert r.status_code == 409


def test_neue_version_requires_versendet_source(client, mandant):
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok, vorgang["id"])
    r = client.post(f"/angebote/{angebot['id']}/neue-version", headers=_auth(tok))
    assert r.status_code == 409


def test_neue_version_copies_positionen(client, mandant, monkeypatch):
    monkeypatch.setattr(email_service.mailclient, "send_message", lambda *a, **kw: "<sent@x>")
    tok = _login(client, mandant, "buero@shk.de")
    _, vorgang = _setup_vorgang(mandant)
    from app.features.email import repository as email_repo
    email_repo.upsert_konto(mandant, "imap.x", 993, "post@shk.de", "encrypt:" + "A" * 44, True,
                            "smtp.x", 465, "post@shk.de", "encrypt:" + "A" * 44, True)

    angebot = _create_angebot(client, tok, vorgang["id"])
    client.post(f"/angebote/{angebot['id']}/positionen", headers=_auth(tok), json=POSITION)
    client.post(f"/angebote/{angebot['id']}/freigabe", headers=_auth(tok))
    client.post(f"/angebote/{angebot['id']}/senden", headers=_auth(tok), json={})

    r = client.post(f"/angebote/{angebot['id']}/neue-version", headers=_auth(tok))
    assert r.status_code == 201, r.text
    neu = r.json()
    assert neu["version"] == 2
    assert neu["status"] == "entwurf"
    assert len(neu["positionen"]) == 1
    assert neu["angebot_nummer"] != angebot["angebot_nummer"]


def test_cross_tenant_angebot_not_visible(client, mandant):
    tok_a = _login(client, mandant, "buero-a@shk.de")
    _, vorgang_a = _setup_vorgang(mandant)
    angebot = _create_angebot(client, tok_a, vorgang_a["id"])

    mandant_b = make_mandant("B")
    tok_b = _login(client, mandant_b, "buero-b@shk.de")
    r = client.get(f"/angebote/{angebot['id']}", headers=_auth(tok_b))
    assert r.status_code == 404


def test_numbering_survives_rollback(mandant):
    # Direktes Repository-Level: next_angebot_nummer erhöht den Zähler nur bei
    # erfolgreichem Commit; zwei aufeinanderfolgende Aufrufe liefern unterschiedliche
    # Nummern und keine Lücke.
    n1 = angebote_repo.next_angebot_nummer(mandant)
    n2 = angebote_repo.next_angebot_nummer(mandant)
    assert n1 != n2
    assert n1.endswith("0001")
    assert n2.endswith("0002")


def test_totals_with_decimal_db_values(mandant):
    # DB liefert NUMERIC-Spalten als Decimal. _totals darf nicht mit
    # float += Decimal abbrechen (PROJ-Fix angebote/service.py).
    from decimal import Decimal

    positionen = [
        {"menge": Decimal("2"), "einzelpreis": Decimal("80.00"),
         "rabatt_typ": "prozent", "rabatt_wert": Decimal("10"),
         "steuersatz": Decimal("19.00")},
        {"menge": Decimal("1"), "einzelpreis": Decimal("100.00"),
         "rabatt_typ": "betrag", "rabatt_wert": Decimal("20.00"),
         "steuersatz": Decimal("19.00")},
    ]
    netto, steuer, brutto = angebote_service._totals(positionen)
    assert isinstance(netto, float) and isinstance(brutto, float)
    assert netto == 224.0  # 144 + 80
    assert brutto == 266.56  # 224 + 42.56
