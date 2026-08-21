# Feature-Index

**Next Available ID:** PROJ-13

| ID | Feature | Priorität | Status | Abhängigkeiten | ImmoCRM-Reuse |
|---|---|---|---|---|---|
| PROJ-1 | Mandanten, Anmeldung und Rollen | P0 | Approved | — | Auth, Passwort-, JWT-, TOTP- und Audit-Muster; RLS neu |
| PROJ-2 | Geführte SHK-Website, Branding und Anfrageformular | P0 | Deployed | PROJ-1 | Branding-Settings und Logo-Speicher; Website neu |
| PROJ-3 | Kunden, Objekte, Vorgänge und Dokumente | P0 | Deployed | PROJ-1 | Deployed 2026-08-17, v0.1.2 · biz.app.msce.info; QA bestanden 6/6 AC, Security-Audit ohne Befund, BUG-1 gefixt+retestet |
| PROJ-4 | E-Mail-Inbox und Vorgangskommunikation | P0 | Approved | PROJ-1, PROJ-3 | IMAP/SMTP, MIME, Polling und Fehlerlogik extrahieren |
| PROJ-5 | Angebote: Positionen, PDF, Freigabe und Versand | P0 | Deployed | PROJ-3, PROJ-4 | Versand- und Speicherpfade; Angebotslogik/PDF neu |
| PROJ-6 | Terminplanung und Teamzuweisung | P0 | Deployed | PROJ-3, PROJ-1 | Deployed 2026-08-18, v0.1.7 · biz.app.msce.info; QA bestanden 7/7 AC, Security-Audit ohne Befund, BUG-1 gefixt+retestet |
| PROJ-7 | Begleitetes Onboarding: Betriebsdaten, Branding und Postfach | P0 | Deployed | PROJ-1, PROJ-2, PROJ-4, PROJ-5 | Deployed v0.1.8, 2026-08-19; Postfach-Tests und Settings als Vorlage |
| PROJ-8 | PDF-Rechnungen und Rechnungsdokumente | P0 | Approved | PROJ-3, PROJ-5 | Speicher- und Versandpfade; Rechnungsvorlage neu; QA: READY (Bugfix verifiziert) |
| PROJ-9 | Mobile Monteuransicht und Auftragsabschluss | P1 | Proposed | PROJ-3, PROJ-6 | Kein UI-Reuse; responsive Webansicht neu |
| PROJ-10 | Erinnerungen und Statusautomationen | P1 | Proposed | PROJ-4, PROJ-5, PROJ-6 | Reminder-Sweeper und Versandvorbereitung als Vorlage |
| PROJ-11 | Datenschutz, Datenexport und Aufbewahrung | P1 | Proposed | PROJ-1 | Retention-, Lösch- und Exportmuster als Vorlage |
| PROJ-12 | Freier Website-Baukasten und hochwertige Landingpage | P1 | In Progress | PROJ-1, PROJ-2 | Nutzt vorhandenes Branding, Bildspeicher, Leistungen und Anfrageformular |

## Empfohlene Build-Reihenfolge

1. PROJ-1 → PROJ-3 → PROJ-2 → PROJ-4
2. PROJ-5 → PROJ-6 → PROJ-7
3. PROJ-8 → PROJ-12 → PROJ-9 → PROJ-10 → PROJ-11
