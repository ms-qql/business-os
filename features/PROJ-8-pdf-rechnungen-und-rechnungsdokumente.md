# PROJ-8: PDF-Rechnungen und Rechnungsdokumente

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-3 — Kunde, Vorgang und Dokumentablage.
- Requires: PROJ-5 — Angebotspositionen, PDF- und Versandablauf.

## Reuse aus ImmoCRM
- Dokument-Speicher und Versandpfade als Vorlage. Rechnungsnummern, Vorlage und fachliche Regeln werden neu umgesetzt.

## User Stories
- Als Inhaber möchte ich aus einem erledigten Vorgang eine einfache PDF-Rechnung erstellen.
- Als Büro möchte ich Rechnungen am Vorgang wiederfinden und per E-Mail senden.
- Als Inhaber möchte ich den Zahlungsstatus sehen, ohne eine Buchhaltung zu führen.

## Acceptance Criteria
- [ ] Inhaber und Büro können eine Rechnung mit Rechnungsnummer, Rechnungsdatum, Leistungsdatum, Kundendaten, Positionen, Netto-, Steuer- und Bruttosummen erstellen.
- [ ] Rechnungspositionen können aus einem Angebot übernommen und vor Freigabe angepasst werden.
- [ ] Die Freigabeansicht zeigt Empfänger, Betreff, PDF und Gesamtsumme; erst „Rechnung senden“ löst den Versand aus.
- [ ] Nach Versand werden PDF, Version, Empfänger und Zeitpunkt unveränderbar am Vorgang gespeichert.
- [ ] Der Zahlungsstatus ist „Offen“, „Bezahlt“ oder „Storniert“ und wird manuell gepflegt.
- [ ] V1 erzeugt nur PDF; kein XRechnung-, ZUGFeRD-, DATEV- oder Buchhaltungsexport.

## Edge Cases
- Eine Rechnung ohne Leistungsdatum, Kundendaten oder Positionen kann nicht freigegeben werden.
- Eine vergebene Rechnungsnummer wird nie erneut vergeben, auch nicht nach einer Stornierung.
- Eine Korrektur nach Versand erfolgt als Storno oder neue Rechnung, nicht durch Änderung des versendeten Dokuments.
- Fehlgeschlagener Versand ändert den Zahlungsstatus nicht und zeigt „Rechnung wurde nicht versendet.“

## Technical Requirements
- Security: Nur Inhaber und Büro dürfen Rechnungen erstellen, freigeben oder den Zahlungsstatus ändern.
- Audit: Nummernvergabe, Freigabe, Versand und Storno werden protokolliert.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
