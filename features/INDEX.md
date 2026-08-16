# Feature-Index

**Next Available ID:** PROJ-12

| ID | Feature | Priorität | Status | Abhängigkeiten | ImmoCRM-Reuse |
|---|---|---|---|---|---|
| PROJ-1 | Mandanten, Anmeldung und Rollen | P0 | Architected | — | Auth, Passwort-, JWT-, TOTP- und Audit-Muster; RLS neu |
| PROJ-2 | Geführte SHK-Website, Branding und Anfrageformular | P0 | Planned | PROJ-1 | Branding-Settings und Logo-Speicher; Website neu |
| PROJ-3 | Kunden, Objekte, Vorgänge und Dokumente | P0 | Planned | PROJ-1 | Objekt- und Anhangspeicher; Datenmodell neu |
| PROJ-4 | E-Mail-Inbox und Vorgangskommunikation | P0 | Planned | PROJ-1, PROJ-3 | IMAP/SMTP, MIME, Polling und Fehlerlogik extrahieren |
| PROJ-5 | Angebote: Positionen, PDF, Freigabe und Versand | P0 | Planned | PROJ-3, PROJ-4 | Versand- und Speicherpfade; Angebotslogik/PDF neu |
| PROJ-6 | Terminplanung und Teamzuweisung | P0 | Planned | PROJ-3 | Kalender- und Verfügbarkeitsablauf als Vorlage |
| PROJ-7 | Begleitetes Onboarding: Betriebsdaten, Branding und Postfach | P0 | Planned | PROJ-1, PROJ-2, PROJ-4 | Postfach-Tests und Settings als Vorlage |
| PROJ-8 | PDF-Rechnungen und Rechnungsdokumente | P0 | Planned | PROJ-3, PROJ-5 | Speicher- und Versandpfade; Rechnungsvorlage neu |
| PROJ-9 | Mobile Monteuransicht und Auftragsabschluss | P1 | Proposed | PROJ-3, PROJ-6 | Kein UI-Reuse; responsive Webansicht neu |
| PROJ-10 | Erinnerungen und Statusautomationen | P1 | Proposed | PROJ-4, PROJ-5, PROJ-6 | Reminder-Sweeper und Versandvorbereitung als Vorlage |
| PROJ-11 | Datenschutz, Datenexport und Aufbewahrung | P1 | Proposed | PROJ-1 | Retention-, Lösch- und Exportmuster als Vorlage |

## Empfohlene Build-Reihenfolge

1. PROJ-1 → PROJ-3 → PROJ-2 → PROJ-4
2. PROJ-5 → PROJ-6 → PROJ-7
3. PROJ-8 → PROJ-9 → PROJ-10 → PROJ-11
