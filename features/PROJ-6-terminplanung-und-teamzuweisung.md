# PROJ-6: Terminplanung und Teamzuweisung

## Status: Approved
**Created:** 2026-08-16
**Last Updated:** 2026-08-18

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
- Router-Registration erfolgt zentral in `backend/app/main.py:25-36` via `app.include_router(...)`.
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
- `POST /termine` → Termin anlegen (Vorgang, Beginn, Ende, Adresse optional, Notiz, Monteure[]).
- `GET /termine/{id}` → einen Termin mit seinen Zuweisungen lesen.
- `PATCH /termine/{id}` → Termin ändern/verschieben; Antwort enthält bei Überschneidung `konflikt: true` mit Liste betroffener Monteure.
- `POST /termine/{id}/absagen` → Termin absagen (kein hartes Löschen; bleibt in Historie).
- `POST /termine/{id}/zuweisungen` und `DELETE /termine/{id}/zuweisungen/{nutzer_id}` → Monteur zuweisen/entziehen.
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

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
