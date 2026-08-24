# PROJ-23: Dedizierter Bildspeicher und WebP-Optimierung

## Status: Approved
**Created:** 2026-08-23
**Last Updated:** 2026-08-23 (QA-Re-Test: READY)

## Dependencies
- Requires: PROJ-2 — bestehende Website-, Branding- und Bild-Upload-Grundlage.
- Requires: PROJ-12 — Sektionsbild-Upload im Landingpage-Baukasten.

## Ziel

Neue Bilder des Landingpage-Baukastens werden ausschließlich im eigenen
Business-OS-MinIO gespeichert und vor der Ablage als komprimierte WebP-Datei
bereitgestellt. Dadurch bleibt Business OS vom ImmoCRM-Dateispeicher getrennt
und öffentliche Landingpages laden kleinere, passend zugeschnittene
Bilddateien.

## User Stories
- Als Inhaber möchte ich ein PNG oder JPEG wie bisher als Sektionsbild hochladen, damit ich keine Bildbearbeitung vorab machen muss.
- Als Inhaber möchte ich nach dem Upload unmittelbar eine Bildvorschau sehen, damit ich sicher bin, dass mein Bild übernommen wurde.
- Als Inhaber möchte ich, dass mein Bild ohne Verzerrung zum Format der gewählten Sektion passt, damit die Landingpage ein ruhiges, einheitliches Layout behält.
- Als Inhaber möchte ich einen verständlichen Bildnamen sehen, damit ich Bilder im Editor ohne Öffnen unterscheiden kann.
- Als Besucher möchte ich optimierte Sektionsbilder laden, damit die Landingpage auch bei mobilen Verbindungen flüssig bleibt.
- Als Betreiber möchte ich den Bildspeicher von ImmoCRM getrennt betreiben, damit ein System keine Dateien oder Zugangsdaten des anderen verwendet.

## Acceptance Criteria
- [ ] Neue Uploads für Hero- und Text-mit-Bild-Sektionen akzeptieren die bisher erlaubten Rasterbildformate und speichern das Auslieferungsbild ausschließlich als WebP im dedizierten Business-OS-MinIO.
- [ ] Der Upload-Endpunkt liefert nach einem erfolgreichen Upload weiterhin die bestehende proxied Bild-URL; Vorschau im Editor und Bild auf der öffentlichen Landingpage funktionieren ohne direkten MinIO-Zugriff des Browsers.
- [ ] Das gespeicherte WebP ist gegenüber dem hochgeladenen Ausgangsbild komprimiert und für die Darstellung einer Landingpage dimensioniert; die Bildqualität bleibt für normale Website-Fotos sichtbar brauchbar.
- [ ] Ein neues Bild wird ohne Verzerrung auf das feste Seitenverhältnis der jeweiligen Sektion angepasst; überstehende Bildbereiche werden einheitlich beschnitten und die resultierende Vorschau entspricht der öffentlichen Darstellung.
- [ ] Jedes neue Sektionsbild erhält einen eindeutigen, verständlichen Anzeigenamen aus Sektionstyp und Sektionsüberschrift; dieser Name ist im Editor sichtbar und wird bei gleicher Bezeichnung unterscheidbar ergänzt.
- [ ] Die Business-OS-MinIO-Zugangsdaten, der Bucket und die gespeicherten Objektpfade sind von ImmoCRM vollständig getrennt.
- [ ] Bestehende Sektionsbilder werden weder kopiert, konvertiert noch gelöscht; sie bleiben über ihren aktuellen Speicherpfad sichtbar.
- [ ] Bei ungültigem Bild, Konvertierungsfehler oder nicht verfügbarem Bildspeicher wird kein neuer Bildverweis gespeichert und das bisherige Bild der Sektion bleibt erhalten; die Fehlermeldung ist deutsch und verständlich.

## Edge Cases
- Ein bereits als WebP hochgeladenes Bild wird nicht mehrfach konvertiert oder vergrößert, sondern nur passend für die Auslieferung gespeichert.
- Transparente PNGs bleiben nach der WebP-Verarbeitung mit Transparenz nutzbar.
- Ein animiertes oder anderweitig nicht zuverlässig als statisches WebP konvertierbares Format wird mit einer verständlichen Meldung abgewiesen; das bestehende Bild bleibt unverändert.
- Sehr große Quellbilder werden vor der Speicherung auf eine für Landingpages geeignete Maximalgröße begrenzt, damit Speicherverbrauch und Ladezeit nicht unverhältnismäßig wachsen.
- Ist die Sektionsüberschrift leer, verwendet der Anzeigename die deutsche Sektionsbezeichnung (zum Beispiel „Hero-Bild" oder „Text-mit-Bild").
- Hat ein Quellbild ein deutlich abweichendes Hoch- oder Querformat, bleibt es unverzerrt; der sichtbare Ausschnitt folgt trotzdem dem Sektionenformat.
- Schlägt die Speicherung nach der Konvertierung fehl, wird kein unreferenziertes Bild veröffentlicht und der Upload kann erneut versucht werden.
- Alte, noch im bisherigen Speicher liegende Sektionsbilder und neue WebP-Bilder können während des Übergangs parallel ausgeliefert werden.

## Nicht-Ziele
- Keine Migration, Konvertierung oder Bereinigung bereits gespeicherter Bilder.
- Kein manuelles Zuschneiden, keine Filter, KI-Optimierung oder mehrere responsive Bildvarianten.
- Keine Änderung der Bild-Uploads außerhalb der Landingpage-Sektionen.

## Technical Requirements
- Security: Die Auslieferung bleibt über die bestehende Business-OS-App-HTTPS-Route mandantenisoliert; Browser erhalten keine MinIO-Zugangsdaten oder direkten Bucket-Zugriff.
- Performance: Für neue Sektionsbilder wird nur die optimierte WebP-Auslieferungsdatei abgelegt; keine parallele Rohdatei im Business-OS-Bildspeicher.
- Compatibility: Bestehende, noch nicht migrierte Bildpfade bleiben lesbar; neue Uploads sind nach erfolgreichem Speichern als `image/webp` auslieferbar.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-23 · **Stack:** Next.js/shadcn + FastAPI + PostgreSQL/raw SQL/RLS + dediziertes MinIO · **Branch:** main

### Umfang und Leitentscheidung

PROJ-23 erweitert ausschließlich den vorhandenen Upload für `hero` und
`text_mit_bild`. Die bestehenden Routen, die gleiche HTTPS-Origin-URL
`/public/sections/{section_id}/bild` und die bestehenden Bilder bleiben
erhalten. Neue Dateien werden serverseitig geprüft, auf ein festes
Sektionsformat zugeschnitten, als genau eine WebP-Datei abgelegt und nur über
den App-Proxy ausgeliefert. Es gibt weder Rohdatei-Ablage noch Browserzugriff
auf MinIO.

Die bestehende `MINIO_*`-Ablage bleibt Legacy-Speicher für bereits vorhandene
Objekte und andere Business-OS-Dateitypen. Neue Sektionsbilder nutzen eine
separate Business-OS-MinIO-Instanz bzw. ein separates Konto und einen eigenen,
nicht mit ImmoCRM geteilten Bucket. Kein Fallback auf ImmoCRM-Variablen oder
Buckets ist zulässig.

### Komponenten und Ablauf

```
WebsiteBuilderPage (Next.js, bestehend)
└── SectionEditor
    ├── Bild-Upload mit Vorschau und Anzeigename
    └── bestehender POST /website-builder/sections/{id}/bild

FastAPI Website Builder
├── Auth/Rolle Inhaber und Mandant aus JWT
├── Bildprüfung, Dekodierung, Zuschnitt und WebP-Konvertierung
├── eigener WebsiteImageStorage (dediziertes MinIO)
└── bestehende Builder- und Public-Read-Modelle

PostgreSQL/RLS
└── website_section_bild: Speicherort, WebP-Metadaten, Anzeigename

Public Website (Next.js)
└── GET /public/sections/{section_id}/bild als gleicher-Origin-Proxy
```

1. Der Inhaber wählt wie bisher eine Datei im `SectionEditor`; der Client
   sendet sie mit `version` und `alt_text` an den bestehenden Upload-Endpunkt.
   `version` bleibt Query-Parameter, `datei` und `alt_text` liegen im
   Multipart-Formular. **Bestehender Bug, hier zu beheben:**
   `nextjs_app/lib/api/website-builder.ts:95` hängt `alt_text` aktuell als
   Query-Parameter an, während `builder_routes.py:60` es als
   `Annotated[str, Form()]` erwartet — der Server erhält daher immer einen
   leeren `alt_text`. Der Next.js-Client muss `alt_text` stattdessen per
   `form.append("alt_text", altText)` in die `FormData` legen und aus den
   Query-Params entfernen.
2. FastAPI nimmt `mandant_id` ausschließlich aus dem JWT, prüft Sektion,
   Typ, Version, Dateigröße und echte Bilddaten, dekodiert statisch und
   erzeugt das Zielbild.
3. Das fertige WebP wird privat in den dedizierten Bucket geschrieben. Erst
   danach wird der Bildverweis mandantenbegrenzt ersetzt und der vollständige
   Builder-Status zurückgegeben. Bei jeder Vorstufe bleibt der alte Verweis
   unverändert.
4. Editor-Vorschau und öffentliche Website verwenden weiter dieselbe proxied
   URL. Der Proxy wählt anhand des gespeicherten Speicherorts Legacy- oder
   Website-Images-Speicher; Objektpfade und Zugangsdaten verlassen das Backend
   nie.

### Bildregelwerk

| Sektionsart | Zielformat | maximale Ausgabe | Anpassung |
|---|---:|---:|---|
| Hero | 16:9 | 1920 × 1080 px | mittig `cover`, Überstand einheitlich beschneiden |
| Text mit Bild | 4:3 | 1200 × 900 px | mittig `cover`, Überstand einheitlich beschneiden |

- Akzeptiert bleiben die bisher per Magic Bytes erlaubten Rasterformate JPEG,
  PNG, GIF und WebP, maximal 8 MB. MIME-Header und Dateiendung sind keine
  Vertrauensquelle.
- Es werden nur zuverlässig statische, dekodierbare Bilder verarbeitet;
  animierte GIF/WebP werden mit deutscher Meldung abgewiesen. Transparenz aus
  PNG/WebP bleibt in WebP erhalten. Bereits hochgeladenes WebP wird nur bei
  notwendiger Verkleinerung oder beim Format-Zuschnitt neu kodiert, nie
  vergrößert.
- Ziel ist je Sektion exakt eine `image/webp`-Datei mit WebP-Qualität 82.
  Größere Quellbilder werden vor Ausgabe begrenzt; kleinere Bilder werden nicht
  künstlich hochskaliert. Renderer und Editor erhalten für beide Formate das
  gleiche feste Seitenverhältnis mit `object-fit: cover`, damit Vorschau und
  öffentliche Darstellung den identischen Ausschnitt zeigen.
- Der verständliche Anzeigename entsteht beim erfolgreichen Upload aus der
  deutschen Sektionsbezeichnung und der aktuellen Überschrift, etwa
  `Hero – Dachsanierung`. Bei leerer Überschrift gilt `Hero-Bild` bzw.
  `Text-mit-Bild`. Ein mandantenweit gleicher Name erhält deterministisch
  ` (2)`, ` (3)` usw. Der Name bleibt beim späteren Ändern der Überschrift
  stabil, damit er ein echtes Bildkennzeichen ist.

### Datenmodell, Owner und Lesepfade

Keine neue Fachentität: `website_section_bild` wird erweitert. Die bestehende
eine-zu-eins-Beziehung zur Sektion, `mandant_id` und RLS bleiben erhalten.

| Feld | Bedeutung und Constraint | Schreiber (Owner) | notwendige Lesepfade |
|---|---|---|---|
| `id`, `mandant_id`, `section_id` | bestehende UUIDs; ein Bild je Sektion, Mandantenisolation | bestehender Upload-Endpunkt, nur Rolle `Inhaber` | `GET /website-builder/startseite`; intern `GET /public/site` und Bild-Proxy nach Domainauflösung |
| `objektpfad` | interner, nicht vom Dateinamen abgeleiteter Key `website-sections/{mandant_id}/{section_id}/{uuid}.webp` (Präfix konsistent mit bestehendem Legacy-Muster in `builder_service.py:186`); niemals API-Ausgabe | bestehender Upload-Endpunkt nach erfolgreicher Speicherung | ausschließlich Backend beim Bild-Proxy und beim Ersetzen/Löschen |
| `speicher_backend` | `legacy` oder `website_images`; `legacy` Default für vorhandene Zeilen, `website_images` für alle neuen Uploads | Upload-Endpunkt; Migration setzt nur Default | Backend-Bild-Proxy wählt korrekten Storage; niemals Frontend |
| `content_type` | für neue Zeilen verpflichtend `image/webp`; für Legacy-Zeilen leer und wie bisher aus dem Objektpfad ableitbar | Upload-Endpunkt | Bild-Proxy setzt Response-`Content-Type` |
| `anzeigename` | lesbarer, mandantenweit eindeutiger Name; für alte Zeilen leer/`NULL`; partielle eindeutige DB-Regel nur für gesetzte Werte | Upload-Endpunkt | `GET /website-builder/startseite` für `SectionEditor` und Sektionsliste; nicht öffentlich nötig |
| `alt_text` | bestehender, optionaler Barrierefreiheitstext | Upload-Endpunkt aus Formular | `GET /website-builder/startseite`, `GET /public/site`, öffentliche Bilddarstellung |
| `created_at` | bestehender Zeitstempel | Datenbank beim Insert, nicht Client | nur internes Audit/Support; kein neuer UI-Pfad |

Die neue Raw-SQL-Datei `backend/sql/011_website_section_images.sql` ergänzt die
drei neuen Spalten, einen Check für
`speicher_backend` und einen partiellen Unique-Index auf
`(mandant_id, anzeigename) WHERE anzeigename IS NOT NULL`. Sie aktiviert keine
neue Tabelle und ergänzt die bestehende RLS-Policy nicht nur implizit: alle
Reads/Writes bleiben mit `mandant_id` und der existierenden RLS-Policy
`website_section_bild_isolation` gebunden. Jede Repository-Abfrage übergibt den
Mandantenkontext. Der öffentliche Pfad leitet den Mandanten aus der aktiven
Domain ab; er akzeptiert weder eine Mandanten-ID noch einen Objektpfad vom
Browser.

**Betriebsdaten (kein Datenbankobjekt):** `WEBSITE_IMAGES_MINIO_ENDPOINT`,
`WEBSITE_IMAGES_MINIO_ACCESS_KEY`, `WEBSITE_IMAGES_MINIO_SECRET_KEY`,
`WEBSITE_IMAGES_MINIO_BUCKET` und `WEBSITE_IMAGES_MINIO_SECURE` werden nur
durch Dokploy-Betrieb/Deployment gesetzt. Der Bucket wird einmalig als
privater Business-OS-Bucket provisioniert; sein Servicekonto darf nur diesen
Bucket lesen, schreiben und löschen. Leser sind ausschließlich der Backend-
Service; Next.js und Browser erhalten diese Werte nie.

### API-Contracts

| Methode und Pfad | Auth/Leser | Änderung |
|---|---|---|
| `POST /website-builder/sections/{section_id}/bild?version={n}` | JWT, Rolle `Inhaber`, `mandant_id` aus Token | Vertrag bleibt multipart mit `datei` und `alt_text`. Bei Erfolg `200` mit vollständigem `BuilderStateRead`; `bild` enthält zusätzlich `anzeigename`. Akzeptierte Eingabe wird nur als WebP gespeichert. |
| `GET /website-builder/startseite` | JWT, Rolle `Inhaber`, eigener Mandant | liefert weiter den vollständigen Builder-Zustand; vorhandenes Bild erhält zusätzlich optionalen `anzeigename`, damit Editor ihn zeigt. |
| `GET /public/site` | öffentlich, Mandant nur aus verifizierter aktiver Domain | unverändert: sichtbare Sektionen enthalten nur proxied Bild-URL und `alt_text`, keinen Anzeigenamen, Speicherort oder Objektpfad. |
| `GET /public/sections/{section_id}/bild` | öffentlich, Mandant nur aus verifizierter aktiver Domain | unveränderter Pfad. Liefert für neue Bilder `image/webp`, für Legacy unverändert den bisherigen Content-Type; nur sichtbare Bildsektionen des aufgelösten Mandanten. |
| `DELETE /website-builder/sections/{section_id}/bild?version={n}` | JWT, Rolle `Inhaber`, `mandant_id` aus Token | unverändert. Löscht Verweis und versucht Objekt nur im durch `speicher_backend` bestimmten Storage zu löschen. |

Fehler bleiben deutsch und fachlich verständlich: ungültiges/animiertes Bild,
Konvertierung fehlgeschlagen, Datei zu groß, Bildspeicher nicht erreichbar und
veraltete `version` ergeben keinen neuen Verweis. Der Editor zeigt die
Servermeldung im bestehenden Bild-Fehlerbereich; das bisherige Bild und seine
Vorschau bleiben sichtbar.

### Konsistenz und Fehlerbehandlung

- Versionsprüfung vor Verarbeitung und nochmals vor dem Verweiswechsel. Ein
  zwischenzeitlicher Builder-Konflikt erzeugt `409`; das neue private Objekt
  wird gelöscht, der alte Verweis bleibt bestehen.
- Bei Prüf-, Dekodier-, Konvertierungs- oder Storagefehler wird weder Datenbank
  noch alter Speicherstand geändert. Schlägt das Speichern der Metadaten nach
  Object-Write fehl, löscht das Backend das neue Objekt sofort best-effort und
  protokolliert einen verbleibenden Aufräumfehler ohne es auszuliefern.
- Erst nach erfolgreichem Verweiswechsel wird das vorherige neue-Bild-Objekt
  best-effort gelöscht. Legacy-Objekte werden beim ersten Ersetzen nicht
  migriert oder konvertiert; ihr bisheriger Verweis bleibt bis zu einem
  bewusst neuen Upload lesbar.

### Technische Entscheidungen / ADRs

**ADR-23-1: Separater Website-Images-MinIO-Contract.** Eigener Endpoint,
Account und Bucket statt eines Prefixes im allgemeinen Speicher. Das trennt
Business OS belastbar von ImmoCRM und begrenzt einen Schlüssel auf genau diesen
Zweck. Bestehende `MINIO_*`-Nutzer bleiben unangetastet.

**ADR-23-2: Serverseitige WebP-Verarbeitung.** Die Browser senden weiter ihr
gewohntes Bild; FastAPI validiert und erzeugt das einzige Auslieferungsformat.
So sind Größe, Zuschnitt und Dateityp unabhängig vom Client verlässlich und es
existiert keine Rohkopie im neuen Speicher.

**ADR-23-3: Bestehende Proxy-URL statt presigned/direct URL.** Public Site und
Editor behalten gleiche URLs und Browser brauchen keinen MinIO-Zugang. Der
Backend-Proxy kann Speicherwechsel transparent behandeln und erzwingt die
Domain-/Mandantengrenze.

**ADR-23-4: Bestehende Bildtabelle erweitern.** Ein Speicherort-Flag ermöglicht
Legacy- und WebP-Bilder parallel ohne Migration. Eine neue Tabelle oder
responsive Varianten lösen kein Acceptance Criterion und werden nicht gebaut.

### Abhängigkeiten und Deployment

- **Backend neu:** `Pillow` für sichere Bilddekodierung, statische
  Frame-Prüfung, Zuschnitt und WebP-Encoding. Das Backend-Image muss beim Build
  WebP-Unterstützung verifizieren; ohne sie darf der Dienst nicht als
  uploadfähig bereitgestellt werden.
- **Backend vorhanden:** `minio`, FastAPI multipart und bestehender
  `BaseStorage`-Stil werden wiederverwendet.
- **Frontend:** keine neue Bibliothek. Bestehendes Next.js/shadcn nutzt den
  vorhandenen Upload-Client, hängt `alt_text` korrekt an `FormData`, ergänzt
  `anzeigename` und feste Bildcontainer.
- **Dokploy:** dedizierten MinIO-Service/Bucket plus die fünf
  `WEBSITE_IMAGES_MINIO_*`-Variablen im Backend setzen; nur Backend erhält
  diese Secrets. Deployment-Smoke: neues PNG/JPEG hochladen, `image/webp` über
  gleiche Origin abrufen, Legacy-Bild weiter abrufen und Speicherfehler ohne
  Verweiswechsel prüfen.

### Akzeptanzkriterien-Zuordnung

- WebP, dedizierter Speicher, keine Rohkopie: Bildregelwerk, ADR-23-1/2.
- Proxied URL und kein Browser-MinIO: API-Contracts, ADR-23-3.
- Kompression, Größenlimit und brauchbare Qualität: Bildregelwerk.
- Verzerrungsfreier, gleicher Ausschnitt: Zielformate und Renderer-Regel.
- Verständlicher, eindeutiger Name: `anzeigename`, Builder-Lesepfad.
- Trennung von ImmoCRM: Betriebsdaten und ADR-23-1.
- Keine Legacy-Migration: `speicher_backend=legacy`, ADR-23-4.
- Fehler ohne Verweiswechsel: Konsistenz und Fehlerbehandlung.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-23 · **Verdict:** Architected

### Checklist
- [x] Component structure — Upload bleibt in bestehendem `SectionEditor`, keine neue UI-Struktur nötig.
- [x] Data model — `website_section_bild` (`mandant_id`, RLS-Policy `website_section_bild_isolation`) bestätigt in `backend/sql/010_website_landingpage.sql:29-53`; neue Spalten technisch klar typisiert.
- [x] Owner-Check — jedes Feld hat genau einen Schreibpfad (Upload-Endpunkt `POST /website-builder/sections/{id}/bild`, Rolle `Inhaber`), verifiziert gegen `builder_routes.py:57-65` (`require_role("Inhaber")` via `_owner`, `builder_service.upload_section_bild`).
- [x] Lesepfad-Check — jeder Owner hat dokumentierte Lesepfade (`GET /website-builder/startseite`, `GET /public/site`, Bild-Proxy `GET /public/sections/{id}/bild`); alle drei existieren real (`builder_routes.py:18-20`, `routes.py:37-50`, `builder_service.py:51-58,234-257`).
- [x] API shape — alle 5 Endpunkte (POST/GET/DELETE Builder, GET/GET public) existieren bereits 1:1 im Code; Contract-Änderungen (WebP-only, `anzeigename`) sind additiv.
- [x] Tech-Entscheidungen — 4 ADRs mit Begründung vorhanden.
- [x] Dependencies — `Pillow` neu (fehlt in `backend/requirements.txt`, bestätigt), `minio`/`python-multipart` bereits vorhanden (`requirements.txt:8-9`).
- [x] Konflikt-frei — Migration `011_website_section_images.sql` frei (höchste bestehende ist `010_website_landingpage.sql`); kein Routen-/Namenskonflikt.
- [x] Acceptance-Criteria-Zuordnung — alle 8 Kriterien haben ein Tech-Design-Zuhause.

### CodeGraph-Cross-Check (Explore-Agent gegen echten Code)
- Upload-Endpunkt-Contract bestätigt: `builder_routes.py:57-65` (`alt_text: Annotated[str, Form()]`, `datei: File`, `version: Query`).
- **Gefundener echter Bug** (Design-Text war ungenau, jetzt präzisiert): Client sendet `alt_text` aktuell als Query-Param (`nextjs_app/lib/api/website-builder.ts:95`), Server erwartet es aber als `Form()`-Feld — der Server erhält daher immer einen leeren `alt_text`. In der Spec korrigiert (Abschnitt „Komponenten und Ablauf", Schritt 1) mit exaktem Fix-Auftrag für `/abc-frontend`.
- `MinioStorage`/`BaseStorage`-Abstraktion bestätigt in `backend/app/storage.py:9-100`; neuer `WebsiteImageStorage` kann denselben Stil (`put_object`/`get_object`/`delete_object`, lazy Client) wiederverwenden.
- RLS-Policy `website_section_bild_isolation` real vorhanden (`010_website_landingpage.sql:52-53`); neue Migration muss nur Spalten ergänzen, keine neue Policy nötig — Design sagt das bereits korrekt.
- `_resolve_mandant` aus Hostname (`service.py:78-82`) bestätigt Mandantenauflösung des öffentlichen Proxys ohne Client-Input.
- Kein `Pillow` in `requirements.txt` (bestätigt neu), kein bestehendes `WEBSITE_IMAGES_MINIO_*` (bestätigt, da neu vorgeschlagen).
- Kein Routen-/Tabellennamenskonflikt gefunden.

### Autonom behoben
- Objektpfad-Präfix in der Datenmodell-Tabelle von `sections/...` auf `website-sections/...` korrigiert, konsistent mit bestehendem Legacy-Muster in `builder_service.py:186`.
- Schritt 1 im Ablauf präzisiert: aus vager/zweideutiger Formulierung wurde ein expliziter, code-referenzierter Bugfix-Auftrag für den Next.js-Client (Query-Param → FormData für `alt_text`).

### Offene Fragen
Keine. Owner-Check und Lesepfad-Check bestehen für jede Datenmodell-Zeile.

## QA Test Results
**Getestet:** 2026-08-23 · **Status: NOT READY**

### Automatisiert
- Backend: `.venv/bin/python -m pytest` → 221/221 grün (kein conda-Env in diesem Worktree, `.venv` verwendet).
- Migration `011_website_section_images.sql`: idempotent (`ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`) — bestätigt durch Lesen.
- Frontend: `npx tsc --noEmit` → EXIT 0. `alt_text`-Fix in `website-builder.ts:97-99` verifiziert: liegt jetzt in `FormData`, nicht mehr in Query-Params. Vertrag mit `builder_routes.py:60` (`Form()`) stimmt.

### Acceptance Criteria (eigene Testläufe gegen echten FastAPI-TestClient, SQLite-Fixture)
1. WebP-Speicherung im dedizierten MinIO — **PASS**. Upload konvertiert nach WebP, landet in `image_storage` (`bizos_bilder`), nicht in `storage` (Legacy). Verifiziert per eigenem Testskript.
2. Proxied Bild-URL ohne Browser-MinIO-Zugriff — **PASS**. `bild.url` bleibt `/public/sections/{id}/bild`.
3. Kompression/Dimensionierung mit brauchbarer Qualität — **PASS** (Qualität 82, `WEBP_MAX_EDGE=1600`).
4. **Verzerrungsfreier Zuschnitt auf festes Seitenverhältnis (16:9 Hero / 4:3 Text-mit-Bild) — FAIL.** Spec fordert `cover`-Crop auf exakt 1920×1080 bzw. 1200×900. `_to_webp()` in `builder_service.py:236-257` macht nur `img.thumbnail((max_edge, max_edge))` — behält das Ausgangsseitenverhältnis bei und schneidet nie zu. Eigener Test: 3000×1000-Upload auf Hero landet als 1600×533 (statt 1920×1080, 16:9-cover); 500×3000-Upload auf Text-mit-Bild landet als 267×1600 (statt 1200×900). Editor/Public-Renderer erzwingen `object-cover`/`aspect-[4/3]` nur clientseitig per CSS — das befriedigt AC4 nicht, weil "Vorschau entspricht der öffentlichen Darstellung" nur zufällig stimmt und das gespeicherte Bild selbst nicht zugeschnitten ist (unnötig große/kleine Dateien, falsches Seitenverhältnis in Rohdaten).
5. **Eindeutiger Anzeigename aus Sektionstyp+Überschrift (`anzeigename`) — FAIL.** Komplett nicht implementiert: kein `anzeigename`-Feld in `builder_schemas.BildRead`, `builder_repository.upsert_bild`/`get_bild`, `builder_service.upload_section_bild`. Migration 011 fügt auch keine `anzeigename`-Spalte hinzu (obwohl Tech-Design das für Zeile `anzeigename` in der Datenmodell-Tabelle explizit fordert, inkl. partiellem Unique-Index `(mandant_id, anzeigename) WHERE anzeigename IS NOT NULL`). Kein Namens-Deduplizierung ` (2)`, ` (3)` vorhanden.
6. Getrennte MinIO-Zugangsdaten/Bucket von ImmoCRM — **PASS**. Eigene `BILDSPEICHER_MINIO_*`-Env-Variablen (`config.py:32-36`), eigener `image_storage`-Client (`storage.py:110-116`), eigener Default-Bucket `business-os-bilder`.
   - **Hinweis (Abweichung von der Spec):** Spec nennt die Env-Variablen `WEBSITE_IMAGES_MINIO_*` und den Check-Constraint-Wert `website_images`; Implementierung nutzt `BILDSPEICHER_MINIO_*` und `bizos_bilder`. Funktional äquivalent (Trennung ist gegeben), aber Namensabweichung von Tech-Design — für Dokploy-Deployment relevant, da Deployment-Doku ggf. falsche Variablennamen erwartet. Als Doku-Bug (Low) vermerkt, kein Blocker.
7. Bestehende Bilder bleiben unverändert (`speicher_backend=legacy` Default) — **PASS**. Migration setzt nur Default, keine Konvertierung/Kopie bestehender Zeilen.
8. **Fehler ohne Verweiswechsel bei Speicherfehler, deutsche Fehlermeldung — FAIL.** Eigener Test: `image_storage.put_object` wirft `RuntimeError` (simulierter MinIO-Ausfall) → Route liefert **HTTP 500 "Internal Server Error"** statt eines gefangenen, deutschen Fehlers. `builder_service.upload_section_bild()` fängt nur Fehler in `_to_webp()` (Pillow-Decodierfehler) ab; der `storage_mod.image_storage.put_object(...)`-Aufruf in Zeile 198 ist ungeschützt. Positiv: der alte Bildverweis in der DB bleibt tatsächlich unverändert (kein Verweiswechsel), aber der Nutzer sieht einen technischen 500-Fehler statt der geforderten "deutschen, verständlichen" Meldung — verletzt sowohl AC8 als auch den Fehlerbehandlungs-Abschnitt im Tech-Design ("Bildspeicher nicht erreichbar" als expliziter Fehlerfall).

### Edge Cases
- **Animierte GIFs werden nicht abgewiesen — FAIL (Edge Case, siehe auch AC8-Umfeld).** Spec: "Ein animiertes ... Format wird mit einer verständlichen Meldung abgewiesen". Eigener Test: 2-Frame-Animated-GIF-Upload → `200 OK`, wird klaglos als (erstes-Frame-)WebP gespeichert. `_to_webp()` prüft `img.mode`/lädt nur `img.load()`, aber nie `getattr(img, "is_animated", False)`. Kein Reject, keine Fehlermeldung.
- Transparente PNG: strukturell plausibel (RGBA/LA/P-Pfad in `_to_webp()`), nicht separat pixelverifiziert.
- Sehr große Quellbilder: Begrenzung über `max_edge=1600` vorhanden, aber siehe AC4 — das ist keine feste Zielgröße, sondern nur eine Kantenbegrenzung ohne Crop.
- Parallelbetrieb Legacy+WebP: strukturell durch `speicher_backend`-Flag gegeben, durch bestehenden Test `test_upload_bild_stored_as_webp_in_dedicated_storage` abgedeckt.

### Security-Red-Team
- Cross-Tenant (`test_owner_cannot_see_other_tenant_sections`): PASS, bestehender Test grün.
- `mandant_id` kommt ausschließlich aus JWT (`user.mandant_id`), keine Client-Eingabe im Upload-Pfad — kein Injection-Vektor über Sektions-/Bild-Endpunkte gefunden.
- Magic-Byte-Sniffing (`_sniff_image_ext`) statt MIME-Header-Vertrauen — vorhanden, korrekt.
- Kein Objektpfad/Speicherort in API-Antworten (`objektpfad` nicht in `BildRead`/`BuilderSectionRead`) — bestätigt per Schema-Lektüre.
- Kein neuer Angriffsvektor durch `anzeigename` identifiziert (Feld fehlt komplett, siehe AC5).

### Regression
- Volle Backend-Suite (221 Tests) grün, keine Regression in anderen Features festgestellt.

### Bugs
| # | Schweregrad | Beschreibung | Fundort |
|---|---|---|---|
| BUG-1 | **High** | Kein Cover-Crop auf festes Seitenverhältnis (AC4) — Bilder behalten Ausgangsformat, nur Kantenbegrenzung statt fester Zielgröße/-verhältnis. | `backend/app/features/website/builder_service.py:236-257` (`_to_webp`) |
| BUG-2 | **High** | `anzeigename` (AC5) komplett nicht implementiert — fehlt in Schema, Repository, Service und Migration. | `builder_schemas.py`, `builder_repository.py`, `builder_service.py`, `sql/011_website_section_images.sql` |
| BUG-3 | **High** | Speicherfehler beim Upload (z. B. MinIO nicht erreichbar) führt zu ungefangenem HTTP 500 statt deutscher Fehlermeldung (AC8). | `backend/app/features/website/builder_service.py:198` |
| BUG-4 | **Medium** | Animierte GIFs werden nicht erkannt/abgewiesen — werden klaglos als Standbild-WebP gespeichert (Edge Case aus Spec). | `backend/app/features/website/builder_service.py:236-269` (`_to_webp`, `_sniff_image_ext`) |
| BUG-5 | **Low** | Env-Variablen-/Constraint-Namen weichen vom Tech-Design ab (`BILDSPEICHER_MINIO_*`/`bizos_bilder` statt `WEBSITE_IMAGES_MINIO_*`/`website_images`). Funktional unkritisch, aber Deployment-Doku-Risiko. | `backend/app/config.py:32-36`, `sql/011_website_section_images.sql:10` |

### Produktionsreife-Empfehlung: **NOT READY**
3 High-Bugs (BUG-1, BUG-2, BUG-3) blockieren Deployment. BUG-4 (Medium) und BUG-5 (Low) sollten mitgefixt bzw. dokumentiert werden.

## QA Re-Test Results

**Getestet:** 2026-08-23 · **Status: NOT READY**

### Akzeptanzkriterien

- [x] AC-1 bis AC-4: Neue Uploads werden als WebP im dedizierten Speicher abgelegt, über die Proxy-URL ausgeliefert und korrekt zugeschnitten.
- [x] AC-5 Backend: Name aus Sektionsart/Überschrift, inklusive ` (2)`-Deduplizierung, wird gespeichert und geliefert.
- [x] AC-6 bis AC-8: Legacy-Bilder bleiben lesbar; getrennte Storage-Konfiguration und deutscher 503 ohne Verweiswechsel sind verifiziert.
- [ ] AC-5 Editor: `anzeigename` fehlt in Next.js-Typ und `SectionEditor`; der Name ist für Nutzer nicht sichtbar.

### Edge Cases und Sicherheit

- [x] Kleine Bilder werden nicht hochskaliert; animierte GIFs werden mit 422 abgelehnt.
- [x] Auth, Inhaber-Rolle, Magic-Byte-Validierung und Tenant-Grenze sind durch Route/Tests abgesichert.
- [ ] Ein paralleler Edit während der Bildverarbeitung wird nicht erneut gegen die Version geprüft.

### Automatisierte Tests

- Backend Website-Builder: **27 bestanden, 1 fehlgeschlagen** (der neue Konflikt-Test).
- Next.js: **28 bestanden**; `npm run typecheck` erfolgreich.

### Bugs

| # | Schweregrad | Befund |
|---|---|---|
| BUG-6 | **High** | Ein Upload mit veralteter Version wird nach einem parallelen Edit mit 200 gespeichert, statt 409 zu liefern. Der fehlgeschlagene Test `test_upload_bild_rejects_version_changed_during_processing` belegt den überschriebenen Bildverweis. |
| BUG-7 | **High** | `anzeigename` wird vom Backend geliefert, fehlt aber in `website-builder-types.ts` und `section-editor.tsx`; AC-5 ist im Editor nicht erfüllt. |
| BUG-8 | **Medium** | `uploadSectionBild` sendet `alt_text` weiter als Query-Parameter, die Route erwartet es als Form-Feld. Das gespeicherte Alt-Attribut bleibt daher leer. |

### Produktionsreife

**NOT READY** — BUG-6 und BUG-7 vor Deployment beheben. BUG-8 im selben Frontend-Fix mitnehmen.

## QA Final Re-Test

**Getestet:** 2026-08-23 · **Status: READY**

- [x] BUG-6: Der Upload prüft die Version nach der Verarbeitung erneut, löscht das neue Objekt bei Konflikt und liefert 409.
- [x] BUG-7: Der Editor zeigt den vom Backend gelieferten Anzeigenamen.
- [x] BUG-8: Der Client sendet `alt_text` im Multipart-Formular.
- [x] Backend: vollständige Pytest-Suite grün.
- [x] Next.js: 29 Tests, Typecheck und Production-Build grün.

### Produktionsreife

**READY** — keine offenen Critical- oder High-Bugs.

## Deployment
_To be added by /deploy_
