# PROJ-8: PDF-Rechnungen und Rechnungsdokumente

## Status: In Review
**Created:** 2026-08-16

## Annahmen
- PROJ-8 deckt die einfache, manuell freigegebene Rechnung nach Abschluss eines Vorgangs ab. Zahlungsabwicklung, Buchhaltung, strukturierte E-Rechnungen und Mahnungen gehören nicht zu diesem Feature.
- Pro Mandant sind vollständige Rechnungsstellerdaten und eine gültige Steuerkennzeichnung bereits vor der Rechnungsfreigabe gepflegt.

## Dependencies
- Requires: PROJ-3 — Kunde, Vorgang und Dokumentablage.
- Requires: PROJ-5 — Angebotspositionen, PDF- und Versandablauf.

## Reuse aus ImmoCRM
- Dokument-Speicher und Versandpfade als Vorlage. Rechnungsnummern, Vorlage und fachliche Regeln werden neu umgesetzt.

## Umfang und Abgrenzung
- Eine Rechnung wird aus einem erledigten Vorgang als Entwurf erstellt, geprüft, ausdrücklich versendet und am Vorgang abgelegt.
- Positionen eines vorhandenen Angebots dürfen als Ausgangspunkt übernommen werden; sie bleiben im Rechnungsentwurf fachlich anpassbar.
- Die Rechnung bildet keinen Zahlungseingang ab. Der Zahlungsstatus ist ausschließlich eine manuelle Betriebsnotiz.
- Kein XRechnung-, ZUGFeRD-, DATEV- oder Buchhaltungsexport, keine Zahlungsanbieter-Anbindung, keine Mahnungen und keine automatische Rechnungserstellung.

## User Stories
- Als Inhaber möchte ich aus einem erledigten Vorgang eine einfache PDF-Rechnung erstellen.
- Als Büro möchte ich Rechnungen am Vorgang wiederfinden und per E-Mail senden.
- Als Inhaber möchte ich den Zahlungsstatus sehen, ohne eine Buchhaltung zu führen.
- Als Büro möchte ich Angebotspositionen übernehmen und vor dem Versand für die tatsächlich erbrachte Leistung anpassen.
- Als Kunde möchte ich eine lesbare Rechnung erhalten, aus der Rechnungsnummer, Leistung, Steuer und Gesamtbetrag eindeutig hervorgehen.

## Acceptance Criteria
- [ ] Inhaber und Büro können nur aus einem Vorgang mit Status „Erledigt“ einen Rechnungsentwurf anlegen; bei jedem anderen Vorgangsstatus wird die Anlage mit einer deutschen Hinweismeldung abgelehnt.
- [ ] Jeder Rechnungsentwurf enthält Rechnungsnummer, Rechnungsdatum, Leistungsdatum, vollständige Rechnungssteller- und Kundendaten, mindestens eine Position sowie Netto-, Steuer- und Bruttosumme.
- [ ] Jede Position enthält Bezeichnung, Menge, Einheit, Netto-Einzelpreis und Steuersatz; die sichtbaren Summen werden aus den Positionen konsistent auf zwei Nachkommastellen berechnet.
- [ ] Für einen Vorgang mit Angebot können Inhaber und Büro dessen Positionen in einen neuen Rechnungsentwurf übernehmen und danach Positionen, Mengen, Preise und Steuersätze vor dem Versand ändern.
- [ ] Vor dem Versand zeigt die Freigabeansicht Empfänger, Betreff, Rechnungsnummer, PDF-Vorschau und Bruttosumme. Nur der ausdrückliche Klick „Rechnung senden“ löst den Versand aus.
- [ ] Eine versendete Rechnung speichert unveränderbar das versendete PDF, Rechnungsnummer, Empfänger, Versandzeitpunkt und zugehörige Rechnungsfassung am Vorgang.
- [ ] Der manuell pflegbare Zahlungsstatus einer versendeten Rechnung ist genau „Offen“, „Bezahlt“ oder „Storniert“; eine Statusänderung verändert weder PDF noch Rechnungspositionen.
- [ ] Eine Korrektur einer versendeten Rechnung erfolgt ausschließlich als Storno der ursprünglichen Rechnung oder als neue Rechnung; die ursprüngliche Rechnung bleibt abrufbar.
- [ ] Nur Inhaber und Büro dürfen Rechnungen erstellen, freigeben, senden, stornieren oder den Zahlungsstatus ändern. Monteure sehen keine Rechnungsdaten.
- [ ] V1 stellt Rechnungen ausschließlich als PDF bereit und bietet keine E-Rechnung, keinen DATEV-/Buchhaltungsexport, keine Mahnung und keine automatische Rechnungserstellung an.

## Edge Cases
- Eine Rechnung ohne Leistungsdatum, Kundendaten oder Positionen kann nicht freigegeben werden.
- Eine vergebene Rechnungsnummer wird nie erneut vergeben, auch nicht nach einer Stornierung.
- Eine Korrektur nach Versand erfolgt als Storno oder neue Rechnung, nicht durch Änderung des versendeten Dokuments.
- Fehlgeschlagener Versand ändert den Zahlungsstatus nicht und zeigt „Rechnung wurde nicht versendet.“
- Ein Vorgang ohne Kunden-E-Mail kann als Entwurf vorbereitet, aber nicht per E-Mail versendet werden; die Freigabe nennt die fehlende E-Mail-Adresse.
- Rundungsdifferenzen werden je Position auf zwei Nachkommastellen ausgewiesen und ergeben exakt die angezeigten Gesamtbeträge.
- Zwei gleichzeitige Freigaben dürfen keine identische Rechnungsnummer erzeugen; eine einmal vergebene Nummer bleibt reserviert.
- Wird eine Rechnung nach Versand auf „Storniert“ gesetzt, bleibt das versendete Original-PDF verfügbar und eindeutig als storniert erkennbar.

## Nachvollziehbarkeit
- Nummernvergabe, Freigabe, Versand, Zahlungsstatusänderung und Storno sind mit Nutzer und Zeitpunkt am Vorgang nachvollziehbar.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-19 · **Stack:** Next.js/shadcn + FastAPI + PostgreSQL/raw SQL/RLS + MinIO/Dokploy · **Branch:** main

### Ausgangslage und Ziel
PROJ-8 ergänzt den bestehenden Angebotsablauf (`angebote`) um eine eigene Rechnungsdomäne. Sie nutzt denselben Vorgang, Dokument-Speicher, PDF-Renderer und E-Mail-Versand; Angebot und Rechnung bleiben jedoch getrennte fachliche Objekte. Ein Angebot ist verhandelbar und versionierbar, eine versendete Rechnung ist ein unveränderlicher Beleg.

Der bestehende Code enthält derzeit nur `mandanten.name` und beim Kunden Name/E-Mail/Telefon; vollständige Rechnungssteller- und Empfängeranschriften existieren noch nicht. Deshalb gehört ein Rechnungsstellerprofil sowie die Entnahme der Kundenanschrift aus dem zum Vorgang gehörenden Objekt verbindlich in diese Umsetzung. Ohne vollständige Snapshot-Daten darf keine Freigabe erfolgen.

### A) Komponentenstruktur (Next.js)
```
VorgangDetail (bestehend; nur Inhaber/Büro)
└── VorgangRechnungen (neu, neben VorgangAngebote)
    ├── RechnungListe (Nummer, Status, Betrag, Zahlungsstatus, PDF)
    ├── RechnungEntwurf
    │   ├── Kopfdaten (Rechnungs-/Leistungsdatum)
    │   ├── AngebotspositionenUebernehmen (optional)
    │   ├── RechnungspositionenTabelle
    │   └── SummenBlock (Serverwerte)
    └── RechnungFreigabe
        ├── EmpfaengerUndBetreff
        ├── PdfVorschau
        ├── Bruttosumme
        └── RechnungSenden (einzige Versandaktion)

Einstellungen/Rechnungssteller (neu, nur Inhaber)
└── RechnungsstellerprofilForm (Name, ladungsfähige Anschrift, Steuerkennzeichnung)
```
Monteur sieht weder Rechnungs-Card noch Rechnungs-API-Daten. Das Backend erzwingt dies unabhängig von der UI.

### B) Datenmodell und Unveränderlichkeit
Alle neuen Fachtabellen tragen `mandant_id`. FastAPI liest ihn ausschließlich aus dem JWT; raw-SQL-Queries filtern zusätzlich nach `mandant_id`; PostgreSQL-RLS beschränkt jede Tabelle auf `app.current_mandant_id`.

- **rechnungsstellerprofil:** genau ein fachliches Profil je Mandant: Name, vollständige Anschrift sowie Steuerkennzeichnung. Es ist Quelle für neue Entwürfe, nicht für bereits versendete Belege.
- **rechnung:** gehört zu einem Vorgang. Felder: Nummer, Rechnungs- und Leistungsdatum, Status (`entwurf`, `versendet`, `storniert`), Zahlungsstatus (`Offen`, `Bezahlt`, `Storniert`), Summen, Empfänger-E-Mail, Freigabe-/Versandzeitpunkt, versendender Nutzer, Verweis auf aktuelle Rechnungsfassung und optionaler Stornozeitpunkt/-nutzer. Eine versendete oder stornierte Rechnung ist nicht mehr änderbar. Der Kunde ist über den Vorgang referenziert; ein Kunde mit Rechnung darf nicht gelöscht werden.
- **rechnung_position:** gehört nur zum Entwurf: Bezeichnung, Menge, Einheit, Netto-Einzelpreis, Steuersatz, Sortierung. Netto, Steuer und Brutto werden pro Position auf zwei Nachkommastellen gerundet und daraus aggregiert. Keine Rabatte in V1: Rechnungen übernehmen daraus resultierende Angebotswerte als Preise, nicht Angebotsrabattlogik.
- **rechnung_fassung:** bei erfolgreichem Versand exakt eine unveränderliche Fassung. Sie hält den Rechnungs-Kopf, Rechnungssteller-Snapshot, Kunden-/Objektanschrift-Snapshot, Positionen und Summen als Belegstand sowie `dokument_id`. Spätere Stammdatenänderungen berühren sie nicht.
- **rechnung_nummernkreis:** ein Zähler pro Mandant. Nummer wird beim Anlegen des Entwurfs reserviert, damit sie bereits im Entwurf sichtbar und auch bei Storno nie wiederverwendet ist. Der Zähler wird innerhalb einer DB-Transaktion gesperrt und erhöht; eine zusätzliche eindeutige DB-Constraint auf `(mandant_id, rechnungsnummer)` ist die zweite Absicherung gegen parallele Anfragen.
- **vorgang_dokument (bestehend):** speichert nur Metadaten und MinIO-Objektpfad des versendeten PDFs. Das Objekt liegt z. B. unter `rechnungen/<mandant>/<rechnung>/<nummer>.pdf`; öffentliche URLs werden nie gespeichert, nur berechtigte kurzlebige Download-URLs erzeugt.
- **vorgang_historie (bestehend):** protokolliert Nummernreservierung, Positionsübernahme, Freigabevorbereitung, Versand, Zahlungsstatuswechsel und Storno mit Nutzer und Zeitpunkt.

**Storno:** `POST /rechnungen/{id}/storno` setzt Fach- und Zahlungsstatus auf `storniert`/`Storniert`, bewahrt Fassung/PDF unverändert und erzeugt keinen Ersatzbeleg. Eine Korrektur ist danach nur ein separater neuer Entwurf aus demselben erledigten Vorgang, mit neuer Nummer und neuer Fassung.

### C) API-Contracts und Rollen
Alle folgenden Endpunkte verlangen JWT und `require_role("Buero", "Inhaber")`; `mandant_id` kommt nie aus Request-Pfad oder Body. Monteur erhält 403, auch bei erratenen IDs.

| Methode + Pfad | Aktion / Vertrag |
|---|---|
| `GET /einstellungen/rechnungssteller` | Profil für Freigabe-Voraussetzung lesen; Inhaber. |
| `PUT /einstellungen/rechnungssteller` | Profil vollständig speichern; Inhaber. |
| `GET /vorgaenge/{id}/rechnungen` | Rechnungen des Vorgangs, neueste zuerst; Büro/Inhaber. |
| `POST /vorgaenge/{id}/rechnungen` | Entwurf samt reservierter Rechnungsnummer anlegen. Nur `vorgang.status = Erledigt`; sonst 409 mit deutscher Hinweismeldung. Body enthält Rechnungs-/Leistungsdatum und optional `angebot_id` zur Übernahme. |
| `GET /rechnungen/{id}` | Entwurf bzw. Beleg inkl. Positionen, Summen, Zahlungs- und Stornostatus lesen. |
| `PATCH /rechnungen/{id}` | Nur Entwurf: Rechnungs-/Leistungsdatum und Empfänger-E-Mail ändern. |
| `POST /rechnungen/{id}/positionen` | Nur Entwurf: Position anlegen. |
| `PATCH /rechnungen/{id}/positionen/{position_id}` | Nur Entwurf: Position ändern. |
| `DELETE /rechnungen/{id}/positionen/{position_id}` | Nur Entwurf: Position entfernen. |
| `POST /rechnungen/{id}/freigabe` | Prüft vollständige Snapshot-Daten, mindestens eine Position, Leistungsdatum und Empfänger; rendert serverseitig PDF-Vorschau aus gespeicherten Daten, versendet nichts; liefert Empfänger, Betreff, Nummer, Summen, PDF-URL. |
| `POST /rechnungen/{id}/senden` | Nur nach erfolgreicher Freigabe; verschickt über bestehenden `send_vorgang_email`-Pfad, schreibt Fassung/PDF/Versandmetadaten atomar fachlich zusammen und setzt Status `versendet`. Versandfehler lässt Entwurf und Zahlungsstatus unverändert und liefert „Rechnung wurde nicht versendet.“ |
| `GET /rechnungen/{id}/pdf` | Kurzlebige berechtigte URL: Entwurfs-Vorschau oder unveränderliches Versand-PDF. |
| `PATCH /rechnungen/{id}/zahlungsstatus` | Nur versendet: genau `Offen`, `Bezahlt` oder `Storniert`; ändert nie PDF, Fassung oder Positionen. `Storniert` wird ausschließlich durch den Storno-Endpunkt gesetzt. |
| `POST /rechnungen/{id}/storno` | Nur versendet: Original stornieren, Audit schreiben; PDF bleibt lesbar und als storniert markiert. |

### D) Schreib-Owner und Lesepfade (verbindlich)

| Entität | Schreib-Owner | Benötigter Lesepfad vor Schreiben | Regel |
|---|---|---|---|
| **rechnungsstellerprofil** | Inhaber über `PUT /einstellungen/rechnungssteller` / Einstellungen-Screen | `GET /einstellungen/rechnungssteller` | Profil ist vollständiger Freigabe-Input; Büro kann es lesen, aber nicht ändern. |
| **rechnung (Entwurf + Nummer)** | Büro/Inhaber über `POST /vorgaenge/{id}/rechnungen` | `GET /vorgaenge/{id}` (Status `Erledigt`, Kunde, Objekt); optional `GET /vorgaenge/{id}/angebote` und `GET /angebote/{angebot_id}` vor Übernahme | Service prüft Vorgang, Angebotszugehörigkeit und Status serverseitig; Nummer intern reservieren. |
| **rechnung_position** | Büro/Inhaber über `POST/PATCH/DELETE /rechnungen/{id}/positionen*` | `GET /rechnungen/{id}` | Nur im Entwurf; Antwort liefert stets serverberechnete Summen. |
| **rechnung_nummernkreis** | kein Nutzer; Rechnungsservice innerhalb von `POST /vorgaenge/{id}/rechnungen` | keiner, systemintern | Transaktionssperre + Unique-Constraint; niemals API-schreibbar. |
| **rechnung_fassung** | Rechnungsservice ausschließlich bei erfolgreichem `POST /rechnungen/{id}/senden` | Erfolgreiches `POST /rechnungen/{id}/freigabe`, das geprüfte gespeicherte Daten/PDF zeigt | Nicht per Client editierbar; sendet exakt diesen Snapshot. |
| **vorgang_dokument für Rechnungs-PDF** | Rechnungsservice bei Freigabe-Vorschau bzw. Versand, kein Client-Upload | `GET /rechnungen/{id}` bzw. erfolgreicher Freigabepfad | Nach Versand kein Update/Delete über Rechnungswege. |
| **rechnung.status / Versandmetadaten** | Büro/Inhaber nur via `POST /rechnungen/{id}/senden` | `POST /rechnungen/{id}/freigabe` erfolgreich | Einziger Versandpfad; verhindert Auto-Versand. |
| **zahlungstatus und Storno** | Büro/Inhaber via Zahlungsstatus- bzw. Storno-Endpunkt | `GET /rechnungen/{id}` | Nur versendet; Statuswechsel erzeugt Historie, verändert Belegdaten nie. |
| **vorgang_historie** | Rechnungsservice als Nebeneffekt jedes oben genannten Fachschritts | Zugehörigkeit wurde im jeweiligen Rechnungs-Lesepfad geprüft | Kein direkter Client-Schreibpfad. |
| **Kunde-Löschsperre bei Rechnung (bestehender Pfad)** | Büro/Inhaber über bestehenden `DELETE /kunden/{id}`; `delete_kunde`-Service | `GET /kunden/{id}`; systemintern `has_vorgaenge(mandant_id, kunde_id)` und neu `has_rechnungen(mandant_id, kunde_id)` | `has_rechnungen` prüft mandantenbegrenzt Rechnungen des Kunden über deren Vorgang. Besteht mindestens eine, beendet der Service den Löschvorgang mit 409; die Rechnung und ihr Beleg bleiben erhalten. |

### E) Technische Entscheidungen (ADRs)
- **ADR-8-1 – Eigenständige Rechnungstabellen:** Keine Erweiterung von `angebot` oder `vorgang_dokument`. So bleiben Angebotsversionen und rechtlich relevante, unveränderliche Belege sauber getrennt; PDF-Ablage und Versand werden trotzdem wiederverwendet.
- **ADR-8-2 – Snapshot beim Versand:** Der Beleg darf nicht von späteren Änderungen an Kunde, Objekt oder Betrieb abhängen. PDF und `rechnung_fassung` entstehen nur aus serverseitig gespeicherten Daten; Client-HTML ist keine Quelle.
- **ADR-8-3 – Nummer beim Entwurf reservieren:** Erfüllt die sichtbare Rechnungsnummer im Entwurf und das Nie-Wiederverwenden. Mandantentrennter Zähler mit DB-Sperre plus Unique-Constraint löst parallele Entwürfe sicher ohne globale, informationsleckende Sequence.
- **ADR-8-4 – Freigabe und Versand bleiben zwei Schritte:** `freigabe` bereitet vor und verschickt nie. Nur `senden` löst SMTP aus; das übernimmt den vorhandenen E-Mail-/Thread-/Historienpfad mit optionalem PDF-Anhang.
- **ADR-8-5 – Zahlungsnotiz getrennt vom Beleg:** `zahlungstatus` ist keine Buchhaltung. Der Wechsel ändert ausschließlich Status/Historie; Storno bewahrt den Originalbeleg und sperrt Änderungen.
- **ADR-8-6 – Kein neues Frontend- oder PDF-Paket:** Next.js/shadcn-Komponenten sowie bestehende `xhtml2pdf`/Jinja- und MinIO-Pfade reichen. Kein Flutter, keine E-Rechnungs- oder Buchhaltungsintegration.

### F) Umsetzungsgrenzen und Abnahmekriterien
- `VorgangRechnungen` wird nur für Büro/Inhaber im bestehenden Vorgangsdetail angezeigt; Liste, Detail, PDF und alle Rechnungs-Endpunkte erhalten denselben Rollen-Guard.
- Angebotsübernahme kopiert nur Positionen in die neue Rechnung. Danach gibt es keine Kopplung: Rechnungspositionen dürfen geändert werden, Angebotspositionen bleiben unverändert.
- Freigabe lehnt fehlendes Rechnungsstellerprofil, fehlende Kunden-/Objektanschrift, Leistungsdatum, Position oder E-Mail mit deutscher Meldung ab. Ein fehlendes Objekt ist daher kein stiller Fallback auf eine unvollständige Kundenadresse.
- Die bestehende Kundenlöschung wird mit PROJ-8 vervollständigt: `delete_kunde` prüft neben Vorgängen auch `has_rechnungen(mandant_id, kunde_id)` im Kunden-Repository und lehnt bei vorhandener Rechnung mit 409 ab. Das schützt Entwürfe, versendete Belege und Stornos vor dem Verlust ihres Kundenbezugs.
- Keine automatische Rechnungsanlage, Mahnung, Zahlungsschnittstelle, DATEV-, XRechnung- oder ZUGFeRD-Ausgabe.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-19 (Re-Review nach Nachbesserung) · **Verdict:** Architected

### Re-Review (Runde 2)
Nachbesserung geprüft: Kunde-Löschsperre-Zeile in Abschnitt D + Umsetzungsgrenzen-Satz in Abschnitt F ergänzt (`has_rechnungen(mandant_id, kunde_id)`). Gegen Code verifiziert: `backend/app/features/kunden/routes.py:45-47` (`DELETE /kunden/{id}` → `delete_kunde`-Service), `kunden/repository.py:98-116` (bestehender `delete_kunde`, `has_vorgaenge`-Vorbild, ponytail-TODO für `has_rechnungen` genau an erwarteter Stelle). Kein weiterer offener Punkt.

### Checklist
- [x] Component structure — ok, `VorgangRechnungen`/`RechnungEntwurf`/`RechnungFreigabe` neben bestehendem `VorgangAngebote`; kein vages UI.
- [x] Data model — jede neue Tabelle trägt `mandant_id`; RLS-Ansatz konsistent zu `backend/sql/001_init.sql:92-110` (current_setting `app.current_mandant_id`).
- [x] API shape — jeder Endpoint mit Methode+Pfad+Rolle; `require_role("Buero","Inhaber")` deckt sich mit Muster `backend/app/features/angebote/routes.py:12`.
- [x] Tech decisions — 6 ADRs mit Begründung (Snapshot, Nummernreservierung, getrennte Zahlungsnotiz, kein neues Paket).
- [x] Dependencies — keine neuen Pakete; ADR-8-6 bestätigt Reuse von `xhtml2pdf` (`backend/app/features/angebote/pdf.py:29`) und MinIO `storage.put_object` (`backend/app/features/angebote/service.py:230`).
- [x] Branch field — `**Branch:** main` vorhanden.
- [x] Conflict-free — CodeGraph-Check: keine `rechnung*`-Tabelle in `backend/sql/001_init.sql`…`008_onboarding.sql`; kein `/einstellungen`-Präfix im Backend vorhanden. Keine Kollisionen.
- [x] Acceptance-criteria coverage — alle 10 AC auf Endpoints/Komponenten gemappt (u. a. AC1→`POST /vorgaenge/{id}/rechnungen` mit Statusprüfung, AC6→`rechnung_fassung` bei `senden`, AC9→`require_role`+Frontend-Guard).

### CodeGraph-Cross-Check (Belege)
- `backend/app/features/vorgaenge/schemas.py:8` — `VorgangStatus` enthält `"Erledigt"`, bestätigt AC1-Vorbedingung.
- `backend/app/features/vorgaenge/service.py:57` (`get_vorgang_detail`) und `routes.py:34` (`GET /{vorgang_id}`) — existierender Lesepfad, den PROJ-8 vor `POST /vorgaenge/{id}/rechnungen` referenziert.
- `backend/app/features/angebote/repository.py:15-30` (`next_angebot_nummer`, `SELECT...FOR UPDATE`) — exaktes Vorbild für `rechnung_nummernkreis`; PROJ-8 übernimmt Muster korrekt inkl. zusätzlichem Unique-Constraint.
- `backend/app/features/angebote/routes.py:28-30,39` — `GET /vorgaenge/{id}/angebote`, `GET /angebote/{id}` existieren bereits und sind exakt die von PROJ-8 referenzierten Lesepfade vor Positionsübernahme.
- `backend/app/features/email/service.py:149` (`send_vorgang_email`) — existiert, inkl. optionalem `attachment`-Parameter für PDF-Anhang; PROJ-8 kann ihn wie in Angebote nutzen.
- Kunde-Tabelle (`backend/sql/003_kunden_vorgaenge.sql:8-17`) hat kein Adressfeld — Kundenanschrift kommt ausschließlich aus `objekt.adresse`. Tech Design Abschnitt F blockt Freigabe explizit bei fehlendem Objekt/Adresse — kein stiller Fallback, damit korrekt behandelt.

### Owner-Check (hart) — bestanden
Jede im Datenmodell genannte Entität hat einen expliziten Schreibpfad in Abschnitt D: `rechnungsstellerprofil` → `PUT /einstellungen/rechnungssteller`; `rechnung` → `POST /vorgaenge/{id}/rechnungen`; `rechnung_position` → `POST/PATCH/DELETE .../positionen*`; `rechnung_nummernkreis` → systemintern (kein Client-Schreibpfad, korrekt); `rechnung_fassung` → Service bei `senden`; `vorgang_dokument` (Rechnungs-PDF) → Service bei Freigabe/Versand; `zahlungstatus`/Storno → dedizierte Endpoints; `vorgang_historie` → Nebeneffekt.

### Lesepfad-Check (hart) — bestanden
Abschnitt D benennt für jeden Schreibpfad den nötigen Lesepfad (z. B. `GET /vorgaenge/{id}` vor Entwurfsanlage, `GET /vorgaenge/{id}/angebote` + `GET /angebote/{id}` vor Positionsübernahme, `GET /rechnungen/{id}` vor Positions-/Zahlungsstatusänderung, erfolgreiche `POST /rechnungen/{id}/freigabe` vor `senden`). Alle referenzierten Lesepfade existieren bereits im Code oder werden im selben Design neu geschaffen.

### Autonom behoben
- Keine Korrekturen nötig — Tech Design war bei Übergabe bereits vollständig (Datenmodell inkl. Owner/Lesepfade, API-Contracts, Rollen, ADRs).

### Offene Fragen
- Keine. Status wird auf Architected gesetzt.

## QA Test Results
**Getestet:** 2026-08-19 · **Ergebnis:** NOT READY (2 Bugs: 1 Critical, 1 Medium)

### Automatisierte Tests
- Backend: `.venv/bin/python -m pytest` — 189/189 grün (156 bestehend + 33 rechnungen), keine Regression.
- Eigene Red-Team-Suite `backend/tests/features/rechnungen/test_qa_redteam.py` (8 Tests, unabhängig vom Feature-Entwickler geschrieben) — alle grün: Cross-Tenant über alle 9 Endpunkte, Monteur-403 auf allen Routen, Büro darf Rechnungsstellerprofil nicht schreiben, JWT-Tampering (falsche Signatur → 401), SQL-Injection in `bezeichnung` (literal gespeichert, keine Injection), `mandant_id` aus Body wird ignoriert.
- Frontend: `npx tsc --noEmit` — clean.

### Akzeptanzkriterien (AC1–AC10)
| # | Kriterium | Ergebnis |
|---|---|---|
| AC1 | Nur aus „Erledigt“-Vorgang anlegen, sonst 409 mit dt. Meldung | ✅ PASS |
| AC2 | Entwurf enthält Nummer/Datum/Steller/Kunde/≥1 Position/Summen | ✅ PASS |
| AC3 | Position mit Bezeichnung/Menge/Einheit/Preis/Steuersatz, Summen konsistent auf 2 NK | ✅ PASS (Test: 2×80€ @19% = 160/30.40/190.40) |
| AC4 | Angebotspositionen übernehmbar, danach unabhängig änderbar | ✅ PASS |
| AC5 | Freigabeansicht zeigt Empfänger/Betreff/Nummer/PDF/Brutto, nur „Senden“ löst Versand aus | ✅ PASS (Backend zweistufig `freigabe`→`senden`); Frontend-Dialog exakt so implementiert |
| AC6 | Versendete Rechnung unveränderlich: PDF/Nummer/Empfänger/Zeitpunkt/Fassung am Vorgang | ✅ PASS (Test: PATCH nach Versand → 409) |
| AC7 | Zahlungsstatus exakt Offen/Bezahlt/Storniert, ändert nie PDF/Positionen | ✅ PASS („Storniert“ nur über Storno-Endpoint, Backend-Test bestätigt) |
| AC8 | Korrektur nur als Storno oder neue Rechnung, Original bleibt abrufbar | ✅ PASS |
| AC9 | Nur Inhaber/Büro dürfen schreiben/lesen; Monteur sieht nichts | ✅ PASS (Backend `require_role` + Frontend `darfSchreiben`-Gate; Red-Team bestätigt 403 auf allen Routen) |
| AC10 | Nur PDF, kein E-Rechnung/DATEV/Mahnung/Auto-Erstellung | ✅ PASS (kein entsprechender Code vorhanden) |

Alle Edge Cases aus der Spec inhaltlich im Backend abgedeckt (Nummer nie wiederverwendet nach Storno — eigener Test bestätigt; Versandfehler ändert Zahlungsstatus nicht — eigener Test bestätigt; fehlende Objektanschrift/E-Mail blockt Freigabe — eigener Test bestätigt).

### Gefundene Bugs

**BUG-1 (Critical) — Rechnungssteller-Profil: Feldnamen-Mismatch Frontend/Backend, Feature komplett blockiert**
- Backend-Contract (`backend/app/features/rechnungen/schemas.py::RechnungsstellerProfilIn/Read`, deckt sich mit Tech Design Abschnitt B): `firma_name, strasse, hausnummer, plz, ort, steuernummer, ust_id`.
- Frontend (`nextjs_app/lib/schemas/rechnung.ts::rechnungsstellerSchema`, `lib/api/rechnungen.ts::RechnungsstellerProfil`, `rechnungssteller-profil-form.tsx`) verwendet stattdessen: `name, anschrift, steuerkennzeichnung`.
- Reproduktion (eigener Testlauf, kein Übernehmen von Dev-Aussage): `PUT /einstellungen/rechnungssteller` mit dem Payload, den das Frontend-Formular tatsächlich sendet, liefert `422 Field required` für alle 5 Backend-Pflichtfelder.
- Auswirkung: Inhaber kann das Rechnungsstellerprofil über die UI **nie** speichern → `POST /rechnungen/{id}/freigabe` schlägt für **jede** Rechnung mit „Es ist noch kein vollständiges Rechnungsstellerprofil hinterlegt“ fehl → **kein Versand über die UI möglich**. Kernfunktion des Features nicht nutzbar.
- Fix-Vorschlag: Frontend-Schema/Formular/API-Typ an Backend-Contract angleichen (5 Felder `firma_name/strasse/hausnummer/plz/ort` + optionale `steuernummer/ust_id`), nicht umgekehrt — Backend folgt korrekt dem reviewten Tech Design.

**BUG-2 (Medium) — „Storniert am“ wird nie angezeigt (Feldnamen-Mismatch)**
- Backend liefert `storniert_at`/`storniert_von` (`RechnungListItem`/`RechnungDetail` in `schemas.py`, deckt sich mit DB-Spalte `rechnung.storniert_at`).
- Frontend (`app/(app)/rechnungen/[id]/page.tsx:182`, `lib/api/rechnungen.ts` Interface `Rechnung`) liest/deklariert `storno_at`/`storno_von`.
- Auswirkung: Nach Storno bleibt der Zeitpunkt in der UI unsichtbar (Feld ist immer `undefined`); Storno-Status selbst (Badge) funktioniert, da er aus `status` kommt, nicht betroffen. Kein Datenverlust, nur fehlende Anzeige — Nachvollziehbarkeit-Anforderung („mit Nutzer und Zeitpunkt … nachvollziehbar“) ist im Backend/Historie erfüllt, nur nicht in diesem UI-Feld sichtbar.
- Fix-Vorschlag: Frontend-Feldnamen auf `storniert_at`/`storniert_von` korrigieren.

### Security-Audit (Red Team)
Keine Findings über die dokumentierten 2 Bugs hinaus. Cross-Tenant-Isolation über alle 9 Rechnungs-Endpunkte + Rechnungsstellerprofil bestätigt hart (404/403, keine Datenlecks). RLS-Policies in `009_rechnungen.sql` vorhanden und konsistent zum bestehenden Muster. `mandant_id` ausschließlich aus JWT, nie aus Pfad/Body (Body-Injection-Versuch mit fremder `mandant_id` bestätigt wirkungslos). SQL-Injection-Versuch über unvalidiertes Textfeld schlägt fehl (parametrisierte Queries). JWT-Tampering (Mandanten-ID ändern + neu signieren mit falschem Secret) wird mit 401 abgelehnt.

### Production-Ready-Entscheidung
**NOT READY** — BUG-1 ist Critical (Kernfunktion nicht nutzbar), BUG-2 Medium. Beide müssen vor Deploy gefixt werden.

## QA Re-Verifikation (Fix-Runde 1)
**Getestet:** 2026-08-19 · **Ergebnis:** READY

Frontend-Fix (t_0b632a10) unabhängig re-verifiziert (kein Übernehmen von Dev-Aussage) — eigener Codeabgleich Frontend↔Backend-Contract + eigener Testlauf.

- **BUG-1 (Critical):** ✅ VERIFIED FIXED. `rechnungsstellerSchema` (`lib/schemas/rechnung.ts`), `RechnungsstellerProfil`-Interface (`lib/api/rechnungen.ts`) und Formular (`rechnungssteller-profil-form.tsx`) nutzen jetzt exakt die 7 Backend-Felder `firma_name/strasse/hausnummer/plz/ort` (Pflicht) + `steuernummer/ust_id` (optional) — 1:1 Abgleich gegen `backend/app/features/rechnungen/schemas.py::RechnungsstellerProfilIn/Read` bestätigt.
- **BUG-2 (Medium):** ✅ VERIFIED FIXED. `page.tsx:182` liest jetzt `rechnung.storniert_at`, Interface `Rechnung` deklariert `storniert_at`/`storniert_von` — deckt sich mit Backend (`repository.py`, `schemas.py`).
- Backend unangetastet, wie angekündigt (`git status`/`git diff --stat` bestätigt).

### Automatisierte Tests (eigener Lauf)
- `backend/.venv/bin/python -m pytest -q` (volle Suite): grün, keine Regression.
- `backend/.venv/bin/python -m pytest tests/features/rechnungen/ -q`: 31/31 grün (inkl. 8 Red-Team-Tests).
- `npx tsc --noEmit`: clean.
- `npm run build`: exit 0, `/rechnungen/[id]` und `/einstellungen/rechnungssteller` bauen ohne Fehler.

### Production-Ready-Entscheidung
**READY** — keine offenen Critical/High/Medium-Bugs. Freigegeben für Deploy.

## Deployment
_To be added by /deploy_
