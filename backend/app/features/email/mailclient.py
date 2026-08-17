from __future__ import annotations

import email
import imaplib
import smtplib
import uuid
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

import bleach

from app.crypto import decrypt_secret

# Allow-List für HTML-Bereinigung — kein Script/Tracking im Frontend.
_ALLOWED_TAGS = [
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "li", "ol", "p", "pre", "span", "strong",
    "sub", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul",
]
_ALLOWED_ATTRS = {"a": ["href", "title"]}


def sanitize_html(raw_html: str) -> str:
    """Bereinigt eingehendes HTML serverseitig vor der Anzeige im Frontend."""
    if not raw_html:
        return ""
    return bleach.clean(
        raw_html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True,
    )


def decrypt_konto(konto: dict) -> dict:
    """Liefert eine Kopie des Kontos mit entschlüsselten Passwörtern."""
    out = dict(konto)
    out["imap_passwort"] = decrypt_secret(konto["imap_passwort"])
    out["smtp_passwort"] = decrypt_secret(konto["smtp_passwort"]) if konto.get("smtp_passwort") else ""
    if not out.get("smtp_user"):
        out["smtp_user"] = out["imap_user"]
    if not out.get("smtp_passwort"):
        out["smtp_passwort"] = out["imap_passwort"]
    return out


def _sniff(data: bytes) -> tuple[str, str] | None:
    """Magic-Byte-Sniffing für Anhänge; nie dem Client-Content-Type trauen."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif", "image/gif"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data.startswith(b"%PDF-"):
        return "pdf", "application/pdf"
    if data.startswith(b"PK\x03\x04"):
        # ZIP-Container: docx/xlsx/pptx sowie gewöhnliche ZIP-Archive.
        return "zip", "application/zip"
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        return "doc", "application/msword"
    return None


def parse_message(raw_bytes: bytes) -> dict:
    """Zerlegt eine rohe RFC822-Mail in strukturierte Felder + Anhänge."""
    msg = email.message_from_bytes(raw_bytes)
    absender = parseaddr(msg.get("From", ""))[1] or msg.get("From", "")
    empfaenger = parseaddr(msg.get("To", ""))[1] or msg.get("To", "")
    betreff = msg.get("Subject")
    message_id = msg.get("Message-ID")
    in_reply_to = msg.get("In-Reply-To")
    references = msg.get("References")

    text_html = None
    text_plain = None
    anhaenge: list[dict] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()
            if disp == "attachment" or (disp is None and ctype.startswith("application/")):
                filename = part.get_filename()
                if filename:
                    data = part.get_payload(decode=True) or b""
                    anhaenge.append({"dateiname": filename, "data": data})
                continue
            if ctype == "text/html" and text_html is None:
                text_html = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text_html = text_html.decode(charset, errors="replace")
            elif ctype == "text/plain" and text_plain is None:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text_plain = payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        body = payload.decode(charset, errors="replace")
        if msg.get_content_type() == "text/html":
            text_html = body
        else:
            text_plain = body

    return {
        "absender": absender,
        "empfaenger": empfaenger,
        "betreff": betreff,
        "text_html": text_html,
        "text_plain": text_plain,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
        "stabile_mail_kennung": message_id,
        "anhange": anhaenge,
    }


def fetch_unseen(konto: dict) -> list[dict]:
    """Holt alle ungelesenen Mails via IMAP und gibt sie geparst zurück.

    ``konto`` muss bereits entschlüsselte Passwörter enthalten (siehe
    ``decrypt_konto`` bzw. den Test-Endpoint, der Klartext-Passwörter nutzt)."""
    k = konto
    client = imaplib.IMAP4_SSL(k["imap_host"], k["imap_port"]) if k["imap_tls"] \
        else imaplib.IMAP4(k["imap_host"], k["imap_port"])
    try:
        client.login(k["imap_user"], k["imap_passwort"])
        client.select("INBOX")
        status, data = client.search(None, "UNSEEN")
        if status != "OK" or not data or not data[0]:
            return []
        ids = data[0].split()
        result: list[dict] = []
        for mid in ids:
            _, raw = client.fetch(mid, "(RFC822)")
            for response_part in raw:
                if isinstance(response_part, tuple):
                    parsed = parse_message(response_part[1])
                    result.append(parsed)
        return result
    finally:
        try:
            client.close()
            client.logout()
        except Exception:
            pass


def send_message(konto: dict, to: str, subject: str, body: str,
                 in_reply_to: str | None = None, references: str | None = None,
                 message_id: str | None = None) -> str:
    """Versendet eine Text/E-Mail via SMTP und liefert die Message-ID zurück.

    ``konto`` muss bereits entschlüsselte Passwörter enthalten."""
    k = konto
    msg = EmailMessage()
    msg["From"] = formataddr(("", k["smtp_user"]))
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    mid = message_id or f"<{uuid.uuid4()}@business-os.local>"
    msg["Message-ID"] = mid
    msg.set_content(body)

    host, port = k["smtp_host"], k["smtp_port"]
    if k["smtp_tls"] and port == 465:
        smtp = smtplib.SMTP_SSL(host, port)
    else:
        smtp = smtplib.SMTP(host, port)
        if k["smtp_tls"]:
            smtp.starttls()
    try:
        smtp.login(k["smtp_user"], k["smtp_passwort"])
        smtp.send_message(msg)
    finally:
        smtp.quit()
    return mid


def test_connection(konto: dict) -> tuple[bool, bool, str]:
    """Prüft IMAP-Empfang und SMTP-Versand; liefert (imap_ok, smtp_ok, detail).

    ``konto`` muss bereits entschlüsselte Passwörter enthalten."""
    k = konto
    imap_ok = False
    smtp_ok = False
    detail = ""
    try:
        client = imaplib.IMAP4_SSL(k["imap_host"], k["imap_port"]) if k["imap_tls"] \
            else imaplib.IMAP4(k["imap_host"], k["imap_port"])
        try:
            client.login(k["imap_user"], k["imap_passwort"])
            client.select("INBOX")
            imap_ok = True
        finally:
            try:
                client.logout()
            except Exception:
                pass
    except Exception as exc:  # noqa: BLE001
        detail = f"IMAP: {exc}"

    try:
        host, port = k["smtp_host"], k["smtp_port"]
        if k["smtp_tls"] and port == 465:
            smtp = smtplib.SMTP_SSL(host, port)
        else:
            smtp = smtplib.SMTP(host, port)
            if k["smtp_tls"]:
                smtp.starttls()
        try:
            smtp.login(k["smtp_user"], k["smtp_passwort"])
            probe = EmailMessage()
            probe["From"] = formataddr(("", k["smtp_user"]))
            probe["To"] = k["smtp_user"]
            probe["Subject"] = "Business OS Verbindungstest"
            probe.set_content("SMTP-Versandtest erfolgreich.")
            smtp.send_message(probe)
            smtp_ok = True
        finally:
            smtp.quit()
    except Exception as exc:  # noqa: BLE001
        detail = (detail + " | " if detail else "") + f"SMTP: {exc}"

    return imap_ok, smtp_ok, detail
