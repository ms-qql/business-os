# PROJ-5: Angebote, PDF, Freigabe und Versand

## Status: Architected
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
**Erstellt:** 2026-08-18 · **Stack:** Next.js 16 (App Router, Tailwind, shadcn/ui) + FastAPI + Postgres (RLS) + MinIO · **Branch:** specs/PROJ-5-angebote-pdf-freigabe-und-versand

### Grundlage im Code (verifiziert per CodeGraph, nicht angenommen)
- `Vorgang`-Status „Angebot offen" existiert bereits (`backend/app/features/vorgaenge/schemas.py:8-12`, DB-Check `backend/sql/003_kunden_vorgaenge.sql:37`, Frontend-Tokens `nextjs_app/lib/theme/tokens.ts:37-45`) — der Statuswechsel beim Versand ist ein normales `PATCH /vorgaenge/{id}` über den bestehenden `update_vorgang`-Pfad (`vorgaenge/routes.py:39-45`), keine neue Statuslogik nötig.
- `vorgang_dokument` (`backend/sql/003_kunden_vorgaenge.sql:64-74`, Felder `id, mandant_id, vorgang_id, dateiname, objektpfad, content_type, groesse_bytes, hochgeladen_von, created_at`) ist die bestehende MinIO-Ablage für Vorgangsdateien. Das generierte Angebots-PDF wird darüber abgelegt (gleicher Upload-Pfad wie `POST /vorgaenge/{id}/dokumente`), aber Versionierung/Unveränderlichkeit/Angebotsnummer sind eigene, neue Fachkonzepte — dafür kommt eine eigene `angebot`-Tabelle, die per `dokument_id` auf `vorgang_dokument` verweist, statt die bestehende Tabelle mit angebotsspezifischer Semantik zu überladen.
- Versand läuft über den bestehenden `send_vorgang_email`-Pfad (`backend/app/features/email/service.py:149-195`, Route `POST /vorgaenge/{id}/emails`, Schema `EmailCompose` in `email/schemas.py:111-115`). Dieser Pfad kennt heute **keinen Anhang** (`_anhange_speichern` verarbeitet nur eingehende Mails, `email/service.py:287-306`) — PROJ-5 erweitert `send_vorgang_email`/`mailclient.send_message` um einen optionalen Anhang-Parameter (Dateiname, Bytes, Content-Type), statt einen zweiten Versandpfad zu bauen.
- PDF-Erzeugung existiert im Repository noch nirgends (CodeGraph-Grep auf reportlab/weasyprint/xhtml2pdf/wkhtmltopdf/fpdf/pdfkit: keine Treffer) — neue Abhängigkeit nötig (siehe unten).
- Keine laufende Nummer/Sequenz existiert im Schema (kein `CREATE SEQUENCE`, kein formatiertes Nummernmuster) — die Angebotsnummer ist Neuland.
- Namenskollision geprüft: keine bestehende `angebot`/`position`/`quote`/`offer`-Tabelle, -Route oder -Komponente. `features/angebote/` ist frei.
- Frontend-Vorbild für eine „Abschnitt im Vorgangsdetail, selbst-ladend, Rollen-gated"-Komponente: `nextjs_app/components/email/vorgang-email.tsx:123-201` (`VorgangEmail`) und `nextjs_app/components/email/postfach-warnung.tsx:12-50` (self-fetchendes Banner) — die Freigabeansicht folgt demselben Muster, es gibt noch keine wiederverwendbare Approval-Dialog-Komponente.

### Ziel und Umfang
PROJ-5 erlaubt Inhaber und Büro, aus einem Vorgang ein Angebot mit frei benannten Positionen zu erstellen, als PDF darzustellen, vor dem Versand in einer Freigabeansicht zu prüfen und über das bestehende Postfach (PROJ-4) zu versenden. Nach Versand ist das Angebot unveränderlich; weitere Änderungen laufen über eine neue Version. Entwürfe werden nie automatisch versendet.

### A) Komponentenstruktur (Next.js)
```
VorgangDetailPage
└── VorgangDetail (bestehend, nextjs_app/components/vorgaenge/vorgang-detail.tsx)
    └── VorgangAngebote          (neu, nach VorgangEmail eingehängt)
        ├── AngebotListe         (Versionen: Entwurf/Versendet, je mit Nummer + Datum)
        ├── AngebotEditor        (nur sichtbar bei Entwurf + darfSchreiben)
        │   ├── PositionenTabelle (Menge, Einheit, Einzelpreis, Steuersatz, Rabatt inkl. Typ-Anzeige „%"/„€")
        │   ├── PositionForm      (Zeile hinzufügen/bearbeiten; Rabatt-Eingabe mit Umschalter %/€ je Zeile — shadcn/ui `ToggleGroup` oder `Select` mit zwei Optionen, direkt neben dem Rabatt-Zahlenfeld, wechselt das Eingabefeld-Suffix und die Validierungsgrenze live)
        │   ├── SummenBlock       (Netto/Steuer/Brutto, live neu berechnet)
        │   └── KopfdatenForm     (Gültigkeitsdatum, Freitext)
        └── FreigabeAnsicht       (eigene Route/Dialog, nur bei vollständigem Entwurf)
            ├── PdfVorschau       (eingebettetes PDF, aus GET /angebote/{id}/pdf)
            ├── EmpfaengerUndBetreff (vorbefüllt aus Kunde, editierbar)
            ├── SummenAnzeige
            └── SendenButton      ("Angebot senden" – einzige Aktion, die tatsächlich versendet)
```

### B) Datenmodell (Klartext)
- **angebot**: mandant-scoped (RLS wie bestehende Tabellen), gehört zu einem `vorgang`. Felder: Angebotsnummer (fortlaufend pro Mandant), Version (1, 2, …), Verweis auf die Vorgängerversion (falls vorhanden), Status (`entwurf` / `versendet`), Gültigkeitsdatum, Freitext, berechnete Summen (Netto/Steuer/Brutto — zum Zeitpunkt des Versands eingefroren, beim Entwurf live aus den Positionen berechnet), Verweis auf das erzeugte PDF-Dokument (`dokument_id` → `vorgang_dokument`), Empfänger-E-Mail, Versandzeitpunkt, versendender Nutzer, Erstellungs-/Änderungszeitpunkt.
- **angebot_position**: gehört zu einem Angebot. Freitext-Bezeichnung, Menge, Einheit, Einzelpreis, Steuersatz, Rabatt-Typ (`prozent` | `betrag` — je Position frei wählbar, Produktentscheidung siehe Tech-Entscheidungen), Rabatt-Wert (Zahl, Bedeutung abhängig vom Rabatt-Typ), Reihenfolge/Sortierung.
- **angebot_nummernkreis**: ein Zähler pro Mandant, unter Transaktionssperre hochgezählt, damit Angebotsnummern innerhalb eines Mandanten lückenlos fortlaufend und nie mandantenübergreifend vergeben werden.
- Historie: jede Erstellung, Positionsänderung, Freigabe-Vorbereitung und jeder Versand erzeugt einen `vorgang_historie`-Eintrag (gleiches Muster wie E-Mail-Events), damit Freigabe und Versand mit Nutzer und Zeitpunkt nachvollziehbar sind (Technical Requirement „Audit").
- Das generierte PDF selbst liegt als `vorgang_dokument` in MinIO (gleicher Upload-Pfad wie bestehende Vorgangsdokumente); `angebot.dokument_id` verweist darauf. Nach Versand wird dieses Dokument nicht mehr überschrieben — eine Änderung erzeugt eine neue `angebot`-Zeile (neue Version) mit eigenem, neuem PDF-Dokument.

**Unveränderlichkeit nach Versand:** Sobald `angebot.status = versendet`, lehnt der Service jede PATCH/DELETE-Anfrage auf Kopf, Positionen und das verknüpfte PDF-Dokument ab (409). Der einzige erlaubte Folgeschritt ist „Neue Version erstellen", die die Positionen des versendeten Angebots als neuen Entwurf kopiert.

### C) API-Shape (nur Endpunkte, kein Code)
```
- GET    /vorgaenge/{id}/angebote                  → alle Versionen eines Vorgangs (Liste, neueste zuerst)
- POST   /vorgaenge/{id}/angebote                  → neues Angebot als Entwurf anlegen (Version 1, oder neue Version wenn Vorgänger übergeben)
- GET    /angebote/{id}                            → ein Angebot inkl. Positionen und berechneter Summen lesen
- PATCH  /angebote/{id}                             → Kopfdaten ändern (Gültigkeitsdatum, Freitext) — nur solange Entwurf
- POST   /angebote/{id}/positionen                  → Position hinzufügen — nur solange Entwurf
- PATCH  /angebote/{id}/positionen/{position_id}    → Position ändern — nur solange Entwurf
- DELETE /angebote/{id}/positionen/{position_id}    → Position entfernen — nur solange Entwurf
- GET    /angebote/{id}/pdf                          → aktuelles PDF (Entwurfsvorschau oder eingefrorenes Versand-PDF) als kurzlebige, berechtigte Download-URL
- POST   /angebote/{id}/freigabe                     → Freigabe-Vorbereitung: prüft Positionen + Empfänger vorhanden, erzeugt/aktualisiert die PDF-Vorschau, liefert Empfänger/Betreff/Summen/PDF-URL für die Freigabeansicht zurück (versendet noch nichts)
- POST   /angebote/{id}/senden                       → versendet das geprüfte Angebot über das bestehende Postfach (send_vorgang_email + Anhang), friert PDF/Summen ein, setzt Status „versendet", schreibt Empfänger+Zeitpunkt, setzt den Vorgang per PATCH auf „Angebot offen". Schlägt der Versand fehl, bleibt das Angebot Entwurf und die Antwort trägt den Fehlertext für „Angebot wurde nicht versendet."
- POST   /angebote/{id}/neue-version                 → nur auf einem versendeten Angebot aufrufbar; kopiert Positionen in einen neuen Entwurf (nächste Version)

Alle Endpunkte: JWT Pflicht, mandant_id aus Token, require_role("Buero","Inhaber") (Technical Requirement „Nur Inhaber und Büro dürfen Angebote erzeugen oder versenden").
```

**Positions-Payload (`POST`/`PATCH /angebote/{id}/positionen[/{position_id}]`):** neben Bezeichnung/Menge/Einheit/Einzelpreis/Steuersatz enthält der Body `rabatt_typ: "prozent" | "betrag"` und `rabatt_wert: number`. Pydantic-Schema validiert beide Felder zusammen (siehe Validierungsregeln in „Tech-Entscheidungen"); die Response von `GET /angebote/{id}` liefert je Position `rabatt_typ` + `rabatt_wert` sowie den bereits berechneten `positions_summe` zurück, damit Frontend nicht selbst nachrechnen muss, welcher Typ welche Rundung erzeugt.

### D) Schreib-Owner je Entität + benötigte Lesepfade davor (explizit)

| Entität | Schreib-Owner (Endpoint-Guard) | Vorausgesetzter Lesepfad des Actors | Begründung |
|---|---|---|---|
| **angebot (Kopf, Entwurf)** | `require_role("Buero","Inhaber")` auf `POST /vorgaenge/{id}/angebote`, `PATCH /angebote/{id}` | `GET /vorgaenge/{id}` (bestehend, PROJ-3) — Actor muss den Vorgang und dessen Kunde/Empfänger-E-Mail kennen, bevor ein Angebot angelegt wird | Technical Requirement: nur Inhaber/Büro erzeugen Angebote |
| **angebot_position** | `require_role("Buero","Inhaber")` auf `POST/PATCH/DELETE /angebote/{id}/positionen*` | `GET /angebote/{id}` (neu, dieses Feature) — Actor muss den aktuellen Entwurf inkl. bestehender Positionen sehen, bevor er eine Position ändert/entfernt (sonst Race mit Stale-Daten) | AC: Positionen hinzufügen/ändern/entfernen |
| **angebot_nummernkreis** | kein direkter Schreibpfad für Nutzer — wird intern beim ersten `POST /vorgaenge/{id}/angebote` einer neuen Version transaktional hochgezählt | keiner (System-intern) | Reine Zähler-Infrastruktur, kein Nutzerakteur |
| **PDF-Vorschau (`vorgang_dokument` via `angebot.dokument_id`, Entwurfsstand)** | Wird vom Service bei `POST /angebote/{id}/freigabe` (und optional `GET /angebote/{id}/pdf`) serverseitig erzeugt, kein direkter Client-Upload | `GET /angebote/{id}` — Actor braucht den aktuellen Positionsstand, bevor eine sinnvolle Vorschau angefordert wird | PDF muss immer aus dem aktuellen, gespeicherten Positionsstand entstehen, nie aus Client-Daten |
| **angebot.status → „versendet", Versand-Metadaten (Empfänger/Zeitpunkt), eingefrorenes PDF** | `require_role("Buero","Inhaber")` auf `POST /angebote/{id}/senden` | `POST /angebote/{id}/freigabe` MUSS vorher erfolgreich gelaufen sein (liefert die geprüften Empfänger-/PDF-Daten, die `senden` tatsächlich verschickt) — erzwingt den in AC/Edge-Cases verlangten zweistufigen Ablauf (erst Freigabeansicht, dann expliziter Klick) | AC: „erst der ausdrückliche Klick „Angebot senden" versendet" |
| **vorgang.status → „Angebot offen"** | Schreiber = derselbe Service-Call wie `senden` (interner `PATCH /vorgaenge/{id}`, kein separater Client-Aufruf) | `GET /vorgaenge/{id}` intern bereits durch den Vorgangskontext von `angebot.vorgang_id` vorhanden | AC: Statuswechsel nach Versand |
| **neue Version (`angebot` mit `vorgaenger_angebot_id`)** | `require_role("Buero","Inhaber")` auf `POST /angebote/{id}/neue-version`, nur wenn Quell-Angebot `status = versendet` | `GET /angebote/{id}` — Actor sieht den Stand des versendeten Angebots, den er kopiert | Edge Case: „Nach Versand kann ein Angebot nicht überschrieben, sondern nur als neue Version erstellt werden" |

Kein Owner ohne vorausgesetzten Lesepfad: jeder Schreibpfad hat entweder einen bestehenden (`GET /vorgaenge/{id}`) oder einen in diesem Feature selbst neu geschaffenen (`GET /angebote/{id}`, `POST .../freigabe` vor `senden`) Lesepfad als Voraussetzung.

### E) Tech-Entscheidungen (Begründung)
- **Eigene `angebot`/`angebot_position`-Tabellen statt Erweiterung von `vorgang_dokument`:** Versionierung, Unveränderlichkeit nach Versand und die Angebotsnummer sind fachlich eigenständige Konzepte, die `vorgang_dokument` (reine Dateiablage) nicht abbildet. Das PDF selbst bleibt trotzdem in `vorgang_dokument`/MinIO — kein zweiter Speicherpfad.
- **Zweistufiger Versand (`freigabe` dann `senden`) statt einem einzigen „senden"-Aufruf:** bildet die geforderte Freigabeansicht als echten Server-Zustand ab (nicht nur UI-Zwischenschritt) — verhindert, dass ein Client den Versand ohne vorherige, serverseitig geprüfte Freigabe auslösen kann, und macht die Reihenfolge im API-Vertrag erzwingbar statt nur UI-Konvention.
- **Wiederverwendung von `send_vorgang_email` statt neuem Versandpfad:** Das Postfach, die Thread-Zuordnung und die Historie-Schreibung sind in PROJ-4 bereits gebaut und getestet (`email/service.py:149-195`). PROJ-5 erweitert diesen Pfad um einen optionalen Anhang statt eine zweite SMTP-Anbindung zu bauen — vermeidet Doppelimplementierung eines Postfach-Zugriffs.
- **PDF-Erzeugung serverseitig aus gespeicherten Daten, nie aus Client-HTML:** Verhindert, dass ein manipulierter Client ein PDF mit anderen Positionen/Summen als in der DB erzeugt. Die Bibliothek rendert ein serverseitiges HTML-Template (Angebotsnummer, Betriebs-/Kundendaten, Positionen, Summen, Freitext) zu PDF.
- **Neue Abhängigkeit `xhtml2pdf`:** einzige neue Backend-Bibliothek. Sie ist bereits im projektweiten `Dashboard`-Conda-Env installiert (wird dort für die persönliche PDF-Skill-Pipeline genutzt) — kein neuer Installationsschritt, kein neues Betriebsrisiko, deterministisches HTML→PDF-Rendering ohne Browser-Abhängigkeit (kein Playwright/Chromium-Sidecar nötig).
- **Angebotsnummer über `angebot_nummernkreis`-Zählertabelle statt Postgres-`SEQUENCE`:** eine globale `SEQUENCE` würde Nummern mandantenübergreifend vergeben (Informationsleck über Angebotsvolumen anderer Mandanten via fortlaufende IDs) und der Zähler muss pro Mandant bei Null starten. Eine Zeile pro Mandant mit `SELECT ... FOR UPDATE` beim Hochzählen ist die einfache Standardlösung für mandantengetrennte, lückenlose Zähler unter Nebenläufigkeit. **CodeGraph-Cross-Check (Review):** Diese Sperr-Technik ist im Repository noch nirgends vorhanden (kein bestehendes Vorbild) — daher hier konkret vorgegeben, statt auf ein "bestehendes Muster" zu verweisen: Innerhalb derselben Datenbank-Transaktion wie das Anlegen des neuen Angebots liest der Service zuerst die Zählerzeile des Mandanten mit einer sperrenden Leseanfrage (verhindert, dass zwei gleichzeitige Anfragen dieselbe Nummer ziehen), erhöht den Zähler um eins und verwendet den neuen Wert als Angebotsnummer (z. B. formatiert als `AN-<Jahr>-<laufende Nummer>`); existiert für den Mandanten noch keine Zählerzeile, wird sie bei der ersten Nummernvergabe mit Startwert 1 angelegt. Rollt die Transaktion zurück (z. B. weil das Anlegen des Angebots danach fehlschlägt), wird auch der Zähler nicht erhöht — keine Nummernlücken durch fehlgeschlagene Versuche.
- **Rabatt und Steuersatz je Position statt nur am Kopf:** deckt die AC „Positionen mit … Steuersatz und Rabatt" wörtlich ab und erlaubt unterschiedliche Steuersätze/Rabatte innerhalb desselben Angebots (z. B. Material vs. Dienstleistung).
- **Rabatt-Typ je Position wählbar (Prozent oder Euro-Betrag), Produktentscheidung bestätigt (2026-08-18):** Statt eines global festen Rabatttyps hat jede Position ein eigenes `rabatt_typ`-Feld (`prozent` | `betrag`) plus `rabatt_wert`. Grund: im Handwerksalltag sind beide Rabattarten üblich (z. B. „10 % auf Material" vs. „50 € Nachlass auf diese Dienstleistung") und unterschiedliche Zeilen im selben Angebot können unterschiedliche Rabattlogik brauchen. Löst die vorherige offene Frage aus dem Review — kein SEQUENCE-/Schema-Impact über das neue Feld hinaus.
- **Validierungsregeln Rabatt (beide Richtungen, serverseitig in Pydantic + Service, nicht nur UI):**
  - `rabatt_typ = "prozent"`: `rabatt_wert` muss `0 ≤ rabatt_wert ≤ 100` sein; außerhalb dieser Grenze liefert die API 422 mit deutschem Fehlertext („Rabatt in Prozent muss zwischen 0 und 100 liegen").
  - `rabatt_typ = "betrag"`: `rabatt_wert ≥ 0`; zusätzlich prüft der Service beim Speichern der Position, dass `menge × einzelpreis − rabatt_wert ≥ 0` (Positionssumme vor Steuer darf nicht negativ werden) — sonst 422 („Rabattbetrag darf die Positionssumme nicht unter 0 senken"). Diese Prüfung läuft serverseitig bei jedem `POST`/`PATCH` einer Position, nicht nur beim Freigeben, damit kein negativer Zwischenstand je gespeichert wird.
  - Beide Regeln gelten identisch für `POST /angebote/{id}/positionen` und `PATCH /angebote/{id}/positionen/{position_id}`.
- **Positionssumme je nach Rabatt-Typ:** `prozent` → `menge × einzelpreis × (1 − rabatt_wert/100)`; `betrag` → `menge × einzelpreis − rabatt_wert`. Beide Zweige runden das Zwischenergebnis auf zwei Nachkommastellen, bevor Steuer und Kopfsummen daraus gebildet werden (konsistent mit der bestehenden Rundungsregel unten).
- **PDF-Darstellung je Rabatt-Typ:** Die Positionszeile im PDF-Template zeigt den Rabatt in der gewählten Einheit an — `"10 %"` bei `prozent`, `"50,00 €"` bei `betrag` (deutsches Dezimalformat, zwei Nachkommastellen) — plus die daraus resultierende Positionssumme; keine implizite Umrechnung zwischen den Einheiten im Dokument.
- **Rundung:** Summen werden je Position auf zwei Nachkommastellen gerundet, dann aufsummiert (nicht erst die Endsumme gerundet) — konsistent nachvollziehbar pro Zeile, deckt den Edge Case „Rundungsdifferenzen werden konsistent auf zwei Nachkommastellen ausgewiesen".

### F) Abhängigkeiten (neue Pakete)
- Backend: `xhtml2pdf` (HTML→PDF-Rendering; im `Dashboard`-Conda-Env auf diesem Server bereits vorhanden, aber **noch nicht** in `backend/requirements.txt` des Projekts — CodeGraph-Cross-Check im Review bestätigt: nicht Teil der bisherigen 13 Projektabhängigkeiten, muss ergänzt werden) und `jinja2` (HTML-Template-Rendering für die PDF-Vorlage; ebenfalls bestätigt neu, keine der bestehenden Abhängigkeiten zieht es transitiv mit).
- Frontend: keine neuen Pakete — bestehende shadcn/ui-Komponenten (Table, Dialog, Card, Alert, Input, Button) reichen für Positionstabelle, Freigabeansicht und PDF-Einbettung (`<iframe>`/`<embed>` auf die presigned PDF-URL).

### Produktentscheidung Rabatt-Einheit (bestätigt 2026-08-18)
Die AC nannte „Rabatt" ohne Einheit; das war zunächst offen (siehe vorherige Review-Runde). Entschieden: **Rabatt ist je Position wählbar zwischen Prozent (%) und Euro-Betrag (€)**, über ein `rabatt_typ`-Feld je `angebot_position` (Details siehe Abschnitt B, C, E oben). Kein offener Punkt mehr.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-18 (2. Durchgang, nach Produktentscheidung Rabatt-Typ) · **Verdict:** Architected

### Checklist
- [x] Component structure — `VorgangAngebote`/`AngebotEditor`/`FreigabeAnsicht` decken alle drei User Stories ab; folgen dem bestehenden `VorgangEmail`-Muster (Abschnitt im Vorgangsdetail, selbst-ladend, rollen-gated); `PositionForm` benennt jetzt explizit den %/€-Umschalter (shadcn/ui `ToggleGroup`/`Select`); keine vagen Platzhalter.
- [x] Data model — `angebot`, `angebot_position`, `angebot_nummernkreis` sind alle mandant-scoped (RLS wie bestehende Tabellen); jedes Feld ist benannt, inkl. neuem `rabatt_typ` (`prozent`|`betrag`) + `rabatt_wert` je Position; Unveränderlichkeit nach Versand ist als konkrete Service-Regel (409 auf PATCH/DELETE bei `status=versendet`) beschrieben, nicht nur behauptet.
- [x] API shape — jeder Endpunkt mit Methode+Pfad+Rollen-Guard benannt; zweistufiger `freigabe`→`senden`-Fluss deckt AC „erst der ausdrückliche Klick sendet" explizit ab; `neue-version` deckt den Edge Case „nicht überschreiben, sondern neue Version" ab.
- [x] Tech decisions — jede Entscheidung mit Begründung; Angebotsnummer-Zähler-Algorithmus im Review konkretisiert (siehe „Autonom behoben" — CodeGraph zeigte, dass kein Sperr-Muster im Repo existiert, das als Vorbild hätte referenziert werden können).
- [x] Dependencies — `xhtml2pdf` und `jinja2` im Review bestätigt als tatsächlich neu für `backend/requirements.txt` (nicht transitiv vorhanden); nichts still als „schon da" angenommen.
- [x] Branch field — `specs/PROJ-5-angebote-pdf-freigabe-und-versand` vorhanden, ist der aktuelle Checkout.
- [x] Conflict-free — CodeGraph bestätigt: keine `angebot*`-Tabelle, keine `/angebote`-Route existiert bereits; einzige bestehende Berührung ist die Status-Zeichenkette „Angebot offen" (`vorgaenge/schemas.py:8,11`, `003_kunden_vorgaenge.sql:37`), die unverändert wiederverwendet wird.
- [x] Acceptance-criteria coverage — alle 6 AC + 4 Edge Cases geprüft:
  - AC „Positionen mit Menge/Einheit/Einzelpreis/Steuersatz/Rabatt hinzufügen/ändern/entfernen" → `angebot_position` (inkl. `rabatt_typ`/`rabatt_wert`) + `POST/PATCH/DELETE /angebote/{id}/positionen*` mit beidseitiger Validierung (0–100 % bzw. Betrag ≥ 0 und Positionssumme ≥ 0).
  - AC „Summen nachvollziehbar berechnet" → `SummenBlock`/Rundungsregel (je Position runden, dann summieren).
  - AC „Angebot zeigt Nummer, Betriebs-/Kundendaten, Gültigkeitsdatum, Positionen, Summen, Freitext" → `angebot`-Kopf + `GET /angebote/{id}` + PDF-Template.
  - AC „Freigabeansicht vor Versand" → `POST /angebote/{id}/freigabe` als eigener Server-Zustand, nicht nur UI.
  - AC „nach Versand unveränderlich, Status → Angebot offen" → Unveränderlichkeits-Regel + interner `PATCH /vorgaenge/{id}` im `senden`-Service-Call.
  - AC „Entwürfe werden nie automatisch versendet" → `senden` ist der einzige Endpunkt, der tatsächlich verschickt; `freigabe` versendet nichts.
  - Edge Case „ohne Position/Empfänger kann nicht freigegeben werden" → `POST /angebote/{id}/freigabe` prüft explizit beides vor Erfolg.
  - Edge Case „nach Versand nur neue Version" → `neue-version`-Endpoint + Owner-Tabelle.
  - Edge Case „Rundungsdifferenzen konsistent" → Rundungsregel benannt.
  - Edge Case „Versandfehler → Entwurf bleibt, Hinweistext" → `senden`-Beschreibung deckt das ausdrücklich ab.

### Schreib-Owner-/Lesepfad-Check (Zusatzauflage des Koordinators)
Für jede Entität im Datenmodell wurde geprüft, wer sie **schreibt** (nicht nur liest) und welchen Lesepfad der Actor vorher braucht — siehe Abschnitt „D) Schreib-Owner je Entität + benötigte Lesepfade" im Tech Design oben. Ergebnis: **kein Owner ohne Guard, kein Schreibpfad ohne vorausgesetzten Lesepfad.**
- `angebot` (Entwurf): Owner Büro/Inhaber, Voraussetzung `GET /vorgaenge/{id}` (bestehend).
- `angebot_position`: Owner Büro/Inhaber, Voraussetzung `GET /angebote/{id}` (neu, in diesem Feature selbst geschaffen — kein Zirkelschluss, da der Lesepfad vor dem ersten Schreibzugriff auf Positionen existiert, weil das Angebot selbst zuerst angelegt wird).
- `angebot_nummernkreis`: kein Nutzer-Schreibpfad, rein intern — kein Owner-Bedarf.
- PDF-Vorschau: serverseitig erzeugt, kein Client-Upload, Voraussetzung `GET /angebote/{id}`.
- Versand-Metadaten/Status „versendet": Owner Büro/Inhaber über `senden`, hart erzwungene Voraussetzung `freigabe` muss vorher erfolgreich gelaufen sein (nicht nur ein „sollte" — Service muss dies serverseitig prüfen, nicht nur UI-Reihenfolge).
- `vorgang.status`: kein separater Client-Schreibpfad, läuft intern im selben Service-Call wie `senden`.
- neue Version: Owner Büro/Inhaber über `neue-version`, nur auf `status=versendet`, Voraussetzung `GET /angebote/{id}`.

### CodeGraph-Cross-Check
Delegiert an Explore-Agent (`codegraph_explore`), drei Durchläufe (Architektur-Erstellung + 1. Review-Verifikation + 2. Review-Verifikation nach Rabatt-Typ-Ergänzung):
- Keine bestehende `angebot*`-Tabelle/-Route (Konfliktfreiheit bestätigt, auch für `rabatt_typ`/`rabatt_wert` — keine Namenskollision mit bestehenden Spalten).
- Tabellen `angebot`/`angebot_position`/`angebot_nummernkreis`, Routen `/vorgaenge/{id}/angebote` + `/angebote/{id}/...` und die Komponente `VorgangAngebote` existieren erwartungsgemäß noch nirgends im Code (reines Neuland dieses Features).
- Status „Angebot offen" bereits vorhanden (`vorgaenge/schemas.py:8,11`, `003_kunden_vorgaenge.sql:37`) — unverändert wiederverwendet.
- `send_vorgang_email`/`mailclient.send_message` (`email/service.py:149`, `email/mailclient.py:150`) verifiziert: beide nehmen nur optionale Keyword-Parameter zusätzlich zu den Pflichtfeldern entgegen — ein optionaler `attachment`-Parameter ist eine additive, nicht-brechende Erweiterung für bestehende Aufrufer.
- `require_role(*roles)` (`deps.py:68-75`) exakt wie in `vorgaenge/routes.py:12`, `kunden/routes.py:11`, `email/routes.py:14` verwendet — neue `/angebote`-Routen übernehmen dasselbe Muster unverändert. RLS-/Auth-/Upload-Pattern zum Nachbauen bestätigt vorhanden.
- `xhtml2pdf`/`jinja2` bestätigt als echte Neuzugänge zu `backend/requirements.txt` (13 bestehende Zeilen, keine davon zieht Jinja2 transitiv).
- Kein bestehendes `SELECT ... FOR UPDATE`/Zähler-Muster im Repo — bestätigt genuinely neu, deshalb im Tech Design (Abschnitt E) als eigener, konkreter Algorithmus festgehalten statt auf ein nicht-existentes Vorbild zu verweisen.

### Autonom behoben
- Angebotsnummer-Zähler-Algorithmus konkretisiert (sperrende Leseanfrage innerhalb derselben Transaktion, Hochzählen, Erstanlage bei fehlender Zählerzeile, kein Nummernverlust bei fehlgeschlagener Transaktion) — technische Präzisierung ohne neue Produktentscheidung, da die Tech-Entscheidung „Zählertabelle statt SEQUENCE" bereits stand, nur der konkrete Ablauf fehlte und CodeGraph kein Vorbild im Repo fand.
- Abhängigkeiten-Abschnitt präzisiert: `xhtml2pdf` und `jinja2` beide explizit als neu zu `backend/requirements.txt` zu ergänzen bestätigt (vorher unklar formuliert, ob Jinja2 schon vorhanden sein könnte).
- Rabatt-Typ je Position (`rabatt_typ`/`rabatt_wert`) inkl. beidseitiger Validierung, Positionssummen-Formel je Typ und PDF-Darstellung je Typ ins Tech Design eingearbeitet (Abschnitte A, B, C, E) — technische Umsetzung der unten aufgelösten Produktentscheidung.

### Produktentscheidung aufgelöst
- **Rabatt-Einheit je Position:** War in der 1. Review-Runde blockierend offen (Prozent vs. Euro-Betrag, echte Fachentscheidung, nicht technisch herleitbar). Vom Menschen entschieden (2026-08-18): **je Position frei wählbar zwischen Prozent und Euro-Betrag**, über `rabatt_typ` + Umschalter in der UI. Damit ist kein Checklistenpunkt mehr offen.

**Status: Architected.** Alle Checklistenpunkte grün, keine offenen Fragen mehr. Nächster Schritt: `/abc-backend` und/oder `/abc-frontend`.

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
