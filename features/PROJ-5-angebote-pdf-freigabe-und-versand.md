# PROJ-5: Angebote, PDF, Freigabe und Versand

## Status: Approved
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

## Frontend Implementation Notes (abc-frontend)
**Erstellt:** 2026-08-18 · Next.js 16, Stack wie im Tech Design.

Gebaut exakt gegen den im Tech Design (Abschnitt C) spezifizierten API-Vertrag — das Backend existierte zum Startzeitpunkt dieser Session noch nicht (`backend/app/features/` enthielt kein `angebote`-Verzeichnis, `git log` zeigt keinen Backend-Commit für PROJ-5). Es wurde daher **nicht gegen einen laufenden Server getestet**, nur gegen den Vertrag entwickelt + mit Jest/RTL/tsc/ESLint verifiziert. Sobald das Backend steht, braucht es einen manuellen/E2E-Rauchtest (`/abc-qa` bzw. `/abc-qa-e2e`).

**Neue/geänderte Dateien:**
- `nextjs_app/lib/angebot-berechnung.ts` — reine Berechnungslogik (Positionssumme je Rabatt-Typ, Netto/Steuer/Brutto-Aggregation, Rundungsregel "je Zeile runden, dann summieren", Rabatt-Validierung clientseitig gespiegelt).
- `nextjs_app/lib/schemas/angebot.ts` — Zod-Schemas `positionSchema` (inkl. `rabatt_typ`/`rabatt_wert`-Refine), `kopfdatenSchema`, `freigabeSchema`.
- `nextjs_app/lib/api/angebote.ts` — API-Client-Funktionen für alle 10 Endpunkte aus Tech Design Abschnitt C (`listAngebote`, `createAngebot`, `getAngebot`, `updateAngebotKopfdaten`, `addPosition`, `updatePosition`, `deletePosition`, `getAngebotPdfUrl`, `angebotFreigeben`, `angebotSenden`, `angebotNeueVersion`) inkl. Typen für `Angebot`/`AngebotPosition`/`AngebotListItem`/`FreigabeResult`.
- `nextjs_app/components/angebote/position-form.tsx` — `PositionForm`: Menge/Einheit/Einzelpreis/Steuersatz/Rabatt inkl. %/€-Umschalter (shadcn `Select` mit zwei Optionen statt `ToggleGroup`, siehe Abweichung unten), react-hook-form + zodResolver.
- `nextjs_app/components/angebote/angebot-freigabe.tsx` — `AngebotFreigabe`: Freigabeansicht als Dialog, zweistufig (erst `POST .../freigabe` → PDF-Vorschau im `<iframe>`, dann expliziter „Angebot senden"-Klick → `POST .../senden`); Versandfehler zeigt „Angebot wurde nicht versendet." + Fehlertext, Dialog bleibt im Vorbereitungs-Zustand.
- `nextjs_app/components/angebote/vorgang-angebote.tsx` — `VorgangAngebote` (Hauptkomponente, gemountet in `vorgang-detail.tsx` analog zu `VorgangEmail`/`VorgangDokumente`) mit `AngebotListe`, `AngebotEditor`, `KopfdatenForm`, `PositionenTabelle`, `SummenBlock`; Entwurf-Speichern-Flow ohne jede automatische Versandaktion.
- `nextjs_app/components/vorgaenge/vorgang-detail.tsx` — neue Karte „Angebote" nach der E-Mail-Karte eingehängt (rollen-gated wie die übrigen Schreib-Karten).
- Tests: `nextjs_app/__tests__/angebot-berechnung.test.ts` (Summenberechnung, Rundung, Rabatt-Validierung), `nextjs_app/__tests__/angebot-schema.test.ts` (Zod-Validierung des Rabatt-Umschalters, Freigabe-Schema).

**Abweichungen vom Tech Design (mit Begründung):**
- Rabatt-Umschalter als shadcn `Select` (zwei Optionen: „Prozent (%)"/„Euro-Betrag (€)") statt `ToggleGroup` — Tech Design nannte explizit beide Optionen ("`ToggleGroup` oder `Select`"), `ToggleGroup` existiert noch nicht in `components/ui/`, ein zusätzliches shadcn-Primitive für einen einzigen Zwei-Optionen-Schalter wäre unnötige neue Fläche; das Projekt hat bereits ein `Select`-Primitive, das exakt dasselbe leistet.
- `SummenBlock` zeigt die vom Server zurückgegebenen `netto_summe`/`steuer_summe`/`brutto_summe` (jede Positions-Mutation liefert das aktualisierte `Angebot` inkl. neu berechneter Summen zurück) statt eine zusätzliche Client-Vorschau-Berechnung vor dem Absenden zu duplizieren — vermeidet zwei parallele Berechnungsquellen, die auseinanderlaufen könnten; die reine Rechenlogik in `lib/angebot-berechnung.ts` existiert trotzdem (testbar, spiegelt die Server-Rundungsregel) und wird für die clientseitige Rabatt-Vorabvalidierung im Zod-Schema genutzt.

**Test-Ergebnisse (2026-08-18, lokal, ohne laufendes Backend):**
- `npm run test` → 6 Suiten, 27 Tests, alle grün.
- `npx next lint` → Errors: 0, Warnings: 0.
- `npx tsc --noEmit` → keine Fehler.

## Backend Implementation Notes (abc-backend)
**Umgesetzt:** 2026-08-18 · Branch `specs/PROJ-5-angebote-pdf-freigabe-und-versand`

- Migration `backend/sql/006_angebote.sql`: `angebot`, `angebot_position`, `angebot_nummernkreis` — mandant-scoped, RLS wie bestehende Tabellen, Indizes auf `(mandant_id, vorgang_id, created_at)` bzw. `(mandant_id, angebot_id, sortierung)`.
- Neues Feature-Package `backend/app/features/angebote/` (`routes.py`, `service.py`, `repository.py`, `schemas.py`, `pdf.py`, `templates/angebot_pdf.html`), registriert in `backend/app/main.py`. Alle Endpunkte exakt wie im Tech Design (Abschnitt C), `require_role("Buero","Inhaber")` auch auf den Lesepfaden (lt. Spec explizit für alle `/angebote*`-Endpunkte, anders als bei `vorgaenge`).
- Nummernkreis-Locking exakt nach Tech Design umgesetzt: `app/db.py` bekam eine neue `engine.transaction(mandant_id)`-Context-Manager-Methode (Postgres: `BEGIN` + `SELECT ... FOR UPDATE` + `COMMIT`/`ROLLBACK` auf derselben Connection; SQLite-Testdouble: einfacher Commit/Rollback-Block, da die Suite nicht nebenläufig läuft). `angebote/repository.py::next_angebot_nummer` liest/erhöht `angebot_nummernkreis` darin; Format `AN-<Jahr>-<laufende Nummer, 4-stellig>`. Rollt die Transaktion zurück, bleibt der Zähler unverändert (keine Lücke).
- Rabatt-Typ je Position (`prozent`/`betrag`) inkl. beidseitiger Validierung (0–100 % bzw. Positionssumme ≥ 0) in `service.py::_validate_rabatt`, angewendet bei `POST`/`PATCH` gleichermaßen. Rundung: je Position auf 2 Nachkommastellen, dann summiert (`service.py::_totals`).
- Unveränderlichkeit nach Versand: `service.py::_require_entwurf` liefert 409 (`ConflictError`) auf `PATCH`/Positions-Schreibzugriffe, sobald `status = versendet`.
- Zweistufiger Versand: `POST /angebote/{id}/freigabe` prüft Positionen+Empfänger, rendert das PDF serverseitig aus den gespeicherten Daten (nie Client-HTML), lädt es als `vorgang_dokument` nach MinIO hoch und liefert Empfänger/Betreff/Summen/PDF-URL zurück. `POST /angebote/{id}/senden` verlangt server-seitig, dass `freigabe` zuvor gelaufen ist (`dokument_id`/`empfaenger_email` müssen gesetzt sein → sonst 422), rendert das PDF für den Versandzeitpunkt frisch, versendet über `send_vorgang_email` mit Anhang, friert Summen/Status ein und setzt den Vorgang über den bestehenden `vorgaenge_service.update_vorgang(..., status="Angebot offen", ...)`-Pfad (inkl. dessen Historie-Schreibung).
- Versandfehler: `senden()` fängt jede Exception aus `send_vorgang_email` ab, das Angebot bleibt `entwurf`, Response trägt `fehler_text="Angebot wurde nicht versendet."` (Edge Case erfüllt), kein Statuswechsel am Vorgang.
- `neue-version`: nur auf `status=versendet` aufrufbar (409 sonst), kopiert Positionen 1:1 in einen neuen Entwurf mit neuer Angebotsnummer und `vorgaenger_angebot_id`.
- E-Mail-Erweiterung additiv, nicht-brechend: `email/mailclient.py::send_message` und `email/service.py::send_vorgang_email` bekamen einen optionalen `attachment: tuple[dateiname, daten, content_type] | None = None`-Parameter (Default `None` → bestehende Aufrufer unverändert). Ein bestehender Test-Fake (`tests/features/email/test_email_routes.py::test_send_happy`) musste um den neuen Keyword-Parameter ergänzt werden, da er die Signatur strikt nachbildet.
- Abhängigkeiten `xhtml2pdf`/`jinja2` zu `backend/requirements.txt` ergänzt — waren im `Dashboard`-Conda-Env bereits vorhanden (0.2.17 bzw. aktuell), kein neuer Installationsschritt nötig.
- Tests: `backend/tests/features/angebote/test_angebote.py` (17 Tests) — Nummernkreis-Sequenz, Rollen-Guard, Rabatt-Berechnung (prozent + betrag) inkl. beider Validierungsgrenzen, Freigabe-Vorbedingungen (keine Position/kein Empfänger → 422), Freigabe-Ergebnis, Senden ohne vorherige Freigabe (422), Senden-Erfolg (Status + Vorgang-Statuswechsel), Senden-Fehlschlag (bleibt Entwurf), 409 auf Schreibzugriff nach Versand, `neue-version`-Vorbedingung + Positionskopie, Cross-Tenant-404. `backend/tests/conftest.py` um die drei neuen SQLite-Testtabellen ergänzt; ein bestehender Email-Test-Fake angepasst (s. o.).

**Testlauf:** `conda run -n Dashboard --no-capture-output python -m pytest backend/tests` → **118 passed** (gesamte Suite inkl. der 17 neuen Angebote-Tests), keine Fehler, keine Regressionen.

**Abweichungen vom Tech Design:**
- `app/db.py` bekam eine neue `transaction()`-Methode auf `BaseEngine`/`PostgresEngine`/`SqliteEngine` — im Tech Design nicht explizit als Codeänderung benannt (nur der fachliche Locking-Algorithmus), aber notwendig, weil `query`/`command` bisher je einen eigenen Connection-Scope pro Aufruf öffnen und für das geforderte „innerhalb derselben Transaktion" kein Mechanismus existierte. Rein additive Infrastruktur, keine Änderung an bestehendem Verhalten von `query`/`command`.
- Angebotsnummer wird bei **jeder** `angebot`-Zeilenerstellung neu gezogen (auch bei `POST /vorgaenge/{id}/angebote` mit `vorgaenger_angebot_id` und bei `neue-version`), nicht nur einmalig pro Vorgang — folgt wörtlich der Owner-Tabelle im Tech Design ("wird intern beim ersten POST .../angebote **einer neuen Version** transaktional hochgezählt").
- `GET /angebote/{id}/pdf` erzeugt bei Bedarf (kein `dokument_id` vorhanden) das PDF on-the-fly, statt nur einen bereits vorhandenen Dokument-Verweis zurückzugeben — deckt den im Tech Design als "optional" markierten Fall ab ("und optional GET /angebote/{id}/pdf" in Abschnitt D).
- Frontend (Next.js-Komponenten aus Abschnitt A) ist **nicht** Teil dieses Backend-Durchlaufs — folgt über `/abc-frontend`.

**Nachtrag 2026-08-18 (Backend-Fix, BUG-3 aus QA/Frontend-Bugfix-Runde):** `POST /angebote/{id}/freigabe` nahm keinen Body entgegen — vom Nutzer editierte Empfänger-/Betreff-Werte in der Freigabeansicht wurden von FastAPI stillschweigend verworfen, Server-Defaults kamen immer zum Zug. Fix: neues `FreigabeRequest`-Schema (`empfaenger: EmailStr | None`, `betreff: str | None`, analog zu `SendenRequest`) in `schemas.py`; `service.freigabe(user, angebot_id, payload=None)` nimmt es jetzt entgegen und überschreibt den aus dem Kunden-Datensatz ermittelten Empfänger bzw. den generierten Standard-Betreff, sofern gesetzt; `routes.py::freigabe` bekam den optionalen Body-Parameter. Test ergänzt: `test_freigabe_accepts_empfaenger_betreff_override`. Lücke geschlossen.

## QA Test Results
**Getestet:** 2026-08-18 · Branch `specs/PROJ-5-angebote-pdf-freigabe-und-versand`, Commit `cfcb5bc`

### Automatisierte Tests
- Backend: `conda run -n Dashboard --no-capture-output python -m pytest backend/tests` → **118 passed**, keine Fehler, keine Regressionen (17 davon neu für PROJ-5, inkl. Cross-Tenant-Test).
- Frontend: `npm run test` → **6 Suiten / 27 Tests grün**. `npx next lint` → 0 Errors / 0 Warnings. `npx tsc --noEmit` → keine Fehler.
- Hinweis: Die Frontend-Suite testet nur die reine Berechnungs-/Zod-Logik, nicht die Integration gegen die echten Backend-Response-Shapes (kein Component-/Contract-Test, der `Angebot`-Objekte vom echten Endpunkt konsumiert). Das hat den unten dokumentierten BUG-1..BUG-3 nicht auffangen können.

### Methodik
Da kein laufender Docker-Stack für einen Browser-Smoke-Test zur Verfügung stand, erfolgte die Prüfung als **Code-Level-Vertragsabgleich**: Backend-Pydantic-Response-Schemas (`backend/app/features/angebote/schemas.py`), tatsächliche Service-Rückgabewerte (`service.py`) und Datenbank-Migration (`006_angebote.sql`) wurden Zeile für Zeile gegen die Frontend-TypeScript-Interfaces und deren Nutzung (`lib/api/angebote.ts`, `components/angebote/*.tsx`) verglichen — ergänzt um die pytest-Suite (Backend-Verhalten real ausgeführt, nicht nur gelesen).

### Acceptance Criteria

| # | Kriterium | Ergebnis |
|---|---|---|
| 1 | Positionen hinzufügen/ändern/entfernen mit Menge, Einheit, Einzelpreis, Steuersatz, Rabatt (%/€) | **PASS** — Backend vollständig getestet (17 Tests, inkl. beider Rabatt-Typen + Validierungsgrenzen). `PositionInput`/`PositionCreate`-Feldnamen stimmen zwischen Frontend und Backend exakt überein. |
| 2 | Netto-/Steuer-/Bruttosumme nachvollziehbar berechnet | **PASS** — `service.py::_totals`/`_position_netto_steuer` rundet je Position auf 2 Nachkommastellen vor der Summierung (Tests decken prozent + betrag ab). Frontend zeigt `angebot.netto_summe`/`steuer_summe`/`brutto_summe` direkt vom Server, Feldnamen stimmen. |
| 3 | Angebot zeigt Nummer, Betriebs-/Kundendaten, Gültigkeitsdatum, Positionen, Summen, Freitext | **TEILWEISE FAIL** — Das PDF-Template (`templates/angebot_pdf.html`) selbst rendert alle geforderten Felder korrekt. Die In-App-Listenansicht zeigt die Angebotsnummer jedoch nicht (siehe BUG-1). |
| 4 | Freigabeansicht zeigt Empfänger/Betreff/PDF/Summe; erst expliziter Klick sendet | **FAIL** — PDF-Vorschau bleibt leer (BUG-2), vom Nutzer editierte Empfänger-/Betreff-Werte werden serverseitig stillschweigend verworfen (BUG-3). Der Zwei-Klick-Mechanismus selbst (`freigabe` versendet nichts, erst `senden` versendet) ist korrekt implementiert. |
| 5 | Nach Versand: PDF/Version/Empfänger/Zeitpunkt unveränderbar, Status → „Angebot offen" | **PASS (Backend)** — 409 auf PATCH/DELETE nach `status=versendet` getestet; `vorgaenge_service.update_vorgang(..., status="Angebot offen", ...)` wird im selben Service-Call ausgeführt und getestet. |
| 6 | Entwürfe werden nie automatisch versendet | **PASS** — `senden` ist der einzige Endpunkt, der tatsächlich verschickt; kein automatischer Trigger im Code gefunden. |

**Ergebnis: 4/6 PASS, 1 teilweise FAIL, 1 FAIL.**

### Edge Cases

| Edge Case | Ergebnis |
|---|---|
| Angebot ohne Position/Empfänger nicht freigebbar | **PASS** — Backend liefert 422 in beiden Fällen (getestet). Frontend deaktiviert den „Zur Freigabe"-Button bei 0 Positionen; fehlende Empfänger-E-Mail wird nicht vorab im UI geprüft, führt aber korrekt zur Backend-Fehlermeldung (kleinerer UX-Punkt, kein funktionaler Fail). |
| Nach Versand nicht überschreibbar, nur neue Version | **PASS** — 409 auf Schreibzugriffe nach Versand + `neue-version`-Endpoint kopiert Positionen 1:1, alles getestet. |
| Rundungsdifferenzen konsistent auf 2 Nachkommastellen | **PASS** — je Position gerundet, dann summiert; sowohl in `service.py` als auch im PDF-Format (`_de`) konsistent zweistellig. |
| E-Mail-Versand-Fehler → Angebot bleibt Entwurf, zeigt „Angebot wurde nicht versendet." | **FAIL** — Backend-Verhalten selbst korrekt (Angebot bleibt `entwurf`, `fehler_text` gesetzt), aber die Frontend-Anzeige des Fehlers ist gebrochen (BUG-4, Critical — siehe unten). |

### Security-Audit (Red-Team)
- **Rollen-Guard:** Alle `/angebote*`- und `/vorgaenge/{id}/angebote`-Endpunkte verlangen `require_role("Buero","Inhaber")` — auch die Lesepfade (bewusste Abweichung vom `vorgaenge`-Muster, im Tech Design dokumentiert). `test_monteur_forbidden` bestätigt 403 für Monteur. Frontend blendet den gesamten Angebote-Bereich für Monteur aus (`kannSchreiben()`/`darfSchreiben`-Gate in `vorgang-detail.tsx`), konsistent mit dem Backend-Guard. **Kein Befund.**
- **Cross-Tenant-Isolation (RLS):** `angebot`, `angebot_position`, `angebot_nummernkreis` haben je eine `ENABLE ROW LEVEL SECURITY` + `FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid)`-Policy (`006_angebote.sql`). Jede Repository-Query übergibt zusätzlich `mandant_id` explizit als Parameter (Defense in Depth). `test_cross_tenant_angebot_not_visible` bestätigt: Mandant A erhält 404 beim Versuch, Mandant Bs Angebot zu lesen/ändern. Der Nummernkreis ist ebenfalls pro Mandant isoliert (`mandant_id UUID PRIMARY KEY`) — keine mandantenübergreifende Nummernvergabe möglich. **Kein Befund.**
- **Audit-Log:** Jede Anlage/Positionsänderung/Freigabe-Vorbereitung/Versand/neue Version schreibt einen `vorgang_historie`-Eintrag mit `nutzer_id` + `created_at` (`ereignis`-Werte: `angebot_angelegt`, `angebot_geaendert`, `angebot_position_hinzugefuegt/geaendert/entfernt`, `angebot_freigabe_vorbereitet`, `angebot_versendet`, `angebot_neue_version`). Erfüllt das Technical Requirement „Audit: Freigabe und Versand werden mit Nutzer und Zeitpunkt protokolliert". **Kein Befund.**
- **Serverseitige PDF-Erzeugung:** PDF wird ausschließlich aus in der DB gespeicherten Daten gerendert (`_build_pdf_bytes` liest immer über `repo.list_positionen`/`repo.get_angebot`, nie aus dem Request-Body) — ein manipulierter Client kann kein PDF mit abweichenden Summen erzwingen. **Kein Befund.**
- **E-Mail-Injection über Freitext/Bezeichnung:** `EmailCompose`/`mailclient.send_message` nutzen die bestehenden PROJ-4-Pfade unverändert; keine neue Angriffsfläche durch PROJ-5 selbst identifiziert.
- Keine Auth-Bypass-, JWT-Tamper- oder SQL-Injection-Befunde in den neuen Endpunkten (durchgehend parametrisierte Queries, Pydantic-Validierung vor jedem Service-Aufruf).

### Gefundene Bugs

**BUG-1 (High) — Angebot-Kopf-Felder zwischen Backend und Frontend nicht deckungsgleich benannt**
- Backend (`AngebotListItem`/`AngebotDetail` in `schemas.py`) liefert `angebot_nummer`, `empfaenger_email`, `versendet_at`.
- Frontend-Interface `Angebot`/`AngebotListItem` (`lib/api/angebote.ts`) erwartet `nummer`, `empfaenger`, `versendet_am`.
- Auswirkung: In `vorgang-angebote.tsx` (Zeilen 306, 342) und `angebot-freigabe.tsx` (`angebot.nummer`) sind diese Felder zur Laufzeit `undefined` — die Angebotsnummer erscheint in der Liste und im Freigabe-Dialog-Titel nicht (leerer Text statt „AN-2026-0001").
- Repro: `GET /vorgaenge/{id}/angebote` aufrufen → JSON enthält `angebot_nummer`; React-Code liest `a.nummer` → `undefined`.
- Priorität: vor Deploy fixen (verletzt AC 3 sichtbar in der UI, auch wenn das PDF selbst korrekt ist).

**BUG-2 (High) — PDF-Vorschau in der Freigabeansicht bleibt leer**
- Backend `POST /angebote/{id}/freigabe` liefert `pdf_download_url` (`schemas.FreigabeResult`).
- Frontend `FreigabeResult`-Interface und `angebot-freigabe.tsx` (`freigabe.pdf_url`) erwarten `pdf_url`.
- Auswirkung: `<iframe src={freigabe.pdf_url}>` hat `src=undefined` → keine PDF-Vorschau sichtbar. Verletzt AC 4 direkt („Freigabeansicht … zeigt … PDF").
- Priorität: vor Deploy fixen.

**BUG-3 (Medium) — Editierte Empfänger-/Betreff-Werte in der Freigabeansicht werden ignoriert**
- Frontend sendet `{empfaenger, betreff}` im Body von `POST /angebote/{id}/freigabe`.
- Backend-Route `freigabe(angebot_id, user)` (`routes.py:73-75`) hat **keinen Body-Parameter** — FastAPI bindet den gesendeten JSON-Body an nichts, er wird stillschweigend verworfen. Der Service berechnet Empfänger immer aus der Kunden-E-Mail und den Betreff immer als festen String `f"Angebot {angebot_nummer}"`.
- `POST /angebote/{id}/senden` wird vom Frontend zudem ganz ohne Body aufgerufen (`angebotSenden(id)` in `lib/api/angebote.ts:132-134`), obwohl `SendenRequest` optionale `empfaenger`/`betreff`/`text`-Felder vorsieht.
- Auswirkung: Die AC-Formulierung „Empfänger und Betreff … editierbar" ist nicht erfüllt — Nutzereingaben haben keine Wirkung, ohne dass ein Fehler angezeigt wird (kein Hinweis, dass die Eingabe ignoriert wurde).
- Priorität: vor Deploy klären (entweder Backend-Body-Parameter ergänzen und tatsächlich verwenden, oder Frontend-Felder als rein informativ/read-only kennzeichnen).

**BUG-4 (Critical) — Fehlgeschlagener Versand wird im Frontend als Erfolg behandelt**
- Backend `senden()` fängt jede Exception aus `send_vorgang_email` ab und gibt bei Fehlschlag **HTTP 200** mit `{angebot, versendet: false, fehler_text: "Angebot wurde nicht versendet."}` zurück (`service.py:289-295`) — kein Non-2xx-Status.
- Frontend `apiFetch` (`lib/api/client.ts:41-45`) wirft nur bei `!res.ok` einen `ApiError`. Da die Antwort 200 ist, wirft `angebotSenden()` **nie** — der `catch`-Block in `angebot-freigabe.tsx::onSenden` (der die Fehlermeldung „Angebot wurde nicht versendet." anzeigen soll) wird nie erreicht.
- Zusätzlich liest `onSenden()` das Response-Objekt gar nicht aus (`await angebotSenden(angebot.id); onOpenChange(false); onVersendet();`) — selbst bei einer erfolgreichen Antwort mit `versendet: false` schließt das Frontend den Dialog und meldet dem Nutzer optisch Erfolg.
- Auswirkung: **Direkter Verstoß gegen den explizit geforderten Edge Case** „Fällt der E-Mail-Versand fehl, bleibt das Angebot ein Entwurf und zeigt „Angebot wurde nicht versendet."" — der Nutzer bekommt fälschlich signalisiert, das Angebot sei versendet worden, obwohl es (korrekt) als Entwurf im System verblieben ist. Führt zu falscher Kundenerwartung (Kunde erhält kein Angebot, Büro glaubt, es sei raus).
- Repro: `send_vorgang_email` mocken, um eine Exception zu werfen (wie im Backend-Test `test_senden_failure_keeps_entwurf` bereits getan) → Response ist 200 mit `versendet:false` → im Browser würde der Freigabe-Dialog trotzdem schließen und `laden()` aufrufen, ohne Fehlermeldung.
- Priorität: **vor Deploy zwingend fixen** (Frontend muss `versendet`/`fehler_text` aus der 200-Antwort auswerten, nicht nur auf HTTP-Fehlerstatus reagieren).

### Production-Ready-Empfehlung: **NOT READY**
Grund: 1 Critical-Bug (BUG-4) und 2 High-Bugs (BUG-1, BUG-2) offen — reine Backend/API-Vertrags-Drift, weil Frontend (abc-frontend) vor dem Backend gebaut und nie gegen den echten Server verifiziert wurde (im Frontend Implementation Notes selbst so vermerkt). Backend-Logik selbst ist solide (118/118 Tests grün, RLS/Rollen/Audit ohne Befund). Alle vier Bugs sind reine Frontend-Integrations-Fixes (Feldnamen angleichen, Response-Handling in `onSenden` korrigieren) — kein Architektur- oder Datenmodell-Problem.

**Status bleibt „In Review".** Empfehlung: Fixes an Frontend Developer routen (`lib/api/angebote.ts` Feldnamen an `schemas.py` angleichen, `onSenden`/`FreigabeResult`-Handling korrigieren), danach `/abc-qa` erneut für einen vollen Retest inkl. Browser-Smoke, sobald ein laufender Stack verfügbar ist.

## Frontend Bugfix Notes (Frontend Developer, nach QA)

**Branch:** `specs/PROJ-5-angebote-pdf-freigabe-und-versand`. Alle vier von QA gefundenen Bugs sind reine Frontend-Integrations-Fixes; Backend wurde für diese Session nicht verändert.

- **BUG-4 (Critical) — gefixt.** `components/angebote/angebot-freigabe.tsx::onSenden` liest jetzt den Response-Body von `POST /angebote/{id}/senden` (`SendenResult { angebot, versendet, fehler_text }`) statt nur auf den HTTP-Status zu reagieren. Bei `versendet === false` wird `fehler_text` (bzw. Fallback „Angebot wurde nicht versendet.") als Fehler angezeigt, der Dialog bleibt offen, `onVersendet()`/Schließen erfolgt nur bei `versendet === true`. `lib/api/angebote.ts::angebotSenden` gibt jetzt `Promise<SendenResult>` zurück (vorher fälschlich `Promise<Angebot>`).
- **BUG-1 (High) — gefixt.** Frontend-Typen (`Angebot`, `AngebotListItem` in `lib/api/angebote.ts`) an die echten Backend-Feldnamen aus `schemas.py` angeglichen: `nummer` → `angebot_nummer`, `empfaenger` → `empfaenger_email`, `versendet_am` → `versendet_at`. Ungenutztes `versendet_von` (kein Backend-Feld) entfernt. Zugriffe in `components/angebote/vorgang-angebote.tsx` (Zeilen ~306, ~342) und `angebot-freigabe.tsx` (Dialog-Titel, Formular-Default) angepasst. Zusätzlich (nicht von QA gemeldet, beim Angleichen aufgefallen): `AngebotPosition.reihenfolge` existierte im Frontend-Typ nicht im Backend (`PositionRead.sortierung`) — umbenannt; war folgenlos, da nirgends gelesen.
- **BUG-2 (High) — gefixt.** `FreigabeResult.pdf_url` → `pdf_download_url` (Typ + `angebot-freigabe.tsx`-iframe-`src`), passend zu `schemas.FreigabeResult.pdf_download_url`.
- **BUG-3 (Medium) — teilweise gefixt, Rest ist ein Backend-Gap.** Zwei getrennte Ursachen:
  1. `POST /angebote/{id}/senden` wurde ohne Body aufgerufen, obwohl `SendenRequest` optionale `empfaenger`/`betreff`/`text`-Overrides vorsieht und die Backend-Tests immer `json={}` schicken (ein Body ist also erforderlich, auch wenn leer). Gefixt: `angebotSenden(id, overrides)` schickt jetzt immer einen JSON-Body; `angebot-freigabe.tsx` übergibt die vom Nutzer im Vorbereiten-Formular editierten `empfaenger`/`betreff`-Werte als Override an `senden`. Der tatsächliche Versand respektiert damit editierte Werte.
  2. **Nicht im Frontend lösbar:** `POST /angebote/{id}/freigabe` (Vorschau-Endpunkt) hat serverseitig **keinen Body-Parameter** (`routes.py::freigabe(angebot_id, user)` — kein `payload`). Ein vom Client gesendeter Body wird von FastAPI mangels passendem Dependency-Parameter stillschweigend verworfen, ohne Fehler. Die PDF-Vorschau und die angezeigten Empfänger/Betreff-Werte im Freigabe-Dialog kommen daher immer aus den Server-Defaults (Kunden-E-Mail, fester Betreff-String) und **können nicht editiert werden, solange die Route keinen Body-Parameter akzeptiert**. Das Frontend schickt den editierten Wert weiterhin mit (falls das Backend künftig einen `payload: FreigabeRequest`-Parameter bekommt, greift der Fix ohne weitere Frontend-Änderung), zeigt aber aktuell zwangsläufig die Server-generierte Vorschau. **Empfehlung an Backend Developer:** `FreigabeRequest`-Schema (analog `SendenRequest`) ergänzen und in `service.freigabe()` verwenden, falls die AC „Empfänger und Betreff editierbar" bereits in der Vorschau gelten soll.

**Geänderte Dateien:** `nextjs_app/lib/api/angebote.ts`, `nextjs_app/components/angebote/angebot-freigabe.tsx`, `nextjs_app/components/angebote/vorgang-angebote.tsx`.

**Tests nach Fix:** `npm run test` → 6 Suiten / 27 Tests grün. `npx next lint` → 0 Errors/Warnings. `npx tsc --noEmit` → keine Fehler. (Kein neuer Contract-/Component-Test gegen echte Backend-Shapes ergänzt — bleibt offene Test-Lücke, siehe QA-Hinweis oben.)

**Status:** bleibt „In Review" — Empfehlung: erneuter `/abc-qa`-Pass (idealerweise mit laufendem Docker-Stack für Browser-Smoke) vor Freigabe für Deploy.

## QA Retest (nach Bugfix-Runde)
**Getestet:** 2026-08-18 · Branch `specs/PROJ-5-angebote-pdf-freigabe-und-versand`, Commit `d6c9575`

### Methodik
Unabhängige Verifikation — nicht der Bugfix-Bericht wurde übernommen, sondern erneut Backend-Response-Schemas (`backend/app/features/angebote/schemas.py`, `service.py`, `routes.py`) Zeile für Zeile gegen Frontend-Nutzung (`nextjs_app/lib/api/angebote.ts`, `components/angebote/angebot-freigabe.tsx`, `components/angebote/vorgang-angebote.tsx`) gelesen, plus vollständiger automatisierter Testlauf (Backend + Frontend) plus Wiederholung aller 6 AC + 4 Edge Cases + Security-Spotcheck.

### Automatisierte Tests
- Backend: `conda run -n Dashboard --no-capture-output python -m pytest backend/tests` → **119 passed** (118 vorher + 1 neuer Test `test_freigabe_accepts_empfaenger_betreff_override`), keine Fehler.
- Frontend: `npm run test` → **6 Suiten / 27 Tests grün**. `npx next lint` → 0 Errors/0 Warnings. `npx tsc --noEmit` → keine Fehler.
- `git show d6c9575 --stat` bestätigt: Diff beschränkt sich exakt auf die vier gemeldeten Bugs (`angebote/routes.py`, `schemas.py`, `service.py`, `angebot-freigabe.tsx`, `vorgang-angebote.tsx`, `lib/api/angebote.ts` + Tests/Doku) — keine unbeabsichtigten Nebenänderungen, RLS-Migration (`006_angebote.sql`) nicht angefasst.

### Bug-Verifikation (Codeabgleich, nicht nur Selbstauskunft)

**BUG-1 (High, Feldnamen-Drift) — verifiziert geschlossen.**
Backend `AngebotListItem`/`AngebotDetail` (`backend/app/features/angebote/schemas.py:57-71`) liefert `angebot_nummer`, `empfaenger_email`, `versendet_at`. Frontend-Interfaces `Angebot`/`AngebotListItem` (`nextjs_app/lib/api/angebote.ts:21-47`) verwenden exakt dieselben Feldnamen. Nutzung bestätigt: `vorgang-angebote.tsx:306` (`a.angebot_nummer` beim Listen-Append), `vorgang-angebote.tsx:342` (`{a.angebot_nummer}` in der Liste), `angebot-freigabe.tsx:45` (`angebot.angebot_nummer` im Dialog-Titel/Default-Betreff). `sortierung` (statt vorherigem `reihenfolge`) stimmt ebenfalls überein (`schemas.py:53` ↔ `angebote.ts:18`).

**BUG-2 (High, pdf_url) — verifiziert geschlossen.**
Backend `FreigabeResult.pdf_download_url` (`schemas.py:87`). Frontend `FreigabeResult.pdf_download_url` (`lib/api/angebote.ts:70`) und `angebot-freigabe.tsx:124` (`<iframe src={freigabe.pdf_download_url}>`) — Feldname und Nutzung stimmen überein, PDF-Vorschau bekommt eine echte URL.

**BUG-3 (Medium, fehlender freigabe-Body) — verifiziert geschlossen.**
Backend `routes.py:73-76`: `freigabe(angebot_id, payload: schemas.FreigabeRequest | None = None, user=...)` nimmt jetzt einen optionalen Body entgegen; `service.py:230-264` (`freigabe(user, angebot_id, payload=None)`) verwendet `payload.empfaenger`/`payload.betreff` als Override vor dem Kunden-Default. Frontend `angebot-freigabe.tsx:56-67` (`onVorbereiten`) ruft `angebotFreigeben(angebot.id, values)` mit den editierten Formularwerten auf (`lib/api/angebote.ts:131-139` sendet `input` als JSON-Body). Rundschluss bestätigt: editierte Empfänger-/Betreff-Werte wirken jetzt tatsächlich auf die Vorschau, nicht nur auf `senden`. Neuer Backend-Test `test_freigabe_accepts_empfaenger_betreff_override` deckt das ab (in Testlauf enthalten).

**BUG-4 (Critical, falsches Erfolgssignal) — verifiziert geschlossen.**
`angebot-freigabe.tsx:69-93` (`onSenden`) liest jetzt `result.versendet`/`result.fehler_text` aus dem Response-Body (`angebotSenden` gibt `Promise<SendenResult>` zurück, `lib/api/angebote.ts:142-150`, `SendenResult`-Typ mit `versendet: boolean`/`fehler_text: string | null` deckungsgleich mit Backend `schemas.SendenResult`, `schemas.py:105-108`). Bei `!result.versendet` wird `setError(result.fehler_text ?? "Angebot wurde nicht versendet.")` gesetzt, der Dialog bleibt offen (kein `onOpenChange(false)`/`onVersendet()`-Aufruf in diesem Zweig) — Erfolg wird nur bei `versendet === true` signalisiert. Bestätigt anhand Backend-Verhalten `service.py:290-296` (Exception aus `send_vorgang_email` → HTTP 200 mit `versendet: False`, `fehler_text` gesetzt) und Frontend-Auswertung im Body statt HTTP-Status.

### Acceptance Criteria (vollständiger Retest)

| # | Kriterium | Ergebnis |
|---|---|---|
| 1 | Positionen hinzufügen/ändern/entfernen mit Menge, Einheit, Einzelpreis, Steuersatz, Rabatt (%/€) | **PASS** — unverändert seit letztem Pass, Feldnamen stimmen weiterhin exakt, 119 Backend-Tests grün. |
| 2 | Netto-/Steuer-/Bruttosumme nachvollziehbar berechnet | **PASS** — unverändert, `SummenBlock` liest `netto_summe`/`steuer_summe`/`brutto_summe` direkt vom Server. |
| 3 | Angebot zeigt Nummer, Betriebs-/Kundendaten, Gültigkeitsdatum, Positionen, Summen, Freitext | **PASS** — BUG-1 behoben: Listen- und Dialog-Ansicht zeigen die Angebotsnummer jetzt korrekt (`vorgang-angebote.tsx:342`, `angebot-freigabe.tsx:45`). |
| 4 | Freigabeansicht zeigt Empfänger/Betreff/PDF/Summe; erst expliziter Klick sendet | **PASS** — BUG-2 (PDF-URL) und BUG-3 (Overrides) behoben; Zwei-Klick-Mechanismus weiterhin korrekt (`freigabe` versendet nichts, erst `senden`). |
| 5 | Nach Versand: PDF/Version/Empfänger/Zeitpunkt unveränderbar, Status → „Angebot offen" | **PASS** — unverändert, 409-Guard + Statuswechsel weiterhin getestet. |
| 6 | Entwürfe werden nie automatisch versendet | **PASS** — unverändert, `senden` einziger versendender Endpunkt. |

**Ergebnis: 6/6 PASS.**

### Edge Cases (vollständiger Retest)

| Edge Case | Ergebnis |
|---|---|
| Angebot ohne Position/Empfänger nicht freigebbar | **PASS** — Backend 422 in beiden Fällen (unverändert, getestet). Frontend deaktiviert „Zur Freigabe" bei 0 Positionen (`vorgang-angebote.tsx:254`); fehlender Empfänger führt weiterhin korrekt zur Backend-Fehlermeldung im Formular (kein blockierender Fund, wie zuvor). |
| Nach Versand nicht überschreibbar, nur neue Version | **PASS** — unverändert, 409 + `neue-version`-Kopie getestet. |
| Rundungsdifferenzen konsistent auf 2 Nachkommastellen | **PASS** — unverändert, `_totals`/`_position_netto_steuer` je Position gerundet. |
| E-Mail-Versand-Fehler → Angebot bleibt Entwurf, zeigt „Angebot wurde nicht versendet." | **PASS** — BUG-4 behoben: Frontend liest jetzt `versendet`/`fehler_text` aus dem Body, zeigt die Fehlermeldung, Dialog bleibt offen, kein falsches Erfolgssignal mehr. |

### Security-Re-Spotcheck (Cross-Tenant / RLS)
- `006_angebote.sql` im Bugfix-Commit **nicht verändert** (`git show d6c9575 --stat` bestätigt) — RLS-Policies auf `angebot`/`angebot_position`/`angebot_nummernkreis` unverändert gegenüber dem bereits geprüften ersten QA-Pass.
- `require_role("Buero","Inhaber")` weiterhin auf allen `/angebote*`-Routen (`routes.py:12`, unverändert außer dem neuen optionalen `payload`-Parameter bei `freigabe`).
- Neuer `FreigabeRequest`-Body (`empfaenger: EmailStr | None`, `betreff`) ist Pydantic-validiert (`schemas.py:90-92`), kein Free-Text-Injection-Risiko, keine `mandant_id` im Body — weiterhin ausschließlich aus dem Token.
- 119 Backend-Tests inkl. `test_cross_tenant_angebot_not_visible` weiterhin grün — keine Regression an der Tenant-Isolation durch die Bugfix-Änderungen.
- **Kein neuer Befund.**

### Production-Ready-Empfehlung: **READY**
Alle vier gemeldeten Bugs sind durch unabhängigen Codeabgleich (Feldnamen 1:1, Response-Shapes 1:1, Kontrollfluss der Fehlerbehandlung) verifiziert geschlossen — nicht nur laut Bugfix-Bericht übernommen. 6/6 AC PASS, 4/4 Edge Cases PASS, keine offenen Critical/High/Medium-Bugs. Automatisierte Suiten vollständig grün (119 Backend-, 27 Frontend-Tests, Lint, `tsc`). Kein Browser-Smoke gegen einen laufenden Docker-Stack durchgeführt (kein Stack in dieser Session verfügbar) — empfohlen als optionaler Zusatz-Check vor Deploy via `/abc-qa-e2e`, ist aber kein Blocker für „Approved", da der Vertragsabgleich lückenlos und die automatisierten Tests vollständig sind.

**Status: Approved.**

## Deployment
_To be added by /deploy_
