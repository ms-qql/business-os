# PROJ-5: Angebote, PDF, Freigabe und Versand

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-3 — Vorgang, Kunde, Dokumente.
- Requires: PROJ-4 — Versand aus dem Betriebspostfach.

## Reuse aus ImmoCRM
- Dokument-Speicher und E-Mail-Versand wiederverwenden. Leistungspositionen, Angebots-PDF und Freigabeansicht neu erstellen.

## User Stories
- Als Inhaber möchte ich für einen Vorgang ein Angebot mit einfachen Positionen erstellen.
- Als Büro möchte ich einen Angebotsentwurf prüfen lassen, bevor er versendet wird.
- Als Kunde möchte ich ein lesbares Angebot als PDF erhalten.

## Acceptance Criteria
- [ ] Inhaber und Büro können einem Angebot frei benannte Positionen mit Menge, Einheit, Einzelpreis, Steuersatz und Rabatt hinzufügen, ändern und entfernen.
- [ ] Das System berechnet Netto-, Steuer- und Bruttosumme nachvollziehbar aus den Positionen.
- [ ] Ein Angebot zeigt Angebotsnummer, Betriebs- und Kundendaten, Gültigkeitsdatum, Positionen, Summen und Freitext.
- [ ] Vor dem Versand zeigt eine Freigabeansicht Empfänger, Betreff, PDF und Gesamtsumme; erst der ausdrückliche Klick „Angebot senden“ versendet.
- [ ] Nach Versand werden PDF, Version, Empfänger und Zeitpunkt unveränderbar am Vorgang abgelegt und der Status wechselt auf „Angebot offen“.
- [ ] Entwürfe können gespeichert werden; sie werden nie automatisch versendet.

## Edge Cases
- Angebot ohne Position oder Empfänger kann nicht freigegeben werden.
- Nach Versand kann ein Angebot nicht überschrieben, sondern nur als neue Version erstellt werden.
- Rundungsdifferenzen werden konsistent auf zwei Nachkommastellen ausgewiesen.
- Fällt der E-Mail-Versand fehl, bleibt das Angebot ein Entwurf und zeigt „Angebot wurde nicht versendet.“

## Technical Requirements
- Security: Nur Inhaber und Büro dürfen Angebote erzeugen oder versenden.
- Audit: Freigabe und Versand werden mit Nutzer und Zeitpunkt protokolliert.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
