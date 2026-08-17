from app.features.email import repository as email_repo
from app.features.email import service as email_service
from app.features.email import mailclient
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo
from conftest import make_mandant

KONTO = {
    "imap_host": "imap.x", "imap_port": 993, "imap_user": "post@shk.de",
    "imap_passwort": "encrypt:" + "A" * 44, "imap_tls": True,
    "smtp_host": "smtp.x", "smtp_port": 465, "smtp_user": "post@shk.de",
    "smtp_passwort": "encrypt:" + "A" * 44, "smtp_tls": True,
}


def _mail(absender, kennung, **kw):
    base = {
        "absender": absender, "empfaenger": "post@shk.de", "betreff": "Betreff",
        "text_html": "<p>Hi</p>", "text_plain": "Hi", "message_id": kennung,
        "in_reply_to": None, "references": None, "stabile_mail_kennung": kennung,
        "anhange": [],
    }
    base.update(kw)
    return base


def _seed_konto(mandant_id):
    email_repo.upsert_konto(
        mandant_id, KONTO["imap_host"], KONTO["imap_port"], KONTO["imap_user"],
        KONTO["imap_passwort"], True, KONTO["smtp_host"], KONTO["smtp_port"],
        KONTO["smtp_user"], KONTO["smtp_passwort"], True,
    )


def test_unknown_sender_creates_kunde_and_vorgang(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen",
                        lambda k: [_mail("neu@extern.de", "<n1@x>")])
    res = email_service.poll_postfach(mid)
    assert res["verarbeitet"] == 1
    assert kunden_repo.get_kunde_by_email(mid, "neu@extern.de")
    threads = email_repo.list_inbox(mid, True)
    assert threads and threads[0]["vorgang_id"]


def test_known_sender_no_thread_stays_unassigned(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    kunden_repo.create_kunde(mid, "Bekannt", "bekannt@extern.de", None, None)
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen",
                        lambda k: [_mail("bekannt@extern.de", "<b1@x>")])
    email_service.poll_postfach(mid)
    threads = email_repo.list_inbox(mid, False)
    assert threads and threads[0]["kunde_id"] and threads[0]["vorgang_id"] is None


def test_reply_matches_existing_thread(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    kunde = kunden_repo.create_kunde(mid, "K", "k@extern.de", None, None)
    vorgang = vorgaenge_repo.create_vorgang(mid, kunde["id"], None, "Neu", "E-Mail", "Anliegen", None)
    thread_id = email_repo.create_thread(mid, vorgang["id"], kunde["id"], "Anliegen")
    email_repo.create_nachricht(
        mid, thread_id, "ausgehend", "post@shk.de", "k@extern.de", "Anliegen",
        None, "Text", "<orig@x>", None, None, "<orig@x>", None, None,
    )
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen",
                        lambda k: [_mail("k@extern.de", "<r1@x>", in_reply_to="<orig@x>")])
    email_service.poll_postfach(mid)
    msgs = email_repo.list_thread_messages(mid, thread_id)
    assert len(msgs) == 2  # ausgehend + eingehend im selben Thread


def test_dedupe_skips_second_poll(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    mail = _mail("neu@extern.de", "<dup@x>")
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen", lambda k: [mail])
    assert email_service.poll_postfach(mid)["verarbeitet"] == 1
    assert email_service.poll_postfach(mid)["uebersprungen"] == 1


def test_html_is_sanitized(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    dirty = _mail("neu@extern.de", "<s1@x>", text_html='<p>Ok</p><img src="https://tracker.example/pixel"><script>alert(1)</script>')
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen", lambda k: [dirty])
    email_service.poll_postfach(mid)
    threads = email_repo.list_inbox(mid, True)
    nachricht = email_repo.list_thread_messages(mid, threads[0]["thread_id"])[0]
    assert "<script>" not in (nachricht["text_html"] or "")
    assert "<img" not in (nachricht["text_html"] or "")


def test_unknown_attachment_marked_unprocessed(monkeypatch):
    mid = make_mandant("A")
    _seed_konto(mid)
    mail = _mail("neu@extern.de", "<a1@x>", anhange=[{"dateiname": "x.exe", "data": b"MZ\x90\x00bad"}])
    monkeypatch.setattr(email_service.mailclient, "fetch_unseen", lambda k: [mail])
    email_service.poll_postfach(mid)
    threads = email_repo.list_inbox(mid, True)
    nachricht = email_repo.list_thread_messages(mid, threads[0]["thread_id"])[0]
    anhang = email_repo.list_anhang(mid, nachricht["id"])[0]
    assert not anhang["verarbeitet"]
    assert "nicht verarbeitet" in anhang["fehler_text"]


def test_connection_sends_smtp_probe(monkeypatch):
    sent = []

    class Imap:
        def login(self, *_): pass
        def select(self, *_): pass
        def logout(self): pass

    class Smtp:
        def login(self, *_): pass
        def send_message(self, message): sent.append(message)
        def quit(self): pass

    monkeypatch.setattr(mailclient.imaplib, "IMAP4_SSL", lambda *_: Imap())
    monkeypatch.setattr(mailclient.smtplib, "SMTP_SSL", lambda *_: Smtp())
    result = mailclient.test_connection({
        "imap_host": "imap.test", "imap_port": 993, "imap_user": "post@test.de",
        "imap_passwort": "secret", "imap_tls": True, "smtp_host": "smtp.test",
        "smtp_port": 465, "smtp_user": "post@test.de", "smtp_passwort": "secret", "smtp_tls": True,
    })
    assert result[:2] == (True, True)
    assert sent and sent[0]["To"] == "post@test.de"
