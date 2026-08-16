# PROJ-7: Begleitetes Onboarding: Betriebsdaten, Branding und Postfach

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — Betrieb und Inhaber.
- Requires: PROJ-2 — Branding und öffentliche Website.
- Requires: PROJ-4 — E-Mail-Kanal.

## Reuse aus ImmoCRM
- Einstellungen, E-Mail-Kontoformular und IMAP-/SMTP-Verbindungstests als Vorlage.

## User Stories
- Als Onboarding-Verantwortlicher möchte ich einen Betrieb in einem Termin startklar machen.
- Als Inhaber möchte ich erkennen, welche Einrichtungsschritte noch fehlen.
- Als Inhaber möchte ich die erste Anfrage testweise durchspielen, bevor die Website live geht.

## Acceptance Criteria
- [ ] Der Onboarding-Status enthält Betriebsdaten, Logo/Farben, mindestens eine Leistungsseite, Website-Domain, Betriebspostfach und Testanfrage.
- [ ] Jeder Schritt zeigt „Offen“, „In Bearbeitung“ oder „Erledigt“ und eine konkrete fehlende Eingabe.
- [ ] Das Postfach kann erst als erledigt markiert werden, wenn Empfang und Versand erfolgreich getestet wurden.
- [ ] Eine Testanfrage erstellt einen klar gekennzeichneten Testvorgang und kann anschließend vollständig gelöscht werden.
- [ ] Erst wenn alle Pflichtschritte erfüllt sind, kann die Website veröffentlicht werden.
- [ ] Der Inhaber kann Betriebsdaten später selbst ändern; Zugangsdaten zum Postfach werden nie wieder im Klartext angezeigt.

## Edge Cases
- Ein fehlgeschlagener Verbindungstest speichert keine unvollständige Einrichtung als erfolgreich.
- Abbruch eines Onboarding-Termins erhält bereits gespeicherte Eingaben.
- Eine Domain darf nicht gleichzeitig zwei aktiven Mandanten zugeordnet sein.
- Testvorgänge sind in Auswertungen und Nummernkreisen ausgeschlossen.

## Technical Requirements
- Security: E-Mail-Zugangsdaten sind nur für Verbindung und Versand nutzbar, nicht über die Oberfläche auslesbar.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
