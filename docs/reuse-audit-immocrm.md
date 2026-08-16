# ImmoCRM-Reuse-Audit für Business OS

**Stand:** 2026-08-16  
**Entscheidung:** Neues Produkt, gezielte Extraktion technischer Bausteine; kein Fork und keine gemeinsame Bibliothek.

## Ergebnis

| Baustein aus ImmoCRM | Bewertung | Verwendung im Business OS |
|---|---|---|
| Konfiguration, MinIO-`ObjectStorage`, Credential-Vault | Direkt übernehmen, nach kleinem Test | Grundlage für Logos, Fotos, PDFs und verschlüsselte E-Mail-Zugänge |
| Passwort-Hashing, JWT, TOTP, Audit-Logging | Als Vorlage übernehmen | Neue Authentifizierung mit drei festen Rollen und RLS-Mandantenmodell |
| E-Mail: IMAP/SMTP, MIME-Parsing, Anhänge, Polling und Fehlerprotokoll | Extrahieren und vereinfachen | Ein gemeinsamer E-Mail-Kanal für Anfrage und Antwort; keine Immobilienzuordnung |
| E-Mail-Kontoeinrichtung und Verbindungstest | Als Vorlage übernehmen | Geführtes Onboarding für das Betriebspostfach |
| Termin- und Verfügbarkeitsablauf | Als Verhalten wiederverwenden | Schlichter Teamkalender ohne Makler-, Besichtigungs- oder Buchungslogik |
| Dokument-Upload, Download und Löschpfade | Extrahieren und vereinfachen | Anhänge, Auftragsfotos, Angebots- und Rechnungs-PDFs |
| Erinnerungs-Sweeper und Versandvorbereitung | Als Vorlage übernehmen | Angebotsnachfassen, Rückruf und Terminbestätigung |
| Kunden-CSV-Import | Als Vorlage übernehmen | Nur klar abbildbare Kundenfelder; keine Propstack-/Immobilienfelder |
| Retention- und Datenexport-Muster | Als Vorlage übernehmen | Löschkonzept und vollständiger Mandantenexport |

## Nicht übernehmen

- Das separate Datenbank-Mandantenmodell (`MasterDatabase`/`TenantDatabaseRouter`): Business OS braucht ein gemeinsames Postgres-Schema mit RLS.
- Flutter-Code: Das Produkt benötigt öffentliche, SEO-fähige Website-Routen und eine responsive Web-App. Aus Flutter wird keine Oberfläche kopiert.
- `main.py`, Immobilien-, IS24-, OpenImmo-, Exposé-, Objekt-, Makler- und Buchungslogik.
- Die 4.500-zeilige E-Mail-Fachlogik als Ganzes. Sie ist mit Interessenten, Objekten, Aufbewahrung und Portalen gekoppelt.
- Exposé-PDFs. Angebote und Rechnungen benötigen neue, rechtlich passende Vorlagen.

## Konsequenz für den MVP

Der erste funktionierende MVP nutzt nur den bewährten technischen Unterbau und endet beim kleinsten vollständigen Ablauf:

```text
geführte SHK-Website oder E-Mail
→ Anfrage und Anhänge
→ Kunde + Vorgang
→ menschlich freigegebene Antwort, Angebot oder Termin
→ PDF-Dokument und Verlauf
```

PDF-Rechnung bleibt Teil des vereinbarten P0. Monteuransicht, Automationen, Import und Export bleiben im Backlog und sind nicht Voraussetzung für den ersten Referenzbetrieb.

## Quellen im ImmoCRM-Bestand

- `backend/app/storage.py`, `backend/app/vault.py`, `backend/app/config.py`
- `backend/app/auth/` und `backend/app/auth/audit.py`
- `backend/app/services/email_service.py`, `backend/app/routes/email_settings.py`, `backend/app/routes/email_mailbox.py`
- `backend/app/routes/appointments.py`, `backend/app/routes/agents.py`
- `backend/app/routes/documents.py`, `backend/app/routes/import_export.py`
- `backend/app/services/reminder_sweeper.py`, `backend/app/routes/tenant_settings.py`
