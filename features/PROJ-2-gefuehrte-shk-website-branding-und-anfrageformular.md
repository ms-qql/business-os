# PROJ-2: Geführte SHK-Website, Branding und Anfrageformular

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — Mandant und Inhaberzugriff.

## Reuse aus ImmoCRM
- Logo-Speicher und Betriebs-Settings als Vorlage. Öffentliche Website und Formulare werden neu gebaut.

## User Stories
- Als Inhaber möchte ich Logo, Kontaktdaten und Leistungen hinterlegen, damit meine Website professionell wirkt.
- Als Interessent möchte ich eine Leistung finden und eine Anfrage auch mit Fotos absenden.
- Als Interessent möchte ich eine klare Bestätigung erhalten, damit ich weiß, dass die Anfrage angekommen ist.

## Acceptance Criteria
- [ ] Jeder Betrieb erhält eine geführte SHK-Vorlage mit Startseite, Leistungen, Über-uns-/Kontaktbereich, Impressum und Datenschutzhinweis.
- [ ] Inhaber können Logo, Farben, Firmenname, Adresse, Telefonnummer, E-Mail, Öffnungszeiten und vorgegebene Leistungsseiten ändern.
- [ ] Das Formular erfasst Name, Kontaktweg, Adresse, Anliegen, Dringlichkeit, gewünschtes Zeitfenster und bis zu fünf Bilder.
- [ ] Pflichtfelder werden vor Versand mit deutscher Feldmeldung angezeigt; die Website bleibt ohne Anmeldung nutzbar.
- [ ] Eine erfolgreiche Formularübermittlung erzeugt genau einen Vorgang im richtigen Mandanten und zeigt „Vielen Dank. Wir melden uns zeitnah bei Ihnen.“
- [ ] Öffentliche Seiten sind mobil bedienbar und je Mandant nur über dessen Domain erreichbar.

## Edge Cases
- Ungültige oder zu große Dateien werden abgewiesen, ohne die bereits eingegebenen Formulardaten zu verlieren.
- Ein unbekannter oder inaktiver Domainname zeigt keine Daten eines anderen Betriebs.
- Mehrfaches Absenden derselben Anfrage erzeugt keine doppelten Vorgänge.
- Ein nicht gepflegtes Leistungsangebot blendet die betreffende Leistungsseite aus.

## Technical Requirements
- Security: Rate-Limit und Bot-Schutz am öffentlichen Formular; Uploads serverseitig prüfen.
- Accessibility: Beschriftete Felder, Tastaturbedienung und verständliche Fehlermeldungen.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-16 · **Stack:** Next.js 16 + FastAPI + PostgreSQL (RLS) + MinIO · **Branch:** dev

### Ziel und Umfang

PROJ-2 liefert pro Betrieb eine öffentliche, mobil nutzbare SHK-Website mit
einer festen Seitenstruktur und einem Anfrageformular. Der Inhaber pflegt nur
die vorgesehenen Betriebs- und Inhaltsfelder. Eine freie Seitenerstellung,
eigene Layouts, E-Mail-Empfang und die fachliche Bearbeitung des Vorgangs sind
nicht Teil dieses Features.

### Komponentenstruktur

```text
Öffentliche Betriebswebsite (über die Betriebsdomain)
├── Startseite
│   ├── Kopfbereich mit Logo, Kontakt und Handlungsaufruf
│   ├── Leistungsübersicht
│   └── Über-uns- und Kontaktbereich
├── Leistungsseite (nur für gepflegte Leistungen)
├── Anfrageformular
│   ├── Kontaktdaten, Adresse und Anliegen
│   ├── Dringlichkeit und Zeitfenster
│   ├── Fotoauswahl (maximal fünf Bilder)
│   └── Bestätigungsseite
└── Impressum und Datenschutzhinweis

Angemeldete Betriebszentrale (nur Inhaber)
└── Website-Einstellungen
    ├── Branding und Kontaktdaten
    ├── Öffnungszeiten und Leistungsseiten
    └── Domainstatus
```

Die öffentliche Route löst den Betrieb ausschließlich über den angefragten
Hostnamen auf. Unbekannte oder deaktivierte Domains enden auf einer neutralen
Nicht-gefunden-Seite; sie zeigen niemals einen anderen Betrieb.

### Datenmodell

- **Website-Einstellungen:** genau ein Datensatz je Mandant mit Firmenname,
  Logo, Farben, Kontakt- und Adressdaten, Öffnungszeiten sowie Domainstatus.
- **Leistungsseite:** vordefinierte SHK-Leistung mit aktivem/inaktivem Status
  und den dafür freigegebenen Textfeldern. Inaktive Leistungen werden weder
  verlinkt noch direkt ausgeliefert.
- **Öffentliche Domain:** eindeutige Zuordnung eines Hostnamens zu einem
  aktiven Mandanten. Sie ist die alleinige Quelle für den öffentlichen
  Mandantenkontext.
- **Anfrage:** ein neuer Vorgang mit Name, gewähltem Kontaktweg, Adresse,
  Anliegen, Dringlichkeit, Zeitfenster, Eingangszeitpunkt und Quelle
  `Website`.
- **Anfragebild:** ein geprüftes Bildobjekt mit Bezug zur Anfrage; die
  Binärdatei liegt in MinIO, die Metadaten im Vorgang.
- **Übermittlungskennung:** vom Browser einmalig erzeugte Kennung je
  Formularversuch. Sie verhindert bei Wiederholung genau denselben Vorgang
  innerhalb eines Mandanten.

Alle neuen Geschäftsdaten tragen die Mandantenkennung und unterliegen dem in
PROJ-1 festgelegten RLS-Kontext. Der öffentliche Endpunkt übernimmt den
Mandanten nie aus einer Browserangabe, sondern aus der bestätigten Domain.

### API-Form

- `GET /public/site` → öffentliche Website-Einstellungen und nur aktive
  Leistungsseiten für die aufgelöste Domain liefern.
- `GET /public/leistungen/{slug}` → eine aktive Leistungsseite der
  aufgelösten Domain liefern; inaktive oder fremde Seiten wie nicht vorhanden
  behandeln.
- `POST /public/anfragen/uploads` → bis zu fünf Bilddateien für einen
  begonnenen Formularversuch entgegennehmen und serverseitig prüfen.
- `POST /public/anfragen` → Anfrage samt gültigen Upload-Referenzen genau
  einmal als Vorgang im per Domain ermittelten Mandanten anlegen.
- `GET /website-settings` → Website-Einstellungen des angemeldeten Inhabers
  lesen.
- `PATCH /website-settings` → Branding, Kontaktdaten, Öffnungszeiten und
  Leistungsinhalte des eigenen Betriebs ändern (nur Inhaber).
- `POST /website-settings/logo` → ein geprüftes Logo ablegen und die
  Einstellung aktualisieren (nur Inhaber).

Öffentliche Endpunkte verlangen keine Sitzung. Sie sind auf die aufgelöste
Domain, Formulardaten und geprüfte Upload-Referenzen begrenzt; alle
Einstellungen-Endpunkte verwenden den Mandantenkontext aus PROJ-1.

### Technische Entscheidungen

- **Eine feste Vorlage statt Baukasten:** deckt alle Akzeptanzkriterien ab und
  vermeidet einen zweiten, nicht validierten Produktbereich.
- **Next.js für öffentliche und angemeldete Flächen:** servergerenderte
  öffentliche Seiten bleiben mobil schnell und suchmaschinenfreundlich,
  während Website-Einstellungen dieselbe Anwendung und dieselben
  Design-Tokens nutzen.
- **Domain als öffentliche Mandantengrenze:** verhindert, dass ein
  URL-Parameter oder ein Formularfeld einen fremden Betrieb auswählen kann.
- **FastAPI als Schreibgrenze:** validiert Pflichtfelder und Dateien auch bei
  manipuliertem Browser, löst den Mandanten aus der Domain auf und erstellt
  den Vorgang atomar.
- **MinIO nur für Logo und Bilder:** Binärdaten gehören nicht in PostgreSQL;
  Datenbankeinträge referenzieren ausschließlich geprüfte Objektpfade.
- **Doppelschutz für Formularversand:** der Browser sperrt den Senden-Knopf;
  die serverseitige Übermittlungskennung macht Wiederholungen auch bei
  Netzabbrüchen idempotent.
- **Rate-Limit und Honeypot am öffentlichen Eingang:** begrenzen
  automatisierten Missbrauch, ohne eine Anmeldung oder einen externen
  Captcha-Anbieter zur Pflicht zu machen. Upload-Größe, Bildformat und Anzahl
  werden vor der Speicherung serverseitig geprüft.
- **Keine E-Mail-Zustellung in PROJ-2:** die Bestätigung ist eine Website-Seite;
  die Inbox- und Kommunikationskette folgt bewusst erst in PROJ-4.

### Abhängigkeiten

- **Next.js 16, Tailwind und shadcn/ui:** responsive Website und zugängliche
  Einstellungsformulare.
- **FastAPI und Pydantic:** öffentliche Formulareingänge sowie geschützte
  Inhaber-Einstellungen.
- **PostgreSQL mit RLS:** Mandantentrennung für Einstellungen und Vorgänge.
- **MinIO:** Logo- und Bildobjekte.
- **Kein neues Drittanbieterpaket vorgesehen:** Browser-Formularfunktionen,
  vorhandene Authentifizierung und serverseitige Validierung genügen für V1.

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
