from __future__ import annotations

import io
import re

from app import db
from app.errors import ConflictError, NotFoundError, ValidationError
from app.features.email import mailclient
from app.features.email import repository as email_repo
from app.features.onboarding import repository as repo
from app.features.onboarding import schemas

HOSTNAME_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$"
)

# Schritt-IDs exakt nach Frontend-Contract (lib/api/onboarding.ts).
_SCHRITT_IDS = [
    "betriebsdaten", "branding", "leistungsseiten", "domain",
    "postfach", "preisliste", "testanfrage",
]


def _validate_hostname(raw: str) -> str:
    hostname = raw.strip().lower()
    if not HOSTNAME_RE.match(hostname):
        raise ValidationError(
            "Ungültige Domain. Bitte nur den Hostnamen angeben (z. B. beispiel.de), "
            "ohne https:// oder Pfad."
        )
    return hostname


# --- Statusberechnung (ADR-7-1: berechnet, nicht abgehakt) ----------------

def get_onboarding_status(mandant_id: str) -> schemas.OnboardingStatus:
    settings = repo.get_website_settings(mandant_id)
    domain = repo.get_domain(mandant_id)
    active_leistungen = repo.count_active_leistungen(mandant_id)
    konto = repo.get_konto_version(mandant_id)
    preisliste_anzahl = repo.count_preisliste(mandant_id)
    testvorgang = repo.get_testvorgang(mandant_id)

    # Postfach: nur ein Test mit passender Konfigurationsversion zählt.
    postfach_test: schemas.PostfachTestInfo | None = None
    if konto:
        latest = repo.get_latest_postfach_test(mandant_id, konto["id"])
        if latest and int(latest["konfiguration_version"]) == int(konto["konfiguration_version"]):
            postfach_test = schemas.PostfachTestInfo(
                imap_ok=bool(latest["imap_ok"]), smtp_ok=bool(latest["smtp_ok"]),
                tested_at=latest["created_at"],
            )

    schritte: list[schemas.OnboardingSchritt] = []

    # 1) Betriebsdaten
    fehlend_bd = _fehlende_betriebsdaten(settings)
    if fehlend_bd:
        schritte.append(_schritt("betriebsdaten", "Betriebsdaten", True,
                                  "offen" if not settings else "in_bearbeitung",
                                  fehlend_bd, "Website-Einstellungen"))
    else:
        schritte.append(_schritt_erledigt("betriebsdaten", "Betriebsdaten", True, ziel="Website-Einstellungen"))

    # 2) Branding
    fehlend_bg = _fehlende_branding(settings)
    if fehlend_bg:
        schritte.append(_schritt("branding", "Branding", True,
                                  "offen" if not (settings and settings.get("logo_objektpfad"))
                                  else "in_bearbeitung", fehlend_bg, "Website-Einstellungen"))
    else:
        schritte.append(_schritt_erledigt("branding", "Branding", True, ziel="Website-Einstellungen"))

    # 3) Leistungsseiten
    if active_leistungen > 0:
        schritte.append(_schritt_erledigt("leistungsseiten", "Leistungsseiten", True, ziel="Website-Einstellungen"))
    else:
        schritte.append(_schritt("leistungsseiten", "Leistungsseiten", True, "offen",
                                  "Mindestens eine Leistungsseite mit Titel, Kurzbeschreibung und Inhalt fehlt.",
                                  "Website-Einstellungen"))

    # 4) Website-Domain (Frontend-ID: "domain")
    if domain:
        if domain.get("status") == "aktiv":
            schritte.append(_schritt_erledigt("domain", "Website-Domain", True, ziel="Onboarding",
                                              domain_status=domain.get("status")))
        else:
            # Reserviert (inaktiv) -> im Frontend "in_bearbeitung"; veroeffentlichen
            # aktiviert die Domain und schließt den Schritt ab.
            schritte.append(_schritt("domain", "Website-Domain", True, "in_bearbeitung",
                                     "Domain ist reserviert, aber noch nicht veröffentlicht.",
                                     "Onboarding", domain_status=domain.get("status")))
    else:
        schritte.append(_schritt("domain", "Website-Domain", True, "offen",
                                  "Noch keine Domain zugeordnet.", "Onboarding", domain_status=None))

    # 5) Betriebspostfach (Frontend-ID: "postfach")
    if not konto:
        schritte.append(_schritt("postfach", "Betriebspostfach", True, "offen",
                                 "Kein Postfach verbunden.", "Postfach-Einstellungen"))
    elif not postfach_test:
        schritte.append(_schritt("postfach", "Betriebspostfach", True, "in_bearbeitung",
                                 "IMAP/SMTP-Test steht aus.", "Postfach-Einstellungen",
                                 postfach_test=postfach_test))
    elif postfach_test.imap_ok and postfach_test.smtp_ok:
        schritte.append(_schritt_erledigt("postfach", "Betriebspostfach", True, ziel="Postfach-Einstellungen",
                                          postfach_test=postfach_test))
    else:
        teile = []
        if not postfach_test.imap_ok:
            teile.append("IMAP-Empfangstest fehlgeschlagen")
        if not postfach_test.smtp_ok:
            teile.append("SMTP-Versandtest fehlgeschlagen")
        schritte.append(_schritt("postfach", "Betriebspostfach", True, "in_bearbeitung",
                                 "; ".join(teile) + ".", "Postfach-Einstellungen",
                                 postfach_test=postfach_test))

    # 6) Preisliste (nicht pflicht für Veröffentlichung)
    if preisliste_anzahl > 0:
        schritte.append(_schritt_erledigt("preisliste", "Preisliste", False, ziel="Onboarding"))
    else:
        schritte.append(_schritt("preisliste", "Preisliste", False, "offen",
                                 "Noch keine Katalogposition erfasst.",
                                 "Onboarding"))

    # 7) Testanfrage
    testvorgang_info: schemas.OnboardingTestvorgang | None = None
    if testvorgang:
        testvorgang_info = schemas.OnboardingTestvorgang(
            vorgang_id=testvorgang["vorgang_id"],
            anfrage_id=testvorgang.get("anfrage_id"),
            erstellt_am=testvorgang.get("created_at"),
        )
        schritte.append(_schritt_erledigt("testanfrage", "Testanfrage", True, ziel="Onboarding",
                                          testvorgang=testvorgang_info))
    else:
        schritte.append(_schritt("testanfrage", "Testanfrage", True, "offen",
                                 "Noch kein Testvorgang erzeugt.",
                                 "Onboarding", testvorgang=None))

    veröffentlicht = bool(domain and domain.get("status") == "aktiv")
    # Warnung: Website live, aber ein Pflichtschritt wurde nachträglich unvollständig.
    warnung: str | None = None
    if veröffentlicht:
        unvollstaendig = [s.titel for s in schritte if s.pflicht and s.status != "erledigt"]
        if unvollstaendig:
            warnung = ("Website ist veröffentlicht, aber folgende Pflichtschritte sind unvollständig: "
                       + ", ".join(unvollstaendig) + ".")

    return schemas.OnboardingStatus(
        schritte=schritte, veröffentlicht=veröffentlicht,
        veröffentlicht_am=domain.get("veröffentlicht_am") if veröffentlicht else None,
        warnung=warnung,
        postfach_test=postfach_test,
        domain_status=domain.get("status") if domain else None,
        testvorgang_id=testvorgang["vorgang_id"] if testvorgang else None,
    )


def _fehlende_betriebsdaten(settings: dict | None) -> str | None:
    if not settings:
        return "Firmenname, Telefon, E-Mail und Adresse fehlen."
    fehlend = []
    if not (settings.get("firmenname") or "").strip():
        fehlend.append("Firmenname")
    if not (settings.get("telefon") or "").strip():
        fehlend.append("Telefon")
    if not (settings.get("email") or "").strip():
        fehlend.append("E-Mail")
    if not (settings.get("adresse") or "").strip():
        fehlend.append("Adresse")
    return (", ".join(fehlend) + " fehlt/fehlen") if fehlend else None


def _fehlende_branding(settings: dict | None) -> str | None:
    if not settings:
        return "Logo und Markenfarbe fehlen."
    fehlend = []
    if not settings.get("logo_objektpfad"):
        fehlend.append("Logo")
    if not (settings.get("marken_farbe") or "").strip():
        fehlend.append("Markenfarbe")
    return (", ".join(fehlend) + " fehlt/fehlen") if fehlend else None


def _schritt(id: str, titel: str, pflicht: bool, status: str, fehlend: str | None = None,
             ziel: str | None = None, postfach_test: schemas.PostfachTestInfo | None = None,
             domain_status: str | None = None,
             testvorgang: schemas.OnboardingTestvorgang | None = None) -> schemas.OnboardingSchritt:
    return schemas.OnboardingSchritt(
        id=id, titel=titel, status=status,  # type: ignore[arg-type]
        pflicht=pflicht, fehlende_eingabe=fehlend, bearbeitungsziel=ziel,
        postfach_test=postfach_test, domain_status=domain_status, testvorgang=testvorgang,
    )


def _schritt_erledigt(id: str, titel: str, pflicht: bool, ziel: str | None = None,
                      postfach_test: schemas.PostfachTestInfo | None = None,
                      domain_status: str | None = None,
                      testvorgang: schemas.OnboardingTestvorgang | None = None) -> schemas.OnboardingSchritt:
    return schemas.OnboardingSchritt(
        id=id, titel=titel, status="erledigt", pflicht=pflicht, bearbeitungsziel=ziel,
        postfach_test=postfach_test, domain_status=domain_status, testvorgang=testvorgang,
    )


# --- Domain-Reservierung / Veröffentlichung ------------------------------

def reserve_domain(mandant_id: str, hostname: str) -> schemas.DomainReserveResponse:
    hostname = _validate_hostname(hostname)
    owner = repo.hostname_owner(mandant_id, hostname)
    if owner:
        raise ConflictError("Diese Domain ist bereits einem anderen Betrieb zugeordnet.")
    repo.reserve_domain(mandant_id, hostname)
    return schemas.DomainReserveResponse(hostname=hostname, status="inaktiv")


def veroeffentlichen(mandant_id: str, user_id: str | None) -> schemas.VeroeffentlichenResult:
    status = get_onboarding_status(mandant_id)
    # Domain ist erfüllt, sobald eine Domain reserviert (inaktiv) oder aktiv ist;
    # die generische erledigt-Prüfung unten würde eine reservierte Domain
    # (Status "in_bearbeitung") fälschlich als offen werten. Die eigentliche
    # Domain-Prüfung erfolgt weiter unten über repo.get_domain().
    fehlende = [s.titel for s in status.schritte
                if s.id != "domain" and s.pflicht and s.status != "erledigt"]
    if fehlende:
        return schemas.VeroeffentlichenResult(
            ok=False, domain_status=status.domain_status or "inaktiv",
            fehlende_schritte=fehlende,
        )
    domain = repo.get_domain(mandant_id)
    if not domain:
        return schemas.VeroeffentlichenResult(
            ok=False, domain_status="inaktiv", fehlende_schritte=["Website-Domain"],
        )
    repo.publish_domain(mandant_id, domain["hostname"])
    return schemas.VeroeffentlichenResult(
        ok=True, domain_status="aktiv", veröffentlicht_am=_now(),
    )


def _now() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- Postfach-Test (gegen gespeichertes Konto) ---------------------------

def postfach_test(mandant_id: str, user_id: str | None) -> schemas.PostfachTestResult:
    konto = email_repo.get_konto(mandant_id)
    if not konto:
        raise NotFoundError("Es ist noch kein Postfach verbunden.")
    decrypted = mailclient.decrypt_konto(konto)
    imap_ok, smtp_ok, detail = mailclient.test_connection(decrypted)
    # Ein fehlgeschlagener Test wird versiongebunden protokolliert, damit der
    # Schritt nachvollziehbar "In Bearbeitung" bleibt (Design Abschnitt C).
    # Erst wenn beide Teile ok sind, gilt der Pflichtschritt als erfüllt. Ein
    # späteres Ändern des Kontos erhöht konfiguration_version und entwertet
    # diesen Test automatisch.
    repo.save_postfach_test(
        mandant_id, konto["id"], int(konto["konfiguration_version"]),
        imap_ok, smtp_ok, detail, user_id,
    )
    return schemas.PostfachTestResult(
        ok=imap_ok and smtp_ok, imap_ok=imap_ok, smtp_ok=smtp_ok, detail=detail,
    )


# --- Testvorgang (atomar anlegen + kaskadierend löschen) -----------------

def create_testvorgang(mandant_id: str, user_id: str | None) -> schemas.TestvorgangResult:
    """Erzeugt über das echte öffentliche Anfrageformular einen Testvorgang mit
    Testkennzeichen. Die Anfrage wird über dieselbe Repository-Erzeugung wie
    echte Kundenanfragen (website_repository.create_anfrage) angelegt; der
    daraus resultierende Vorgang wird aber als Test markiert (ist_test=TRUE)
    und mit Bestätigungsmail versehen (wenn ein Postfach gebunden+getestet ist).
    Es entsteht genau EIN Vorgang — kein doppelter Nicht-Test-Vorgang."""
    existing = repo.get_testvorgang(mandant_id)
    if existing:
        raise ConflictError(
            "Es existiert bereits ein Testvorgang. Bitte zuerst den bestehenden Testvorgang löschen."
        )
    settings = repo.get_website_settings(mandant_id) or {}
    firmenname = (settings.get("firmenname") or "Test").strip() or "Test"
    email = settings.get("email") or "onboarding-test@beispiel.invalid"
    adresse = settings.get("adresse") or "Testadresse"
    anliegen = "Onboarding-Durchstich: Testanfrage"

    # Echte Anfrage über das öffentliche Formular (Repository-Ebene, wie
    # website_service.submit_anfrage, nur ohne den automatischen
    # Nicht-Test-Vorgang — dieser wird hier als Testvorgang geführt).
    from app.features.website import repository as website_repo
    from app.features.vorgaenge import repository as vorgaenge_repo
    kennung = f"onboarding-test-{_uuid()}"
    anfrage_id = website_repo.create_anfrage(
        mandant_id, f"Onboarding-Test ({firmenname})", "E-Mail", None, email,
        adresse, anliegen, "Normal", None, kennung,
    )

    kunde_id = repo.create_test_kunde(mandant_id, f"Onboarding-Test ({firmenname})", email)
    objekt_id = repo.create_test_objekt(mandant_id, kunde_id, adresse)
    vorgang_id = repo.create_test_vorgang(
        mandant_id, kunde_id, objekt_id, anliegen, "Onboarding-Test"
    )
    repo.link_testvorgang(mandant_id, vorgang_id, kunde_id, objekt_id, anfrage_id, user_id)
    # Anfrage mit dem (Test-)Vorgang verknüpfen (wie bei echter Übernahme).
    vorgaenge_repo.mark_anfrage_uebernommen(mandant_id, anfrage_id, vorgang_id)

    bestaetigt = _send_test_bestaetigung(mandant_id, vorgang_id, email)
    return schemas.TestvorgangResult(
        vorgang_id=vorgang_id, anfrage_id=anfrage_id,
        erstellt_am=_now(), ist_test=True,
        detail="" if bestaetigt else "Bestätigungsmail nicht versendet (Postfach nicht verbunden/getestet).",
    )


def _hostname_for_mandant(mandant_id: str) -> str | None:
    dom = repo.get_domain(mandant_id)
    return dom["hostname"] if dom else None


def _last_anfrage_id(mandant_id: str, kennung: str) -> str | None:
    rows = db.engine.query(
        "SELECT id FROM anfrage WHERE mandant_id = %s AND uebermittlungskennung = %s "
        "ORDER BY created_at DESC LIMIT 1",
        (mandant_id, kennung), mandant_id=mandant_id,
    )
    return rows[0]["id"] if rows else None


def _uuid() -> str:
    import uuid as _uuid_mod
    return str(_uuid_mod.uuid4())


def _send_test_bestaetigung(mandant_id: str, vorgang_id: str, empfaenger: str) -> bool:
    from app.features.email import mailclient as _mc
    from app.features.email import repository as _email_repo
    konto = _email_repo.get_konto(mandant_id)
    if not konto:
        return False
    try:
        decrypted = _mc.decrypt_konto(konto)
        _mc.send_message(
            decrypted, empfaenger, "Onboarding-Test: Ihre Anfrage ist eingegangen",
            "Dies ist eine automatische Bestätigung des Onboarding-Testvorgangs. "
            "Sie können diesen Testvorgang jederzeit vollständig löschen.",
        )
        return True
    except Exception:
        return False


def delete_testvorgang(mandant_id: str, vorgang_id: str) -> None:
    zuordnung = repo.get_testvorgang_zuordnung(mandant_id, vorgang_id)
    if not zuordnung:
        raise NotFoundError("Kein Onboarding-Testvorgang für diese ID gefunden.")
    kunde_id = zuordnung["kunde_id"]
    objekt_id = zuordnung.get("objekt_id")

    with db.engine.transaction(mandant_id=mandant_id) as tx:
        repo.cascade_delete_testvorgang(tx, mandant_id, vorgang_id, kunde_id, objekt_id)


# --- Preisliste / Leistungskatalog (PROJ-7, Schritt 6) -------------------

def list_preisliste(mandant_id: str) -> schemas.KatalogListe:
    positionen = [schemas.PreislistePosition(**p) for p in repo.list_preisliste(mandant_id)]
    return schemas.KatalogListe(positionen=positionen)


def create_preisliste_position(mandant_id: str, payload: schemas.PreislistePositionInput) -> schemas.PreislistePosition:
    bezeichnung = payload.bezeichnung.strip()
    if not bezeichnung:
        raise ValidationError("Bezeichnung ist erforderlich.")
    einheit = (payload.einheit or "Stk.").strip() or "Stk."
    if repo.find_preisliste_by_bezeichnung(mandant_id, bezeichnung):
        raise ConflictError(f"Eine Katalogposition mit der Bezeichnung „{bezeichnung}“ existiert bereits.")
    position = repo.create_preisliste_position(
        mandant_id, bezeichnung, einheit, payload.netto_einzelpreis, payload.steuersatz,
    )
    return schemas.PreislistePosition(**position)


def delete_preisliste_position(mandant_id: str, position_id: str) -> None:
    if not repo.get_preisliste_position(mandant_id, position_id):
        raise NotFoundError("Katalogposition nicht gefunden.")
    repo.delete_preisliste_position(mandant_id, position_id)


def import_preisliste_csv(mandant_id: str, inhalt: bytes) -> schemas.KatalogImportResult:
    """Importiert eine CSV mit optionalem Header:
        bezeichnung;einheit;netto_einzelpreis;steuersatz
    Komma statt Punkt oder Währungszeichen im Preis werden normalisiert (Edge Case).
    Jede fehlerhafte Zeile wird mit Zeilennummer + Grund gemeldet, korrekte übernommen.
    Duplikate (gleiche Bezeichnung) werden als Fehler gemeldet, nicht doppelt angelegt."""
    text = inhalt.decode("utf-8-sig", errors="replace")
    reader = io.StringIO(text)
    zeilen = [ln.rstrip("\n").rstrip("\r") for ln in reader if ln.strip() != ""]

    uebernommen: list[schemas.KatalogImportZeile] = []
    fehler: list[schemas.KatalogImportFehler] = []
    anzahl = 0

    # Optionale Kopfzeile erkennen (klein, deutsche Spaltennamen).
    start = 0
    if zeilen and _is_header(zeilen[0]):
        start = 1

    for idx in range(start, len(zeilen)):
        zeilennr = idx + 1
        teile = [t.strip() for t in zeilen[idx].split(";")]
        if len(teile) < 4:
            fehler.append(schemas.KatalogImportFehler(
                zeile=zeilennr,
                grund="Zeile muss bezeichnung;einheit;netto_einzelpreis;steuersatz enthalten.",
            ))
            continue
        bezeichnung, einheit, preis_raw, steuer_raw = teile[0], teile[1], teile[2], teile[3]
        if not bezeichnung:
            fehler.append(schemas.KatalogImportFehler(zeile=zeilennr, grund="Bezeichnung fehlt."))
            continue
        preis = _parse_preis(preis_raw)
        if preis is None:
            fehler.append(schemas.KatalogImportFehler(
                zeile=zeilennr, grund=f"Netto-Einzelpreis ungültig: „{preis_raw}“."))
            continue
        steuer = _parse_preis(steuer_raw)
        if steuer is None:
            fehler.append(schemas.KatalogImportFehler(
                zeile=zeilennr, grund=f"Steuersatz ungültig: „{steuer_raw}“."))
            continue
        if repo.find_preisliste_by_bezeichnung(mandant_id, bezeichnung):
            fehler.append(schemas.KatalogImportFehler(
                zeile=zeilennr,
                grund=f"Duplikat: „{bezeichnung}“ existiert bereits."))
            continue
        repo.create_preisliste_position(mandant_id, bezeichnung, einheit or "Stk.", preis, steuer)
        uebernommen.append(schemas.KatalogImportZeile(zeile=zeilennr, uebernommen=True))
        anzahl += 1

    return schemas.KatalogImportResult(uebernommen=uebernommen, fehler=fehler, anzahl_uebernommen=anzahl)


def _is_header(zeile: str) -> bool:
    lower = zeile.lower()
    return "bezeichnung" in lower and "steuersatz" in lower


def _parse_preis(raw: str) -> float | None:
    """Normalisiert Preisangaben: entfernt Währungszeichen/Leerzeichen, wandelt
    Komma in Punkt um. Gibt None bei ungültigem Wert zurück."""
    s = raw.strip().replace("€", "").replace("EUR", "").replace("$", "").strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".") if ("," in s and "." in s) else s.replace(",", ".")
    try:
        wert = float(s)
    except ValueError:
        return None
    if wert < 0:
        return None
    return round(wert, 2)
