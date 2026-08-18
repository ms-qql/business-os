# PROJ-2: Geführte SHK-Website, Branding und Anfrageformular

## Status: Deployed
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

## Implementation Note — 2026-08-17

Website-Anfragen werden nach dem Speichern sofort über den bestehenden
Übernahmepfad als Vorgang angelegt; die Anfrage bleibt als nachvollziehbare
Quelle mit `vorgang_id` verknüpft. Migration `005_website_anfragen_uebernehmen.sql`
übernimmt noch nicht verknüpfte Altanfragen inklusive Bilder beim nächsten
Backend-Start idempotent.

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
  Kein separates Textfeld für Impressum/Datenschutz: beide Seiten werden aus
  den vorhandenen Stammdaten (Firmenname, Adresse, Kontakt) serverseitig
  generiert, nicht frei editiert.
- **Leistungsseite:** vordefinierte SHK-Leistung mit aktivem/inaktivem Status
  und den dafür freigegebenen Textfeldern. Inaktive Leistungen werden weder
  verlinkt noch direkt ausgeliefert.
- **Öffentliche Domain:** eindeutige Zuordnung eines Hostnamens zu einem
  aktiven Mandanten. Sie ist die alleinige Quelle für den öffentlichen
  Mandantenkontext.
- **Anfrage:** eigenständige Tabelle mit Name, gewähltem Kontaktweg, Adresse,
  Anliegen, Dringlichkeit, Zeitfenster, Eingangszeitpunkt und Quelle
  `Website`. PROJ-3 (Vorgänge, Status: Planned) existiert im Code noch nicht;
  `anfrage` referenziert kein `vorgang` und wird bei Einführung von PROJ-3
  migriert/verknüpft, nicht vorweggenommen.
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
Einstellungen-Endpunkte verwenden `Depends(get_current_user)` +
`require_role("Inhaber")` (`backend/app/deps.py:33-74`) und den
Mandantenkontext (`mandant_id` aus dem Token, RLS via `SET LOCAL
app.current_mandant_id` in `backend/app/db.py:36-69`) aus PROJ-1.

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
- **Rate-Limit und Honeypot am öffentlichen Eingang:** kein Rate-Limit-Paket
  im Code vorhanden (kein slowapi o. ä.); Wiederverwendung des bestehenden
  Musters aus `login_versuche` (`backend/sql/001_init.sql:57-63`) — eine neue
  Tabelle protokolliert Anfrageversuche je IP/Zeitfenster, ohne neue
  Drittanbieter-Abhängigkeit. Begrenzt automatisierten Missbrauch, ohne eine
  Anmeldung oder einen externen Captcha-Anbieter zur Pflicht zu machen.
  Upload-Größe, Bildformat und Anzahl werden vor der Speicherung serverseitig
  geprüft.
- **Keine E-Mail-Zustellung in PROJ-2:** die Bestätigung ist eine Website-Seite;
  die Inbox- und Kommunikationskette folgt bewusst erst in PROJ-4.

### Abhängigkeiten

- **Next.js 16, Tailwind und shadcn/ui:** responsive Website und zugängliche
  Einstellungsformulare.
- **FastAPI und Pydantic:** öffentliche Formulareingänge sowie geschützte
  Inhaber-Einstellungen.
- **PostgreSQL mit RLS:** Mandantentrennung für Einstellungen und Vorgänge.
- **MinIO:** Logo- und Bildobjekte. Im Code noch keine MinIO/S3-Anbindung
  vorhanden (erste Integration dieser Art) — neues Paket `minio` (Python SDK)
  für Objekt-Upload und Presigned URLs.
- **Migrationsdatei:** `backend/sql/002_website.sql` nach dem Muster von
  `backend/sql/001_init.sql` (einzige Migrationsquelle, kein Alembic;
  `CREATE TABLE IF NOT EXISTS` + RLS-Policy + Index je Tabelle) für
  `website_settings`, `leistungsseite`, Domain-Zuordnung, `anfrage`,
  `anfragebild` und die Rate-Limit-Tabelle.
- **Sonst kein neues Drittanbieterpaket:** Browser-Formularfunktionen,
  vorhandene Authentifizierung und serverseitige Validierung genügen
  darüber hinaus für V1.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-16 · **Verdict:** Architected

### Checklist
- [x] Component structure — ok, jede Fläche bildet auf shadcn/ui + Next.js Route ab.
- [x] Data model — Impressum/Datenschutz: automatisch aus Stammdaten generiert (User-Entscheidung), kein zusätzliches Textfeld nötig.
- [x] API shape — ok; Rollen-Guard (`require_role("Inhaber")`) und RLS-Herkunft jetzt explizit ergänzt.
- [x] Tech decisions — jede Entscheidung mit Begründung.
- [x] Dependencies — MinIO-Paket (`minio` SDK) und Migrationsdatei-Konvention ergänzt; kein bestehendes Muster im Code, jetzt benannt.
- [x] Branch field — `dev`, aktueller Branch, gültig.
- [x] Conflict-free — CodeGraph: keine Tabellen/Routen-Kollision (nur `mandanten, nutzer, sitzungen, einladungen, passwort_resets, login_versuche, audit_events, betreiber, betreiber_sitzungen` existieren; kein `/public/*`, kein `/website-settings`).
- [x] Acceptance-criteria coverage — AC1 (Impressum/Datenschutz) jetzt gedeckt durch Ableitung aus Stammdaten.

### Autonom behoben
- Rollen-Guard für `/website-settings*` explizit auf `require_role("Inhaber")` + `backend/app/deps.py:33-74` referenziert (war implizit).
- RLS-Mechanik konkretisiert: `SET LOCAL app.current_mandant_id`, `backend/app/db.py:36-69` (war nur "RLS-Kontext aus PROJ-1").
- „Anfrage" von „neuer Vorgang" zu eigenständiger Tabelle korrigiert — PROJ-3 (Vorgänge) ist Status Planned und existiert im Code nicht; keine Fremdreferenz vorwegnehmen.
- Rate-Limit-Ansatz konkretisiert: kein Rate-Limit-Paket im Code vorhanden — Wiederverwendung des `login_versuche`-Musters (`backend/sql/001_init.sql:57-63`) statt unspezifizierter Drittanbieter.
- MinIO als neue, im Code noch nicht vorhandene Integration benannt (`minio`-SDK) statt stillschweigend vorausgesetzt.
- Migrationsdatei-Konvention ergänzt: `backend/sql/002_website.sql` nach Muster `001_init.sql` (kein Alembic im Projekt).
- Offene Frage geklärt (User): Impressum & Datenschutzhinweis werden automatisch aus Stammdaten (Firmenname, Adresse, Kontakt) generiert — Datenmodell-Abschnitt entsprechend ergänzt, kein zusätzliches Textfeld.



## Implementation Notes (Frontend)
**Umgesetzt:** 2026-08-16 · Next.js 16 App Router, TypeScript, Tailwind + hand-gerollte shadcn-artige Primitives, Zod + react-hook-form

### Gebaut
- **Host-basiertes Routing (`nextjs_app/proxy.ts`):** neue Datei (Next 16 heißt die Middleware-Konvention „proxy"). Requests, deren Hostname nicht in `APP_HOST` (Default `localhost,127.0.0.1`) enthalten ist und nicht bereits unter `/site/*` liegen, werden serverseitig auf `/site/*` umgeschrieben (URL im Browser bleibt unverändert). Die eigentliche Mandantenauflösung passiert weiterhin im Backend über den Hostnamen (`GET /public/site`); der Proxy entscheidet nur, welcher Next.js-Routenbaum gerendert wird. `/site/*` bleibt zusätzlich direkt erreichbar — praktisch für lokale Entwicklung ohne Host-Manipulation.
- **Öffentliche Website** unter `nextjs_app/app/site/`: `layout.tsx` (+ `site-context.tsx` mit `SiteProvider`/`useSite`/`useSiteBase`) lädt `GET /public/site` einmal und rendert Kopf-/Fußbereich (`components/site/site-header.tsx`, `site-footer.tsx`); Markenfarbe wird als CSS-Variable `--color-brand` pro Betrieb überschrieben (Laufzeitdaten, keine Compile-Time-Tokens). Seiten: `page.tsx` (Startseite: Hero, Leistungsübersicht, Kontakt), `leistungen/[slug]/page.tsx` (lädt `GET /public/leistungen/{slug}`, zeigt neutrale "nicht verfügbar"-Seite bei 404/inaktiv), `anfrage/page.tsx` (Formular), `anfrage/danke/page.tsx` (Bestätigung), `impressum/page.tsx` und `datenschutz/page.tsx` (aus den Website-Stammdaten clientseitig zusammengesetzt, keine freien Textfelder — wie im Tech Design festgelegt).
- **Anfrageformular** (`app/site/anfrage/page.tsx`): react-hook-form + Zod mit deutschen Fehlermeldungen (Pflichtfelder, bedingte Validierung Telefon/E-Mail je nach Kontaktweg). Bis zu 5 Bilder, clientseitige Vorprüfung (Anzahl, Bildtyp, 8 MB je Datei) mit Fehlermeldung ohne Verlust der übrigen Formulardaten (kein `reset()` bei Fehler). Client-Idempotenz: `crypto.randomUUID()` einmalig pro Formularversuch (`uebermittlungskennung`), an alle Uploads und den finalen Submit angehängt. Absenden-Button sperrt sofort (`disabled={wirdGesendet}`) und bleibt bis Erfolg/Fehler gesperrt.
- **Website-Einstellungen** (`app/(app)/website-einstellungen/page.tsx`, `lib/api/website-settings.ts`): nur im Nav für Rolle „Inhaber" sichtbar (`NAV_RECHTE`), wie bei Nutzerverwaltung folgt die eigentliche Durchsetzung dem bestehenden Muster serverseitig (`require_role("Inhaber")`). Branding/Kontakt/Öffnungszeiten/Über-uns-Formular, Logo-Upload, sowie Leistungsliste mit Aktiv-Umschalter und Kurzbeschreibung/Inhalt-Editor.
- **API-Clients:** `lib/api/public.ts` (unauthentifiziert, `/public/site`, `/public/leistungen/{slug}`, `/public/anfragen/uploads`, `/public/anfragen`) und `lib/api/website-settings.ts` (authentifiziert via bestehendem `apiFetch`).
- **Bugfix in `lib/api/client.ts`:** `apiFetch`/`operatorApiFetch` setzten bisher immer `Content-Type: application/json`, sobald ein Body vorhanden war — das hätte den neuen Logo-Upload (FormData/multipart) gebrochen. Fix: Content-Type wird nicht gesetzt, wenn `body instanceof FormData` (Browser setzt dann automatisch die korrekte Multipart-Boundary).
- Neue UI-Primitive: `components/ui/textarea.tsx` (fehlte bisher, analog zu `input.tsx`).
- `lib/theme/tokens.ts`: `NAV_RECHTE.Inhaber` um `website-einstellungen` ergänzt.

### Abweichungen / bewusste Vereinfachungen
- **SSR/SEO für öffentliche Seiten nicht umgesetzt:** Tech Design nennt "servergerenderte öffentliche Seiten" als Vorteil; die öffentlichen Seiten sind hier `"use client"`-Komponenten mit Client-Fetch (wie der Rest der bestehenden Codebasis, kein Precedent für Server-Components-Datenfetching in diesem Repo). Grund: zuverlässiges Weiterreichen des angefragten Hostnamens vom Next.js-Server an das Backend bei echtem serverseitigem Fetch ist ohne laufendes Backend nicht verifizierbar; die bestehende Client-Fetch-Konvention (`apiFetch`-Pattern) funktioniert hostnamen-transparent (Same-Origin-Request trägt den echten Host). Upgrade bei Bedarf: Server Components + `headers()`/`x-forwarded-host`, wenn SEO/Erstladezeit kritisch werden.
- **Zeitfenster als Freitext** statt vordefinierter Auswahl — Spec nennt kein festes Format.
- **Dringlichkeit/Kontaktweg-Werte** (`Normal"/"Dringend"`, `"Telefon"/"E-Mail"`) sind Frontend-Annahmen mangels Vorgabe im Tech Design; müssen mit dem Backend-Schema abgeglichen werden, sobald `backend/app/features/website/` entsteht.
- **Kein `select.tsx`/`dialog.tsx` shadcn-Primitive neu gebaut** — native `<select>`/`<input type="file">`, gestylt wie im bestehenden Nutzerverwaltung-Muster, um keine ungenutzte Abstraktion einzuführen.

### Offen (Backend-Abhängigkeit)
Backend-Routen für PROJ-2 existieren im Code noch nicht (`grep -ri "website|anfrage|public" backend/app` → keine Treffer zum Zeitpunkt dieser Umsetzung). Das Frontend ist vollständig gegen die im Tech Design dokumentierte API-Form gebaut (`GET /public/site`, `GET /public/leistungen/{slug}`, `POST /public/anfragen/uploads`, `POST /public/anfragen`, `GET/PATCH /website-settings`, `POST /website-settings/logo`), aber ungetestet gegen einen echten Server. Insbesondere zu klären, sobald Backend implementiert: exakte Feldnamen/Enums (`kontaktweg`, `dringlichkeit`), Upload-Response-Form (`upload_id`), Fehlerformat bei Validierungsfehlern (aktuell wird `detail` als Klartext-String erwartet, wie im bestehenden `ApiError`-Muster).

`npm run build` und `npx next lint` liefen sauber (0 Fehler, 0 Warnungen); `npx tsc --noEmit` ohne Fehler.

## Implementation Notes (Backend)
**Umgesetzt:** 2026-08-16 · FastAPI, raw SQL (`db.engine.query`/`command`, `SET LOCAL app.current_mandant_id`), Pydantic v2, MinIO (neues `minio`-SDK)

### Gebaut
- **Migration `backend/sql/002_website.sql`** (Muster wie `001_init.sql`): `website_settings` (1 Zeile je Mandant), `website_domains` (Hostname → Mandant, eindeutig, `status` aktiv/inaktiv), `leistungsseite` (Katalogzeile je Mandant+Slug, `aktiv`/`kurzbeschreibung`/`inhalt`), `anfrage` (eigenständig, kein `vorgang`-Bezug, `UNIQUE(mandant_id, uebermittlungskennung)` für Idempotenz), `anfragebild` (Bezug zu `anfrage`, `anfrage_id` zunächst NULL bis Verknüpfung beim Submit), `website_anfrage_versuche` (Rate-Limit nach Vorbild `login_versuche`). RLS + Policy + Index je Tabelle. Domainauflösung läuft über eine `SECURITY DEFINER`-Funktion `website_find_mandant_by_hostname` (analog `auth_find_user_by_email`), da vor Mandantenauflösung kein RLS-Kontext existiert.
- **`backend/app/storage.py`** (neu, flach unter `app/` wie `db.py`/`security.py` — kein `core/`-Ordner im Repo): `BaseStorage`/`MinioStorage`/`InMemoryStorage` + globales `storage`-Objekt mit `set_storage()`, exakt nach dem `db.py`-Muster (`engine`/`set_engine`). `MinioStorage` verbindet sich lazy (erst beim ersten Upload), damit der Import keinen Netzwerkzugriff auslöst. DB speichert nur den Objektpfad; URLs werden zur Lesezeit als Presigned-GET generiert.
- **Feature-Ordner `backend/app/features/website/`**: `schemas.py`, `repository.py`, `service.py`, `routes.py` (zwei Router: `public_router` unter `/public`, `settings_router` unter `/website-settings`, registriert in `app/main.py`).
- **Domainauflösung** (`routes._hostname`): liest `x-forwarded-host` (Next.js-Rewrite-Fall), sonst `host`-Header, Port abgeschnitten. Der Mandant kommt bei öffentlichen Routen ausschließlich hieraus, nie aus Client-/Formulardaten.
- **Leistungskatalog:** fester, vordefinierter Katalog (`service.SEED_LEISTUNGEN`: Heizung, Sanitär, Bad, Notdienst, Energieberatung) — wird beim ersten Zugriff je Mandant automatisch angelegt (`_get_or_create_settings`), alle Leistungen starten inaktiv. Inhaber kann nur `aktiv`/`kurzbeschreibung`/`inhalt` bestehender Katalog-Slugs ändern, keine neuen Leistungen anlegen (Baukasten bewusst nicht Teil von V1).
- **Bild-/Logo-Validierung:** serverseitige Prüfung per Magic-Bytes (`service._sniff_image_ext`), nicht per client-gemeldetem `Content-Type` — verhindert triviales Spoofing. Erlaubt: JPEG/PNG/GIF/WEBP. Limits: 8 MB je Anfragebild (deckt sich mit Frontend-Grenze), 5 MB fürs Logo, max. 5 Bilder je Anfrage (serverseitig zusätzlich zur Client-Prüfung durchgesetzt).
- **Idempotenz:** `POST /public/anfragen` prüft zuerst `anfrage` per `(mandant_id, uebermittlungskennung)`; existiert bereits eine Zeile, wird `200`/`201 {"ok": true}` ohne zweiten Datensatz zurückgegeben (kein Fehler bei Wiederholung nach Netzabbruch).
- **Rate-Limit:** `website_anfrage_versuche` (IP + Zeitstempel) nach `login_versuche`-Muster; gilt gemeinsam für `/public/anfragen/uploads` und `/public/anfragen` (`settings.anfrage_rate_limit_max`, Default 20 je 15 Minuten, konfigurierbar über `ANFRAGE_RATE_LIMIT_MAX`/`ANFRAGE_RATE_LIMIT_WINDOW_MIN`). Überschreitung → `429` (neue `TooManyRequestsError` in `app/errors.py`).
- **`app/config.py`**: neue Settings `minio_endpoint/access_key/secret_key/bucket/secure`, `anfrage_rate_limit_max/window_minutes`; `.env.example` entsprechend ergänzt.
- **`requirements.txt`**: `minio>=7.2` ergänzt (im Dashboard-Conda-Env installiert und verifiziert).
- **Tests:** `backend/tests/features/website/test_public_site.py` (öffentliche Seiten, Domainauflösung inkl. unbekannt/inaktiv, Tenant-Isolation, Upload-Validierung, Idempotenz, Bild-Verknüpfung) und `test_website_settings.py` (Auth 401/403, Owner-CRUD, Leistungs-Patch, Domain-Anzeige, Tenant-Isolation, Logo-Upload inkl. Ablehnung ungültiger Dateien). `tests/conftest.py` um die neuen SQLite-Testtabellen, eine `object_storage`-Autouse-Fixture (schaltet auf `InMemoryStorage` um) und einen `make_domain`-Helper ergänzt.

### Vertragsabgleich mit dem Frontend (`nextjs_app/lib/api/public.ts`, `website-settings.ts`)
Das Tech Design hatte `kontaktweg`/`dringlichkeit`-Werte und die Upload-Response-Form offengelassen ("Frontend-Annahmen mangels Vorgabe"). Da hier kein Widerspruch zum Tech-Design-Text bestand (nur eine Lücke), wurden die vom Frontend bereits implementierten Werte **unverändert als Vertrag übernommen** — keine Abweichung, keine Frontend-Änderung nötig:
- `kontaktweg`: `"Telefon" | "E-Mail"`
- `dringlichkeit`: `"Normal" | "Dringend"`
- Upload-Response: `{"upload_id": "<uuid>"}`
- `POST /public/anfragen`-Body inkl. `upload_ids: string[]` und `uebermittlungskennung: string` — genau wie in `AnfrageInput` im Frontend.
- `WebsiteSettingsRead`/`PublicSite`-Felder (`firmenname`, `logo_url`, `marken_farbe`, `telefon`, `email`, `adresse`, `oeffnungszeiten`, `ueber_uns`, `domain`, `domain_status`, `leistungen[].{slug,titel,aktiv,kurzbeschreibung,inhalt}`) exakt wie in `lib/api/website-settings.ts`/`public.ts` übernommen.

### Bewusste Vereinfachungen
- **Server-seitige Validierungsfehler (422) nutzen das Standard-FastAPI-Format** (`detail: [...]` als Liste) für Pydantic-Feldfehler (z. B. fehlender Pflichtwert), aber das **projektübliche String-`detail`** (`app.errors.ValidationError` → `{"detail": "<deutscher Text>"}`) für alle fachlichen Prüfungen (Pflichtfeld je Kontaktweg, Bildformat/-größe, Rate-Limit, unbekannte Domain). Das ist identisch zum bestehenden Verhalten in `auth`/`users` und wurde nicht neu eingeführt.
- **Domain-Verwaltung selbst ist nicht Teil dieses Features** — `GET/PATCH /website-settings` zeigt nur die (andernorts, z. B. Betreiber-Onboarding, angelegte) Domain an; es gibt keinen Endpunkt zum Setzen/Ändern der Domain. Entspricht dem Tech Design (nur "Domainstatus" unter den Einstellungsfeldern gelistet).
- **Ein Domain-Datensatz je Mandant wird angezeigt** (`ORDER BY created_at LIMIT 1`), falls mehrere existieren sollten — Datenmodell erlaubt mehrere Hostnamen je Mandant, die Owner-Ansicht zeigt bewusst nur einen. Upgrade bei Bedarf: Liste statt Einzelwert.
- **MinIO-Bucket wird lazy und automatisch angelegt** (`bucket_exists`/`make_bucket` beim ersten Objekt-Zugriff), kein separates Infra-Provisioning-Skript nötig.
- **`docker-compose.yml` nicht verändert** — MinIO-Service/Env-Var-Durchreichung ist Deploy-Infrastruktur und bleibt human-gated bei `/abc-deploy`.

### Tests
`conda run -n Dashboard --no-capture-output python -m pytest` → 36 grün (20 bestehende + 16 neue für PROJ-2), keine Regression.

## QA Test Results
**Getestet:** 2026-08-17 · QA Engineer / Red-Team · Backend: `conda run -n Dashboard --no-capture-output python -m pytest` (36 grün) · Frontend: `npx tsc --noEmit` (0 Fehler), `npm run build` (erfolgreich)

### Akzeptanzkriterien

| # | Kriterium | Ergebnis | Anmerkung |
|---|---|---|---|
| 1 | Geführte SHK-Vorlage (Startseite, Leistungen, Über-uns/Kontakt, Impressum, Datenschutz) je Betrieb | PASS | Alle Routen vorhanden (`app/site/page.tsx`, `leistungen/[slug]`, `impressum`, `datenschutz`), Backend liefert Stammdaten dafür. |
| 2 | Inhaber kann Logo, Farben, Firmenname, Adresse, Telefon, E-Mail, Öffnungszeiten, Leistungsseiten ändern | PASS | `GET/PATCH /website-settings`, `POST /website-settings/logo`; per Test verifiziert (`test_owner_reads_and_updates_settings`, `test_owner_updates_leistungen`, `test_owner_uploads_logo`). |
| 3 | Formular erfasst Name, Kontaktweg, Adresse, Anliegen, Dringlichkeit, Zeitfenster, bis zu 5 Bilder | PASS | Felder vorhanden; serverseitiges Limit von 5 Bildern verifiziert (6. Upload → 422). |
| 4 | Pflichtfelder mit deutscher Feldmeldung vor Versand; Website ohne Anmeldung nutzbar | PASS | Zod-Schema mit deutschen Meldungen; öffentliche Routen ohne `Depends(get_current_user)`. |
| 5 | Erfolgreiche Übermittlung erzeugt genau einen Vorgang im richtigen Mandanten + Bestätigungstext „Vielen Dank. Wir melden uns zeitnah bei Ihnen.“ | PASS (mit dokumentierter Abweichung) | Text exakt geprüft (`app/site/anfrage/danke/page.tsx`). „Vorgang“ existiert im Code noch nicht (PROJ-3 Planned) — bewusste, im Tech Design/Architecture-Review dokumentierte Abweichung auf `anfrage`-Tabelle; genau ein Datensatz je Mandant verifiziert (`test_anfrage_wrong_mandant_domain_creates_in_correct_tenant`). |
| 6 | Öffentliche Seiten mobil bedienbar, je Mandant nur über dessen Domain erreichbar | PASS (Re-Test 2026-08-17) | SEC-1 verifiziert behoben, siehe Re-Test-Abschnitt unten. Mobile Bedienbarkeit weiterhin nicht separat verifizierbar (kein Browser-Tooling verfügbar, siehe Einschränkungen) — unverändert gegenüber Erstlauf. |

**6 von 6 Kriterien getestet — 6 PASS (Stand Re-Test 2026-08-17).**

### Edge Cases (aus Spec)

| Edge Case | Ergebnis |
|---|---|
| Ungültige/zu große Dateien abgewiesen, Formulardaten bleiben erhalten | PASS (Client: kein `reset()` bei Fehler) — mit Einschränkung, siehe BUG-1 (Medium). |
| Unbekannte/inaktive Domain zeigt keine fremden Daten | PASS über normalen Host-Header (`test_inactive_domain_returns_404`, `test_public_site_unknown_domain_is_404`); **FAIL** über gespooften `X-Forwarded-Host` (SEC-1). |
| Mehrfaches Absenden derselben Anfrage erzeugt keinen doppelten Vorgang | PASS (`test_anfrage_same_kennung_is_idempotent`); kleine Race-Lücke bei echter Nebenläufigkeit, siehe BUG-2 (Low). |
| Nicht gepflegte Leistungsseite wird ausgeblendet | PASS (`test_leistung_inactive_or_unknown_is_404`, Leistungen starten inaktiv). |

### Frontend-Backend-Vertragsprüfung

`nextjs_app/lib/api/public.ts` / `lib/api/website-settings.ts` gegen `backend/app/features/website/schemas.py` — **exakte Übereinstimmung**, keine Abweichung gefunden:
- `kontaktweg`: `"Telefon" | "E-Mail"` — identisch.
- `dringlichkeit`: `"Normal" | "Dringend"` — identisch.
- Upload-Response `{"upload_id": "<uuid>"}` — identisch (`AnfrageUploadRead`).
- `AnfrageCreate`-Body (`upload_ids`, `uebermittlungskennung`, alle Feldnamen) — identisch zu `AnfrageInput`.
- `WebsiteSettingsRead`/`PublicSite`-Feldnamen — identisch zu `WebsiteSettings`/`PublicSite` im Frontend.

Die Behauptung des Backend-Agents ist damit End-to-End verifiziert (nicht nur per Code-Lesen, sondern über 18 laufende Backend-Tests plus `tsc --noEmit`/`next build` gegen dieselben Typen).

### Security-Findings (Red-Team)

**SEC-1 — Critical — Mandantengrenze über `X-Forwarded-Host`-Header spoofbar (Cross-Tenant-Datenleck + Spam-Einschleusung)**
- **Ort:** `backend/app/features/website/routes.py:20-26` (`_hostname`) — liest `x-forwarded-host` bevorzugt vor `host`, ohne zu prüfen, dass die Anfrage tatsächlich über den internen Next.js-Reverse-Proxy kam (kein Shared Secret, kein IP-Allowlist der vertrauenswürdigen Zwischenstation).
- **Repro (per `TestClient`, entspricht direktem Zugriff auf den Backend-Port oder einem Proxy, der `X-Forwarded-Host` nicht überschreibt):**
  ```
  GET /public/site
  Host: irgendwas-beliebiges.de
  X-Forwarded-Host: a-real.de
  → 200 {"firmenname": "Firma A geheim", ...}   # fremde Betriebsdaten, ohne den echten Hostnamen je gesehen zu haben
  ```
  Ebenso reproduziert für `POST /public/anfragen`: eine Anfrage wurde unter dem gespooften Ziel-Mandanten angelegt, obwohl der tatsächliche `Host`-Header eine erfundene Domain war (`attacker-controlled.com`).
- **Auswirkung:** Ein Angreifer kann mit reinem HTTP-Zugriff (curl/fetch, kein Browser-UI nötig) beliebige Betriebe anhand bekannter/erratener Hostnamen auslesen (Firmenname, Kontakt, Adresse, Leistungen) und beliebig viele Spam-/Fake-Anfragen samt hochgeladener Bilder in einen fremden Mandanten einschleusen — unabhängig davon, unter welcher echten Domain der Request eintrifft. Das widerspricht direkt der im Tech Design festgelegten Sicherheitsannahme „Domain als öffentliche Mandantengrenze“ (Zeile „verhindert, dass ein URL-Parameter oder ein Formularfeld einen fremden Betrieb auswählen kann“ — ein Header ist hier ebenso wenig vertrauenswürdig wie ein Formularfeld).
- **Warum trotzdem ausnutzbar, obwohl `docker-compose.yml` den Backend-Port nur `expose`t statt `ports` zu öffnen:** Der Next.js-eigene Client-Fetch läuft über `API_BASE = "/api"` (relativer Pfad) — die Anfrage geht vom Browser an denselben Host, den der Besucher gerade aufruft, und wird von der Deploy-Infrastruktur (Dokploy/Traefik) zum Backend durchgereicht. Ob dabei ein `X-Forwarded-Host` gesetzt/überschrieben wird, hängt vollständig von der (in diesem Repo nicht versionierten) Proxy-Konfiguration ab — der Code selbst bietet keine zweite Verteidigungslinie. Das ist ein Single Point of Failure außerhalb dieses Repos, den der Code nicht absichern sollte, aber tut.
- **Fix-Empfehlung (nicht selbst umgesetzt):** `X-Forwarded-Host` nur akzeptieren, wenn die Anfrage nachweislich vom internen Next.js-Dienst kommt (z. B. Shared-Secret-Header, der öffentlich nie erreichbar ist, oder IP-Allowlist des internen Docker-Netzes), sonst ausschließlich `request.headers.get("host")` verwenden bzw. den Header serverseitig verwerfen und stattdessen dafür sorgen, dass der Reverse-Proxy ihn immer korrekt neu setzt (z. B. explizite Traefik-Konfiguration dokumentieren und testen).
- **Behoben:** Shared-Secret-Ansatz umgesetzt. `backend/app/features/website/routes.py` (`_hostname`) vertraut `X-Forwarded-Host` nur noch, wenn der Request den Header `X-Internal-Proxy-Secret` mit einem Wert schickt, der `settings.internal_proxy_secret` (neu in `backend/app/config.py`, env `INTERNAL_PROXY_SECRET`) entspricht; ohne gültiges Secret wird ausschließlich der rohe `Host`-Header verwendet. Der Next.js-Proxy (`nextjs_app/proxy.ts`) setzt diesen Header serverseitig auf alle `/api/*`-Requests, bevor Next.js sie per `next.config.mjs`-Rewrite ans Backend weiterreicht — der Secret-Wert ist nie clientseitig sichtbar. `INTERNAL_PROXY_SECRET` neu in `.env.example` und `docker-compose.yml` (beide Services) dokumentiert. Regressionstest `test_spoofed_forwarded_host_without_proxy_secret_is_ignored` in `backend/tests/features/website/test_public_site.py` reproduziert den SEC-1-Angriff (gespoofter `X-Forwarded-Host` ohne bzw. mit falschem Secret) und verifiziert 404 (kein Cross-Tenant-Leck) sowie 200 mit korrektem Secret.

**BUG-1 — Medium — Anfrageformular lädt bei einem fehlgeschlagenen Sende-Versuch bereits ausgewählte Bilder erneut hoch**
- **Ort:** `nextjs_app/app/site/anfrage/page.tsx:107-136` (`onSubmit`).
- **Repro:** Nutzer wählt 3 Bilder, `submitAnfrage` schlägt aus einem unabhängigen Grund fehl (z. B. Netzwerkfehler, Validierungsfehler beim letzten Feld). `bilder`-State wird bei Fehler nicht geleert (bewusst, um Formulardaten zu erhalten — korrekt laut Edge Case). Beim erneuten Klick auf „Anfrage absenden“ werden dieselben 3 Dateien erneut per `uploadAnfrageBild` hochgeladen (gleiche `uebermittlungskennung`, aber neue `anfragebild`-Zeilen) — nach zwei Fehlversuchen mit denselben Bildern sind bereits 6 Uploads für dieselbe Übermittlungskennung angefallen, was am serverseitigen Limit (`MAX_UPLOADS = 5`, `backend/app/features/website/service.py:100-106`) scheitert und die Anfrage komplett blockiert, obwohl der Nutzer nur 3 Bilder ausgewählt hat.
- **Auswirkung:** Nutzer, deren erster Sendeversuch aus einem unabhängigen Grund fehlschlägt, können nach spätestens zwei Wiederholungen keine Anfrage mit Bildern mehr absenden und sehen eine für sie unverständliche „höchstens 5 Bilder“-Fehlermeldung. Zusätzlich verwaiste `anfragebild`-Zeilen in der DB (harmlos, aber unnötig).
- **Fix-Empfehlung:** Bereits hochgeladene `upload_id`s pro Datei clientseitig zwischenspeichern und bei Retry nur noch fehlende Dateien hochladen, oder Upload erst beim endgültigen Submit-Klick statt implizit bei jedem Versuch erneut ausführen.
- **Behoben:** `nextjs_app/app/site/anfrage/page.tsx` cached bereits erhaltene `upload_id`s pro `File`-Objekt in einer `useRef`-`Map` (`hochgeladeneBilder`); `onSubmit` lädt beim Retry nur noch Dateien hoch, für die noch keine `upload_id` bekannt ist, und verwendet sonst die gecachte ID erneut. Verhindert, dass wiederholte Sendeversuche mit denselben Bildern das Server-Limit von 5 Uploads sprengen.

**BUG-2 — Low — Kleines Race-Window bei echter Nebenläufigkeit der Idempotenzprüfung**
- **Ort:** `backend/app/features/website/service.py:125-133` (`submit_anfrage`) — klassisches SELECT-dann-INSERT ohne Exception-Handling um den INSERT.
- **Befund:** Sequentielle Wiederholung (Doppelklick, Netzabbruch + Retry) ist korrekt idempotent (verifiziert). Bei echter Nebenläufigkeit zweier Requests mit identischer `uebermittlungskennung` (z. B. zwei Tabs, doppelter automatischer Retry exakt gleichzeitig) könnten beide den `existing`-Check vor dem jeweils anderen INSERT passieren; die DB-`UNIQUE(mandant_id, uebermittlungskennung)`-Constraint verhindert zuverlässig einen doppelten Datensatz, aber der zweite Request würde dann eine unbehandelte Datenbank-Exception (500) statt eines sauberen `200 {"ok": true}` erhalten. Kein Datenverlust, kein Duplikat — nur eine unschöne Fehlerantwort in einem seltenen Zeitfenster.
- **Fix-Empfehlung:** `IntegrityError`/Unique-Violation in `repo.create_anfrage`-Aufrufer abfangen und wie „bereits vorhanden“ behandeln.

**Kein Fund bei:** Tenant-Isolation über normalen Host-Header (PASS), Auth-Bypass an `/website-settings*` (401 ohne Token, 403 für Rolle „Büro“ — verifiziert), Upload-Missbrauch (>5 Bilder, falsches Format, zu groß — alle korrekt abgewiesen; Pfad-Traversal im Dateinamen strukturell ausgeschlossen, da `objektpfad` serverseitig aus `uuid.uuid4()` gebildet wird, der Client-Dateiname nur als Anzeigefeld `dateiname` gespeichert wird), Rate-Limit (`website_anfrage_versuche` greift korrekt nach 20 Versuchen/15 Min, danach `429`), SQL-Injection über Formularfelder (durchgängig parametrisierte Queries, Prüfung mit `'); DROP TABLE anfrage;--` im Namens-/Anliegenfeld — Tabelle unverändert, kein Effekt).

**Nicht getestet:** abgelaufener Token gegen `/website-settings*` (PROJ-1-Mechanik, nicht PROJ-2-spezifisch verändert — hier nicht erneut isoliert reproduziert, da `require_role`/`get_current_user` unverändert aus PROJ-1 übernommen und dort bereits abgedeckt).

### Regressionstest PROJ-1
`backend/tests/test_auth.py` (5), `test_isolation.py` (3), `test_security.py` (3), `test_users.py` (5), `test_operator.py` (2) — alle grün im selben Testlauf (36 gesamt). Der `apiFetch`/`operatorApiFetch`-Fix für `FormData`-Content-Type (`nextjs_app/lib/api/client.ts`) bricht bestehende JSON-Requests nicht — Content-Type wird weiterhin gesetzt, sobald `body` kein `FormData` ist; keine Regression in Login/Session-Flows feststellbar (`npx tsc --noEmit` + `npm run build` sauber, bestehende Auth-Routen unverändert).

### Einschränkungen dieses Testlaufs
- **Kein manuelles Durchklicken im Browser möglich** — kein Playwright/Browser-Tooling in dieser Session verfügbar. Formular- und Einstellungen-Flow wurden ausschließlich über `pytest` (Backend), `TestClient`-Skripte (Red-Team) und `tsc`/`next build` (Frontend-Typsicherheit) verifiziert, nicht visuell im echten Browser.
- `npm run lint` / `next lint` nicht ausführbar — `eslint` ist keine Dependency in `nextjs_app/package.json` (vorbestehende Repo-Lücke, nicht durch PROJ-2 verursacht); stattdessen `npx tsc --noEmit` (0 Fehler) als Ersatzprüfung durchgeführt.
- Mobile Bedienbarkeit (375/768/1440 px) nicht separat verifiziert (kein Browser-Tooling).

### Produktionsreif-Empfehlung (Erstlauf 2026-08-17, vor Fix): **NEIN**
Grund: SEC-1 (Critical) — die dokumentierte Sicherheitsannahme „Domain als alleinige öffentliche Mandantengrenze“ ist durch einen spoofbaren Header umgehbar und ermöglicht Cross-Tenant-Datenleck plus Spam-Einschleusung ohne jede Authentifizierung. Muss vor Deploy behoben werden. BUG-1 (Medium) sollte vor Rollout ebenfalls behoben werden (bricht ein dokumentiertes Edge-Case-Verhalten bei wiederholten Sendeversuchen). BUG-2 (Low) kann nachgelagert behoben werden.

## QA Re-Test (nach Bugfix)
**Re-Getestet:** 2026-08-17 · QA Engineer / Red-Team · unabhängige Verifikation (nicht nur Behauptung des Backend-Devs übernommen)

### Vorgehen
1. `conda run -n Dashboard --no-capture-output python -m pytest backend/tests -q` → **37 grün** (36 vorher + 1 neuer SEC-1-Regressionstest `test_spoofed_forwarded_host_without_proxy_secret_is_ignored`), keine Regression.
2. Code-Review von `backend/app/features/website/routes.py` (`_hostname`, Zeile 21-32) und `backend/app/config.py` (`internal_proxy_secret`, Default `""` via `INTERNAL_PROXY_SECRET`): `X-Forwarded-Host` wird nur akzeptiert, wenn `settings.internal_proxy_secret` nicht-leer ist UND der Request-Header `X-Internal-Proxy-Secret` exakt damit übereinstimmt; sonst fällt der Code ausschließlich auf den rohen `Host`-Header zurück. **Fail-closed bei unkonfiguriertem Secret** (leerer String macht `trusted_proxy` immer `False`) — ein Betreiber, der `INTERNAL_PROXY_SECRET` vergisst zu setzen, bleibt sicher, statt versehentlich offen zu sein.
3. `nextjs_app/proxy.ts` geprüft: das Secret wird ausschließlich serverseitig in der Next.js-Middleware (`proxy.ts`, läuft nie im Browser) aus `process.env.INTERNAL_PROXY_SECRET` gelesen und als Header an `/api/*`-Requests angehängt, bevor `next.config.mjs` sie per Rewrite ans Backend weiterreicht. Keine `NEXT_PUBLIC_*`-Variable, keine sonstige Referenz im Repo (`grep -rn INTERNAL_PROXY_SECRET nextjs_app` → nur `proxy.ts`). **Aktiv verifiziert:** `npm run build` mit `INTERNAL_PROXY_SECRET=test-secret-canary-xyz` gesetzt, danach `grep -rl` des Canary-Strings über `.next/static` (Client-Bundle) → **kein Treffer**. Secret erreicht den Browser nicht.
4. Eigener, vom Dev-Test unabhängiger Angriffsversuch (temporäre pytest-Datei, nach Verifikation wieder entfernt, nicht committet): 4 Szenarien — (a) Spoofing bei **unkonfiguriertem** Secret (Default `""`, simuliert einen Betreiber, der die Env-Var vergisst) → `404`, kein Leck; (b) mehrere falsch geratene Secret-Werte gegen ein konfiguriertes echtes Secret → alle `404`; (c) `POST /public/anfragen` mit gespooftem `X-Forwarded-Host` ohne Secret → `404`, keine Cross-Tenant-Anfrage-Injection; (d) Kontrollfall mit korrektem Secret → `200`, liefert weiterhin korrekt die per Forwarded-Host aufgelösten Daten (kein Over-Fix, der die Next.js-Rewrite-Funktionalität selbst bricht). **Alle 4 eigenen Angriffs-/Kontrolltests bestanden.**
5. `cd nextjs_app && npx tsc --noEmit && npm run build` → beide grün, 0 Fehler.
6. Code-Review BUG-1-Fix (`nextjs_app/app/site/anfrage/page.tsx:61-124`): `hochgeladeneBilder` ist eine `useRef<Map<File, string>>`, keyed by `File`-Objektreferenz. Bei Retry werden nur `bilder`-Einträge ohne vorhandenen Map-Eintrag neu hochgeladen. Dedupe-Lücke geprüft: entfernt der Nutzer ein Bild (`bildEntfernen`) und/oder wählt neue Dateien über den Datei-Dialog erneut aus, erzeugt der Browser für jede Dateiauswahl **neue** `File`-Objektinstanzen (auch bei identischem Dateiinhalt) — der Map-Lookup per Referenz liefert dann korrekt `undefined`, der Upload läuft frisch, und da `onSubmit` nur über das aktuelle `bilder`-Array iteriert, werden entfernte Bilder nie erneut gezählt oder hochgeladen. Kein Leck der Dedupe-Logik bei geänderter Auswahl zwischen Fehlversuchen gefunden.
7. Alle 6 Akzeptanzkriterien erneut kurz gegen den aktuellen Code geprüft (siehe aktualisierte Tabelle oben) — AC1-AC5 unverändert PASS, AC6 jetzt PASS. Kein Hinweis auf eine durch den Fix verursachte Regression.
8. BUG-2 (Low, Race-Window bei Idempotenz) bleibt bekannt und offen — nicht erneut vertieft, siehe Fund oben.

### Ergebnis
- **SEC-1: Verifiziert behoben.** Fail-closed-Default, kein Client-seitiges Secret-Leak (aktiv per Canary-String im Build-Output geprüft), eigener Angriffsversuch (4 Szenarien inkl. Default-Konfiguration) schlägt durchgehend fehl wie erwartet.
- **BUG-1: Verifiziert behoben.** Dedupe-Logik korrekt, auch bei geänderter Dateiauswahl zwischen Fehlversuchen kein Leck.
- **BUG-2: weiterhin offen (Low)**, unverändert seit Erstlauf — kann nachgelagert behoben werden, kein Blocker.
- Kein Critical/High mehr offen.

### Produktionsreif-Empfehlung (Re-Test 2026-08-17): **JA**
SEC-1 (Critical) und BUG-1 (Medium) sind unabhängig verifiziert behoben, keine Regression in 37 Backend-Tests, `tsc`/`next build` grün, alle 6 Akzeptanzkriterien PASS. Status wird auf **Approved** gesetzt. BUG-2 (Low) kann nachgelagert behoben werden und blockiert den Deploy nicht.

## Deployment
Production URL: https://business-os.dokploy-host (Domain in Dokploy konfiguriert, sync automatisch mit GitHub-Repo).
Deployed: 2026-08-17 · Version: 0.1.1 · Host: Dokploy (Compose, Auto-Deploy via GitHub-Push auf `main`).
Ausgeliefert: geführte SHK-Website (Startseite, Leistungsseiten, Anfrageformular mit Bild-Upload, Impressum/Datenschutz), Website-Einstellungen für Inhaber, Domain-basierte Mandantenauflösung mit Proxy-Secret-Schutz (SEC-1-Fix).
Smoke-Test auf der Produktions-Domain steht noch aus (kein Browser-Zugriff in dieser Session) — bitte nach Auto-Deploy manuell verifizieren: Startseite lädt, Anfrageformular sendet erfolgreich, Website-Einstellungen als Inhaber erreichbar, `/api/health` antwortet.

## Nachtrag: Domain-Self-Service (2026-08-17)
Lücke: `website_domains` hatte keinen Schreibpfad — die Domain war in Website-Einstellungen nur lesbar (`domain`/`domain_status`), der Inhaber konnte sie nie selbst setzen.

Gebaut:
- Backend: `WebsiteSettingsPatch.domain` (neu, optional). `service.update_website_settings` validiert den Hostnamen (trim/lowercase/Regex, kein Protokoll/Pfad), prüft per `repository.find_mandant_id_by_hostname` auf Kollision mit einem fremden Mandanten (→ 409 „Diese Domain ist bereits vergeben.“) und schreibt via neuer `repository.upsert_domain` (Update falls schon eine Domain existiert, sonst Insert; `status = 'aktiv'`).
- Kein neues DB-Constraint/keine Migration nötig: die bestehende SECURITY-DEFINER-Funktion `website_find_mandant_by_hostname` (aus `002_website.sql`) reicht für den Kollisions-Check, RLS-Scoping pro Mandant übernimmt weiterhin die vorhandene `mandant_id`-Spalte. Bewusste Vereinfachung (ponytail-Kommentar in `repository.py`): kein Lock zwischen Kollisionsprüfung und Schreiben — bei echtem Gleichzeitigkeits-Wettrennen zweier Mandanten auf denselben Hostnamen fängt der bestehende `UNIQUE`-Constraint auf `hostname` Dubletten weiterhin ab, würde dann aber als 500 statt 409 auffallen. Nachrüsten, falls das in der Praxis auftritt.
- Frontend: Das bisherige Nur-Lese-Feld in `website-einstellungen/page.tsx` wurde durch ein Eingabefeld „Öffentliche Domain“ ersetzt (vorausgefüllt, Platzhalter `beispiel.de`, deutscher Hilfetext zu DNS), wird beim normalen Speichern mit übermittelt.
- Tests: 3 neue Backend-Tests (`test_owner_sets_domain`, `test_domain_collision_with_other_tenant_rejected`, `test_domain_invalid_format_rejected`) — alle grün, `pytest backend/tests -q` → 40 grün (keine Regression). `tsc --noEmit` + `next build` grün.

Die Test-Domain `bizos-web.app.msce.info` konnte NICHT direkt in der Produktions-DB gesetzt werden — von dieser Session aus ist nur der interne Docker-Hostname `bizos-db` erreichbar (kein `.env`/`DATABASE_URL` mit externem Zugriff im Repo hinterlegt). Der Nutzer muss die Domain einmalig selbst über das neue Feld in Website-Einstellungen eintragen und speichern (Login als Inhaber → Website-Einstellungen → Feld „Öffentliche Domain“ → `bizos-web.app.msce.info` → Speichern).
