# Feature-Index

**Next Available ID:** PROJ-24

> **Hinweis zur Nummerierung (2026-08-23):** `Brainstorm 2.md` verwendet einen eigenen PROJ-1…PROJ-24-Nummernkreis, der mit diesem Index nicht deckungsgleich ist (z. B. ist Brainstorm-PROJ-5 „Auto-Triage", hier ist PROJ-5 „Angebote"). **Verbindlich ist ausschließlich die Nummerierung in diesem Dokument.** Bei Bezug auf den Brainstorm bitte immer über den Feature-Namen abgleichen, nicht über die ID.
>
> **Hinweis zur Spalte „ImmoCRM-Reuse":** Bei PROJ-3, PROJ-6, PROJ-8 enthält diese Spalte Deployment-/QA-Status statt Wiederverwendungsangaben. Historisch gewachsen, hier nicht rückwirkend korrigiert, aber ab sofort bitte Deployment-/QA-Status in einer eigenen Spalte oder im jeweiligen Feature-Dokument führen, nicht mehr hier.

| ID | Feature | Priorität | Status | Abhängigkeiten | ImmoCRM-Reuse |
|---|---|---|---|---|---|
| PROJ-1 | Mandanten, Anmeldung und Rollen | P0 | Approved | — | Auth, Passwort-, JWT-, TOTP- und Audit-Muster; RLS neu |
| PROJ-14 | Branchenpaket-Konfiguration (einmalige Onboarding-Wahl; Formulare, Preislisten, Textbausteine, Objekttypen je Branche) | P0 | In Progress | PROJ-1, PROJ-13, PROJ-7, PROJ-22 | Versionierte Produktvorlagen werden beim Onboarding atomar in den Mandanten kopiert; Voraussetzung für Doppel-Pilot SHK/Entrümpelung |
| PROJ-2 | Geführte Website, Branding | P0 | Deployed | PROJ-1 | Branding-Settings und Logo-Speicher; Website neu |
| PROJ-13 | Formular-Baukasten (Feldtypen-Katalog, Editor, Mehrstufigkeit, Einbindung) | P0 | Deployed | PROJ-2 | Deployed 2026-08-24, v0.1.15 · bizos.app.msce.info; QA 15/15, keine offenen Bugs |
| PROJ-3 | Kunden, Objekte, Projekte und Dokumente | P0 | Deployed | PROJ-1 | Deployed 2026-08-17, v0.1.2 · biz.app.msce.info; QA bestanden 6/6 AC, Security-Audit ohne Befund, BUG-1 gefixt+retestet |
| PROJ-4 | E-Mail-Inbox und Vorgangskommunikation | P0 | Approved | PROJ-1, PROJ-3 | IMAP/SMTP, MIME, Polling und Fehlerlogik extrahieren |
| PROJ-5 | Angebote: Positionen, PDF, Freigabe und Versand | P0 | Deployed | PROJ-3, PROJ-4 | Versand- und Speicherpfade; Angebotslogik/PDF neu; Kalkulationsdetails siehe PROJ-22 |
| PROJ-22 | Gewerke: Kalkulationseinheiten für Angebote (Lohn/Material/Fremdleistung, Zuschläge, Leistungskatalog) | P0 | Proposed | PROJ-3, PROJ-5, PROJ-14 | Kein Reuse — neues Kernkonzept, destilliert aus Plancraft-Screenshots; siehe `Kalkulation_und_Angebotserstellung.md`; Voraussetzung für Formular→Kalkulation-Verknüpfung und SHK-/Entrümpelung-Leistungskataloge |
| PROJ-6 | Terminplanung und Teamzuweisung | P0 | Deployed | PROJ-3, PROJ-1 | Deployed 2026-08-18, v0.1.7 · biz.app.msce.info; QA bestanden 7/7 AC, Security-Audit ohne Befund, BUG-1 gefixt+retestet |
| PROJ-7 | Begleitetes Onboarding: Betriebsdaten, Branding und Postfach | P0 | Deployed | PROJ-1, PROJ-2, PROJ-4, PROJ-5 | Deployed v0.1.8, 2026-08-19; Postfach-Tests und Settings als Vorlage |
| PROJ-8 | PDF-Rechnungen und Rechnungsdokumente | P0 | Approved | PROJ-3, PROJ-5 | Speicher- und Versandpfade; Rechnungsvorlage neu; QA: READY (Bugfix verifiziert) |
| PROJ-15 | Auto-Triage mit Ampel (Passung/Dringlichkeit/Kapazität) | P0 (Vorschlag) | Proposed | PROJ-3 | Kein Reuse — Reaktivierung aus Brainstorm „Hebel 1", im PRD v1 verlorengegangen; Priorität zu bestätigen |
| PROJ-9 | Mobile Monteuransicht und Auftragsabschluss | P1 | Proposed | PROJ-3, PROJ-6 | Kein UI-Reuse; responsive Webansicht neu |
| PROJ-10 | Erinnerungen und Statusautomationen | P1 | Proposed | PROJ-4, PROJ-5, PROJ-6 | Reminder-Sweeper und Versandvorbereitung als Vorlage |
| PROJ-11 | Datenschutz, Datenexport und Aufbewahrung | P1 | Proposed | PROJ-1 | Retention-, Lösch- und Exportmuster als Vorlage; Umfang jetzt konkretisiert (Verarbeitungsverzeichnis, AVV, Self-Service-Portal, Audit-Log, Feldverschlüsselung) |
| PROJ-16 | KI-Assistenz (Zusammenfassungen, Klassifizierung, Textentwürfe) | P1 | Proposed | PROJ-4, PROJ-5 | Kein Reuse — bisher nur Roadmap-Zeile ohne Ticket, jetzt ergänzt |
| PROJ-12 | Freier Website-Baukasten und hochwertige Landingpage | P1 | Deployed | PROJ-1, PROJ-2 | Deployed 2026-08-23, v0.1.10 · bizos.app.msce.info |
| PROJ-23 | Dedizierter Bildspeicher und WebP-Optimierung | P1 | Approved | PROJ-2, PROJ-12 | Eigene Business-OS-MinIO für neue Sektionsbilder; keine Migration bestehender Bilder |
| PROJ-17 | Kunden-Status-Link | P1 | Proposed | PROJ-6 | Kein Reuse — wiederaufgenommen aus Brainstorm #10, im PRD v1 verlorengegangen |
| PROJ-18 | CSV-Export für Buchhaltung (DATEV/lexoffice/sevDesk-kompatibel) | P1 (Vorschlag) | Proposed | PROJ-3, PROJ-8 | Kein Reuse — aus Wettbewerbsvergleich (ENT1PRO) ergänzt, Priorität zu bestätigen |
| PROJ-19 | Angebots-Statustracking & optionale E-Signatur | P2 (offen) | Proposed | PROJ-5 | Kein Reuse — aus Wettbewerbsvergleich (FastMove) ergänzt, unentschieden, nicht spezifiziert |
| PROJ-20 | E-Rechnungen | P2 | Proposed | PROJ-8 | Kein Reuse — bisher nur Roadmap-Zeile ohne Ticket, jetzt ergänzt |
| PROJ-21 | Telefonie, Routen, Kundenportal | P2 | Proposed | — | Kein Reuse — bisher nur Roadmap-Zeile ohne Ticket, jetzt ergänzt; nur bei belegtem Kundenbedarf |

## Empfohlene Build-Reihenfolge

1. PROJ-1 → PROJ-14 → PROJ-3 → PROJ-2 → PROJ-13 → PROJ-4
2. PROJ-5 → PROJ-22 → PROJ-6 → PROJ-7 → PROJ-15
3. PROJ-8 → PROJ-12 → PROJ-23 → PROJ-9 → PROJ-10 → PROJ-11 → PROJ-16
4. PROJ-17 → PROJ-18 → PROJ-19 → PROJ-20 → PROJ-21

**Hinweis:** PROJ-14 (Branchenpaket-Konfiguration) rückt bewusst früh in die Reihenfolge, obwohl PROJ-1 bis PROJ-8 bereits größtenteils deployed sind — diese deployten Teile (insbesondere PROJ-2/Website und PROJ-3/Datenmodell) sollten vor dem Entrümpelung-Piloten daraufhin geprüft werden, was davon SHK-spezifisch hart codiert ist und in die Branchenpaket-Konfiguration wandern muss.

**Hinweis:** PROJ-22 (Gewerke) erweitert das bereits deployte PROJ-5 nachträglich um die Kalkulationslogik, die beim ursprünglichen Angebots-Feature ausdrücklich als offener Platzhalter markiert war („Kalkulationsdetails folgen separat") — kein Rebuild von PROJ-5, sondern Aufsatz auf dem bestehenden Positions-/PDF-Datenmodell. Details: `Kalkulation_und_Angebotserstellung.md`.
