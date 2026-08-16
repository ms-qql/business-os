# PROJ-3: Kunden, Objekte, Vorgänge und Dokumente

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — mandantengetrennte Zugriffe und Rollen.

## Reuse aus ImmoCRM
- Upload-, Download- und Löschpfade des Objektspeichers werden vereinfacht übernommen. Das SHK-Vorgangsmodell ist neu.

## User Stories
- Als Büro möchte ich aus jeder Anfrage einen Kunden und Vorgang sehen, damit nichts verloren geht.
- Als Inhaber möchte ich Kundenobjekte und Historie sehen, um die Arbeit einordnen zu können.
- Als Büro möchte ich Fotos und PDFs am Vorgang ablegen, damit alle Informationen an einer Stelle sind.
- Als Inhaber möchte ich Vorgänge nach Status filtern, um den Tagesüberblick zu behalten.

## Acceptance Criteria
- [ ] Ein Vorgang enthält Status, Quelle, Anliegen, Kunde, optionales Objekt, Notizen, Anhänge und Zeitstempel.
- [ ] Zulässige Status sind „Neu“, „Rückruf“, „Angebot offen“, „Termin geplant“, „Erledigt“ und „Abgeschlossen“.
- [ ] Büro und Inhaber können Kunden, Objekte und Vorgänge anlegen, bearbeiten, suchen und nach Status filtern.
- [ ] Anhänge sind nur berechtigten Nutzern des Mandanten zugänglich; sie können als Foto oder PDF hochgeladen und heruntergeladen werden.
- [ ] Jeder Vorgang zeigt seine Änderungen und zugehörigen Dokumente chronologisch.
- [ ] Das Löschen eines Kunden ist gesperrt, solange Vorgänge oder Rechnungen bestehen.

## Edge Cases
- Gleiche E-Mail oder Telefonnummer erzeugt einen Hinweis auf einen möglichen Bestandskunden, aber keine automatische Zusammenführung.
- Ein gelöschter Anhang bleibt in bereits erzeugten PDFs nicht als kaputter Link sichtbar.
- Ein Monteur kann nur den ihm zugewiesenen Vorgang lesen und keine Kundendaten ändern.
- Fehlende Objektadresse ist erlaubt, wenn die Anfrage noch nicht qualifiziert wurde.

## Technical Requirements
- Security: Dokument-URLs sind nicht öffentlich und werden nur berechtigt ausgeliefert.
- Performance: Vorgangsliste lädt paginiert und filterbar.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
