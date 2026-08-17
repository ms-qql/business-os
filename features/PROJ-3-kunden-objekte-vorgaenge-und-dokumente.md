# PROJ-3: Kunden, Objekte, Vorgänge und Dokumente

## Status: Deployed
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
**Erstellt:** 2026-08-17 · **Stack:** Next.js 16 + FastAPI + PostgreSQL (RLS) + MinIO · **Branch:** specs/PROJ-3-kunden-objekte-vorgaenge-und-dokumente

### Grundlage im Code (nicht angenommen, verifiziert)
- PROJ-1 liefert bereits `mandanten`/`nutzer` mit Rollen `Inhaber`/`Buero`/`Monteur` (`backend/sql/001_init.sql`), JWT-Session-Login (`backend/app/features/auth`) und die Rollen-Guard-Dependency `require_role(*roles)` (`backend/app/deps.py:68`) — wird unverändert für die Schreibrechte dieses Features verwendet.
- PROJ-2 hat bereits `anfrage`/`anfragebild` angelegt (`backend/sql/002_website.sql`); der Migrationskommentar dort sagt ausdrücklich, dass die Verknüpfung zu Vorgängen erst mit PROJ-3 nachgezogen wird — das übernimmt der Endpunkt `POST /anfragen/{id}/uebernehmen` unten.
- Datei-Uploads laufen bereits über `backend/app/storage.py` (`BaseStorage`/`MinioStorage`; DB speichert nur `objektpfad`, Leseweg ausschließlich über kurzlebige `presigned_get_url`) — gleiches Muster für Vorgangsdokumente, kein neuer Speicherpfad.

### Ziel und Umfang

PROJ-3 macht aus einer Website-Anfrage einen bearbeitbaren Kunden und Vorgang. Kunden, optionale Objekte, Vorgänge und Dokumente bleiben mandantengetrennt. Büro und Inhaber verwalten sie vollständig; Monteure sehen ausschließlich ihnen zugewiesene Vorgänge und ändern keine Kundendaten.

### Komponentenstruktur

```text
Vorgangsliste
├── Suche und Statusfilter
├── paginierte Vorgangstabelle
├── Neuer-Vorgang-Dialog
└── Leerzustand

Vorgangsdetail
├── Kopf mit Status, Quelle und Zuständigkeit
├── Kundenkarte
├── optionale Objektkarte
├── Anliegen und interne Notizen
├── Chronik
└── Dokumente
    ├── Upload Foto/PDF
    └── Download und Löschen

Kundenübersicht
├── Suche und Kundenliste
└── Kundendetail mit Objekten und Vorgangshistorie
```

Die bestehende authentifizierte Next.js-App erhält Navigationseinträge für Kunden und Vorgänge. Die Vorgangsdetailseite ist die gemeinsame Arbeitsansicht; Kunden- und Objektinformationen werden dort verlinkt statt doppelt gepflegt.

### Datenmodell

- **Kunde:** Mandant, Name, Kontaktwege und Zeitstempel. Beim Speichern gleicher E-Mail-Adresse oder Telefonnummer erscheint ein Bestandskundenhinweis; zusammengeführt wird nie automatisch.
- **Objekt:** gehört zu einem Kunden und enthält die Einsatzadresse. Es ist optional, damit noch unqualifizierte Anfragen sofort als Vorgang erfasst werden können.
- **Vorgang:** gehört zu Kunde und optionalem Objekt; speichert Status, Quelle, Anliegen, Notizen, Zuständigkeit sowie Erstellungs- und Änderungszeitpunkte. Zulässig sind Neu, Rückruf, Angebot offen, Termin geplant, Erledigt und Abgeschlossen.
- **Vorgangshistorie:** unveränderliche, chronologische Ereignisse für Anlage, Feldänderungen, Statuswechsel, Zuweisungen und Dokumentaktionen.
- **Dokument:** gehört zu einem Vorgang und speichert Dateimetadaten und den internen MinIO-Objektschlüssel, nicht eine öffentliche URL. Erzeugte PDFs enthalten keine Live-Links auf löschbare Dokumente; gelöschte Dokumente werden aus der aktiven Liste entfernt.
- **Zuweisung:** ordnet einen Vorgang einem Monteur zu und ist die Grundlage seiner Leseberechtigung.
- **Website-Anfrage:** bleibt für den öffentlichen Eingang erhalten und wird beim Übernehmen mit Kunde, optionalem Objekt und Vorgang verknüpft. Bestehende Anfragebilder werden mit übernommen.

Alle Fachdatensätze tragen den Mandantenbezug. Der Kunde kann nur gelöscht werden, wenn keine Vorgänge oder Rechnungen darauf verweisen.

### API-Form

- `GET /kunden` und `POST /kunden` — Kunden suchen bzw. anlegen.
- `GET /kunden/{id}`, `PATCH /kunden/{id}`, `DELETE /kunden/{id}` — einen Kunden lesen, ändern oder bei fehlenden Referenzen löschen.
- `GET /kunden/{id}/objekte` und `POST /kunden/{id}/objekte` — Objekte eines Kunden anzeigen bzw. anlegen.
- `GET /vorgaenge` und `POST /vorgaenge` — paginierte, durchsuchbare und nach Status filterbare Vorgangsliste bzw. Anlage. `GET /vorgaenge` nimmt `limit` (serverseitig auf max. 200 gedeckelt, wie `backend/app/features/users/service.py:15-17` es für `GET /users` bereits vormacht) UND `offset` entgegen — bisher hat keine Liste im Code echtes `offset`, `GET /vorgaenge` ist die erste; `GET /kunden` folgt demselben Muster.
- `GET /vorgaenge/{id}`, `PATCH /vorgaenge/{id}` — Vorgang mit Kunde, Objekt, Chronik und Dokumenten lesen bzw. bearbeiten.
- `POST /vorgaenge/{id}/zuweisungen` — Monteur zuweisen oder Zuweisung ändern.
- `POST /vorgaenge/{id}/dokumente` — Foto oder PDF sicher hochladen.
- `GET /vorgaenge/{id}/dokumente/{document_id}/download` — berechtigten, kurzlebigen Download bereitstellen.
- `DELETE /vorgaenge/{id}/dokumente/{document_id}` — Dokument entfernen und die Aktion chronologisch festhalten.
- `POST /anfragen/{id}/uebernehmen` — bestehende Website-Anfrage kontrolliert in Kunde, Objekt und Vorgang überführen.

Jeder Endpunkt nutzt die bestehende Sitzung. Inhaber und Büro erhalten Mandantenrechte; Monteure erhalten nur lesenden Zugriff auf ihre zugewiesenen Vorgänge.

### Schreib-Owner je Entität (explizit, nicht nur Lesezugriff)

| Entität | Schreib-Owner (Endpoint-Guard) | Lesezugriff | Begründung |
|---|---|---|---|
| **Kunde** | `require_role("Buero", "Inhaber")` auf `POST/PATCH/DELETE /kunden*` | Büro, Inhaber; Monteur nicht direkt (nur indirekt über den ihm zugewiesenen Vorgang) | AC: „Monteur … keine Kundendaten ändern" |
| **Objekt** | `require_role("Buero", "Inhaber")` auf `POST/PATCH /kunden/{id}/objekte*` | wie Kunde | Objekt hängt am Kunden, gleiche Sperre |
| **Vorgang** | `require_role("Buero", "Inhaber")` auf `POST /vorgaenge`, `PATCH /vorgaenge/{id}`, `POST /vorgaenge/{id}/zuweisungen` | Büro, Inhaber (alle Vorgänge); Monteur nur lesend und nur der ihm zugewiesene Vorgang (Route prüft Zuweisung serverseitig, sonst 403) | AC: Büro/Inhaber legen an und bearbeiten; Monteur „kann nur den ihm zugewiesenen Vorgang lesen" |
| **Dokument/Anhang** | `require_role("Buero", "Inhaber")` auf `POST /vorgaenge/{id}/dokumente`, `DELETE /vorgaenge/{id}/dokumente/{document_id}` | Download wie Vorgang: Büro/Inhaber immer, Monteur nur am zugewiesenen Vorgang | Spec nennt nur Büro/Inhaber als Akteure für Anlage/Änderung; ein Monteur-Upload (z. B. Baustellenfoto) ist durch die AC nicht gedeckt und wird bewusst nicht spekulativ ergänzt — eigenes Ticket, falls gewünscht |

**Zuweisung als Vorgriff auf PROJ-6:** Die AC dieser Spec setzen voraus, dass ein Vorgang einem Monteur zugewiesen sein kann, obwohl die eigentliche Terminplanung/Teamzuweisung erst PROJ-6 ist (siehe `features/INDEX.md`, PROJ-6 hängt von PROJ-3 ab). PROJ-3 legt daher bereits ein minimales `zuweisung`-Konzept (siehe Datenmodell oben) inklusive `POST /vorgaenge/{id}/zuweisungen` an, ohne Kalender/Verfügbarkeit — PROJ-6 baut darauf auf, legt aber keine zweite, konkurrierende Datenstruktur an. Dieser Punkt ist im Review gegen die künftige PROJ-6-Architektur gegenzuprüfen, sobald sie existiert.

### Technische Entscheidungen

- Der vorhandene Schichtenaufbau aus Route, Fachservice und Repository wird wiederverwendet. Das hält Fachregeln wie Löschsperren und Zugriffsprüfung an einer Stelle.
- Postgres erzwingt die Mandantentrennung zusätzlich zur Anwendungsprüfung. Neue Schreibregeln prüfen sowohl Lesbarkeit als auch zulässige Anlage und Änderung, damit Mandantendaten nicht über Schreiboperationen vermischt werden.
- MinIO speichert die Binärdateien; Postgres hält nur Metadaten und den Objektverweis. Downloads erhalten erst nach Berechtigungsprüfung eine kurzlebige Adresse.
- Die bestehende serverseitige Datei-Prüfung wird für Fotos und PDFs geteilt und erweitert. Dateityp, tatsächlicher Dateiinhalt und Größe werden vor der Ablage geprüft.
- Die schon vorhandenen Website-Anfragen bleiben Eingangsdaten. Eine explizite Übernahme statt automatischer Konvertierung bewahrt Nachvollziehbarkeit und verhindert doppelte Kunden.
- Die Vorgangsliste ist serverseitig paginiert und filterbar, damit der Tagesüberblick auch bei wachsendem Bestand schnell bleibt.
- Die bestehende Next.js-App wird erweitert, statt parallel eine Flutter-App einzuführen: Das ist der im Repository bereits verwendete Client und vermeidet eine zweite Oberfläche für dasselbe Produkt.
- Backend-Anbindung folgt dem bestehenden Zwei-Schritt-Wiring: neues Feature-Modul (z. B. `backend/app/features/kunden`, `backend/app/features/vorgaenge`) exportiert seinen Router aus `__init__.py`, `backend/app/main.py` registriert ihn per `app.include_router(...)` — exakt wie `users`/`website` es bereits tun (`backend/app/main.py:21-26`).

### Abhängigkeiten

- **Backend:** keine neuen Pakete vorgesehen; vorhandene FastAPI-, Postgres- und MinIO-Bausteine reichen aus.
- **Web:** keine neue Bibliothek, aber `nextjs_app/components/ui/` enthält bisher nur `button`, `card`, `input`, `label`, `textarea` — `Table`, `Dialog`, `Select` und `Badge` fehlen noch und müssen als shadcn/ui-Copy-Paste-Primitive ergänzt werden (kein npm-Paket, keine Abweichung von der "shadcn first"-Konvention), bevor die Vorgangs-/Kundenlisten sie nutzen können. Die bestehende Seite `nextjs_app/app/(app)/nutzerverwaltung/page.tsx` ist Präzedenzfall für eine authentifizierte CRUD-Seite, nutzt aber noch eine native `<table>` statt der shadcn-Primitive — PROJ-3 ist die erste Seite, die die neuen Primitive tatsächlich einführt.

### Abnahmebezug

- Vorgangsdaten, Statuswerte, Kunde, optionales Objekt, Notizen, Anhänge und Zeitstempel sind vollständig abgebildet.
- Suche, Statusfilter und Pagination liegen in der Vorgangsliste.
- Chronik und Dokumente erscheinen gemeinsam am Vorgang.
- Dokumente sind mandanten- und vorgangsberechtigt; Monteure erhalten nur die ihnen zugewiesene Lesesicht.
- Die Löschsperre des Kunden berücksichtigt Vorgänge und Rechnungen.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-17 · **Verdict:** Architected

### Checklist
- [x] Component structure — Seitenbaum vollständig (Vorgangsliste, Vorgangsdetail, Kundenübersicht); Primitive-Lücke (Table/Dialog/Select/Badge fehlen im Repo) unter Abhängigkeiten dokumentiert statt stillschweigend vorausgesetzt.
- [x] Data model — jede Entität (Kunde, Objekt, Vorgang, Vorgangshistorie, Dokument, Zuweisung) trägt Mandantenbezug; RLS-Ansatz (`mandant_id` + `current_setting('app.current_mandant_id')`) explizit an PROJ-1/PROJ-2-Muster verankert.
- [x] API shape — jeder Endpunkt mit Methode+Pfad benannt; Pagination jetzt explizit auf `limit`+`offset` präzisiert (CodeGraph zeigte: bisher nur `limit`-only im Code, keine echte Pagination — jetzt korrekt als Neuland markiert statt als Wiederverwendung missverstanden).
- [x] Tech decisions — jede Entscheidung mit Begründung; Router-Wiring-Schritt (`__init__.py` → `main.py include_router`) ergänzt, da CodeGraph zeigte, dass dieser Zwei-Schritt-Mechanismus verbindlich ist.
- [x] Dependencies — keine neuen Pakete; fehlende shadcn-UI-Primitive (Table/Dialog/Select/Badge) jetzt benannt statt implizit vorausgesetzt.
- [x] Branch field — `specs/PROJ-3-kunden-objekte-vorgaenge-und-dokumente` vorhanden, Branch existiert bereits (aktueller Checkout).
- [x] Conflict-free — CodeGraph bestätigt: keine Tabellen-, Routen- oder Ordnernamenskollision (`kunde`, `objekt`, `vorgang`, `/kunden`, `/vorgaenge` sind frei; `backend/app/main.py` registriert bisher nur `auth`, `users`, `operator`, `admin`, `public`, `settings`).
- [x] Acceptance-criteria coverage — alle 6 AC decken sich mit Komponenten/Endpunkten: Vorgangsfelder → Datenmodell; Status-Werte → Vorgang-Enum; Anlegen/Bearbeiten/Suchen/Filtern → API-Form; Anhangszugriff → Schreib-Owner-Tabelle + Storage-Muster; Chronik → Vorgangshistorie + `GET /vorgaenge/{id}`; Löschsperre → Kunde-Datenmodell + `DELETE /kunden/{id}`.

### Explizite Schreib-Owner-Prüfung (Zusatzauflage)
Für jede im Datenmodell genannte Entität ist der Schreib-Owner eindeutig und mit Rollen-Guard belegt (Tabelle "Schreib-Owner je Entität" im Tech Design):
- **Kunde:** `require_role("Buero","Inhaber")` — eindeutig.
- **Objekt:** `require_role("Buero","Inhaber")` — eindeutig.
- **Vorgang:** `require_role("Buero","Inhaber")` für Schreiben; Monteur-Lesezugriff eng auf zugewiesenen Vorgang begrenzt — eindeutig.
- **Dokument/Anhang:** `require_role("Buero","Inhaber")` — eindeutig; Monteur-Upload bewusst nicht spekulativ ergänzt (kein AC-Auftrag dafür).
Kein Owner-Lücke offen.

### CodeGraph-Cross-Check
Delegiert an Explore-Agent (`codegraph_explore`). Ergebnis: keine der im Design genannten Tabellen/Routen existiert bereits (nur `anfrage`/`anfragebild` aus PROJ-2 als Saatdaten, exakt wie im Design erwartet); `require_role`, `storage.py`, RLS-Muster und der Router-Wiring-Mechanismus wurden verifiziert und ins Design zurückgeschrieben; fehlende shadcn-UI-Primitive im Frontend wurden aufgedeckt und dokumentiert.

### Autonom behoben
- Stack-Zeile von "Neon PostgreSQL" auf das projektweit aktuelle "PostgreSQL (RLS)" korrigiert (Dokploy-Postgres, nicht mehr Neon — reine Konsistenzkorrektur, keine Design-Entscheidung).
- "Grundlage im Code"-Abschnitt mit `file:line`-Belegen für PROJ-1/PROJ-2-Wiederverwendung ergänzt.
- Explizite Schreib-Owner-Tabelle je Entität ergänzt (Kunde, Objekt, Vorgang, Dokument) inkl. Rollen-Guard und AC-Bezug.
- PROJ-6-Vorgriff bei der Monteur-Zuweisung explizit benannt und als Review-Punkt für die künftige PROJ-6-Architektur vorgemerkt.
- Pagination von "paginiert" (unspezifisch) auf `limit`+`offset` konkretisiert, mit Hinweis, dass dies der erste echte Pagination-Endpunkt im Code ist (bisherige Listen nutzen nur `limit`).
- Router-Wiring-Schritt (`__init__.py` → `main.py include_router`) als Tech-Entscheidung ergänzt.
- Fehlende shadcn-UI-Primitive (Table/Dialog/Select/Badge) unter Abhängigkeiten benannt statt stillschweigend vorausgesetzt.

### Offene Fragen
Keine. Alle Funde waren technische Lücken (fixable ohne Produktentscheidung), keine ambige Geschäftslogik.

## Implementation Notes (Frontend, /abc-frontend)
**Umgesetzt:** 2026-08-17 · Next.js 16 App Router. Backend wurde parallel im selben Zeitraum gebaut (`backend/app/features/kunden`, `backend/app/features/vorgaenge`, `backend/sql/003_kunden_vorgaenge.sql`); sobald der Code sichtbar war, wurde der Frontend-API-Client gegen die tatsächlichen Pydantic-Schemas abgeglichen und korrigiert (kein laufender Server nötig, reiner Code-Abgleich). Kein manueller End-to-End-Test gegen eine laufende Instanz.

### Abgleich mit dem realen Backend-Code (wichtiger als die ursprüngliche Prosa-Spec)
Beim Abgleich zeigten sich mehrere Abweichungen zwischen der ursprünglichen (aus der Prosa-Spec abgeleiteten) Annahme und dem tatsächlich gebauten Backend — alle im Frontend nachgezogen:
- Such-Query-Parameter heißt `q`, nicht `suche` (`GET /kunden`, `GET /vorgaenge`).
- `POST /kunden` liefert den neuen Kunden **flach** zurück (`KundeCreateRead extends KundeRead`) plus `moegliche_duplikate`, nicht verschachtelt als `{kunde, moegliche_duplikate}`.
- `DELETE /kunden/{id}` und `DELETE /vorgaenge/{id}/dokumente/{id}` liefern `204 No Content`, keinen `{detail}`-Body.
- `Kunde`/`Objekt` haben zusätzlich ein `notiz`-Feld.
- `VorgangListItem.zugewiesener_nutzer_id` statt der angenommenen `zustaendiger_nutzer_id`; es gibt **keinen** Anzeigenamen im Response (weder in der Liste noch im Detail) — die Liste zeigt daher nur „Ja/—" statt eines Monteur-Namens; im Detail wird der Name nur aufgelöst, wenn `listNutzer()` erfolgreich lädt (siehe Einschränkung unten).
- `VorgangDetail` enthält **keine** verschachtelten `kunde`/`objekt`-Objekte, nur `kunde_id`/`objekt_id` — die Detailseite lädt Kunde und Objekt jetzt separat nach (`getKunde`, `listObjekte` + Filter auf `objekt_id`).
- Historie-Feldnamen sind `ereignis`/`detail`/`created_at` (nicht `typ`/`beschreibung`/`erstellt_von_name`); es gibt keinen aufgelösten Nutzernamen, nur `nutzer_id`. Die Chronik-Komponente übersetzt bekannte `ereignis`-Codes (`angelegt`, `status_geaendert`, `feld_geaendert`, `zugewiesen`, `dokument_hochgeladen`, `dokument_geloescht`) in deutsche Labels.
- Dokument-Feldnamen sind `content_type`/`groesse_bytes`/`hochgeladen_von` (nicht `dateityp`/`groesse`); Download-Response-Feld ist `download_url` (nicht `url`).
- `POST /vorgaenge` liefert ein `VorgangListItem` zurück (kein volles Detail mit Historie/Dokumenten).
- Erlaubte Bildtypen laut Backend-Magic-Byte-Prüfung umfassen zusätzlich GIF — Frontend-Client-Vorprüfung entsprechend erweitert (Backend bleibt die maßgebliche Prüfung).

### Neue shadcn-UI-Primitive (fehlten laut Architecture Review)
- `nextjs_app/components/ui/table.tsx`, `dialog.tsx` (natives `<dialog>`, kein Radix nötig), `select.tsx`, `badge.tsx` — handgeschrieben im bestehenden CVA/`cn()`-Stil (Repo hat kein `components.json`/CLI-Setup, `button.tsx`/`card.tsx`/`input.tsx` sind bereits genauso von Hand entstanden).

### Gebaute Seiten/Routen
- `nextjs_app/app/(app)/kunden/page.tsx` — Kundenliste (Suche, Pagination `limit`+`offset`, „Neuer Kunde"-Dialog, rollenabhängig).
- `nextjs_app/app/(app)/kunden/[id]/page.tsx` — Kundendetail (Bearbeiten/Löschen, Objekte, Vorgangshistorie).
- `nextjs_app/app/(app)/vorgaenge/page.tsx` — Vorgangsliste (Suche, Statusfilter, Pagination, „Neuer Vorgang"-Dialog).
- `nextjs_app/app/(app)/vorgaenge/[id]/page.tsx` — Vorgangsdetail (Status ändern, Kunden-/Objektkarte, Zuständigkeit/Zuweisung, interne Notizen, Chronik, Dokumente).
- Navigation in `nextjs_app/app/(app)/layout.tsx` um „Kunden"/„Vorgänge" erweitert; `NAV_RECHTE` in `nextjs_app/lib/theme/tokens.ts` regelt Sichtbarkeit je Rolle (Monteur sieht nur „Vorgänge", kein „Kunden").

### Komponenten
- `nextjs_app/components/kunden/`: `kunden-tabelle.tsx`, `kunde-form-dialog.tsx`, `kunde-detail.tsx`, `objekt-form-dialog.tsx`.
- `nextjs_app/components/vorgaenge/`: `vorgaenge-tabelle.tsx`, `vorgang-form-dialog.tsx`, `vorgang-status-badge.tsx`, `vorgang-detail.tsx`, `vorgang-chronik.tsx`, `vorgang-dokumente.tsx` (Upload mit Client-seitiger Typ-/Größenprüfung, Download über kurzlebige presigned URL, Löschen).
- API-Client: `nextjs_app/lib/api/kunden.ts` (Kunde + Objekt), `nextjs_app/lib/api/vorgaenge.ts` (Vorgang, Chronik, Dokumente, Zuweisung) — folgen dem bestehenden `apiFetch`/`ApiError`-Muster aus `nextjs_app/lib/api/client.ts`.
- Zod-Schemas: `nextjs_app/lib/schemas/kunde.ts`, `nextjs_app/lib/schemas/vorgang.ts` mit `react-hook-form`.

### Rollenabhängige UI
- `kannSchreiben(rolle)` (`nextjs_app/lib/theme/tokens.ts`) blendet Anlegen/Bearbeiten/Löschen/Upload für Monteure aus; Vorgangsdetail zeigt Monteuren keine Kundendaten (E-Mail/Telefon) und keinen Link zum Kundendatensatz. Durchsetzung der eigentlichen Zugriffsgrenze (Monteur sieht nur zugewiesenen Vorgang) erfolgt serverseitig laut Vertrag — Frontend verlässt sich darauf und blendet nur die Schreib-UI aus.

### Abweichungen vom dokumentierten Vertrag (mit Begründung)
- **`GET /vorgaenge` zusätzlicher Query-Parameter `kunde_id`:** Im API-Vertrag nicht explizit genannt, aber für die in der Komponentenstruktur geforderte „Kundendetail mit … Vorgangshistorie" zwingend nötig. Ohne Filter gäbe es keinen Weg, die Vorgänge eines Kunden zu laden. Rückwärtskompatible Ergänzung (optionaler Parameter), Backend muss ihn zusätzlich zu `status`/`suche`/`limit`/`offset` unterstützen.
- **Exakte Feldnamen der JSON-Responses (Kunde, Objekt, Vorgang, Dokument, Chronik-Eintrag) sind vom Frontend abgeleitet**, nicht wörtlich in der Spec fixiert (die Spec beschreibt das Datenmodell nur prosaisch). Verwendete Typen stehen in `nextjs_app/lib/api/kunden.ts` und `nextjs_app/lib/api/vorgaenge.ts` — Backend-Entwicklung sollte sich daran ausrichten oder Abweichungen früh im Review abgleichen.
- **„Anfrage übernehmen"-UI (`POST /anfragen/{id}/uebernehmen`) wurde bewusst nicht gebaut** — nicht Teil des vom Auftrag genannten Bauplans (Kunden-/Objekt-/Vorgangsliste/-Detail, Formulare, Upload/Download, Rollen-UI) und keine zugehörige Anfragenliste existiert im Frontend. Eigenes Ticket/Nachtrag empfohlen, sobald eine Anfragenübersicht existiert.

### Bekannte Einschränkung
- Backend (`backend/app/features/kunden`, `backend/app/features/vorgaenge`) existierte zum Zeitpunkt der Frontend-Umsetzung noch nicht — kein manueller End-to-End-Test gegen einen laufenden Server möglich. Gebaut strikt gegen den Tech-Design-Vertrag; Vertragsabweichungen oben dokumentiert.
- Monteur-Zuweisung im Vorgangsdetail lädt Monteure über `GET /users`, das laut PROJ-1 aktuell `require_role("Inhaber")` verlangt — für Büro (die laut Schreib-Owner-Tabelle auch zuweisen dürfen) schlägt das Laden der Monteurliste mit 403 fehl und die Auswahl bleibt leer (kein Absturz, aber eingeschränkte UX). Das ist eine bestehende Backend-Rechte-Lücke, keine Frontend-Entscheidung — zur Klärung an Backend/Architektur zurückgeben.

### Tests
- `npm run typecheck`, `npm run lint` (`next lint`), `npm run build` (`next build`, inkl. TS-Check) — alle grün.
- `npm run test` (Jest + React Testing Library, neu aufgesetzt via `next/jest`; Setup: `jest.config.js`, `jest.setup.js`, Scripts/Devdependencies in `package.json`) — 3 Suites, 11 Tests, alle grün: `__tests__/vorgang-status-badge.test.tsx`, `__tests__/kunde-schema.test.ts`, `__tests__/vorgaenge-tabelle.test.tsx`.

### Offene Punkte
- Backend-Implementierung gegen denselben Vertrag (parallel laufend laut Auftrag).
- Monteur-Zuweisung braucht eine für Büro zugängliche Monteurliste (Backend-Rechte-Frage, siehe oben).
- „Anfrage übernehmen"-Flow (Anfragenliste + Übernahme-UI) ist nicht Teil dieses Tickets.

## Implementation Notes (Backend, /abc-backend)
**Umgesetzt:** 2026-08-17 · FastAPI + raw SQL (RLS) auf Dokploy-PostgreSQL. Parallel zum Frontend gebaut; Kontrakt wurde gegenseitig abgeglichen (siehe Frontend-Notizen oben — beide Seiten konvergierten auf denselben, hier dokumentierten Vertrag).

### Gebaute Dateien
- `backend/sql/003_kunden_vorgaenge.sql` — Tabellen `kunde`, `objekt`, `vorgang`, `vorgang_historie`, `vorgang_dokument` (alle mit `mandant_id` + RLS-Policy nach dem Muster aus `001_init.sql`/`002_website.sql`); `ALTER TABLE anfrage ADD COLUMN vorgang_id` verknüpft PROJ-2-Anfragen mit dem daraus entstandenen Vorgang; `vorgang.kunde_id` referenziert `kunde(id) ON DELETE RESTRICT` als zweite Verteidigungslinie hinter der Anwendungs-Löschsperre.
- `backend/app/features/kunden/{repository,schemas,service,routes}.py` — `GET/POST /kunden`, `GET/PATCH/DELETE /kunden/{id}`, `GET/POST /kunden/{id}/objekte`. Schreib-Guard `require_role("Buero","Inhaber")` auf allen Endpunkten (Monteur hat laut Schreib-Owner-Tabelle keinen direkten Kunden-/Objekt-Zugriff).
- `backend/app/features/vorgaenge/{repository,schemas,service,routes}.py` — `GET/POST /vorgaenge`, `GET/PATCH /vorgaenge/{id}`, `POST /vorgaenge/{id}/zuweisungen`, `POST /vorgaenge/{id}/dokumente`, `GET /vorgaenge/{id}/dokumente/{id}/download`, `DELETE /vorgaenge/{id}/dokumente/{id}`, `POST /anfragen/{id}/uebernehmen` (eigener `anfragen_router`, gleiche Feature-Slice).
- `backend/app/main.py` — `kunden_router`, `vorgaenge_router`, `anfragen_router` registriert (Zwei-Schritt-Wiring wie im Tech Design gefordert).
- `backend/tests/conftest.py` — SQLite-Testschema um die fünf neuen Tabellen + `anfrage.vorgang_id` erweitert.
- `backend/tests/features/kunden/test_kunden.py`, `backend/tests/features/vorgaenge/test_vorgaenge.py` — neue Testsuiten.

### Finaler API-Vertrag (verifiziert gegen `nextjs_app/lib/api/kunden.ts` + `vorgaenge.ts`)
- Such-Query-Parameter: `q` (nicht `suche`) auf `GET /kunden` und `GET /vorgaenge`. `GET /vorgaenge` unterstützt zusätzlich `kunde_id` (nicht im Prosa-Vertrag benannt, aber für die Kundendetail-Vorgangshistorie zwingend — siehe Frontend-Notizen).
- `POST /kunden` liefert den Kunden **flach** zurück (`KundeCreateRead` erbt von `KundeRead`) plus `moegliche_duplikate: KundeRead[]` — kein verschachteltes `{kunde: ...}`.
- `Kunde`/`Objekt` tragen zusätzlich ein `notiz`-Feld.
- `DELETE /kunden/{id}` und `DELETE /vorgaenge/{id}/dokumente/{id}` liefern `204 No Content`.
- `VorgangListItem.zugewiesener_nutzer_id` (kein aufgelöster Name im Response — Frontend löst das über `GET /users` clientseitig auf).
- `VorgangDetail` liefert nur `kunde_id`/`objekt_id` (keine verschachtelten Objekte); Chronik-Feldnamen sind `ereignis`/`detail`/`nutzer_id`/`created_at`, Dokument-Feldnamen `content_type`/`groesse_bytes`/`hochgeladen_von`; Download-Response-Feld ist `download_url`.
- `POST /vorgaenge` liefert ein `VorgangListItem` (kein volles Detail mit Historie/Dokumenten).
- Erlaubte Datei-Magic-Bytes: JPEG, PNG, GIF, WEBP, PDF (Content-Type wird server-seitig gesnifft, nie vom Client übernommen — gleiches Muster wie `website/service.py::_sniff_image_ext`).

### Fachlogik-Entscheidungen
- **Löschsperre Kunde:** Service prüft `vorgang`-Referenzen vor dem Löschen (409 `ConflictError`), DB-FK `ON DELETE RESTRICT` als zweite Linie. **Offener Punkt:** Die AC verlangt die Sperre auch bei bestehenden *Rechnungen* — PROJ-8 („PDF-Rechnungen") ist laut `features/INDEX.md` noch „Planned", es existiert keine `rechnung`-Tabelle im Code. Ein `ponytail:`-Kommentar in `backend/app/features/kunden/repository.py` markiert die Stelle; sobald PROJ-8 die Tabelle anlegt, muss dort ein zweiter Check (`has_rechnungen`) ergänzt werden.
- **Zuweisung:** minimale Spalte `vorgang.zugewiesener_nutzer_id` (kein eigenes Zuweisungs-Table) — Vorgriff auf PROJ-6 laut Tech Design, absichtlich ohne Kalender/Verfügbarkeit. `POST /vorgaenge/{id}/zuweisungen` validiert, dass der Ziel-Nutzer im selben Mandanten die Rolle `Monteur` hat.
- **Monteur-Leserechte:** `GET /vorgaenge` filtert für Monteure serverseitig auf `zugewiesener_nutzer_id = user.id`; `GET /vorgaenge/{id}` und der Dokument-Download werfen `403` bei fremden Vorgängen. Kunden-/Objekt-Endpunkte sind für Monteure komplett gesperrt (`require_role`).
- **Anfragen-Übernahme:** `POST /anfragen/{id}/uebernehmen` legt (falls kein `kunde_id` übergeben) einen neuen Kunden aus den Anfragedaten an, dedupliziert nicht automatisch (Edge Case „Hinweis, kein Merge"), kopiert `anfragebild`-Objektpfade 1:1 als `vorgang_dokument` (kein Re-Upload) und markiert die Anfrage über `anfrage.vorgang_id` als übernommen (zweite Übernahme wird mit 422 abgelehnt).
- **Historie:** unveränderliche Einträge (`angelegt`, `status_geaendert`, `feld_geaendert`, `zugewiesen`, `dokument_hochgeladen`, `dokument_geloescht`) werden bei jeder Schreiboperation geschrieben; keine Update-/Delete-Route auf `vorgang_historie`.

### Tests
`/home/dev/miniconda3/envs/Dashboard/bin/python3 -m pytest backend/tests/features/kunden backend/tests/features/vorgaenge -q` → **23 grün** (8 Kunden/Objekte, 15 Vorgänge/Dokumente/Übernahme). Vollständige Suite `pytest backend/tests` → **63 grün** (keine Regression in PROJ-1/PROJ-2-Tests). Abgedeckt: Mandanten-Isolation (Kunden + Vorgänge), Rollen-Guards (Monteur kann nicht schreiben/keine fremden Vorgänge lesen/keine Kunden lesen), CRUD-Happy-Path je Entität, Löschsperre bei bestehendem Vorgang, Pagination-Vertrag (`limit`+`offset`+`total`), Dokument-Upload/-Download/-Löschen-Roundtrip inkl. Dateityp-Ablehnung, Anfragen-Übernahme inkl. Doppel-Übernahme-Sperre.

### QA-Fix: BUG-1 (High) — `GET /users` für Büro gesperrt
QA fand: `backend/app/features/users/routes.py:20` verlangte `require_role("Inhaber")` für `GET /users`, obwohl die Schreib-Owner-Tabelle Büro bereits `POST /vorgaenge/{id}/zuweisungen` erlaubt — der Monteur-Zuweisungs-Picker in `vorgang-detail.tsx` blieb für Büro leer (403 beim Laden der Monteurliste), das Feature war für die vorgesehene Rolle unbenutzbar.

**Fix:** `require_role("Inhaber")` → `require_role("Buero", "Inhaber")` in `backend/app/features/users/routes.py:20` (nur `list_users`; `invite_user`/`change_user` bleiben `Inhaber`-only — reine Leseausweitung). Vor dem Fix geprüft, ob das eine Rechteausweitung mit sensiblen Daten ist: `UserRead` (`backend/app/features/users/schemas.py`) enthält nur `id`, `name`, `email`, `role`, `status` — kein `password_hash`, keine Tokens. E-Mail von Kollegen im selben Mandanten für Büro sichtbar zu machen ist unkritisch (gleiche Firma, bereits über Vorgänge/Zuweisungen indirekt sichtbar). RLS/`mandant_id`-Filter in `users/repository.py::list_users` bleibt unverändert — Büro sieht weiterhin ausschließlich Nutzer des eigenen Mandanten.

Neue Tests in `backend/tests/test_users.py`: `test_buero_can_list_users_but_not_invite_or_change` (Büro darf jetzt listen, aber weiterhin nicht einladen/ändern), `test_buero_sees_only_own_tenant_users` (Mandantentrennung bleibt bestehen), `test_monteur_cannot_list_users` (Monteur weiterhin gesperrt, ersetzt die alte `test_non_owner_cannot_list_users`).

**Test nach Fix:** `/home/dev/miniconda3/envs/Dashboard/bin/python3 -m pytest backend/tests -q` → **78 grün** (76 nach QA-Erweiterung + 2 neue Tests für BUG-1), keine Regression.

### Offene Punkte
- Rechnungs-Löschsperre kann erst mit PROJ-8 vollständig umgesetzt werden (siehe oben).
- ~~`GET /users` verlangt laut PROJ-1 `require_role("Inhaber")`~~ — behoben, siehe QA-Fix BUG-1 oben.

## QA Test Results

**Tested:** 2026-08-17
**Backend:** pytest gegen `TestClient(app)` + SQLite-Testschema (`backend/tests/conftest.py`), kein laufender Server nötig
**Frontend:** Code-Review (`nextjs_app/`) — kein laufender Next.js-Server verfügbar in dieser Session, daher kein manueller Browser-Test; `npm run typecheck`, `npm run test` erneut ausgeführt
**Tester:** QA Engineer / Red-Team (AI)

### Vorgehen
1. Feature-Spec vollständig gelesen (AC, Edge Cases, Tech Design, Frontend- und Backend-Implementation-Notes inkl. dort dokumentierter bekannter Einschränkungen).
2. Bestehende Suite ausgeführt: `/home/dev/miniconda3/envs/Dashboard/bin/python3 -m pytest backend/tests -q` → **63 grün**, keine Regression.
3. Code-Review beider Feature-Slices (`backend/app/features/kunden`, `backend/app/features/vorgaenge`, Routes/Service/Repository/SQL-Migration) sowie des Next.js-Frontends (`nextjs_app/app/(app)/kunden`, `.../vorgaenge`, `nextjs_app/components/{kunden,vorgaenge}`, `nextjs_app/lib/api`, `nextjs_app/lib/theme/tokens.ts`).
4. **13 zusätzliche, gezielte Red-Team-Tests selbst geschrieben** (Lücken in der bestehenden Suite: Direkt-ID-Zugriff über Mandantengrenzen statt nur Listen-Filterung, SQL-Injection-Payload, Monteur-Download am eigenen zugewiesenen Vorgang) — alle grün, keine Lücke gefunden:
   - `backend/tests/features/vorgaenge/test_qa_crosstenant_vorgaenge.py` (7 Tests: Cross-Tenant GET/PATCH Vorgang, Cross-Tenant Dokument-Download/-Löschen, Cross-Tenant Vorgang-Anlage gegen fremden Kunden, Cross-Tenant Zuweisung, Monteur-Download am eigenen zugewiesenen Vorgang)
   - `backend/tests/features/kunden/test_qa_crosstenant.py` (6 Tests: Cross-Tenant GET/PATCH/DELETE Kunde, Cross-Tenant Objekte lesen/anlegen, Monteur direkter Kunden-Lesezugriff, SQL-Injection im Such-Query-Parameter)
   - Gesamtsuite danach: **76 grün** (`pytest backend/tests`), keine Regression.

### Acceptance Criteria Status

#### AC-1: Vorgang enthält Status, Quelle, Anliegen, Kunde, optionales Objekt, Notizen, Anhänge und Zeitstempel
- [x] Datenmodell (`backend/sql/003_kunden_vorgaenge.sql`) und `VorgangDetail`-Schema decken alle Felder ab; verifiziert per `test_buero_creates_vorgang_default_status_neu`, `test_document_upload_download_delete_roundtrip`.

#### AC-2: Zulässige Status sind „Neu", „Rückruf", „Angebot offen", „Termin geplant", „Erledigt", „Abgeschlossen"
- [x] DB-`CHECK`-Constraint + Pydantic-`Literal` + Service-Validierung (`VALID_STATUS`) — dreifach abgesichert. `test_invalid_status_filter_rejected` bestätigt 422 bei unbekanntem Status.

#### AC-3: Büro und Inhaber können Kunden, Objekte und Vorgänge anlegen, bearbeiten, suchen und nach Status filtern
- [x] Anlegen/Bearbeiten/Suchen/Statusfilter für Kunde, Objekt, Vorgang vollständig getestet (`test_status_filter`, `test_create_and_list_objekt`, Kunden-CRUD-Tests).
- [ ] BUG (siehe BUG-1): Die laut Schreib-Owner-Tabelle zum „Bearbeiten" gehörende Monteur-**Zuweisung** ist für die Rolle Büro in der UI faktisch nicht nutzbar, weil die Monteurliste nicht geladen werden kann. Der Backend-Endpunkt selbst (`POST /vorgaenge/{id}/zuweisungen`) ist für Büro korrekt freigeschaltet und funktioniert bei direktem API-Aufruf mit bekannter `nutzer_id` (verifiziert), nur die UI-gestützte Auswahl fehlt.

#### AC-4: Anhänge sind nur berechtigten Nutzern des Mandanten zugänglich; Foto/PDF-Upload und -Download
- [x] Upload/Download/Löschen-Roundtrip inkl. Dateityp-Ablehnung (`test_document_upload_download_delete_roundtrip`, `test_document_upload_rejects_invalid_filetype`).
- [x] Monteur kann NICHT hochladen/löschen (`test_monteur_cannot_upload_dokument`, Rollen-Guard `require_role` auf Upload/Delete-Route), KANN aber Dokumente des ihm zugewiesenen Vorgangs herunterladen (neu getestet: `test_monteur_can_download_dokument_of_assigned_vorgang`) — entspricht der Schreib-Owner-Tabelle.
- [x] Cross-Tenant-Download/-Löschen über erratene IDs blockiert (neu getestet, 404 statt Leak).

#### AC-5: Jeder Vorgang zeigt seine Änderungen und zugehörigen Dokumente chronologisch
- [x] `vorgang_historie` unveränderlich, chronologisch sortiert (`ORDER BY created_at ASC`); `test_history_recorded_on_status_change` bestätigt Einträge bei Anlage/Statuswechsel. Frontend übersetzt Ereignis-Codes in deutsche Labels (Code-Review `vorgang-chronik.tsx`).

#### AC-6: Löschen eines Kunden ist gesperrt, solange Vorgänge oder Rechnungen bestehen
- [x] Vorgänge-Seite: App-Check (409) + DB-FK `ON DELETE RESTRICT` als zweite Linie; `test_delete_kunde_blocked_with_vorgang`, `test_delete_kunde_allowed_without_vorgang`. Cross-Tenant-Löschversuch zusätzlich blockiert (neu getestet).
- [~] Rechnungen-Seite: **bestätigt weiterhin nicht umgesetzt** — es existiert keine `rechnung`-Tabelle (PROJ-8 laut `features/INDEX.md` noch „Planned"). Das ist die im Spec bereits dokumentierte, akzeptierte Einschränkung (`ponytail:`-Kommentar in `backend/app/features/kunden/repository.py`) — **kein neuer Bug**, nur bestätigt.

**AC-Ergebnis: 5/6 vollständig bestanden, 1/6 mit dokumentierter/bekannter Teil-Einschränkung (AC-6/Rechnung) + 1 neuem High-Bug innerhalb AC-3 (Zuweisung).**

### Edge Cases Status

#### EC-1: Gleiche E-Mail/Telefonnummer erzeugt Bestandskunden-Hinweis ohne Auto-Merge
- [x] `test_duplicate_email_hint_without_merge` — `moegliche_duplikate` im Response, kein Merge, zwei getrennte Datensätze bleiben bestehen.

#### EC-2: Gelöschter Anhang bleibt nicht als kaputter Link in bereits erzeugten PDFs sichtbar
- [x] Durch Design erfüllt: Es werden keine öffentlichen/persistenten URLs gespeichert oder in Dokumente eingebettet — nur der interne `objektpfad`; Download-URLs werden ausschließlich zur Laufzeit kurzlebig generiert (`presigned_get_url`). PROJ-3 selbst erzeugt keine PDFs (das ist PROJ-8) — dieser Edge Case ist durch die Architektur bereits strukturell ausgeschlossen.

#### EC-3: Monteur kann nur zugewiesenen Vorgang lesen, keine Kundendaten ändern
- [x] `test_monteur_sees_only_assigned_vorgang`, `test_monteur_cannot_patch_vorgang`, `test_monteur_cannot_upload_dokument`, `test_monteur_cannot_uebernehmen_anfrage`; neu: `test_monteur_cannot_read_kunde_directly` (403 bei direktem `GET /kunden/{id}`, nicht nur Listen-Ausblendung).

#### EC-4: Fehlende Objektadresse ist erlaubt (unqualifizierte Anfrage)
- [x] `objekt_id` ist optional in `VorgangCreate`; `test_buero_creates_vorgang_default_status_neu` legt einen Vorgang ohne Objekt an.

### Security Audit Results (Red-Team)
- [x] **Auth:** Alle Routen nutzen `Depends(get_current_user)`/`require_role(...)`; `mandant_id`/`role` kommen ausschließlich aus dem serverseitig verifizierten JWT (`app/deps.py`), niemals aus Client-Payload oder Query-Parametern.
- [x] **Tenant-Isolation (Kunde/Objekt/Vorgang/Dokument):** Jede Query ist über `mandant_id`-Parameter gescoped; zusätzlich RLS-Policies in `backend/sql/003_kunden_vorgaenge.sql` (`current_setting('app.current_mandant_id')`). **12 selbst geschriebene Cross-Tenant-Angriffstests** (direkter Zugriff über erratene UUIDs auf GET/PATCH/DELETE Kunde, GET/PATCH Vorgang, Dokument-Download/-Löschen, Objekt-Liste/-Anlage, Vorgangs-Anlage gegen fremden Kunden, Zuweisung gegen fremden Vorgang) — **alle korrekt mit 404 abgewiesen, kein Leak**.
  - Hinweis (keine neue Lücke, Bestandsmuster): Die Testsuite läuft gegen ein SQLite-Testdouble (`conftest.py`), nicht gegen echtes Postgres — die RLS-Policies selbst werden dadurch nicht am DB-Server verifiziert, nur die Anwendungs-seitige `WHERE mandant_id = %s`-Filterung. Das ist identisch zum bestehenden Testaufbau aus PROJ-1/PROJ-2 und keine PROJ-3-spezifische Lücke.
- [x] **Rollen-Bypass:** Monteur kann keine Kunden/Objekte lesen oder schreiben (403), keine Vorgänge anlegen/bearbeiten/zuweisen/hochladen (403), keine fremden (nicht zugewiesenen) Vorgänge lesen (403), keine Anfragen übernehmen (403). Büro/Inhaber haben vollen Schreibzugriff wie spezifiziert.
- [x] **Dokument-URLs:** Nicht öffentlich; DB speichert nur `objektpfad` (nie eine URL); `GET /vorgaenge/{id}/dokumente/{id}/download` liefert eine kurzlebige presigned URL (Default-Ablauf 3600s, `storage.py::presigned_get_url`) erst nach Berechtigungsprüfung (Mandant + ggf. Monteur-Zuweisung).
- [x] **Datei-Validierung:** Content-Type wird serverseitig aus Magic-Bytes gesnifft (JPEG/PNG/GIF/WEBP/PDF), nie vom Client übernommen; ungültige Typen mit 422 abgelehnt (`test_document_upload_rejects_invalid_filetype`), Größenlimit 15 MB serverseitig geprüft.
- [x] **SQL-Injection:** Alle Queries durchgängig parametrisiert (`%s`-Platzhalter), keine f-String-Interpolation von Nutzerwerten (nur Spaltennamen/WHERE-Fragmente sind Server-kontrolliert, nie Nutzereingabe). Eigener Injection-Payload-Test (`'; DROP TABLE kunde; --` im `q`-Parameter) bestätigt: kein Fehler, keine Datenmanipulation, Tabelle bleibt intakt.
- [x] **Löschsperre Kunde (Vorgänge-Seite):** doppelt abgesichert (App-Check 409 + DB-FK `ON DELETE RESTRICT`), Cross-Tenant-Löschversuch zusätzlich verifiziert blockiert.

### Bugs Found

#### BUG-1: Büro kann Monteur-Zuweisung an einem Vorgang in der UI nicht durchführen (GET /users 403 für Büro)
- **Severity:** High
- **Steps to Reproduce:**
  1. Als Büro-Nutzer einloggen, einen Vorgang öffnen (`/vorgaenge/{id}`).
  2. Im Bereich „Zuständigkeit/Zuweisung" versuchen, einen Monteur auszuwählen.
  3. Erwartet: Laut Schreib-Owner-Tabelle der Spec und laut `POST /vorgaenge/{id}/zuweisungen`-Route (`require_role("Buero","Inhaber")`) soll Büro einem Vorgang einen Monteur zuweisen können.
  4. Tatsächlich: `nextjs_app/components/vorgaenge/vorgang-detail.tsx:65` ruft `listNutzer()` → `GET /users` auf, das aber laut PROJ-1 `require_role("Inhaber")` verlangt (`backend/app/features/users/routes.py:20`, Rolle Büro nicht enthalten). Für Büro schlägt der Request mit 403 fehl, `monteure` bleibt `[]`, und der komplette Zuweisungs-Block wird laut `{monteure.length > 0 && (...)}` (Zeile 192) gar nicht gerendert — Büro hat somit keinerlei UI-Möglichkeit, einen Monteur auszuwählen, obwohl Backend und Spec das für Büro vorsehen.
  5. Der Backend-Endpunkt selbst funktioniert korrekt für Büro bei direktem API-Aufruf mit bekannter `nutzer_id` (durch Code-Review + bestehende Tests plausibilisiert) — der Bug liegt im fehlenden Lesezugriff für die Monteurliste, nicht in der Zuweisungs-Route selbst.
- **Root Cause:** PROJ-1-Rechte-Lücke (`GET /users` zu eng auf „Inhaber" beschränkt), wirkt sich aber konkret als PROJ-3-AC-Verletzung aus (AC-3 „Büro … können … Vorgänge … bearbeiten", Schreib-Owner-Tabelle nennt Büro explizit als Zuweisungs-Owner).
- **Priority:** Fix before deployment (blockiert eine im Alltag zentrale Büro-Aufgabe: Monteure verteilen).
- Bereits in den Implementation Notes (Frontend + Backend) als „Offener Punkt“ dokumentiert — hiermit als QA-Bug mit Schweregrad bestätigt und priorisiert, nicht neu entdeckt.

### Bestätigte, bereits dokumentierte Einschränkungen (kein neuer Bug)
- **Löschsperre Kunde prüft nur `vorgang`, keine `rechnung`:** bestätigt weiterhin zutreffend — keine `rechnung`-Tabelle im Code, PROJ-8 „Planned". Erwartungsgemäß, `ponytail:`-Kommentar vorhanden.
- **„Anfrage übernehmen"-UI nicht gebaut:** bestätigt — kein Frontend-Code unter `nextjs_app/app/(app)/` für Anfragenliste/Übernahme-Dialog gefunden. Backend-Endpunkt (`POST /anfragen/{id}/uebernehmen`) existiert und ist getestet. Kein AC dieser Spec verlangt explizit eine UI dafür — bewusste Scope-Entscheidung, kein Bug.

### Summary
- **Acceptance Criteria:** 5/6 vollständig bestanden, 1/6 (AC-6) mit erwarteter Teil-Einschränkung (Rechnung-Seite, PROJ-8-Vorgriff)
- **Bugs Found:** 1 total (0 Critical, 1 High, 0 Medium, 0 Low)
- **Security:** Pass — keine Tenant-Leaks, keine Rollen-Bypässe, keine SQL-Injection, Dokument-URLs korrekt kurzlebig/berechtigt (12 gezielte Red-Team-Tests, alle bestanden)
- **Tests:** Backend-Gesamtsuite 76/76 grün (63 bestehend + 13 neu von QA); Frontend `npm run test` 11/11 grün, `npm run typecheck` sauber
- **Production Ready:** NO (1 High-Bug offen)
- **Recommendation:** BUG-1 vor Deploy fixen (naheliegendste Lösung: `GET /users` auf `require_role("Buero","Inhaber")` erweitern, analog zum bereits etablierten Schreib-Owner-Muster dieser Spec — Entscheidung liegt beim Backend/PROJ-1-Owner). Danach `/abc-qa` erneut gegen BUG-1 laufen lassen; die übrigen 5 AC + Security-Audit müssen bei einem Re-Test nicht wiederholt werden, nur BUG-1 verifizieren.

### Retest BUG-1 (2026-08-17)

**Fix:** `backend/app/features/users/routes.py:20` — `list_users`-Guard von `require_role("Inhaber")` auf `require_role("Buero", "Inhaber")` erweitert; `invite_user`/`change_user` bleiben bewusst `require_role("Inhaber")`.

Eigenständig retestet (nicht nur Dev-Angaben übernommen), Scope laut Coordinator-Auftrag auf BUG-1 begrenzt — restliche AC + Security-Audit bleiben laut obigem Bericht gültig:
1. **Büro lädt Monteurliste:** Code-Review bestätigt — `vorgang-detail.tsx` ruft `listNutzer()` unbedingt für jede Rolle mit `darfSchreiben` (Büro+Inhaber) auf; vorher schlug das für Büro mit 403 fehl (`monteure` blieb `[]`, Picker unsichtbar wegen `{monteure.length > 0 && (...)}`). Mit dem erweiterten Guard bekommt Büro jetzt 200 und die Liste befüllt sich — kein Frontend-Codechange nötig, das UI war immer korrekt, nur der Endpunkt blockierte. Kein laufender Server verfügbar, daher Verifikation per Code-Review statt Browser-Test.
2. **Cross-Tenant-Angriffsversuch (selbst geschrieben, nicht nur Backend-Selbstauskunft):** `backend/tests/features/kunden/test_qa_crosstenant.py::test_bug1_retest_buero_lists_users_cross_tenant_blocked` — Büro aus Mandant A ruft `GET /users` auf, während Mandant B einen Inhaber und einen Monteur hat; Response enthält ausschließlich die zwei Nutzer aus Mandant A, keine ID aus Mandant B. **Pass.**
3. **Monteur weiterhin blockiert:** `backend/tests/features/kunden/test_qa_crosstenant.py::test_bug1_retest_monteur_still_blocked_from_users` — `GET /users` als Monteur liefert weiterhin 403. **Pass.** (Deckt sich mit unverändertem `test_monteur_cannot_list_users` in `backend/tests/test_users.py`.)

Zusätzlich vom Backend-Dev bereits mitgelieferte, eigens gegengelesene Tests bestätigt: `backend/tests/test_users.py::test_buero_can_list_users_but_not_invite_or_change` (Büro darf lesen, aber nicht `POST`/`PATCH /users` — 403) und `test_buero_sees_only_own_tenant_users` — Diff beschränkt sich auf die eine Guard-Zeile, `invite_user`/`change_user` unverändert Inhaber-only, `UserRead`-Schema exponiert keine sensiblen Felder (Passwort-Hash etc. nicht im Response-Modell).

**Ergebnis:** BUG-1 verifiziert behoben, kein neuer Tenant-Leak eingeführt. Gesamtsuite `pytest backend/tests` → **80 grün** (76 aus dem letzten QA-Lauf + 2 unabhängige Retest-Tests + 2 vom Dev mitgelieferte Tests), keine Regression.

**Finaler Status: Kein Critical/High-Bug mehr offen → Approved.**

## Deployment
Production URL: https://biz.app.msce.info (Domain in Dokploy konfiguriert, sync automatisch mit GitHub-Repo, Auto-Deploy via Push auf `main`).
Deployed: 2026-08-17 · Version: 0.1.2 · Host: Dokploy (Compose).
Ausgeliefert: Kunden-/Objekt-/Vorgangsverwaltung (Liste, Detail, Statusfilter, Pagination), Dokument-Upload/-Download (Foto/PDF, presigned URLs), Vorgangs-Chronik, Rollen-abhängige UI/Rechte (Monteur nur zugewiesener Vorgang, keine Kundendaten), Löschsperre für Kunden mit bestehenden Vorgängen; BUG-1-Fix (`GET /users` für Büro geöffnet, Monteur-Zuweisung im Vorgangsdetail funktionsfähig).
Smoke-Test auf der Produktions-Domain steht noch aus (kein Browser-Zugriff in dieser Session) — bitte nach Auto-Deploy manuell verifizieren: `/api/health` antwortet, Kunden-/Vorgangsliste lädt, neuer Kunde/Vorgang anlegbar, Dokument-Upload/-Download funktioniert, Monteur-Login sieht nur zugewiesenen Vorgang ohne Kundendaten.
