from __future__ import annotations

import uuid

from app import storage as storage_mod
from app.crypto import decrypt_secret, encrypt_secret
from app.errors import NotFoundError, ValidationError
from app.features.email import repository as repo
from app.features.email import mailclient
from app.features.kunden import repository as kunden_repo
from app.features.vorgaenge import repository as vorgaenge_repo

MAX_EMAIL_ANHANG_BYTES = 25 * 1024 * 1024


# --- Postfach-Konto --------------------------------------------------------

def get_konto_read(mandant_id: str) -> dict:
    konto = repo.get_konto(mandant_id)
    if not konto:
        raise NotFoundError("Es ist noch kein Postfach verbunden.")
    konto.pop("imap_passwort", None)
    konto.pop("smtp_passwort", None)
    return konto


def save_konto(mandant_id: str, cfg) -> dict:
    existing = repo.get_konto(mandant_id)
    if not existing and not cfg.imap_passwort:
        raise ValidationError("IMAP-Passwort ist erforderlich.")
    konto = repo.upsert_konto(
        mandant_id, cfg.imap_host, cfg.imap_port, cfg.imap_user,
        encrypt_secret(cfg.imap_passwort) if cfg.imap_passwort else existing["imap_passwort"], cfg.imap_tls,
        cfg.smtp_host, cfg.smtp_port, cfg.smtp_user,
        encrypt_secret(cfg.smtp_passwort) if cfg.smtp_passwort else (existing.get("smtp_passwort") if existing else None),
        cfg.smtp_tls,
    )
    konto.pop("imap_passwort", None)
    konto.pop("smtp_passwort", None)
    return konto


def test_konto(cfg) -> dict:
    konto = {
        "imap_host": cfg.imap_host, "imap_port": cfg.imap_port,
        "imap_user": cfg.imap_user, "imap_passwort": cfg.imap_passwort,
        "imap_tls": cfg.imap_tls, "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port,
        "smtp_user": cfg.smtp_user or cfg.imap_user,
        "smtp_passwort": cfg.smtp_passwort or cfg.imap_passwort,
        "smtp_tls": cfg.smtp_tls,
    }
    imap_ok, smtp_ok, detail = mailclient.test_connection(konto)
    return {
        "ok": imap_ok and smtp_ok,
        "imap_ok": imap_ok,
        "smtp_ok": smtp_ok,
        "detail": detail,
    }


# --- Inbox / Nachrichten ---------------------------------------------------

def get_inbox(mandant_id: str, zugeordnet: bool | None) -> dict:
    konto = repo.get_konto(mandant_id)
    items = [
        {
            "thread_id": r["thread_id"],
            "betreff": r["betreff"],
            "absender": r["absender"],
            "empfaenger": r["empfaenger"],
            "vorgang_id": r["vorgang_id"],
            "kunde_id": r["kunde_id"],
            "letzte_nachricht_am": r["letzte_nachricht_am"],
            "letzte_nachricht_id": r["letzte_nachricht_id"],
        }
        for r in repo.list_inbox(mandant_id, zugeordnet)
    ]
    return {
        "items": items,
        "konto_status": konto.get("letzter_abruf_status") if konto else None,
        "konto_fehler_text": konto.get("letzter_abruf_fehler_text") if konto else None,
    }


def get_nachricht(mandant_id: str, nachricht_id: str) -> dict:
    nachricht = repo.get_nachricht(mandant_id, nachricht_id)
    if not nachricht:
        raise NotFoundError("Nachricht nicht gefunden.")
    anhaenge = [_anhang_read(a) for a in repo.list_anhang(mandant_id, nachricht_id)]
    thread = repo.get_thread(mandant_id, nachricht["thread_id"])
    return {**nachricht, "vorgang_id": thread.get("vorgang_id") if thread else None,
            "kunde_id": thread.get("kunde_id") if thread else None, "anhaenge": anhaenge}


def zuordnen(mandant_id: str, nachricht_id: str, vorgang_id: str) -> dict:
    nachricht = repo.get_nachricht(mandant_id, nachricht_id)
    if not nachricht:
        raise NotFoundError("Nachricht nicht gefunden.")
    if not vorgaenge_repo.get_vorgang(mandant_id, vorgang_id):
        raise NotFoundError("Vorgang nicht gefunden.")
    repo.assign_thread(mandant_id, nachricht["thread_id"], vorgang_id)
    thread = repo.get_thread(mandant_id, nachricht["thread_id"])
    vorgaenge_repo.add_historie(
        mandant_id, vorgang_id, "email_zugeordnet", nachricht["betreff"] or "", None,
    )
    return thread


def nachricht_zu_vorgang(mandant_id: str, nachricht_id: str, payload) -> dict:
    nachricht = repo.get_nachricht(mandant_id, nachricht_id)
    if not nachricht:
        raise NotFoundError("Nachricht nicht gefunden.")
    if repo.get_thread(mandant_id, nachricht["thread_id"]).get("vorgang_id"):
        raise ValidationError("Diese Nachricht ist bereits einem Vorgang zugeordnet.")

    absender = nachricht["absender"]
    kunde = kunden_repo.get_kunde_by_email(mandant_id, absender)
    if not kunde:
        kunde = kunden_repo.create_kunde(
            mandant_id, payload.kunde_name or absender, absender, None, None,
        )
    vorgang = vorgaenge_repo.create_vorgang(
        mandant_id, kunde["id"], None, "Neu", "E-Mail",
        payload.anliegen or nachricht["betreff"] or "(ohne Betreff)", None,
    )
    repo.assign_thread(mandant_id, nachricht["thread_id"], vorgang["id"])
    vorgaenge_repo.add_historie(
        mandant_id, vorgang["id"], "email_empfangen", nachricht["betreff"] or "", None,
    )
    return repo.get_thread(mandant_id, nachricht["thread_id"])


def list_vorgang_emails(mandant_id: str, vorgang_id: str) -> list[dict]:
    if not vorgaenge_repo.get_vorgang(mandant_id, vorgang_id):
        raise NotFoundError("Vorgang nicht gefunden.")
    threads = []
    for thread in repo.list_threads_for_vorgang(mandant_id, vorgang_id):
        messages = [
            {**m, "anhaenge": [_anhang_read(a) for a in repo.list_anhang(mandant_id, m["id"])]}
            for m in repo.list_thread_messages(mandant_id, thread["id"])
        ]
        threads.append({**thread, "nachrichten": messages})
    return threads


# --- Senden ----------------------------------------------------------------

def send_vorgang_email(user, vorgang_id: str, compose) -> dict:
    vorgang = vorgaenge_repo.get_vorgang(user.mandant_id, vorgang_id)
    if not vorgang:
        raise NotFoundError("Vorgang nicht gefunden.")
    konto = repo.get_konto(user.mandant_id)
    if not konto:
        raise ValidationError("Es ist kein Postfach verbunden.")
    empfaenger = compose.empfaenger
    if not empfaenger:
        kunde = kunden_repo.get_kunde(user.mandant_id, vorgang["kunde_id"])
        empfaenger = kunde.get("email") if kunde else None
    if not empfaenger:
        raise ValidationError("Der Vorgangskunde hat keine E-Mail-Adresse.")

    in_reply_to = None
    references = None
    if compose.antwort_an_nachricht_id:
        orig = repo.get_nachricht(user.mandant_id, compose.antwort_an_nachricht_id)
        if orig:
            in_reply_to = orig.get("message_id")
            refs = (orig.get("referenzen") or "").split()
            if orig.get("message_id"):
                refs.append(orig["message_id"])
            references = " ".join(refs) or None

    decrypted = mailclient.decrypt_konto(konto)
    message_id = mailclient.send_message(
        decrypted, empfaenger, compose.betreff, compose.text,
        in_reply_to=in_reply_to, references=references,
    )

    thread = repo.find_thread_for_vorgang(user.mandant_id, vorgang_id)
    if not thread:
        thread_id = repo.create_thread(user.mandant_id, vorgang_id, vorgang.get("kunde_id"),
                                       compose.betreff)
    else:
        thread_id = thread["id"]

    nachricht = repo.create_nachricht(
        user.mandant_id, thread_id, "ausgehend", decrypted["smtp_user"],
        empfaenger, compose.betreff, None, compose.text, message_id,
        in_reply_to, references, message_id, user.id, None,
    )
    vorgaenge_repo.add_historie(
        user.mandant_id, vorgang_id, "email_gesendet", compose.betreff, user.id,
    )
    return nachricht


def get_download_url(user, vorgang_id: str, email_id: str, anhang_id: str) -> str:
    if not vorgaenge_repo.get_vorgang(user.mandant_id, vorgang_id):
        raise NotFoundError("Vorgang nicht gefunden.")
    nachricht = repo.get_nachricht(user.mandant_id, email_id)
    if not nachricht:
        raise NotFoundError("Nachricht nicht gefunden.")
    anhang = repo.get_anhang(user.mandant_id, email_id, anhang_id)
    if not anhang:
        raise NotFoundError("Anhang nicht gefunden.")
    if not anhang["verarbeitet"]:
        raise ValidationError("Anhang konnte nicht verarbeitet werden.")
    return storage_mod.storage.presigned_get_url(anhang["objektpfad"])


# --- Interner Abruf (Dokploy-Cron) ----------------------------------------

def poll_postfach(mandant_id: str) -> dict:
    konto = repo.get_konto(mandant_id)
    if not konto:
        return {"verarbeitet": 0, "uebersprungen": 0}
    decrypted = mailclient.decrypt_konto(konto)
    try:
        mails = mailclient.fetch_unseen(decrypted)
    except Exception as exc:  # noqa: BLE001
        repo.update_abruf_status(mandant_id, "fehler", str(exc)[:500])
        return {"verarbeitet": 0, "uebersprungen": 0, "fehler": str(exc)[:500]}

    verarbeitet = 0
    uebersprungen = 0
    for mail in mails:
        kennung = mail.get("stabile_mail_kennung")
        if repo.message_exists(mandant_id, kennung):
            uebersprungen += 1
            continue
        _eingehend_speichern(mandant_id, mail)
        verarbeitet += 1

    repo.update_abruf_status(mandant_id, "ok", None)
    return {"verarbeitet": verarbeitet, "uebersprungen": uebersprungen}


def _eingehend_speichern(mandant_id: str, mail: dict) -> None:
    # Drei-Stufen-Zuordnung (Tech Design D).
    thread_id = _bestimme_thread(mandant_id, mail)
    text_html = mailclient.sanitize_html(mail.get("text_html") or "")
    nachricht = repo.create_nachricht(
        mandant_id, thread_id, "eingehend", mail["absender"], mail["empfaenger"],
        mail.get("betreff"), text_html, mail.get("text_plain"),
        mail.get("message_id"), mail.get("in_reply_to"), mail.get("references"),
        mail.get("stabile_mail_kennung"), None, None,
    )
    _anhange_speichern(mandant_id, nachricht["id"], mail.get("anhange", []))

    thread = repo.get_thread(mandant_id, thread_id)
    if thread and thread.get("vorgang_id"):
        vorgaenge_repo.add_historie(
            mandant_id, thread["vorgang_id"], "email_empfangen",
            mail.get("betreff") or "", None,
        )


def _bestimme_thread(mandant_id: str, mail: dict) -> str:
    # (1) Thread-Treffer über In-Reply-To / References.
    kandidaten = []
    if mail.get("in_reply_to"):
        kandidaten.append(mail["in_reply_to"])
    if mail.get("references"):
        kandidaten.extend(mail["references"].split())
    treffer = repo.find_message_by_message_id(mandant_id, kandidaten)
    if treffer:
        return treffer["thread_id"]

    absender = mail["absender"]
    # (2) Unbekannter Absender -> neuer Kunde + neuer Vorgang.
    if not kunden_repo.get_kunde_by_email(mandant_id, absender):
        kunde = kunden_repo.create_kunde(mandant_id, absender, absender, None, None)
        vorgang = vorgaenge_repo.create_vorgang(
            mandant_id, kunde["id"], None, "Neu", "E-Mail",
            mail.get("betreff") or "(ohne Betreff)", None,
        )
        return repo.create_thread(mandant_id, vorgang["id"], kunde["id"], mail.get("betreff"))

    # (3) Bekannter Absender ohne Thread-Treffer -> unzugeordnet in der Inbox.
    return repo.create_thread(
        mandant_id, None,
        kunden_repo.get_kunde_by_email(mandant_id, absender)["id"], mail.get("betreff"),
    )


def _anhange_speichern(mandant_id: str, nachricht_id: str, anhaenge: list[dict]) -> None:
    for a in anhaenge:
        data = a.get("data") or b""
        sniffed = mailclient._sniff(data)
        if not sniffed or len(data) > MAX_EMAIL_ANHANG_BYTES:
            repo.create_anhang(
                mandant_id, nachricht_id, a.get("dateiname", "anhang"), "",
                "application/octet-stream", len(data), False,
                "Anhang konnte nicht verarbeitet werden."
                if not sniffed else "Anhang ist zu groß.",
            )
            continue
        ext, content_type = sniffed
        objektpfad = f"email/{mandant_id}/{nachricht_id}/{uuid.uuid4()}.{ext}"
        storage_mod.storage.put_object(objektpfad, data, content_type)
        repo.create_anhang(
            mandant_id, nachricht_id, a.get("dateiname", f"anhang.{ext}"), objektpfad,
            content_type, len(data), True, None,
        )


def _anhang_read(a: dict) -> dict:
    return {
        "id": a["id"], "dateiname": a["dateiname"], "content_type": a["content_type"],
        "groesse_bytes": a["groesse_bytes"], "verarbeitet": a["verarbeitet"],
        "fehler_text": a.get("fehler_text"),
    }
