# PROJ-22: Gewerke – Kalkulationseinheiten für Angebote

## Status: Approved
**Created:** 2026-08-24
**Last Updated:** 2026-08-24 (Re-QA: READY — alle Bugs verifiziert gefixt)

## Dependencies
- Requires: PROJ-3 (Kunden, Objekte, Projekte und Dokumente) — Angebote sind einem Projekt zugeordnet.
- Requires: PROJ-5 (Angebote: Positionen, PDF, Freigabe und Versand) — Gewerke werden als Angebotspositionen verwendet.
- Integrates with: PROJ-14 (Branchenpaket-Konfiguration) — Branchenvorlagen liefern Kategorien und Beispiel-Gewerke.

## Scope

Ein Gewerk ist eine wiederverwendbare Kalkulationseinheit für eine Leistung. Es besteht aus Kostenzeilen der festen Kostenarten Lohn, Material, Fremdleistung und Sonstiges/Geräte. Je Kostenart wird aus Einkaufspreis und Zuschlag der Verkaufspreis berechnet. Gewerke können je Bezugseinheit oder als Gesamtpreis kalkuliert und als Position in ein Angebot übernommen werden.

V1 enthält Branchenvorlagen und manuelle Katalogpflege. GAEB-, Datanorm-, CSV- oder Excel-Import sowie Nachkalkulation gehören nicht zum Feature.

## User Stories
- Als Inhaber möchte ich Kategorien und Gewerke für meinen Betrieb anlegen und pflegen, damit wiederkehrende Leistungen nicht für jedes Angebot neu kalkuliert werden müssen.
- Als Inhaber oder Büro möchte ich einem Gewerk Kostenzeilen für Lohn, Material, Fremdleistung und Sonstiges/Geräte mit Zuschlägen hinzufügen, damit sein Verkaufspreis nachvollziehbar berechnet wird.
- Als Inhaber oder Büro möchte ich ein Gewerk mit Menge in ein Angebot übernehmen, damit daraus eine Angebotsposition mit Einheit, Beschreibung, Einzel- und Gesamtpreis entsteht.
- Als Inhaber oder Büro möchte ich den kalkulierten Verkaufspreis einer Angebotsposition überschreiben und intern begründen, damit begründete Pauschalpreise möglich sind und die Abweichung nachvollziehbar bleibt.
- Als Inhaber oder Büro möchte ich eine negative Angebotsposition anlegen, damit Wertanrechnungen und Rabatte die Angebotssumme mindern können.

## Acceptance Criteria
- [ ] Inhaber und Büro können in ihrem Mandanten Kategorien sowie Gewerke mit Kurzbeschreibung, optionaler Langbeschreibung, Einheit und Kalkulationsart „je Einheit" oder „Gesamtpreis" anlegen, ändern und löschen.
- [ ] Ein Gewerk enthält eine oder mehrere Kostenzeilen der festen Kostenarten Lohn, Material, Fremdleistung oder Sonstiges/Geräte; jede Kostenzeile enthält Menge, Einheit, Einkaufspreis und einen Zuschlag in Prozent.
- [ ] Das System berechnet je Kostenzeile den Verkaufspreis als `Einkaufspreis + (Einkaufspreis × Zuschlag)` und zeigt daraus Preis je Einheit bzw. Gesamtpreis des Gewerks an.
- [ ] Beim Übernehmen eines Gewerks in ein Angebot werden Bezeichnung, Einheit, kalkulierter Einzelpreis und Gesamtpreis vorausgefüllt; Änderungen am Katalog verändern bereits übernommene Angebotspositionen nicht.
- [ ] Inhaber und Büro können den Verkaufspreis einer Angebotsposition ändern; vor dem Speichern ist eine interne Begründung erforderlich. Die Begründung und der ursprüngliche kalkulierte Wert sind intern am Angebot nachvollziehbar und erscheinen nicht im PDF.
- [ ] Angebotspositionen dürfen negative Einzel- oder Gesamtpreise haben; Nettosumme, Umsatzsteuer und Bruttosumme werden korrekt einschließlich negativer Positionen berechnet.
- [ ] Beim Speichern eines Gewerks mit gleicher Bezeichnung und Einheit im selben Katalog zeigt das System eine Warnung, erlaubt das Speichern nach Bestätigung jedoch weiterhin.
- [ ] Gewerke, Kostenzeilen, Preis-Overrides und ihre internen Begründungen sind strikt auf den jeweiligen Mandanten beschränkt.
- [ ] Bei nicht erreichbarer API zeigt die Oberfläche die Fehlermeldung „Keine Verbindung zum Server. Änderungen wurden nicht gespeichert."; Offline-Bearbeitung und spätere Synchronisierung sind nicht Teil von V1.

## Edge Cases
- Ein Gewerk ohne Kostenzeile kann nicht gespeichert werden; die Oberfläche zeigt „Mindestens eine Kostenzeile ist erforderlich.".
- Ein negativer Preis ist nur für Angebotspositionen erlaubt; Kostenzeilen eines Gewerks dürfen keinen negativen Einkaufspreis haben.
- Menge, Einkaufspreis und Zuschlag müssen gültige Zahlen sein; Mengen und Einkaufspreise müssen größer als null sein, der Zuschlag darf nicht negativ sein.
- Wird eine verwendete Katalogposition geändert oder gelöscht, bleiben frühere Angebotspositionen unverändert; neue Übernahmen verwenden den aktuellen Katalogstand.
- Fällt die Verbindung während einer Änderung aus, wird nichts als gespeichert dargestellt und die Eingabe wird nicht automatisch synchronisiert.
- Ein Zugriff auf Katalog- oder Angebotsdaten eines anderen Mandanten wird abgewiesen und liefert keine Daten.

## Non-Goals
- Keine Importfunktion für GAEB, Datanorm, CSV, Excel oder Großhändlerdaten.
- Keine Nachkalkulation, Soll-Ist-Vergleiche, Lager- oder Materialwirtschaft.
- Keine frei definierbaren Kostenarten.
- Keine Anzeige des Preis-Overrides oder seiner Begründung im Kunden-PDF.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-24 · **Stack:** Next.js 16/shadcn-artige UI, FastAPI, PostgreSQL raw SQL + RLS, MinIO, Dokploy · **Branch:** main

### Zielbild und Anschluss an bestehenden Code

PROJ-22 ist ein Aufsatz auf das bestehende Angebotsmodell, kein neues
Dokumentensystem. `angebot_position` enthält heute bereits Menge, Einheit,
Einzelpreis, Steuer, Rabatt und Sortierung (`backend/sql/006_angebote.sql:38-51`);
das Angebot berechnet seine Summen aus diesen Snapshots
(`backend/app/features/angebote/service.py:48-85`). Das Gewerk ergänzt nur den
Weg, einen nachvollziehbar kalkulierten Snapshot zu erzeugen. Spätere
Katalogänderungen ändern weder Position, Summen noch PDF eines bestehenden
Angebots.

Die kleinste vollständige Lösung hat drei neue Katalogtabellen und erweitert
die bestehende Angebotsposition um Kalkulations-/Override-Nachweise. Es gibt
keinen Materialkatalog, keine freien Kostenarten, keine Importfunktion und
keine neue Flutter-Fläche. Die vorhandene einfache `preisliste` wird nicht
parallel weitergeführt: ihre vorhandenen Datensätze werden einmalig als
Gewerke mit einer Kostenzeile `sonstiges_geraete`, EK gleich bisherigem Preis
und 0 % Zuschlag übernommen. Danach ersetzt der Gewerkekatalog deren UI und
Contract. So bleiben Bestandsangebote unverändert und es entstehen keine zwei
Wahrheiten für Preise.

### Flächen und Komponenten

```text
Kalkulation (neue Next.js-Seite, Inhaber/Büro)
├── Kategorie-Liste
├── Gewerkeliste mit Suche, Einheit und kalkuliertem Verkaufspreis
├── Gewerk-Editor
│   ├── Kurz-/Langbeschreibung, Kategorie, Einheit, Kalkulationsart
│   ├── Kostenzeilen Lohn | Material | Fremdleistung | Sonstiges/Geräte
│   └── Preiszusammenfassung je Zeile und Gewerk
└── Löschen- und Duplikatwarnung

Bestehendes Vorgangsdetail > Angebot-Editor
├── „Gewerk übernehmen“-Dialog: Kategorie/Suche, Menge, Preisvorschau
├── bestehende Positionstabelle mit Kennzeichnung „kalkuliert/Preis angepasst“
└── Preis-anpassen-Dialog mit Pflichtfeld „interne Begründung“
```

Die vorhandene manuelle Position bleibt verfügbar; sie ist für freie und
negative Positionen gedacht. Der neue Gewerk-Dialog ergänzt sie. Beide Flächen
nutzen die vorhandenen Next.js-/shadcn-artigen Komponenten und zeigen bei jedem
fehlgeschlagenen Schreibaufruf exakt „Keine Verbindung zum Server. Änderungen
wurden nicht gespeichert.“; es gibt keinen Offline-Puffer.

### Datenmodell, Owner und Lesepfade

Alle geschäftlichen Tabellen tragen `mandant_id`. FastAPI gewinnt ihn aus der
Sitzung zum JWT-`sub`, nie aus einem Request-Feld (`backend/app/deps.py:71-104`).
Jede Repository-Abfrage filtert zusätzlich nach `mandant_id`; PostgreSQL-RLS
begrenzt jede Tabelle auf `app.current_mandant_id`, das die DB-Schicht pro
Transaktion setzt (`backend/app/db.py:40-103`). Alle hier genannten geschützten
Pfade erlauben nur `Inhaber` oder `Buero`; `Monteur` erhält weder Katalog- noch
Angebotskalkulationszugriff.

| Entität | Inhalt und Regeln | Schreiber / Owner | Nötige Lesepfade |
|---|---|---|---|
| `gewerk_kategorie` (neu) | Mandanteneigener Name; Löschen nur, wenn kein Gewerk zugeordnet ist. | `POST/PATCH/DELETE /gewerke/kategorien/{id}`, Inhaber/Büro. Initial zusätzlich atomare Paketübernahme durch `POST /onboarding/branchenpaket-uebernehmen`. | `GET /gewerke/kategorien` vor Anlegen/Bearbeiten eines Gewerks und im Übernahme-Dialog zum Filtern. |
| `gewerk` (neu) | Kategorie, Bezeichnung, optionale Langbeschreibung, Einheit, `kalkulationsart` `je_einheit` oder `gesamtpreis`, berechnete Preisprojektion. Gleiche Bezeichnung plus Einheit im selben Mandanten erzeugt nur eine bestätigungspflichtige Warnung, keinen Konflikt. Ohne mindestens eine Kostenzeile nicht speicherbar. | `POST/PATCH/DELETE /gewerke/{id}`, Inhaber/Büro; Paketübernahme ist alleiniger Initial-Owner der Vorlagen. | `GET /gewerke?suchbegriff=&kategorie_id=` für Liste/Übernahme; `GET /gewerke/{id}` vor Edit, Delete und Preisvorschau. |
| `gewerk_kostenzeile` (neu) | Gehört genau zu einem Gewerk: feste `kostenart` Lohn/Material/Fremdleistung/Sonstiges-Geräte, Menge > 0, Einheit, EK-Einzelpreis > 0, Zuschlag >= 0. Kein negativer EK, keine freie Kostenart. | Nur der Gewerk-Editor schreibt sie als vollständigen Satz innerhalb von `POST/PATCH /gewerke`; keine lose Kostenzeilenroute. Paketübernahme schreibt sie nur im selben atomaren Initialvorgang. | `GET /gewerke/{id}` lädt Kostenzeilen vor Gewerk-Edit und beim Prüfen der Preisvorschau; der Angebotsdialog liest nur die daraus berechnete Gewerkprojektion. |
| `angebot` (bestehend) | Unverändert: Kopf, Status und gespeicherte Netto-/Steuer-/Bruttosummen. | Bestehende Angebotsendpunkte bleiben Owner (`POST /vorgaenge/{id}/angebote`, `PATCH /angebote/{id}`, Freigabe/Versand). | Bestehende `GET /vorgaenge/{id}/angebote` vor Auswahl und `GET /angebote/{id}` vor jeder Positionsänderung/Freigabe. |
| `angebot_position` (bestehend, erweitert) | Bleibt der vollständige Beleg-Snapshot. Neu: nullable `kalkulierter_einzelpreis` und nullable `preis_override_begruendung`. Gewerkübernahme setzt den kalkulierten Wert; bei abweichendem Verkaufspreis ist die Begründung Pflicht. Manuelle Positionen haben keinen kalkulierten Ausgangswert. Negative Einzelpreise sind nur hier zulässig. | Bestehendes manuelles `POST/PATCH/DELETE /angebote/{id}/positionen/{id}` bleibt Owner; neu `POST /angebote/{id}/positionen/aus-gewerk` erzeugt den Snapshot. Alle nur im Entwurf durch Inhaber/Büro. | `GET /angebote/{id}` vor Edit, Override, Delete, Freigabe und PDF; der interne Angebotseditor liest Kalkulationswert/Begründung, PDF-Renderer erhält ausschließlich Bezeichnung, Menge, Einheit, tatsächlichen Preis und Steuer. |
| `preisliste` (bestehend, abgelöst) | Nur Migrationsquelle; nach Übernahme keine Katalog-UI und kein neuer Fachschreiber mehr. | Einmaliger Migrationsschreiber in `014_gewerke.sql`; frühere Zeilen werden dabei zu Gewerken. Die alten `/katalog*`-Schreibpfade und CSV-Import entfallen, weil sie V1-Import wieder einführen würden. | Migration liest `preisliste`; Onboarding ersetzt in seinem Duplikatschutz `count_preisliste` durch `count_gewerke`. Kein Runtime-Lesepfad nach Umstellung. |
| `BranchenpaketVorlage` (bestehendes Release-Artefakt, keine DB-Tabelle) | Versionierte SHK-/Entrümpelungs-Kategorien, Gewerke und Kostenzeilen. | Produktentwicklung beim Release; Runtime nur der einmalige Paketübernahme-Endpunkt. | `GET /onboarding/branchenpakete` zeigt weiter nur Wahltexte; der Übernahmeweg liest vollständige Vorlage serverintern. |

### Rechen- und Snapshot-Regeln

- Je Kostenzeile gilt auf zwei Dezimalstellen: `VK = EK + (EK × Zuschlag / 100)`.
  Der Gewerkpreis ist die Summe der Zeilen-VK. Bei `je_einheit` ist er der
  Angebots-Einzelpreis; bei `gesamtpreis` wird eine Angebotsposition mit Menge
  1 angelegt und derselbe Wert ist ihr Einzel-/Gesamtpreis.
- Ein Gewerk wird erst nach mindestens einer gültigen Kostenzeile gespeichert.
  Alle Prüfungen liegen serverseitig; die UI spiegelt sie nur.
- `POST .../aus-gewerk` kopiert Bezeichnung, Langbeschreibung soweit im
  Angebotseditor vorgesehen, Einheit, Steuersatz, kalkulierten Einzelpreis und
  tatsächlichen Einzelpreis in die Angebotsposition. Es speichert keine
  Live-Referenz auf das Gewerk; daher bleiben Änderungen und Löschen im Katalog
  ohne Rückwirkung.
- Ändert ein Nutzer bei einer kalkulierten Entwurfsposition den tatsächlichen
  Einzelpreis, verlangt der Server eine nichtleere interne Begründung und
  speichert Ausgangswert plus Begründung. Wird exakt auf den kalkulierten Wert
  zurückgestellt, werden beide Override-Felder geleert. Rabatt bleibt die
  bestehende, separate Angebotsfunktion.
- Negative Preise sind bei manuellen Angebotspositionen erlaubt. Die bestehende
  Angebotsvalidierung und Summenberechnung müssen dafür `einzelpreis < 0`
  akzeptieren und Netto, Steuer sowie Brutto mit negativem Vorzeichen rechnen.
  Kostenzeilen bleiben stets positiv.

### API-Contracts

Alle Antworten und Fehler folgen den vorhandenen FastAPI-Contracts; bei fremder
oder fehlender Mandantenressource liefert der Pfad keine Daten bzw. `404`.
Alle Schreibpfade prüfen Angebotsstatus `entwurf` wie heute
(`backend/app/features/angebote/service.py:30-34`).

- `GET /gewerke/kategorien` — Kategorien des aktuellen Mandanten.
- `POST /gewerke/kategorien`, `PATCH /gewerke/kategorien/{id}`, `DELETE /gewerke/kategorien/{id}` — Kategoriewartung; nichtleere Kategorie: `409`.
- `GET /gewerke?suchbegriff=&kategorie_id=` — paginierte, filterbare Gewerkeliste mit Einheit, Art und berechnetem Verkaufspreis.
- `POST /gewerke`, `GET /gewerke/{id}`, `PATCH /gewerke/{id}`, `DELETE /gewerke/{id}` — kompletter Gewerk-Contract einschließlich Kostenzeilen. Doppelter Name/Einheit liefert eine Warnungsinformation; erst `duplikat_bestaetigt=true` erlaubt den sonst gültigen Write.
- `POST /angebote/{angebot_id}/positionen/aus-gewerk` — nimmt `gewerk_id`, Menge und Sortierung; liest das Gewerk im aktuellen Mandanten, erzeugt einen Snapshot und liefert das aktualisierte Angebotsdetail. Ungültige Menge, fehlendes Gewerk oder nicht-Entwurf: `422`/`404`/`409`.
- Bestehendes `POST/PATCH /angebote/{angebot_id}/positionen` erweitert sein Lesemodell um `kalkulierter_einzelpreis`, `preis_override_begruendung` und Kennzeichnung `preis_angepasst`. PATCH verlangt Begründung nur bei einer Abweichung von vorhandenem kalkulierten Wert. Seine Preisvalidierung erlaubt negative Werte; Menge bleibt > 0.
- `GET /angebote/{angebot_id}` liefert die internen Override-Felder nur an angemeldete Inhaber/Büro. `GET /angebote/{id}/pdf`, Freigabe und Versand verwenden unverändert die Position-Snapshots, aber niemals interne Override-Begründungen.

### Migration, Branchenpakete und Auslieferungsreihenfolge

1. Neue idempotente raw-SQL-Migration `backend/sql/014_gewerke.sql` nach
   `013_branchenpakete.sql`: drei neue RLS-Tabellen, Erweiterung von
   `angebot_position`, Indizes auf `(mandant_id, kategorie_id)` und
   `(mandant_id, bezeichnung, einheit)`, jeweils Policies wie in
   `006_angebote.sql:54-69`.
2. Sie migriert jede bestehende `preisliste`-Zeile als beschriebenes
   Null-Zuschlag-Gewerk und lässt historische Angebotspositionen unverändert.
   Danach werden alte `/katalog`-Routen/UI/CSV-Import entfernt und der
   Onboarding-Status zählt Gewerke. Keine Daten werden stillschweigend gelöscht.
3. PROJ-14 erweitert seine vorhandene atomare Übernahme von Preislisten
   (`onboarding/service.py:418-433`) auf Kategorien, Gewerke und Kostenzeilen.
   Im selben Change erweitert `uebernehmen_branchenpaket` den Konflikt-Guard
   `onboarding/service.py:406-408`: `repo.count_gewerke(mandant_id) > 0`
   ersetzt dort `repo.count_preisliste(mandant_id) > 0` (nicht zusätzlich). So
   kann ein Mandant mit manuell angelegten Gewerken kein zweites Paket übernehmen;
   der abgelöste Preislistenbestand bleibt kein relevanter Zielinhalt mehr. Die
   Paketvorlagen enthalten echte positive Kostenzeilen; es gibt keinen zweiten
   Seed-Pfad und keine Übernahme in schon gefüllte Mandanten.
4. Backend-Routen, bestehender Angebots-Contract und Next.js-Katalogseite
   liefern gemeinsam aus. Danach prüfen QA insbesondere RLS, Snapshot-Stabilität,
   Override-Unsichtbarkeit im PDF, negative Positionen und Offline-Fehler.

MinIO und Dokploy erhalten keine neue Fachintegration: Dieses Feature speichert
keine Binärdaten. Bestehende Angebot-PDFs bleiben im aktuellen MinIO-Pfad.
Keine neuen Packages nötig.

### Architekturentscheidungen (ADRs)

- **ADR-22-1: Gewerk mit eingebetteten Kostenzeilen, kein Materialstamm.** Die
  Spec verlangt Kostenarten, nicht Lager- oder Artikelverwaltung. Eingebettete
  Zeilen erfüllen V1 ohne nicht verlangte Materialreferenzen.
- **ADR-22-2: Angebot speichert Snapshot statt Gewerkreferenz.** Katalogpflege
  darf nie historische Angebote oder PDFs verändern; der kleinste sichere Weg
  ist ein vollständiger Positionssnapshot.
- **ADR-22-3: Override auf bestehender Position.** Zwei zusätzliche
  Nachweisfelder reichen für Ausgangswert und Begründung. Eine neue
  Preisänderungs-Historie wäre ohne Anforderung zusätzliche Komplexität.
- **ADR-22-4: Bestehende Preisliste gezielt ablösen.** Ihr flacher Preis-Contract
  kann keine Kostenkalkulation ausdrücken. Einmalige Migration vermeidet
  Datenverlust und parallele Kataloge; CSV/Excel/GAEB bleiben Non-Goals.
- **ADR-22-5: RLS plus Repository-Scope.** Mandant aus JWT/Sitzung und DB-RLS
  bleiben doppelte Sicherheitsgrenze, passend zu bestehenden Angebotsdaten.

### Codebezug für Umsetzung und Review

- Angebotsrouten schützen heute alle Lese-/Schreibpfade mit
  `require_role("Buero", "Inhaber")` (`backend/app/features/angebote/routes.py:9-12`);
  PROJ-22 übernimmt diesen Guard.
- Die aktuelle `PositionCreate/Update`-Validierung verbietet negative Preise
  (`backend/app/features/angebote/schemas.py:22-41`) und ist gezielt zu ändern.
- Der aktuelle Angebotseditor hat nur manuelles `PositionForm` und muss um den
  Gewerk-Dialog ergänzt werden (`nextjs_app/components/angebote/vorgang-angebote.tsx:165-261`).
- Der aktuelle `/katalog`-Contract und der Onboarding-Schritt sind ein
  Ablöse-Hotspot (`nextjs_app/lib/api/katalog.ts:12-85`,
  `backend/app/features/onboarding/routes.py:73-96`); sie dürfen nicht neben
  dem neuen Gewerkekatalog weiter Preise schreiben.

## QA Test Results
**Datum:** 2026-08-24 · **Tester:** jupiter-qa · **Branch:** specs/PROJ-22-gewerke-kalkulationseinheiten

### Testumfang
- Backend: `backend/.venv/bin/python -m pytest` (kein conda-Env in diesem Projekt) → 273/273 grün.
- Frontend: `npm run typecheck` (tsc --noEmit) grün, `npm run build` grün, Route `/gewerke` generiert.
- Code-Review Backend (routes/service/repository/schemas/SQL-Migration) + Frontend (gewerke-Komponenten, API-Clients, Angebots-Integration).
- Kein laufender Server verfügbar für abc-qa-e2e-Browser-Smoke in diesem Lauf — Fokus auf Code-Verifikation + bestehende Testsuite; s. Empfehlung unten.

### Acceptance Criteria
| # | Kriterium | Status |
|---|---|---|
| 1 | Kategorien + Gewerke CRUD (Kurz-/Langbeschreibung, Einheit, Kalkulationsart) | ✅ PASS (Backend vollständig; Kategorie-Anzeige im Frontend s. BUG-3) |
| 2 | Kostenzeilen mit fester Kostenart, Menge, Einheit, EK, Zuschlag | ✅ PASS |
| 3 | VK-Berechnung `EK + EK×Zuschlag%` je Zeile, Summierung zu Einheit-/Gesamtpreis | ✅ PASS (test_gewerk_erstellen_und_vk_berechnung, test_gewerk_gesamtpreis_art) |
| 4 | Übernahme in Angebot: Bezeichnung/Einheit/Preis vorausgefüllt, Snapshot ohne Live-Ref | ⚠️ TEILWEISE — Backend/Snapshot-Logik korrekt (test_position_aus_gewerk_snapshot), aber UI-Override-Button ist funktional unerreichbar, siehe BUG-1 |
| 5 | Preis-Override mit Begründungspflicht, intern sichtbar, nicht im PDF | ⚠️ TEILWEISE — Backend + PDF-Template korrekt (Begründung fehlt im Template komplett), aber UI-Trigger blockiert, siehe BUG-1 |
| 6 | Negative Einzel-/Gesamtpreise bei Angebotspositionen, korrekte Summenbildung | ✅ PASS (test_manuelle_position_negative_preise_erlaubt; `_totals` verarbeitet negative Werte arithmetisch korrekt) |
| 7 | Duplikat-Guard: gleiche Bezeichnung+Einheit → Warnung, Speichern nach Bestätigung möglich | ✅ PASS (test_gewerk_duplikat_guard, 409 + duplikat_bestaetigt) |
| 8 | Mandanten-Isolation für Gewerke/Kostenzeilen/Override/Begründung | ✅ PASS (test_gewerk_mandanten_isolation; RLS in 014_gewerke.sql + App-Layer-Filter; Hinweis: RLS nur produktionswirksam, Testsuite läuft auf SQLite) |
| 9 | Offline-Fehlermeldung „Keine Verbindung zum Server. Änderungen wurden nicht gespeichert.“ | ❌ FAIL — Fehlerbehandlung im Frontend ist invertiert, siehe BUG-2 |

**Ergebnis: 6/9 PASS, 3/9 mit Bugs (1 Critical, 2 High).**

### Bugs

**BUG-1 (Critical) — Preis-Override in der UI nie erreichbar, weil Backend-Contract-Feld `aus_gewerk` fehlt.**
`nextjs_app/lib/api/angebote.ts:20` definiert `AngebotPosition.aus_gewerk: boolean`, und `vorgang-angebote.tsx:141,147,164` rendert Badge „Gewerk“ sowie den einzigen Button, der `PositionOverride` öffnet (`onOverrideStarten`), ausschließlich wenn `p.aus_gewerk` truthy ist. Das Backend-`PositionRead`-Schema (`backend/app/features/angebote/schemas.py:46-60`) hat **kein** Feld `aus_gewerk` — weder im Response-Model noch in `_position_read()` (`backend/app/features/angebote/service.py:83-91`). `aus_gewerk` existiert im Backend nur als Funktionsname (`add_position_aus_gewerk`), nie als Response-Feld. Folge: JSON liefert `aus_gewerk: undefined` → im Frontend immer falsy → Override-Button und „Gewerk“-Badge erscheinen nie, selbst für per Gewerk-Snapshot erzeugte Positionen. AC4 (Herkunftskennzeichnung) und AC5 (Preisanpassung mit Begründung) sind dadurch über die UI **nicht nutzbar**, obwohl Backend-API und Berechnungslogik korrekt sind (per curl/pytest direkt erreichbar).
Fix-Vorschlag: `PositionRead` um `aus_gewerk: bool` ergänzen (z. B. `kalkulierter_einzelpreis is not None`), `_position_read()` entsprechend füllen.

**BUG-2 (High) — Offline-Fehlermeldung in allen 4 Gewerke-Frontend-Komponenten invertiert.**
`gewerk_editor.tsx:176`, `kategorie_verwaltung.tsx` (mehrere Stellen), `gewerk_uebernahme.tsx:44,76`, `position_override.tsx:55` prüfen jeweils `err instanceof ApiError ? SERVER_FEHLER : "..."`. `lib/api/client.ts` wirft aber bei **jedem** erfolgreichen Request/Response-Zyklus mit Nicht-2xx-Status (validierte Serverantwort, z. B. 422/409/404) eine `ApiError` — das ist der Normalfall für erwartete Validierungsfehler. Ein echter Netzwerkausfall (kein `fetch`-Response, z. B. `TypeError: Failed to fetch`) ist dagegen **keine** `ApiError`, sondern ein generischer `Error`/`TypeError`. Die Bedingung ist verkehrt herum: Bei jedem normalen Server-Validierungsfehler (z. B. Pflichtfeld leer, Duplikat ohne Bestätigung außerhalb des expliziten 409-Zweigs) zeigt die UI fälschlich „Keine Verbindung zum Server. Änderungen wurden nicht gespeichert.“ statt der eigentlichen serverseitigen Fehlermeldung; bei einem echten Verbindungsabbruch erscheint dagegen die falsche generische Meldung („... konnte nicht gespeichert werden.“) statt der geforderten Offline-Meldung. AC9 damit sowohl in die eine als auch die andere Richtung verletzt.
Fix-Vorschlag: Bedingung umdrehen (`!(err instanceof ApiError) ? SERVER_FEHLER : err.message`), konsistent mit dem Muster in bereits deployten Features prüfen (z. B. `position-form.tsx`, falls dort korrekt gelöst).

**BUG-3 (High) — `GewerkKategorie.anzahl_gewerke` wird vom Backend nie geliefert.**
`nextjs_app/lib/api/gewerke.ts:67` deklariert `anzahl_gewerke: number` als Pflichtfeld, `kategorie_verwaltung.tsx:165` rendert `({k.anzahl_gewerke})` in der Kategorie-Sidebar. Backend `KategorieRead` (`backend/app/features/gewerke/schemas.py:34-36`) hat nur `id, name`; `repo.list_kategorien()` selektiert nur `KATEGORIE_COLS = "id, mandant_id, name, created_at, updated_at"` ohne COUNT/JOIN gegen `gewerk`. Verifiziert per direktem Schema-Test: `KategorieRead(id="x", name="Heizung").model_dump()` → `{'id': 'x', 'name': 'Heizung'}`, kein `anzahl_gewerke`. Folge: UI zeigt `(undefined)` statt der Gewerkeanzahl neben jedem Kategorienamen — kein funktionaler Blocker, aber sichtbarer Rendering-Fehler auf jeder Kalkulationsseite.
Fix-Vorschlag: Backend `list_kategorien` um `COUNT(gewerk.id)`-Join erweitern und `KategorieRead.anzahl_gewerke` ergänzen.

### Security-Red-Team
- Cross-Tenant-Zugriff auf Gewerke/Positionen: verifiziert 404 statt Datenleck (test_gewerk_mandanten_isolation).
- RLS-Policies auf allen 3 neuen Tabellen vorhanden (`014_gewerke.sql`), Muster identisch zu bestehenden Tabellen (006/008); Testsuite läuft auf SQLite ohne RLS — Produktions-Verifikation gegen echtes Postgres wird empfohlen, aber nicht blockierend (App-Layer-Filterung zusätzlich vorhanden, alle Repository-Queries filtern nach `mandant_id`).
- Preis-Override-Begründung wird im PDF-Template (`templates/angebot_pdf.html`) nicht gerendert — kein Datenleck an Kunden bestätigt.
- Kostenzeilen: negativer EK durch Pydantic (`gt=0`) + DB-CHECK doppelt abgesichert; kein Bypass über PATCH gefunden (`GewerkUpdate.kostenzeilen` nutzt dieselbe `KostenzeileBase`).
- Rollen-Guard: alle `/gewerke*`-Routen und die neuen `/angebote/*`-Routen nutzen `require_role("Buero", "Inhaber")` konsistent mit bestehendem PROJ-5-Muster; Monteur erhält keinen Zugriff.
- Kein SQL-Injection-Risiko gefunden — durchgehend parametrisierte Queries.

### Regression
- Volle Backend-Suite (273 Tests inkl. onboarding/branchenpaket/angebote/rechnungen/website) grün — keine Regression durch die preisliste→gewerke-Ablösung.
- Frontend-Build unverändert grün, alle bestehenden Routen weiterhin generiert.
- `/katalog`-Backend-Routen vollständig entfernt; Frontend `lib/api/katalog.ts` ist tote Datei (kein Import mehr, nur `.tsbuildinfo`-Reste) — Low-Bug, keine Aktion erforderlich, kann bei Gelegenheit gelöscht werden.

### Empfehlung
**NOT READY.** 1 Critical (BUG-1, macht AC4/AC5 in der UI unbenutzbar) + 2 High (BUG-2 Fehlermeldungslogik, BUG-3 Kategorie-Anzeige) offen. Rückgabe an Frontend zur Fix-Runde, danach Re-Verifikation durch QA.

## Re-QA Test Results (Fix-Verifikation)
**Datum:** 2026-08-24 · **Tester:** jupiter-qa · **Branch:** specs/PROJ-22-gewerke-kalkulationseinheiten

### Testumfang
- Backend: `backend/.venv/bin/python -m pytest` (venv aus Haupt-Repo, Worktree hat kein eigenes `.venv`) → **275/275 grün**, keine Regression.
- Frontend: `npm run typecheck` (tsc --noEmit) grün, `npm run build` grün, Route `/gewerke` weiterhin generiert.
- Eigener unabhängiger API-Testlauf (nicht nur bestehende Suite übernommen): temporärer pytest-Test direkt gegen `TestClient` schreibt Kategorie an, legt Gewerk an, übernimmt es in ein Angebot, liest `PositionRead`- und `KategorieRead`-JSON zurück — Test nach Verifikation wieder entfernt (nicht Teil der permanenten Suite, redundant zu den vom Backend-Worker bereits committeten Regressionstests `test_position_aus_gewerk_setzt_aus_gewerk_flag` und `test_kategorie_liste_liefert_anzahl_gewerke`).
- Code-Review der 8 Frontend-Fehlerbehandlungsstellen (BUG-2) einzeln nachgezählt und Bedingung geprüft.
- Kein laufender Server verfügbar (keine SEED-Postgres-Instanz in diesem Environment) — wie im Vorlauf Fokus auf Code-Verifikation + eigenem API-Testlauf statt Browser-Smoke; für BUG-1/BUG-3 ausreichend, da beide reine Datenkontrakt-Bugs sind und die Frontend-Bedingung (`p.aus_gewerk`, `k.anzahl_gewerke`) bereits im Code als korrekt verifiziert ist — sobald das Backend das Feld liefert, ist die UI-Kette geschlossen.

### Re-Test der offenen Punkte
| Bug | Re-Test | Ergebnis |
|---|---|---|
| BUG-1 (Critical) — `aus_gewerk` fehlt in `PositionRead` | Eigener API-Call: Gewerk in Angebot übernommen, JSON-Response von `POST /angebote/{id}/positionen/aus-gewerk` geprüft. `schemas.py:63` hat jetzt `aus_gewerk: bool = False`, `service.py:92` setzt `"aus_gewerk": kalkuliert is not None`. | ✅ FIXED — `aus_gewerk: true` im Response bestätigt. Frontend-Bedingungen `vorgang-angebote.tsx:141,147,164` (`p.aus_gewerk`) sind unverändert korrekt und greifen jetzt. AC4/AC5 damit über die UI erreichbar. |
| BUG-2 (High) — invertierte Fehlerbehandlung | Alle 8 Stellen einzeln per Grep nachgezählt: `gewerk_uebernahme.tsx` (2), `gewerk_editor.tsx` (1), `kategorie_verwaltung.tsx` (4), `position_override.tsx` (1). Jede prüft jetzt `!(err instanceof ApiError) ? SERVER_FEHLER : err.message`. | ✅ FIXED — Bedingung korrekt umgedreht an allen 8 Stellen; kein Rest-Vorkommen der alten (invertierten) Form gefunden. AC9 damit erfüllbar. |
| BUG-3 (High) — `anzahl_gewerke` fehlt in `KategorieRead` | Eigener API-Call: Kategorie ohne Gewerk (`anzahl_gewerke == 0`), dann mit einem Gewerk (`anzahl_gewerke == 1`) geprüft. `repository.py:23-32` nutzt jetzt `LEFT JOIN` + `COUNT(g.id)` + `GROUP BY`; `schemas.py:38` hat `anzahl_gewerke: int = 0`. | ✅ FIXED — Zähler korrekt in beiden Fällen. Frontend `kategorie_verwaltung.tsx:165` (`k.anzahl_gewerke`) rendert jetzt einen echten Wert statt `undefined`. |

### Acceptance Criteria (Delta zum vorigen Lauf)
| # | Kriterium | Status |
|---|---|---|
| 4 | Übernahme in Angebot: Bezeichnung/Einheit/Preis vorausgefüllt, Snapshot ohne Live-Ref, Herkunftskennzeichnung in UI | ✅ PASS (vorher ⚠️ TEILWEISE — Blocker durch BUG-1 behoben) |
| 5 | Preis-Override mit Begründungspflicht, intern sichtbar, nicht im PDF, über UI erreichbar | ✅ PASS (vorher ⚠️ TEILWEISE — Blocker durch BUG-1 behoben) |
| 9 | Offline-Fehlermeldung korrekt vs. Server-Validierungsfehler | ✅ PASS (vorher ❌ FAIL — BUG-2 behoben) |
| 1 | Kategorien + Gewerke CRUD inkl. Kategorie-Anzeige (`anzahl_gewerke`) | ✅ PASS (vorher ✅ PASS mit Hinweis auf BUG-3 — jetzt vollständig) |

**Ergebnis: 9/9 PASS.**

### Regression
- Volle Backend-Suite: 275/275 grün (2 zusätzliche Tests durch Backend-Fix-Commit, kein Ausfall).
- Frontend-Build unverändert grün, `/gewerke`-Route weiterhin generiert.
- Bestehende BUG-1/BUG-3-Regressionstests aus Commit 3e26fe3 im Repo vorhanden und grün.

### Empfehlung
**READY.** Alle 3 Bugs (1 Critical, 2 High) unabhängig verifiziert behoben, keine Regression, alle 9 Acceptance Criteria PASS. Feature kann zum Pre-Deploy-Gate weiter.

## Deployment
**Deployed:** 2026-08-25 · **Version:** 0.1.17-PROJ-22 · **Environment:** Production (Dokploy)
**URL:** https://bizos.app.msce.info

### Changes
- Version bump from 0.1.16 to 0.1.17
- All 3 QA-identified bugs verified fixed (BUG-1, BUG-2, BUG-3)
- 9/9 Acceptance Criteria PASS
- No regressions in backend suite (275/275 tests green)

### Smoke-Test Checklist
- [ ] `/api/health` returns 200 (same-origin proxy routing verified)
- [ ] Login page renders in German
- [ ] Kalkulationsseite (`/gewerke`) loads and displays
- [ ] Create category → create gewerk with cost lines → calculate VK correctly
- [ ] Override price from angebot position with reason → visible internally, not in PDF
- [ ] No server errors in logs
