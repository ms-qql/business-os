from app.features.email import repository as email_repo
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from conftest import make_mandant, make_user

KONTO = {
    "imap_host": "imap.example.de", "imap_port": 993, "imap_user": "post@shk.de",
    "imap_passwort": "secret", "imap_tls": True, "smtp_host": "smtp.example.de",
    "smtp_port": 465, "smtp_user": "post@shk.de", "smtp_passwort": "secret",
    "smtp_tls": True,
}


def _login(client, mandant, email, role="Buero"):
    make_user(mandant, email, role)
    r = client.post("/auth/login", json={"email": email, "password": "startpasswort123"})
    return r.json()["access_token"]


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def _make_kunde_und_vorgang(client, tok, mandant, email="kunde@extern.de"):
    kr = client.post("/kunden", headers=_auth(tok), json={"name": "Kunde", "email": email})
    kunde_id = kr.json()["id"]
    vr = client.post("/vorgaenge", headers=_auth(tok),
                     json={"kunde_id": kunde_id, "anliegen": "Heizung", "quelle": "E-Mail",
                           "status": "Neu"})
    return kunde_id, vr.json()["id"]


# --- Postfach-Konto --------------------------------------------------------

def test_inhaber_saves_and_reads_konto(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.put("/email-konto", headers=_auth(tok), json=KONTO)
    assert r.status_code == 200, r.text
    assert r.json()["imap_user"] == "post@shk.de"
    assert "imap_passwort" not in r.json()

    r2 = client.get("/email-konto", headers=_auth(tok))
    assert r2.status_code == 200
    assert r2.json()["imap_host"] == "imap.example.de"


def test_konto_update_keeps_password_when_omitted(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    assert client.put("/email-konto", headers=_auth(tok), json=KONTO).status_code == 200
    update = {key: value for key, value in KONTO.items() if "passwort" not in key}
    update["imap_tls"] = False
    update["smtp_tls"] = False
    r = client.put("/email-konto", headers=_auth(tok), json=update)
    assert r.status_code == 200, r.text
    assert not r.json()["imap_tls"] and not r.json()["smtp_tls"]


def test_buero_cannot_put_konto(client, mandant):
    tok = _login(client, mandant, "buero@shk.de", "Buero")
    r = client.put("/email-konto", headers=_auth(tok), json=KONTO)
    assert r.status_code == 403


def test_get_konto_404_when_none(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/email-konto", headers=_auth(tok))
    assert r.status_code == 404


def test_tenant_isolation_konto(client):
    a = make_mandant("A")
    b = make_mandant("B")
    tok_a = _login(client, a, "a@shk.de", "Inhaber")
    client.put("/email-konto", headers=_auth(tok_a), json=KONTO)
    tok_b = _login(client, b, "b@shk.de", "Inhaber")
    assert client.get("/email-konto", headers=_auth(tok_b)).status_code == 404


# --- Inbox / Zuordnung -----------------------------------------------------

def test_inbox_empty_without_konto(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    r = client.get("/email/inbox", headers=_auth(tok))
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_zuordnen_nachricht_zu_vorgang(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    _, vorgang_id = _make_kunde_und_vorgang(client, tok, mandant)

    thread_id = email_repo.create_thread(mandant, None, None, "Frage")
    nachricht = email_repo.create_nachricht(
        mandant, thread_id, "eingehend", "kunde@extern.de", "post@shk.de", "Frage",
        "<p>Hi</p>", "Hi", None, None, None, "<m1@x>", None, None,
    )

    r = client.post(f"/email/nachrichten/{nachricht['id']}/zuordnen", headers=_auth(tok),
                    json={"vorgang_id": vorgang_id})
    assert r.status_code == 200, r.text
    assert r.json()["vorgang_id"] == vorgang_id

    inbox = client.get("/email/inbox?zugeordnet=true", headers=_auth(tok)).json()
    assert inbox["items"][0]["thread_id"] == thread_id


def test_nachricht_zu_vorgang_legt_neuen_vorgang_an(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    thread_id = email_repo.create_thread(mandant, None, None, "Neue Anfrage")
    nachricht = email_repo.create_nachricht(
        mandant, thread_id, "eingehend", "neu@extern.de", "post@shk.de", "Neue Anfrage",
        None, "Text", None, None, None, "<m2@x>", None, None,
    )
    r = client.post(f"/email/nachrichten/{nachricht['id']}/vorgang", headers=_auth(tok),
                    json={"anliegen": "Neue Anfrage"})
    assert r.status_code == 200, r.text
    assert r.json()["vorgang_id"] is not None
    # Neuer Kunde aus unbekanntem Absender angelegt.
    assert kunden_repo.get_kunde_by_email(mandant, "neu@extern.de")


def test_zuordnen_fremder_vorgang_404(client, mandant):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    thread_id = email_repo.create_thread(mandant, None, None, "X")
    nachricht = email_repo.create_nachricht(
        mandant, thread_id, "eingehend", "a@b.de", "post@shk.de", "X", None, "x",
        None, None, None, "<m3@x>", None, None,
    )
    r = client.post(f"/email/nachrichten/{nachricht['id']}/zuordnen", headers=_auth(tok),
                    json={"vorgang_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404


# --- Senden ----------------------------------------------------------------

def test_send_ohne_konto_422(client, mandant, monkeypatch):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    _, vorgang_id = _make_kunde_und_vorgang(client, tok, mandant)
    r = client.post(f"/vorgaenge/{vorgang_id}/emails", headers=_auth(tok),
                    json={"empfaenger": "kunde@extern.de", "betreff": "Antwort",
                          "text": "Hallo"})
    assert r.status_code == 422


def test_send_happy(client, mandant, monkeypatch):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    client.put("/email-konto", headers=_auth(tok), json=KONTO)
    _, vorgang_id = _make_kunde_und_vorgang(client, tok, mandant)

    captured = {}

    def fake_send(konto, to, subject, body, in_reply_to=None, references=None,
                  message_id=None):
        captured["to"] = to
        captured["subject"] = subject
        return "<sent@x>"

    monkeypatch.setattr("app.features.email.service.mailclient.send_message", fake_send)

    r = client.post(f"/vorgaenge/{vorgang_id}/emails", headers=_auth(tok),
                    json={"empfaenger": "kunde@extern.de", "betreff": "Antwort",
                          "text": "Hallo"})
    assert r.status_code == 201, r.text
    assert captured["to"] == "kunde@extern.de"
    assert r.json()["richtung"] == "ausgehend"

    # Nachricht erscheint im Vorgang-Thread.
    emails = client.get(f"/vorgaenge/{vorgang_id}/emails", headers=_auth(tok)).json()
    assert emails and emails[0]["nachrichten"]


def test_send_uses_vorgang_kunde_email_when_omitted(client, mandant, monkeypatch):
    tok = _login(client, mandant, "inh@shk.de", "Inhaber")
    client.put("/email-konto", headers=_auth(tok), json=KONTO)
    _, vorgang_id = _make_kunde_und_vorgang(client, tok, mandant)
    monkeypatch.setattr("app.features.email.service.mailclient.send_message", lambda *args, **kwargs: "<sent@x>")
    r = client.post(f"/vorgaenge/{vorgang_id}/emails", headers=_auth(tok),
                    json={"betreff": "Antwort", "text": "Hallo"})
    assert r.status_code == 201, r.text
    assert r.json()["empfaenger"] == "kunde@extern.de"
