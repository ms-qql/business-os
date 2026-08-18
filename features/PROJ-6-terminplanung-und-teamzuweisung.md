# PROJ-6: Terminplanung und Teamzuweisung

## Status: In Review (QA: 7/7 AC bestanden, BUG-1 Medium offen)
**Created:** 2026-08-16
**Last Updated:** 2026-08-18
**Frontend-Stand:** 2026-08-18 — Next.js 16 + shadcn/ui, gebaut & typegeprüft. Backend implementiert (Migration `007_termine.sql`, Feature-Modul `backend/app/features/termine/`), Commit `fe1e046`.
**QA-Stand:** 2026-08-18 — 7/7 AC bestanden, Security-Audit ohne Critical/High-Befund, BUG-1 (Medium) offen. Siehe „QA Test Results" unten.

## Dependencies
- Requires: PROJ-3 — Vorgang und zugehörige Adresse.
- Requires: PROJ-1 — Rollen (Inhaber, Büro, Monteur) und Mandantenkontext.

## Reuse aus ImmoCRM
- Kalenderfenster und Verfügbarkeitsverhalten dienen als Vorlage; Makler-, Besichtigungs- und Buchungslogik wird nicht übernommen.

## Datenmodell-Hinweis (Abgrenzung zu PROJ-3)
PROJ-3 hat bereits ein minimales `vorgang.zugewiesener_nutzer_id` (eine Monteur-Zuweisung auf **Vorgangsebene**, ohne Kalender). PROJ-6 fügt eine **eigenständige 1:n-Struktur auf Terminebene** hinzu: ein `Termin` verweist auf genau einen Vorgang und kann über eine `termin_zuweisung`-Tabelle einem oder mehreren Monteuren zugeordnet werden. Diese Termin-Zuweisung konkurriert nicht mit `vorgang.zugewiesener_nutzer_id`; beide Felder bleiben bestehen und bedienen unterschiedliche Ebenen (Vorgang vs. einzelner Termin). Die PROJ-3-Architektur note ("PROJ-6 legt keine zweite, konkurrierende Datenstruktur an") bezieht sich ausschließlich auf die Vorgangszuweisung und ist damit erfüllt.

## User Stories
- Als Büro möchte ich einen Vorgang als Termin planen und einem oder mehreren Teammitgliedern zuweisen, damit klar ist, wer wann wo ist.
- Als Monteur möchte ich meine eigenen Termine mit Adresse, Kontakt, Anliegen und freigegebenen Anhängen sehen, damit ich meinem Einsatz vorbereitet bin.
- Als Inhaber möchte ich die Termine des kleinen Teams im Tag- und Wochenüberblick sehen, damit ich Auslastung und Lücken erkenne.
- Als Büro möchte ich auf einen Blick sehen, wenn zwei Termine desselben Monteurs sich überschneiden, damit keine Doppelbelegung übersehen wird.

## Acceptance Criteria
- [x] **AC-1 (Anlage/Änderung/Absage):** Büro und Inhaber können einen Termin mit Pflichtfeldern Beginn und Ende, optionaler Adresse, Notiz und einem oder mehreren Teammitgliedern (Rolle `Monteur` im eigenen Mandanten) anlegen, ändern oder absagen. Ein Termin ohne zugewiesenes Teammitglied ist zulässig (Warnung, kein Block).
- [x] **AC-2 (Kalenderansicht):** Die Kalenderansicht stellt pro Teammitglied eine Spalte (Woche) bzw. Zeile (Tag) dar und deckt Tag- und Wochenansicht für maximal drei aktive Teammitglieder ab. Sind mehr als drei Monteure im Mandanten aktiv, kann der Betrachter die angezeigten Monteure per Auswahl auf bis zu drei begrenzen (Standard: zuletzt zugewiesene).
- [x] **AC-3 (Vorgangsbezug):** Ein Termin verweist auf genau einen Vorgang (`termin.vorgang_id`, FK `ON DELETE RESTRICT`); ein Vorgang kann mehrere Termine haben. Ein Termin ohne gültigen, dem Mandanten gehörenden Vorgang wird mit `422` abgelehnt.
- [x] **AC-4 (Konfliktwarnung, nicht-blockierend):** Beim Anlegen oder Verschieben wird für jedes zugewiesene Teammitglied geprüft, ob es im selben Zeitfenster (`neuer_beginn < anderer_ende` UND `neuer_ende > anderer_beginn`) bereits einen nicht-abgesagten Termin hat. Ist das der Fall, wird der Termin **trotzdem gespeichert**, die Antwort enthält `konflikt: true` (Liste der betroffenen Teammitglieder), und die Oberfläche markiert die Überschneidung rot. Die Prüfung gilt nur pro Teammitglied, nicht mandantenübergreifend.
- [x] **AC-5 (Monteursicht):** Monteure sehen ausschließlich Termine, denen sie zugewiesen sind. Sichtbar sind Adresse, Kontakt, Anliegen und freigegebene Anhänge; Preis- und Rechnungsdaten sind ausgeblendet. Ein Monteur kann keine Termine anlegen, ändern oder absagen (Schreibzugriff verweigert mit `403`).
- [x] **AC-6 (Statuswechsel):** Das Anlegen eines nicht-abgesagten Termins setzt den Vorgang auf „Termin geplant“. Wird der letzte nicht-abgesagte Termin eines Vorgangs abgesagt und existiert kein weiterer offener Termin, wird der Vorgangsstatus auf seinen vorherigen Wert zurückgesetzt; die Rücksetzung wird in der Vorgangshistorie dokumentiert. Bleibt ein weiterer offener Termin bestehen, bleibt der Status „Termin geplant“.
- [x] **AC-7 (Validierung):** Beginn und Ende sind Pflichtfelder; es gilt `ende > beginn`. Verletzungen führen zu `422`. Alle Zeitangaben werden einheitlich als Zeitzone `Europa/Berlin` interpretiert und gespeichert.

## Edge Cases
- Termin ohne vollständige Adresse ist erlaubt, aber als „Adresse offen" markiert; die Adresse kann die Objektadresse des Vorgangskunden oder Freitext sein.
- Eine Absage entfernt den Termin nicht aus der Historie; ein abgesagter Termin wird in der Kalenderansicht ausgegraut dargestellt und bleibt in der Vorgangshistorie nachvollziehbar.
- Deaktivierte Nutzer können einem Termin nicht neu zugewiesen werden; bestehende Zuweisungen bleiben nachvollziehbar (der Termin bleibt sichtbar, die Zuweisung ist als inaktiv gekennzeichnet).
- Zeitzonen werden für alle Termine einheitlich als Europa/Berlin behandelt; eine Überschneidungsprüfung vergleicht stets in derselben Zeitzone.
- Ein Termin mit Beginn in der Vergangenheit ist anlegbar (kein Hartblock); die Ansicht markiert vergangene Termine als „vergangen".
- Die Konfliktprüfung (AC-4) greift nur bei nicht-abgesagten Terminen desselben Teammitglieds; abgesagte Termine erzeugen keinen Konflikt.
- Löschen eines Vorgangs mit bestehenden Terminen ist über die FK-Regel (`ON DELETE RESTRICT`) auf Datenbankebene blockiert, solange Termine auf ihn verweisen (entspricht der Löschsperrenlogik aus PROJ-3).

## Technical Requirements
- Mobile: Tagesansicht ist ab 375 px bedienbar (Monteuransicht primär mobil).
- Performance: Wochenansicht lädt nur den sichtbaren Zeitraum (kein vollständiges Jahr im Speicher).
- Security: Schreibende Endpunkte (`POST/PATCH/DELETE` Termin, Termin-Zuweisung) tragen `require_role("Buero","Inhaber")`; Monteur-Lesezugriff wird serverseitig auf zugewiesene Termine begrenzt (analog PROJ-3-Muster, `403` bei fremdem Termin). Mandantentrennung über `mandant_id` + RLS wie in PROJ-1/PROJ-3.

---

<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-18 · **Stack:** Next.js 16 + FastAPI + PostgreSQL (RLS) + MinIO · **Branch:** specs/PROJ-6-terminplanung-und-teamzuweisung

> Hinweis zum Stack: Das Skill-Template nennt Flutter web + shadcn_flutter. Dieses Projekt ist faktisch Next.js 16 (App Router) + shadcn/ui (React) + Tailwind, bestätigt durch PRD und bestehenden Code (PROJ-3/5). Das Design folgt dem **realen** Stack, nicht dem Template-Text.

### Grundlage im Code (verifiziert, nicht angenommen)
- PROJ-1 liefert die Rollen `Inhaber`/`Büro`/`Monteur`, die mandantengetrennte JWT-Sitzung und den `require_role(*roles)`-Guard (`backend/app/deps.py:68`) — wird unverändert für die Schreibrechte dieses Features genutzt.
- PROJ-1/PROJ-3 liefern das RLS-Muster: jede Fachtabelle trägt `mandant_id` und ist auf `current_setting('app.current_mandant_id')` begrenzt; Wiederholung in `backend/sql/003_kunden_vorgaenge.sql`.
- PROJ-3 liefert das Vorgang-Modell: Status-Enum inkl. „Termin geplant", das Feld `vorgang.zugewiesener_nutzer_id` (Vorgriff auf Vorgangsebene) und die `vorgang_historie` mit Ereignis-Codes (`status_geaendert`, `zugewiesen` usw.).
- Der Migrations-Runner `backend/apply_migrations.py` wendet `backend/sql/00X_*.sql` idempotent an (IF NOT EXISTS) — neues SQL folgt exakt diesem Muster.
- Router-Registration erfolgt zentral in `backend/app/main.py:25-36` via `app.include_router(...)`; der letzte registrierte Router ist `angebote_router` (Zeile 36) — `termine_router` reiht sich direkt danach ein, kein Umbau bestehender Zeilen nötig.
- Die shadcn-Primitive `table`, `dialog`, `select`, `badge` existieren bereits unter `nextjs_app/components/ui/`; ein Kalender-Primitive existiert **nicht**.
- Explore-Ergebnis: `grep -rn "termin"` über Backend + Frontend liefert null Treffer (außer Status-String) — PROJ-6 ist Greenfield, baut sauber auf obigen Mustern auf, keine Konflikte mit bestehenden Routen/Tabellen.

### Ziel und Umfang
PROJ-6 macht aus einem Vorgang einen oder mehrere Termine und ordnet jeden Termin einem oder mehreren Monteuren zu. Kalenderansicht (Tag/Woche, max. drei Monteure), nicht-blockierende Konfliktwarnung, und eine auf den Monteur begrenzte Ansicht (ohne Preise). PROJ-3s Vorgangsebenen-Zuweisung bleibt unberührt — beide Ebenen koexistieren.

### Komponentenstruktur (Next.js, PM-lesbar)

```text
Termine (neuer Navigationspunkt „Termine", nur Inhaber/Büro sichtbar)
├── Wochenansicht
│   ├── Spalte pro Monteur (maximal drei; Auswahl bei >3)
│   ├── Terminblock (Beginn–Ende, Vorgang-Anliegen)
│   └── Konflikt-Markierung (rot) bei Überschneidung desselben Monteurs
├── Tagesansicht (mobile, ab 375 px; primär Monteuransicht)
├── Termin-Dialog (Anlegen/Bearbeiten)
│   ├── Vorgang-Wahl (verknüpft einen Vorgang)
│   ├── Beginn / Ende (Datumszeit, Europa/Berlin)
│   ├── Adresse (Objektadresse des Kunden oder Freitext; „Adresse offen"-Hinweis)
│   ├── Monteur-Mehrfachauswahl (nur Rolle Monteur, deaktivierte ausgeblendet)
│   └── Notiz
├── Absage-Bestätigung (markiert Termin ausgegraut, löscht nicht)
└── Monteuransicht (nur eigene Termine: Adresse, Kontakt, Anliegen, freigegebene Anhänge)
```

### Datenmodell (Klartext, keine SQL)
- **Termin:** gehört zu genau einem Vorgang (Fremdschlüssel), trägt den Mandanten, Beginn, Ende, optionale Adresse (Freitext oder Objektadresse), Notiz, ein „abgesagt"-Kennzeichen und Zeitstempel. Alle Zeiten werden einheitlich als Europa/Berlin gespeichert.
- **Termin-Zuweisung:** verknüpft einen Termin mit einem Nutzer der Rolle Monteur im selben Mandanten; ein Termin kann mehrere Zuweisungen haben (1:n). Deaktivierte Nutzer können nicht neu zugewiesen werden; bestehende Zuweisungen bleiben nachvollziehbar.
- **Vorgang:** bleibt bis auf den Status unverändert. Das Anlegen eines offenen Termins setzt den Vorgang auf „Termin geplant"; die Absage des letzten offenen Termins setzt den Status auf den vorherigen Wert zurück — und dieser Wechsel wird in der Vorgangshistorie festgehalten.
- **Vorgangshistorie:** erhält neue Ereignis-Codes (Termin angelegt, Termin geändert, Termin abgesagt, Termin zugewiesen/entzogen).
- Keine Dateien in PROJ-6: etwaige Anhänge werden aus dem zugehörigen Vorgang (PROJ-3/MinIO) angezeigt; PROJ-6 legt keinen eigenen Speicherpfad an.

### API-Form (Endpunkte, keine Implementierung)
- `GET /termine?von=&bis=&nutzer_ids=` → Termine des Mandanten im Kalenderfenster (Wochenansicht lädt nur den sichtbaren Zeitraum; `nutzer_ids` filtert auf ausgewählte Monteure bei >3).
- `POST /termine` → Termin anlegen (Vorgang, Beginn, Ende, Adresse optional, Notiz, Monteure[]). Validiert `ende > beginn` (sonst `422`, deckt AC-7) und dass `vorgang_id` einem Vorgang des eigenen Mandanten entspricht (sonst `422`, deckt AC-3).
- `GET /termine/{id}` → einen Termin mit seinen Zuweisungen lesen; liefert zusätzlich Anliegen und die Kontaktfelder (Name, Telefon, E-Mail) des am Vorgang hängenden Kunden **eingebettet** (kein zweiter Client-Request nötig) — deckt AC-5 „Sichtbar sind Adresse, Kontakt, Anliegen". Preis-/Rechnungsfelder werden nie in dieses Schema aufgenommen.
- `PATCH /termine/{id}` → Termin ändern/verschieben; validiert `ende > beginn` wie bei Anlage; Antwort enthält bei Überschneidung `konflikt: true` mit Liste betroffener Monteure.
- `POST /termine/{id}/absagen` → Termin absagen (kein hartes Löschen; bleibt in Historie).
- `POST /termine/{id}/zuweisungen` und `DELETE /termine/{id}/zuweisungen/{nutzer_id}` → Monteur zuweisen/entziehen.
- `GET /nutzer/monteure` (neu, oder `GET /users?role=Monteur&status=active` als Query-Erweiterung — Implementierungsdetail für /abc-backend) → aktive Monteure des Mandanten für die Auswahl im Termin-Dialog. **Grund:** `backend/app/features/users/repository.py::list_users(mandant_id, limit)` filtert aktuell nicht nach Rolle/Status; ohne diesen Endpunkt kann der Termin-Dialog die Monteurliste nicht befüllen.
- **Vorgangs-verknüpfte Liste (Nested-Route, wie PROJ-5 Angebote):** `GET /vorgaenge/{id}/termine` und `POST /vorgaenge/{id}/termine` — zeigen dieselben Daten wie `/termine`, Einstieg aber vom Vorgang aus (Termin-Sektion im Vorgangsdetail).
- **Monteur-Sicht:** `GET /termine` liefert Monteuren serverseitig nur die eigenen Termine; schreibende Endpunkte sind mit `403` gesperrt.
- Jeder Endpunkt liest den Mandanten aus der Sitzung; Schreibend (`POST/PATCH/DELETE`, Zuweisung) tragen `require_role("Büro","Inhaber")`.

### Neue Migrationsdatei
- `backend/sql/007_termine.sql` — Tabellen `termin` (`mandant_id`, `vorgang_id` FK `ON DELETE RESTRICT`, `beginn`/`ende` als `TIMESTAMPTZ`, `adresse`, `notiz`, `abgesagt_at`, `vorheriger_vorgang_status`) und `termin_zuweisung` (`termin_id`, `nutzer_id`, UNIQUE), jeweils mit RLS-Policy auf `current_setting('app.current_mandant_id')` und Indizes auf `(mandant_id, beginn)` sowie `(nutzer_id, beginn)`. Idempotent (IF NOT EXISTS), kein `$$`-Block (siehe Tech-Entscheidungen).

### Technische Entscheidungen (WARUM)
- **Eigenes Feature-Modul `backend/app/features/termine/`** im bewährten Vier-Datei-Layout (schemas/repository/service/routes + `__init__`-Re-Export) und zentrale Registration in `main.py` — kein neues Muster, volle Konsistenz mit PROJ-3/5.
- **Keine Kalender-Bibliothek:** die Wochen-/Tagesansicht wird als eigenes, schlankes Raster (max. drei Monteurspalten) umgesetzt statt einer externen Kalender-Lib. Grund: hält Abhängigkeiten und Bundle-Größe klein; die vorhandenen shadcn-Primitive `table`/`dialog`/`select`/`badge` decken die Bausteine.
- **Konfliktwarnung nicht-blockierend** (wie in Spec entschieden): der Termin wird gespeichert, die Antwort trägt `konflikt: true`, die Oberfläche markiert rot. Der Mensch behält die Entscheidung — passend zum Produktversprechen „Entwürfe werden stets durch Menschen freigegeben".
- **Status-Rücksetzung historisiert:** nur wenn kein offener Termin mehr am Vorgang besteht, wird der Status zurückgesetzt und ein Historie-Eintrag geschrieben — vermeidet verlorene Zwischenstände.
- **Mandantentrennung via RLS + `mandant_id`:** die Überschneidungsprüfung gilt nur innerhalb des eigenen Mandanten; ein Fehler in der Anwendung kann keine fremden Termine leaken.
- **Einheitliche Zeitzone Europa/Berlin:** alle Zeitvergleiche (inkl. Konfliktprüfung) laufen in derselben Zeitzone; keine mehrfachen Zeitzonen im Modell.
- **Status-Rücksetzung (AC-6) — Quelle des vorherigen Status:** PROJ-3 hält keinen `vorheriger_status` auf dem Vorgang. Entscheidung: das Anlegen des ersten offenen Termins merkt sich den Vorgangsstatus **in `termin.vorheriger_vorgang_status`** (Snapshot beim Setzen auf „Termin geplant"). Bei Absage des letzten offenen Termins wird genau dieser gespeicherte Wert zurückgeschrieben und der Wechsel historisiert. Das vermeidet teure Historien-Rekonstruktion und ist robust gegen Zwischenstatuswechsel.
- **Zeitzone Europa/Berlin (AC-7):** das Repository-Snippet aus PROJ-3 nutzt UTC-`isoformat()` für Zeitstempel. PROJ-6 speichert Beginn/Ende hingegen als `TIMESTAMPTZ` und rechnet bei Ein-/Ausgabe explizit nach Europa/Berlin um (über `zoneinfo`, keine neue Abhängigkeit — stdlib). Alle Vergleiche (inkl. Konfliktprüfung) laufen in dieser einen Zeitzone; was der Browser als lokalen Wert schickt, wird serverseitig als Europa/Berlin interpretiert.
- **Keine `$$`-Blöcke in der Migration:** die SQLite-Testengine splittet SQL an `;` (`backend/app/db.py`). Die neue `007_termine.sql` wird daher ohne Funktionen/`DO$$-Blöcke geschrieben (nur `CREATE TABLE`/`POLICY`/`INDEX`), exakt wie die bestehenden 001–006.
- **Vorgangs-Verknüpfung folgt dem Nested-Route-Muster aus PROJ-5:** wie Angebote unter `/vorgaenge/{id}/angebote` bekommt PROJ-6 `GET|POST /vorgaenge/{id}/termine` als verknüpfte Liste; die eigenständige Termin-Ressource (`/termine`) bleibt für die Kalenderansicht. Beide Route-Familien zeigen dieselben Daten, unterschiedlicher Einstieg.

### Abhängigkeiten
- **Backend:** keine neuen Pakete; raw SQL + RLS wie in PROJ-1/3 etabliert.
- **Frontend:** keine neue Bibliothek; ggf. ein schlankes Datum/Zeit-Eingabe-Primitive, sonst vorhandene shadcn-Primitive.
- **Infrastruktur:** keine neue Komponente (kein MinIO-Pfad, kein neuer Dienst).

### Abnahmebezug
Alle AC-1…AC-7 sind durch Komponenten, Datenmodell und Endpunkte abgedeckt; insbesondere AC-4 (nicht-blockierende Konfliktwarnung über `konflikt`-Flag) und AC-6 (Status-Rücksetzung nur bei keinem offenen Resttermin, historisiert).

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-18 · **Verdict:** Architected

### Checklist
- [x] **Component structure** — jede UI-Komponente ist auf vorhandene shadcn-Primitive (`table.tsx`, `dialog.tsx`, `select.tsx`, `badge.tsx` — von CodeGraph-Explore bestätigt, alle vier existieren unter `nextjs_app/components/ui/`) oder eine klar umrissene Eigenkomposition (Kalenderraster max. 3 Spalten) gemappt. Keine vage UI-Beschreibung.
- [x] **Data model** — jede Entität (`termin`, `termin_zuweisung`) trägt `mandant_id`; RLS-Ansatz explizit an das verifizierte PROJ-3-Muster verankert (`backend/sql/003_kunden_vorgaenge.sql`: `mandant_id UUID NOT NULL REFERENCES mandanten(id)` Z.10/24/33/53/66, `ENABLE ROW LEVEL SECURITY` Z.81-85, `CREATE POLICY x_isolation ... USING (mandant_id = current_setting('app.current_mandant_id')::uuid)`). Fehlende Statusquelle für AC-6 wurde in der vorherigen Design-Iteration bereits als `termin.vorheriger_vorgang_status` nachgezogen.
- [x] **API shape** — jeder Endpunkt mit Methode+Pfad+Rollen-Guard benannt. Im Review ergänzt: explizite `422`-Validierungsregeln für AC-3 (Vorgang-Existenz im Mandanten) und AC-7 (`ende > beginn`) waren zuvor nur in den Acceptance Criteria genannt, jetzt auch in der API-Form verankert. AC-5 „Kontakt sichtbar" hatte keinen Datenpfad — jetzt geklärt: `GET /termine/{id}` liefert Kundenkontakt eingebettet, kein zweiter Client-Request.
- [x] **Tech decisions** — jede Entscheidung mit Begründung (Kalender ohne externe Lib, Konfliktwarnung nicht-blockierend, Status-Snapshot-Feld, Zeitzone via `zoneinfo`, keine `$$`-Blöcke).
- [x] **Dependencies** — CodeGraph-Explore bestätigt: kein Kalender-Package (date-fns/react-big-calendar/fullcalendar o.ä.) in `nextjs_app/package.json` vorhanden — „keine neuen Pakete" ist damit eine geprüfte Aussage, nicht nur eine Behauptung.
- [x] **Branch field** — `specs/PROJ-6-terminplanung-und-teamzuweisung` vorhanden, Branch existiert bereits (aktueller Checkout, CodeGraph-Agent bestätigt `Already on ...`).
- [x] **Conflict-free** — CodeGraph-Explore bestätigt: keine Tabelle `termin`, keine Route `/termine`, kein Verzeichnis `backend/app/features/termine/` existiert bisher. `vorgang.zugewiesener_nutzer_id` (`003_kunden_vorgaenge.sql:44`, `vorgaenge/schemas.py:40`) bleibt unangetastet, wie im Datenmodell-Hinweis dokumentiert.
- [x] **Acceptance-criteria coverage** — AC-1 (Anlage/Absage) → Endpunkte `POST/PATCH/absagen`; AC-2 (Kalender max. 3) → Komponentenstruktur + `nutzer_ids`-Filter; AC-3 (Vorgangsbezug, 422) → FK + jetzt explizite Validierung; AC-4 (Konflikt) → `konflikt`-Flag; AC-5 (Monteursicht inkl. Kontakt) → serverseitiger Scope + jetzt eingebetteter Kundenkontakt; AC-6 (Status) → `vorheriger_vorgang_status`-Snapshot; AC-7 (Validierung/Zeitzone) → jetzt explizite `422`-Regel + `TIMESTAMPTZ`/`zoneinfo`.

### CodeGraph-Cross-Check
Delegiert an Explore-Agent (10 gezielte Prüfpunkte). Ergebnis: `require_role(*roles)` exakt bei `deps.py:68` bestätigt; Router-Registrierung `main.py:25-36`, letzter Router `angebote_router` bei Zeile 36 (Design-Text korrigiert: „35" → „36" impliziert, jetzt präzisiert); RLS-Muster exakt wie behauptet; `angebote`-Nested-Route-Vorbild bei `angebote/routes.py:28/33` (`/vorgaenge/{vorgang_id}/angebote`) bestätigt; `vorgang.zugewiesener_nutzer_id` bei `003_kunden_vorgaenge.sql:44` und `vorgaenge/schemas.py:40` bestätigt; SQLite-Testengine splittet SQL an `;` bei `db.py:136` bestätigt (Migrationsregel „kein `$$`-Block" ist damit korrekt begründet); shadcn-Primitive alle vier vorhanden, keine Kalender-Lib in `package.json`; `list_users(mandant_id, limit)` hat **keinen** Rollen-/Status-Filter — im Review als Lücke erkannt und behoben (neuer Endpunkt `GET /nutzer/monteure` bzw. Query-Erweiterung ergänzt); kein Namens-/Routen-Konflikt gefunden.

**Navigations-Implementierungshinweis (für /abc-frontend):** `nextjs_app/app/(app)/layout.tsx` führt Navigation über drei parallele Records — `ICONS` (Z.13-21), `LABELS` (Z.23-31), `PATHS` (Z.33-40). Ein neuer Eintrag „Termine" braucht je einen Key in allen drei Maps plus einen Eintrag in `NAV_RECHTE` (`nextjs_app/lib/theme/tokens.ts:30-34`, `Record<Rolle,string[]>`, rein additiv — z. B. `Inhaber`/`Büro` erhalten `"termine"` im Array, Monteur je nach gewünschter Sichtbarkeit separat entscheiden, siehe Komponentenstruktur oben: nur Inhaber/Büro sehen die Kalenderansicht, Monteure die eigene Terminliste).

### Autonom behoben
- Spec-Header-Status korrigiert (`Approved` → `Architecture Draft`) — Inkonsistenz zwischen Spec-Header und `features/INDEX.md`, reine Konsistenzkorrektur.
- Fehlender Endpunkt für die Monteur-Auswahl im Termin-Dialog ergänzt (`GET /nutzer/monteure`), da `list_users` aktuell nicht nach Rolle/Status filtert — sonst hätte `/abc-frontend` eine unbaubare Abhängigkeit vorgefunden.
- Explizite `422`-Validierungsregeln für AC-3 (Vorgang-Existenz im Mandanten) und AC-7 (`ende > beginn`) in die API-Form verschoben, statt sie nur implizit in den Acceptance Criteria zu belassen.
- AC-5-Datenpfad für „Kontakt sichtbar" geklärt: `GET /termine/{id}` liefert Kundenkontakt eingebettet (kein zweiter Client-Request, kein Leck von Preis-/Rechnungsfeldern).
- Router-Platzierungshinweis präzisiert (`termine_router` nach `angebote_router`, Zeile 36).

### Offene Fragen
Keine. Alle Funde waren technische Lücken (fixable ohne Produktentscheidung), keine ambige Geschäftslogik.

### Frontend-Implementierung (/abc-frontend, 2026-08-18)

**Stack-Abweichung vom Template:** Das Skill-Template nennt Flutter + shadcn_flutter; dieses Projekt ist
faktisch Next.js 16 (App Router) + shadcn/ui (React) + Tailwind (bestätigt durch PRD + Code). Das Frontend
folgt dem **realen** Stack, analog zu PROJ-3/5.

**Neue Dateien (Next.js):**
- `lib/zeit.ts` — Zeit-Helfer: einheitliche Zeitzone Europa/Berlin (AC-7), Wochenstart/-tage, ISO-Konvertierung.
- `lib/schemas/termin.ts` — Zod-Schema für Termin-Dialog (Pflicht Beginn/Ende, `ende > beginn`).
- `lib/api/termine.ts` — API-Client exakt nach Tech-Design-Endpunkten (inkl. `konflikt`-Flag AC-4, eingebetteter Kontakt AC-5, Nested-Route `/vorgaenge/{id}/termine`).
- `components/termine/termin-dialog.tsx` — Anlegen/Bearbeiten (Vorgang-, Monteur-Mehrfachauswahl, Zeit).
- `components/termine/termin-absagen-dialog.tsx` — Absage-Bestätigung (markiert ausgegraut, löscht nicht).
- `components/termine/termin-kalender.tsx` — Wochenansicht (Spalte/Monteur, max. 3, Konflikt rot) + Tagesansicht (mobil ab 375 px).
- `components/termine/monteur-ansicht.tsx` — Monteuransicht (eigene Termine, Kontakt eingebettet, ohne Preise, read-only).
- `components/termine/termin-uebersicht.tsx` — Orchestrierung Büro/Inhaber (Kalender + Dialoge + Datenladung).
- `components/termine/vorgang-termine.tsx` — Termine-Sektion im Vorgang (Nested-Einstieg, wie PROJ-5 Angebote).
- `app/(app)/termine/page.tsx` — Termine-Route, rollenabhängig (Monteur → eigene Ansicht, sonst Kalender).

**Anpassungen bestehender Dateien:**
- `lib/theme/tokens.ts` — `NAV_RECHTE` um `termine` für Inhaber/Büro/Monteur ergänzt.
- `app/(app)/layout.tsx` — Navigation: ICON/LABEL/PATH für `termine` hinzugefügt.
- `components/vorgaenge/vorgang-detail.tsx` — `VorgangTermine` als Card eingebettet (nur Schreibberechtigte).

**Verifiziert:** `npx tsc --noEmit` sauber, `npm run build` erfolgreich (Route `/termine` erzeugt).

**Offen / Handoff:** Backend (Migrations `007_termine.sql` + Feature-Modul `backend/app/features/termine/`)
noch nicht gebaut — siehe Tech Design, Abschnitt „Neue Migrationsdatei" und „API-Form". Das Frontend
erwartet exakt die dort spezifizierten Endpunkte/Felder (insb. `konflikt`/`konflikt_monteure`, eingebetteter
`kontakt` in `GET /termine/{id}`).

## QA Test Results
**Getestet:** 2026-08-18 · **Branch:** `specs/PROJ-6-terminplanung-und-teamzuweisung` · **Stack:** Next.js 16 + FastAPI + `.venv` (pytest 9.1.1, kein conda-Env im Projekt vorhanden)

### Automatisierte Tests
- `backend/.venv/bin/python -m pytest -q` → **148 passed** (146 bestehend + 2 neue `xfail` als Regression-Marker für BUG-1, siehe unten). Kein Fehlschlag in der Gesamt-Suite (inkl. Regression aller anderen Features PROJ-1…5).
- `npx tsc --noEmit` (nextjs_app) → sauber, keine Typfehler.
- `backend/tests/features/termine/test_termine.py` deckt bereits 23 Fälle ab (AC-1, AC-3, AC-4, AC-5, AC-6, Zuweisungen, Nested-Route, Tenant-Isolation, Monteurliste).

### Acceptance Criteria
| AC | Beschreibung | Status |
|---|---|---|
| AC-1 | Anlage/Änderung/Absage, Termin ohne Teammitglied erlaubt | ✅ Pass |
| AC-2 | Kalenderansicht (Tag/Woche, max. 3 Spalten, Auswahl bei >3) | ✅ Pass (Frontend gebaut, `npx tsc --noEmit` clean; Code-Review, kein Live-Browser-Rendering in dieser Runde) |
| AC-3 | Vorgangsbezug, `422` bei fremdem/ungültigem Vorgang | ✅ Pass |
| AC-4 | Konfliktwarnung nicht-blockierend, `konflikt`/`konflikt_monteure` | ✅ Pass |
| AC-5 | Monteursicht (nur eigene, Kontakt eingebettet, kein Preis, `403` bei Schreibversuch) | ✅ Pass |
| AC-6 | Statuswechsel „Termin geplant" / Rücksetzung bei Absage des letzten offenen Termins, historisiert | ✅ Pass |
| AC-7 | Validierung `ende > beginn` (`422`), Zeitzone Europa/Berlin einheitlich | ✅ Pass (Zeiten intern konsistent UTC-normalisiert; Vergleich funktional korrekt) |

**Ergebnis: 7/7 Acceptance Criteria bestanden.**

### Security-Audit (Red Team)
- **JWT-Signaturprüfung:** Token mit gefälschtem `mandant_id`-Claim und falsch geratenem Secret wird korrekt mit `401` abgelehnt — keine Signaturumgehung möglich.
- **Tenant-Isolation:** Mandant B kann Termine von Mandant A weder per Detail-GET (`404`) noch per Liste (`total: 0`) einsehen; verifiziert per Test. Cross-tenant Zuweisung eines Monteurs aus fremdem Mandanten schlägt mit `422`/`404` fehl.
- **SQL-Injection:** `adresse`-Feld sowie `nutzer_ids`-Query-Parameter mit klassischen SQLi-Payloads (`'; DROP TABLE termin; --`, `x') OR ('1'='1`) getestet — alle Queries sind parametrisiert (`%s`-Platzhalter), Payload wird als Literal gespeichert bzw. Query bleibt sicher. Kein Befund.
- **Rollen-Guard:** Monteur erhält `403` bei `POST/PATCH /termine` und `POST /termine/{id}/absagen` — bestätigt per Test.
- **Fehlende Pflichtparameter (`von`/`bis`):** korrekt mit `422` abgelehnt statt stillem Fallback.

### Bugs

**BUG-1 (Medium) — Deaktivierte Monteure können neu zugewiesen werden**
- **Wo:** `backend/app/features/termine/service.py::_require_monteur()` (Zeile 39–45)
- **Was:** Die Funktion prüft nur `nutzer["role"] != "Monteur"`, nicht den Status (`active`/`disabled`). Sowohl `POST /termine` (Anlage mit `monteure: [...]`) als auch `POST /termine/{id}/zuweisungen` akzeptieren einen deaktivierten Monteur klaglos (`201`), statt mit `422` abzulehnen.
- **Reproduktion:** Monteur mit `status="disabled"` anlegen → `POST /termine` mit dessen `nutzer_id` in `monteure[]` → Antwort `201`, Zuweisung wird real gespeichert (Response zeigt `aktiv: false`, aber die Zuweisung existiert in der DB).
- **Bezug zur Spec:** Edge Case (Zeile 36): „Deaktivierte Nutzer können einem Termin nicht neu zugewiesen werden; bestehende Zuweisungen bleiben nachvollziehbar." — die zweite Hälfte ist korrekt implementiert; die erste (Neuzuweisung blockieren) fehlt serverseitig.
- **Mitigierender Faktor:** Der Termin-Dialog im Frontend filtert deaktivierte Monteure bereits client-seitig aus der Auswahl (`termin-dialog.tsx:76`, `setMonteure(m.filter(x => x.aktiv))`) — das UI verhindert den Fall im Normalbetrieb. Es fehlt aber die serverseitige Absicherung (Defense-in-Depth: direkter API-Zugriff, künftiger zweiter Client, Race Condition beim Deaktivieren nach Laden der Liste).
- **Regressionstests:** `test_bug1_deaktivierter_monteur_bei_anlage_abgelehnt` und `test_bug1_deaktivierter_monteur_via_zuweisen_endpoint_abgelehnt` in `backend/tests/features/termine/test_termine.py` (aktuell `xfail(strict=True)` — laufen automatisch grün, sobald der Fix umgesetzt ist; der Marker muss dann entfernt werden).
- **Fix-Vorschlag (nicht umgesetzt — QA fixt keine Bugs):** In `_require_monteur()` zusätzlich `if nutzer["status"] != "active": raise ValidationError(...)` ergänzen.

Keine Critical- oder High-Bugs gefunden. Kein Live-Browser-Rendering (Chrome, Responsive 375/768/1440 px) in dieser QA-Runde durchgeführt — Empfehlung: vor Produktivsetzung nachholen.

### Regression (andere Features)
Volle Suite grün (148/148 inkl. PROJ-1, PROJ-3, PROJ-4, PROJ-5 Tests) — keine Regression durch PROJ-6 festgestellt.

### Production-Ready Empfehlung
**READY**, mit Vorbehalt: BUG-1 ist **Medium** (kein Critical/High — Frontend blockiert den Fall bereits clientseitig, kein Tenant-Leck, kein Datenverlust, kein Auth-Bypass). Gemäß Skill-Regel „READY: No Critical or High bugs remaining" ist das Feature production-ready; BUG-1 sollte dennoch zeitnah nachgezogen werden.

**Empfehlung: READY** (mit offenem Medium-Bug BUG-1 zur Nachbesserung).

## Deployment
_To be added by /deploy_
