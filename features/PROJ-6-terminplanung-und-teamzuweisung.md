# PROJ-6: Terminplanung und Teamzuweisung

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-3 — Vorgang und zugehörige Adresse.

## Reuse aus ImmoCRM
- Kalenderfenster und Verfügbarkeitsverhalten dienen als Vorlage; Makler-, Besichtigungs- und Buchungslogik wird nicht übernommen.

## User Stories
- Als Büro möchte ich einen Vorgang als Termin planen und einem Teammitglied zuweisen.
- Als Monteur möchte ich meine eigenen Termine mit Adresse und Auftragsnotiz sehen.
- Als Inhaber möchte ich die Termine des kleinen Teams im Überblick sehen.

## Acceptance Criteria
- [ ] Büro und Inhaber können einen Termin mit Beginn, Ende, Adresse, Notiz und einem oder mehreren Teammitgliedern anlegen, ändern oder absagen.
- [ ] Die Kalenderansicht zeigt Tag und Woche für maximal drei aktive Teammitglieder.
- [ ] Ein Termin verweist auf genau einen Vorgang; ein Vorgang kann mehrere Termine haben.
- [ ] Beim Anlegen oder Verschieben warnt das System bei zeitlicher Überschneidung desselben Teammitglieds.
- [ ] Monteure sehen nur eigene Termine sowie Adresse, Kontakt, Anliegen und freigegebene Anhänge; Preise sind nicht sichtbar.
- [ ] Ein geplanter Termin setzt den Vorgang auf „Termin geplant“.

## Edge Cases
- Termin ohne vollständige Adresse ist erlaubt, aber als „Adresse offen“ markiert.
- Eine Absage entfernt den Termin nicht aus der Historie.
- Deaktivierte Nutzer können nicht neu zugewiesen werden; bestehende Zuweisungen bleiben nachvollziehbar.
- Zeitzonen werden für alle Termine einheitlich als Europa/Berlin behandelt.

## Technical Requirements
- Mobile: Tagesansicht ist ab 375 px bedienbar.
- Performance: Wochenansicht lädt nur den sichtbaren Zeitraum.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
