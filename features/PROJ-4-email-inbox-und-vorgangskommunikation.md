# PROJ-4: E-Mail-Inbox und Vorgangskommunikation

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — geschützter Mandanten- und Nutzerkontext.
- Requires: PROJ-3 — Kunden, Vorgänge und Dokumente.

## Reuse aus ImmoCRM
- IMAP/SMTP-Verbindung, MIME-Parsing, Anhänge, Polling und Fehlerprotokoll extrahieren; Immobilienzuordnung und Monolith nicht übernehmen.

## User Stories
- Als Büro möchte ich E-Mail-Anfragen in derselben Inbox wie Webanfragen sehen.
- Als Inhaber möchte ich aus einem Vorgang antworten, damit kein zweiter Posteingang entsteht.
- Als Büro möchte ich erkennen, wenn die Postfachanbindung gestört ist.

## Acceptance Criteria
- [ ] Ein Inhaber kann ein Betriebspostfach verbinden und Empfang sowie Versand vor dem Speichern testen.
- [ ] Neue E-Mails werden als neuer Vorgang oder als Nachricht am passenden bestehenden Vorgang abgelegt; Anhänge werden mitgespeichert.
- [ ] Büro und Inhaber können eine E-Mail im Vorgang schreiben, prüfen und senden; gesendete Nachricht und Versandzeit erscheinen im Verlauf.
- [ ] Antworten auf eine gesendete E-Mail werden demselben Vorgang zugeordnet, sofern eine eindeutige Thread-Zuordnung möglich ist.
- [ ] Bei nicht erreichbarem Postfach zeigt die Inbox eine sichtbare Warnung „E-Mail-Abruf fehlgeschlagen. Bitte Verbindung prüfen.“
- [ ] Nur Inhaber und Büro dürfen externe E-Mails senden.

## Edge Cases
- Unbekannte Absender werden als neuer Vorgang angelegt; bekannte Absender werden nicht blind mit einem beliebigen alten Vorgang verknüpft.
- Nicht unterstützte oder gefährliche Anhänge werden nicht ausgeführt und mit „Anhang konnte nicht verarbeitet werden.“ markiert.
- Eine E-Mail ohne Text, aber mit Anhang, wird dennoch verarbeitet.
- Doppelt abgeholte Nachrichten werden anhand stabiler Mail-Kennung nicht erneut angelegt.

## Technical Requirements
- Security: Zugangsdaten verschlüsselt speichern; HTML-E-Mail-Inhalte vor Anzeige bereinigen.
- Reliability: Polling-Fehler protokollieren und je Konto sichtbar machen.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
