# PROJ-15: Auto-Triage mit Ampel

## Status: Deployed (2026-08-25)
**Created:** 2026-08-25
**Last Updated:** 2026-08-25
**Deployed:** 2026-08-25 · Version: v0.1.19-PROJ-15 · Host: bizos.app.msce.info

## Dependencies
- Requires: PROJ-3 — Vorgänge und ihre Anfrageinformationen.
- Uses: PROJ-6 — nächster freier Termin als Kapazitätsangabe.
- Uses: PROJ-13 — Leistungsauswahl im Anfrageformular.

## Ziel und Umfang

Neue oder geänderte Anfragen werden je Mandant nachvollziehbar als Grün, Gelb oder Rot markiert. Die Ampel ist nur eine Sortierhilfe: Sie löscht, verbirgt, verschiebt oder beantwortet keine Anfrage automatisch. KI, Freitext-Schlüsselwörter, Absageentwürfe und Wiedervorlagen gehören nicht zu diesem Feature.

Ein Inhaber konfiguriert, welches Auswahlfeld eines veröffentlichten Anfrageformulars die Leistung beschreibt und welche seiner Werte passend sind. Die Kapazitätsangabe ist ein einzelnes Datum „Nächster freier Termin" für den Betrieb.

Die Standardregel lautet:

- **Rot:** Die ausgewählte Leistung ist als unpassend konfiguriert.
- **Gelb:** Die Leistung ist passend, aber die Anfrage ist dringend oder ihr gewünschter Termin liegt vor dem nächsten freien Termin.
- **Grün:** Die Leistung ist passend und keiner der gelben Hinweise trifft zu.
- **Nicht bewertet:** Keine Leistungsauswahl oder kein nächster freier Termin liegt vor; die fehlende Grundlage wird sichtbar erklärt, statt eine Ampelfarbe zu erfinden.

## User Stories

- Als Büro möchte ich neue Anfragen nach Ampelfarbe sehen und filtern, damit ich zuerst die passenden und zeitkritischen Fälle prüfe.
- Als Inhaber möchte ich passende und unpassende Leistungswerte festlegen, damit die Vorsortierung zu meinem Betrieb passt.
- Als Inhaber möchte ich den nächsten freien Termin pflegen, damit die Triage die aktuelle Kapazität berücksichtigt.
- Als Büro möchte ich die Gründe einer Ampel sehen, damit ich die Bewertung nachvollziehen und fachlich prüfen kann.
- Als Inhaber möchte ich auch rote Anfragen vollständig sehen, damit kein potenziell wertvoller Auftrag verloren geht.

## Acceptance Criteria

- [x] Inhaber können je Mandant genau ein Auswahlfeld eines veröffentlichten Anfrageformulars als Leistungsauswahl bestimmen und dessen Werte als passend oder unpassend markieren. *(Backend: PUT /triage/einstellung, Snapshot-Validierung)*
- [x] Inhaber können ein Datum „Nächster freier Termin" setzen, ändern und entfernen; Büro kann diesen Wert sehen, aber nicht ändern. *(Backend: PATCH /triage/einstellung/kapazitaet, Rollen-Guard)*
- [x] Jede neue oder nachträglich geänderte Anfrage mit vollständigen Grundlagen erhält anhand der festgelegten Regel automatisch die Farbe Grün, Gelb oder Rot. *(Backend: berechnetes Triage-Feld in GET /vorgaenge + /vorgaenge/{id})*
- [x] Die Triage zeigt zu jeder bewerteten Anfrage verständliche Gründe, etwa „Leistung nicht passend", „Dringende Anfrage" oder „Gewünschter Termin vor 12.09.2026". *(Backend: triage.gründe[])*
- [x] Fehlt die Leistungsauswahl, die Kapazitätsangabe oder ein benötigter Terminwert, wird die Anfrage als „Nicht bewertet" mit konkretem Grund angezeigt. *(Backend: Bewertungsreihenfolge)*
- [x] Büro und Inhaber können die Anfragen nach Grün, Gelb, Rot und Nicht bewertet filtern sowie nach Ampelfarbe sortieren. *(Backend: Query-Parameter triage + sort=ampel)*
- [x] Eine Ampelbewertung ändert weder den Vorgangsstatus noch die Anfrage-, Kunden- oder Projektdaten und erzeugt keine Nachricht, Absage, Wiedervorlage oder Löschung. *(Backend: reine Read-Berechnung, keine Schreibpfade zu Vorgang/Kunde/Projekt/Nachricht)*
- [x] Alle Triage-Daten und Einstellungen sind strikt auf den angemeldeten Mandanten begrenzt; Monteure sehen keine Triage-Ansicht oder Einstellungen. *(Backend: JWT-Mandant, RLS, Rollen-Guards, serverseitig ausgelassene Triage-Felder)*

## Edge Cases

- Eine Leistungsauswahl mit einem nicht mehr konfigurierten Wert wird nicht rot geraten, sondern als „Nicht bewertet" mit Hinweis angezeigt.
- Eine Anfrage ohne gewünschtes Datum kann bei passender Leistung und nicht dringender Kennzeichnung grün sein; ihr fehlendes Datum ist kein Kapazitätskonflikt.
- Fällt der nächste freie Termin auf oder vor den gewünschten Termin, liegt kein Termin-Konflikt vor.
- Wird die Leistungskonfiguration oder der nächste freie Termin geändert, werden bestehende Anfragen bei der nächsten Anzeige nach den aktuellen Regeln neu bewertet.
- Eine rote Anfrage bleibt in allen Listen, Suchen und Vorgangsdetails zugänglich; ein Filter darf sie nur ausblenden, niemals archivieren oder löschen.
- Bei mehreren veröffentlichten Formularen gilt nur das vom Inhaber ausgewählte Leistungsfeld; Anfragen anderer Formulare werden als „Nicht bewertet" angezeigt.

## Fachliche Anforderungen

- Die Regeln bleiben deterministisch und ohne KI nachvollziehbar.
- Alle sichtbaren Bezeichnungen, Begründungen und Leerzustände sind deutschsprachig.
- Die Ampel ist eine Arbeitshilfe, keine Preis-, Prioritäts- oder Ablehnungsentscheidung.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-25 · **Stack:** Next.js/shadcn · FastAPI/raw SQL · PostgreSQL RLS · **Branch:** main

### 1. Zielbild und Abgrenzung

Die bestehende Vorgangsliste erhält eine berechnete Arbeitshilfe, keine neue Vorgangsart. Die Bewertung wird bei jedem Listen- und Detailabruf aus der aktuellen Mandanten-Konfiguration und der ursprünglichen Formular-Einsendung neu ermittelt; sie wird nicht gespeichert. Damit wirken Änderungen an Leistungskonfiguration oder Kapazität sofort auch auf bestehende Anfragen und es entstehen weder automatische Statuswechsel noch Nachrichten, Absagen, Wiedervorlagen oder Löschungen.

Bewertung in fester Reihenfolge:

1. Nicht bewertet, falls keine verknüpfte Formular-Einsendung, keine Leistungskonfiguration, kein Wert für das konfigurierte Leistungsfeld, ein anderer Formular-/Feldbezug oder ein nicht konfigurierter Leistungswert vorliegt.
2. Rot, falls der konfigurierte Leistungswert als unpassend markiert ist.
3. Nicht bewertet, falls kein „Nächster freier Termin“ gepflegt ist.
4. Gelb, falls die Anfrage als dringend markiert ist oder ein optional konfiguriertes Wunschdatum vor dem nächsten freien Termin liegt.
5. Grün in allen übrigen Fällen mit passender Leistung und vorhandener Kapazitätsangabe. Ein fehlendes Wunschdatum ist dabei kein Fehler und kein Termin-Konflikt.

Das Wunschdatum ist bewusst ein optionaler zweiter Feldbezug derselben veröffentlichten Form. Ohne diese Konfiguration wertet die Triage keinen Freitext wie das bisherige `zeitfenster` aus. So bleibt die Regel deterministisch; nur ein echtes Formular-Datumsfeld liefert einen vergleichbaren Kalendertag.

### 2. Komponenten und Lesepfade

```
VorgaengeTabelle (bestehende /vorgaenge-Seite, Inhaber/Büro)
├── Suche + bestehender Statusfilter
├── AmpelFilter und Sortierung
├── AmpelBadge je Vorgang
└── Link zum Vorgangsdetail

VorgangDetail (bestehend, Inhaber/Büro)
└── TriageCard: Farbe oder „Nicht bewertet“ mit Gründen

TriageEinstellungen (neue Inhaber-Seite)
├── veröffentlichte Formular-/Feld-Auswahl
├── Zuordnung passender/unpassender Leistungswerte
├── optionale Wunschdatum-Feld-Auswahl
└── „Nächster freier Termin“ setzen, ändern oder entfernen
```

- `VorgaengeTabelle` lädt mit `GET /vorgaenge?triage=<gruen|gelb|rot|nicht_bewertet>&sort=ampel`; ohne Triage-Parameter bleibt das heutige Verhalten erhalten. Sie zeigt Farbe und Kurzgrund.
- `VorgangDetail` liest die vollständige Erklärung mit `GET /vorgaenge/{id}`; der vorhandene Detailpfad liefert bereits die verknüpfte Formular-Einsendung (`backend/app/features/vorgaenge/service.py:57-71`).
- `TriageEinstellungen` liest zuerst `GET /triage/einstellung`, danach `GET /formulare` und pro veröffentlichtem Kandidaten `GET /formulare/{formular_id}/veroeffentlichte-version` (neu, siehe API-Contract). Diese Lesepfade liefern Formularstatus, Auswahlfelder, Optionen und Datumsfelder der tatsächlich veröffentlichten Version; erst danach darf eine Konfiguration geschrieben werden.
  - **Review-Korrektur:** `GET /formulare/{formular_id}` liefert laut Code den Entwurf (`backend/app/features/formulare/service.py:34-60`, `repo.list_felder` auf `formular_feld`/`formular_option`), nicht den unveränderlichen Snapshot der veröffentlichten Version (`formular_version.inhalt`). Entwurf und Snapshot können nach dem letzten Publish auseinanderlaufen. Der einzige Endpoint, der bisher den Snapshot liefert, ist der öffentliche `GET /public/formulare/{public_id}` (`service.py:384-399`, hostname-basiert, kein JWT) — ungeeignet für eine angemeldete Inhaber-Konfigurationsseite. Neuer Lesepfad ergänzt, siehe API-Contract.
- Monteure sehen weder Navigation, Ampelfilter/-badges noch Einstellung. Der Server verweigert Triage-Listenfilter und blendet Triage-Daten im Vorgangsdetail für diese Rolle aus; das ist nicht nur eine Frontend-Ausblendung.

### 3. Datenmodell, Owner und Lesepfade

Bestehende Daten werden wiederverwendet: `vorgang` als Listenobjekt, `anfrage.vorgang_id` als Verbindung und `formular_einsendung.werte` als unveränderliche Antwort (`backend/sql/003_kunden_vorgaenge.sql:31-47`, `backend/sql/011_formular_baukasten.sql:117-130`). Es gibt keine Tabelle für ein Bewertungsergebnis und keine MinIO-Objekte.

| Entität | Felder und Regeln | Schreib-Owner | nötige Lesepfade vor Schreiben |
|---|---|---|---|
| `triage_einstellung` (neu, genau eine Zeile je Mandant) | `id` UUID, `mandant_id` UUID unique, `leistungs_formular_id` UUID, `leistungs_feld_id` UUID, optional `wunschtermin_feld_id` UUID, optional `naechster_freier_termin` DATE, Zeitstempel. Leistungsfeld nur `dropdown`, `kachel` oder `radio`; Wunschdatum nur `datum`; beide müssen zur aktuell veröffentlichten Version desselben Formulars gehören. | Inhaber, `PUT /triage/einstellung` für Formular-/Feldbezüge; Inhaber, `PATCH /triage/einstellung/kapazitaet` für Datum oder `null`. Büro und Monteur schreiben nie. | `GET /triage/einstellung`; `GET /formulare`; `GET /formulare/{formular_id}/veroeffentlichte-version`. Der Service validiert alle IDs erneut im JWT-Mandanten, nicht aus dem Client-Mandanten, und zwar gegen den Snapshot (`formular_version.inhalt`), nicht gegen den Entwurf. |
| `triage_leistungswert` (neu, 0..n pro Einstellung) | `id` UUID, `mandant_id` UUID, `einstellung_id` UUID, `wert` TEXT nicht leer, `klassifikation` `passend|unpassend`, Zeitstempel; unique je Einstellung/Wert. Gespeichert wird der stabile Optionswert, nicht das sichtbare Label. Nicht gelistete Werte führen zu „Nicht bewertet“. | Ausschließlich Inhaber innerhalb des atomaren `PUT /triage/einstellung`; die übermittelte vollständige Werteliste ersetzt die bisherige. | dieselben drei Einstellungen-Lesepfade; zusätzlich liest der Screen die aktuelle Zuordnung aus `GET /triage/einstellung`. |
| bestehende `formular_einsendung` / `anfrage` / `vorgang` | Unverändert. Für die Berechnung nur lesend: Einsendungswert des konfigurierten Feldes, optionale Datumsantwort, Dringlichkeit und Vorgangsbezug. | Öffentlicher Formular-Submit bzw. bestehende Anfrageübernahme; PROJ-15 schreibt diese Entitäten nie. | Triage-Service lädt mandantenbegrenzt über `vorgang` die verknüpfte `anfrage` und Einsendung; die UI erhält nur Ergebnis/Gründe, keine Rohantworten zusätzlich. |
| berechnetes `triage`-Ergebnis | `status` `gruen|gelb|rot|nicht_bewertet`, `gründe[]` deutschsprachig, optional `naechster_freier_termin`; nur Response-Modell, nicht persistiert. | Kein Schreib-Owner: reine, bei jedem Read erneut ausgeführte Berechnung im Backend. | `GET /vorgaenge` bzw. `GET /vorgaenge/{id}` für Büro/Inhaber. |

Alle neuen Tabellen tragen `mandant_id`, aktivieren RLS und erhalten dieselbe `FOR ALL`-Policy auf `current_setting('app.current_mandant_id')` wie `vorgang` und `formular_einsendung`. FastAPI leitet den Mandanten allein aus der JWT-Sitzung ab (`backend/app/deps.py:71-113`); raw-SQL-Repositories übergeben ihn sowohl an ihre Abfrage als auch an den DB-Kontext. Fremd-IDs werden zusätzlich auf den Mandanten und die Formularbeziehung geprüft.

### 4. API-Contract

Alle folgenden Routen verlangen JWT. `mandant_id` kommt nie aus Request, Query oder Body.

| Route | Rolle | Vertrag |
|---|---|---|
| `GET /triage/einstellung` | Inhaber, Büro | Liefert aktuelle Feldbezüge, Leistungswert-Klassifikationen und Kapazitätsdatum. Bei noch fehlender Zeile leere Konfiguration statt Fehler. |
| `GET /formulare/{formular_id}/veroeffentlichte-version` (neu) | Inhaber, Büro | Liefert den unveränderlichen Snapshot (`formular_version.inhalt`) der aktuell veröffentlichten Version — Schritte, Felder, Optionen, Datumsfelder — analog zu `get_public_formular` (`service.py:384-399`), aber mandanten-/JWT-geschützt statt hostname-basiert. 404 falls `formular.veroeffentlicht` false oder keine `aktuelle_version_id`. Notwendig, weil `GET /formulare/{formular_id}` nur den Entwurf liefert, der vom Snapshot abweichen kann. |
| `PUT /triage/einstellung` | Inhaber | Atomar Formular, Leistungsfeld, optionales Wunschdatumfeld und vollständige Liste der Werte `wert + klassifikation` speichern. Leere oder nicht veröffentlichte/inkompatible Auswahl: 422; fremde IDs: 404. |
| `PATCH /triage/einstellung/kapazitaet` | Inhaber | Setzt ISO-Kalendertag oder entfernt ihn mit `null`. Büro erhält 403. |
| `GET /vorgaenge` erweitert | Inhaber, Büro; Monteur ohne Triage-Erweiterung | Neue optionale Query-Parameter `triage` und `sort=ampel`. Antwort erweitert jedes Listenelement um berechnetes `triage`. Sortierung: Rot, Gelb, Grün, Nicht bewertet; innerhalb einer Gruppe wie heute nach Erstelldatum absteigend. Pagination passiert nach Filter/Sortierung. Ungültige Parameter: 422. |
| `GET /vorgaenge/{vorgang_id}` erweitert | Inhaber, Büro | Antwort erweitert um vollständiges berechnetes `triage` mit allen Gründen. Bestehende Vorgangsdaten und Status bleiben unverändert. Monteur erhält kein Triage-Feld. |

Kein neuer öffentlicher Endpoint: Die öffentliche Formularübermittlung bleibt unverändert. Eine neue oder geänderte Einsendung ist beim nächsten angemeldeten Abruf automatisch nach den dann gültigen Regeln sichtbar.

### 5. Berechtigungen und Navigation

- Inhaber: vollständige Triage-Ansicht sowie Einstellungen und Kapazität pflegen.
- Büro: Vorgangsliste/-detail inkl. Farbe, Gründen, Filter und Sortierung; Konfiguration und Kapazität nur lesen.
- Monteur: bestehende, zugewiesene Vorgänge ohne Triage-Daten; keine Triage-Navigation oder -API-Parameter.
- Neue Navigation `Triage` nur für Inhaber. Die bestehende Seite `Vorgänge` ist für Büro und Inhaber der Arbeitsort der Filterung; dadurch keine zweite, konkurrierende Liste.

### 6. Technische Entscheidungen

- Berechnung beim Lesen statt gespeicherter Bewertung: Konfigurationsänderungen wirken sofort und keine Hintergrundjobs oder inkonsistenten Altbewertungen entstehen.
- Wert statt Options-ID speichern: veröffentlichte Antworten enthalten den Optionswert; bei später entfernten oder neuen Optionen wird der Fall transparent „Nicht bewertet“, statt ihn falsch rot zu raten.
- Strukturierte Datumsfeld-Auswahl statt Freitext: Vergleiche bleiben reproduzierbar und erklären exakt „Gewünschter Termin vor DD.MM.YYYY“.
- Erweiterung von `GET /vorgaenge` statt separater Triage-Liste: Suche, Vorgangsrechte, Pagination und rote Zugänglichkeit bleiben an einem etablierten Pfad (`backend/app/features/vorgaenge/routes.py:15-22`).
- Keine neuen Pakete, keine MinIO-Nutzung und keine KI: FastAPI, raw SQL, bestehende Next.js/shadcn-Komponenten und vorhandene Formulardaten reichen aus.

### 7. Akzeptanzkriterien-Mapping

| Akzeptanzkriterium | Architektur-Ort |
|---|---|
| Leistungsauswahl und Wertklassifikation | `TriageEinstellungen`, `triage_einstellung`, `triage_leistungswert`, `PUT /triage/einstellung` |
| Kapazitätsdatum mit getrennten Rechten | Kapazitäts-Card, `PATCH /triage/einstellung/kapazitaet` |
| automatische Grün/Gelb/Rot-Ermittlung | berechnetes Response-Modell in Listen- und Detailpfad |
| verständliche Gründe | `triage.gründe[]` in Badge/Detail-Card |
| Nicht bewertet und konkreter Grund | Bewertungsreihenfolge, `nicht_bewertet`-Filter und Detail-Card |
| filtern und sortieren | erweiterter `GET /vorgaenge`, bestehende Tabelle |
| keine Mutation/Folgeaktion | kein Write-Pfad zu Vorgang, Kunde, Projekt oder Nachricht |
| strikte Mandantentrennung, Monteur-Ausschluss | JWT-Mandantenkontext, RLS, Rollen-Guards und serverseitig ausgelassene Triage-Felder |

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-25 · **Verdict:** Architected

### Checklist
- [x] Component structure — `VorgaengeTabelle`, `VorgangDetail`, `TriageEinstellungen` klar auf bestehende Screens/neue Inhaber-Seite gemappt, kein Vage-UI.
- [x] Data model — `triage_einstellung` (unique `mandant_id`) folgt exakt dem bestehenden `website_settings`-Muster (`backend/sql/002_website.sql:5-7`); RLS/`mandant_id` auf allen neuen Tabellen benannt.
- [x] API shape — jede Route mit Methode/Pfad/Rolle; ein fehlender Lesepfad wurde ergänzt (siehe unten).
- [x] Tech decisions — alle 5 Entscheidungen in Abschnitt 6 mit Begründung.
- [x] Dependencies — keine neuen Pakete; Code-Cross-Check bestätigt vorhandene Muster (RLS, JWT-Mandant aus `deps.py:71-113`, Storage/Upload unberührt).
- [x] Branch field — `main`, passt zum Direkt-im-Workspace-Arbeiten dieses Projekts.
- [x] Conflict-free — keine `/triage/*`-Routenkollision im Code gefunden.
- [x] Acceptance-criteria coverage — jedes AC hat einen Architektur-Ort in Abschnitt 7.

### CodeGraph-Cross-Check (gegen echten Code, nicht nur Spec-Text)
- `anfrage.dringlichkeit` existiert als `TEXT CHECK IN ('Normal','Dringend')` (`backend/sql/002_website.sql:51`) — deckt "dringend markiert" aus der Ampelregel.
- `formular_einsendung.werte` ist per `feld_id` keyed (`_serialize_werte`, `backend/app/features/formulare/service.py:570-571`) — Triage kann den Wert des konfigurierten Feldes direkt auslesen, wie im Datenmodell behauptet.
- `require_role`-Strings `"Inhaber"`, `"Buero"`, `"Monteur"` sind projektweit konsistent (`backend/app/deps.py:107`, u.a. `vorgaenge/routes.py:12`, `formulare/routes.py:15,18`).
- `GET /vorgaenge` erlaubt zusätzliche optionale Query-Parameter ohne Bruch bestehender Aufrufer (`backend/app/features/vorgaenge/routes.py:15-22`, `service.py:45-54`).
- **Lücke gefunden und behoben:** Das Tech Design ließ `TriageEinstellungen` aus `GET /formulare/{formular_id}` lesen. Dieser Endpoint liefert laut Code (`formulare/service.py:34-60`, `_entwurf_to_dict` über `repo.list_felder`) den **Entwurf** (`formular_feld`/`formular_option`), nicht den unveränderlichen Snapshot der veröffentlichten Version (`formular_version.inhalt`). Entwurf und letzter Publish-Snapshot können auseinanderlaufen (z. B. nach Feldänderung ohne erneutes Veröffentlichen) — ein Inhaber hätte damit versehentlich gegen einen Feld-/Optionsstand konfiguriert, der den öffentlich einsendenden Nutzern gar nicht angezeigt wird. Einziger bestehender Snapshot-Lesepfad war der öffentliche, hostname-basierte `GET /public/formulare/{public_id}` (`service.py:384-399`) — ungeeignet für eine angemeldete, mandantengebundene Konfigurationsseite. Kein Produktentscheid nötig (rein technische Präzisierung eines bestehenden Designziels: „nur ein echtes Formular-Datumsfeld liefert einen vergleichbaren Kalendertag" impliziert bereits den Snapshot, nicht den Entwurf). Fix: neuer Lesepfad `GET /formulare/{formular_id}/veroeffentlichte-version` in Komponenten-, Datenmodell- und API-Contract-Abschnitt ergänzt.

### Autonom behoben
- Fehlenden Lesepfad `GET /formulare/{formular_id}/veroeffentlichte-version` in Abschnitt 2 (Komponenten/Lesepfade), Abschnitt 3 (Owner/Lesepfade-Tabelle) und Abschnitt 4 (API-Contract) ergänzt, mit Code-Zitat begründet.

### Offene Fragen
_Keine._

## Backend-Implementierung (2026-08-25)
- Migration `sql/016_triage.sql`: Tabellen `triage_einstellung` (UNIQUE mandant_id, Muster website_settings) + `triage_leistungswert`, beide mit RLS-Policy auf `current_setting('app.current_mandant_id')`.
- Modul `app/features/triage/` (schemas/repository/service/routes): `GET /triage/einstellung`, `PUT /triage/einstellung` (nur Inhaber, atomar, Snapshot-Validierung gegen `formular_version.inhalt`), `PATCH /triage/einstellung/kapazitaet` (Inhaber; Büro → 403).
- Neuer Lesepfad `GET /formulare/{id}/veroeffentlichte-version` (formulare/routes+service): liefert den unveränderlichen Snapshot der aktuellen Version, JWT-/mandantengeschützt, 404 falls nicht veröffentlicht.
- `GET /vorgaenge` + `GET /vorgaenge/{id}` erweitert um berechnetes `triage`-Feld (nicht persistiert). Filter `?triage=` und Sortierung `?sort=ampel`. Monteure erhalten kein Triage-Feld. Sortierung: Rot, Gelb, Grün, Nicht bewertet; innergruppe wie bisher nach Erstelldatum absteigend.
- Berechnungsreihenfolge exakt wie Tech Design §3. 285 Backend-Tests grün (9 neue Triage-Tests).

## QA Test Results
**Getestet:** 2026-08-25 · **Branch:** specs/PROJ-15-auto-triage-mit-ampel (Worktree) · **Verdict: READY**

### Automatisierte Tests
- Backend-Suite gesamt: 285/285 grün (`backend/.venv/bin/python -m pytest`), inkl. 9 neuer Triage-Tests (`test_triage.py`).
- Eigener unabhängiger QA-Red-Team-Testlauf hinzugefügt: `backend/tests/features/triage/test_qa_redteam_triage.py` (4/4 grün) — nicht vom Dev geschrieben, eigenständig verifiziert.
- Frontend: `npx tsc --noEmit` grün, `npm run build` grün, Route `/einstellungen/triage` generiert.

### Acceptance Criteria (8/8 PASS)
| # | Kriterium | Ergebnis |
|---|---|---|
| 1 | Leistungsauswahl + Wertklassifikation je Mandant, Snapshot-Validierung | PASS — `PUT /triage/einstellung` validiert gegen `formular_version.inhalt` (nicht Entwurf); Test `test_put_und_patch_kapazitaet` |
| 2 | Kapazitätsdatum setzen/ändern/entfernen, Büro nur lesend | PASS — `PATCH /triage/einstellung/kapazitaet`; Büro → 403 verifiziert |
| 3 | Automatische Grün/Gelb/Rot-Bewertung bei jedem Read | PASS — `test_triage_gruen_gelb_rot_nicht_bewertet`, alle 4 Fälle korrekt |
| 4 | Verständliche Gründe je Bewertung | PASS — `triage.gruende[]`, dt. Texte inkl. Datum-Formatierung („vor 12.09.2026") |
| 5 | „Nicht bewertet" bei fehlender Grundlage mit konkretem Grund | PASS — `test_triage_nicht_bewertet_ohne_grundlage` (fehlende Einsendung, nicht konfigurierter Wert) |
| 6 | Filtern/Sortieren nach Ampel | PASS — `?triage=` + `?sort=ampel`, ungültige Werte → 422; `test_triage_filter_und_sort` |
| 7 | Keine Mutation von Vorgang/Kunde/Projekt, keine Nachricht/Löschung | PASS — Code-Review: `triage_service.berechne` ist reine Read-Funktion, kein Schreibpfad in vorgaenge/service.py berührt |
| 8 | Strikte Mandantentrennung, Monteur-Ausschluss (Backend + Frontend gespiegelt) | PASS — RLS auf beiden neuen Tabellen, `test_triage_unsichtbar_fuer_monteur` + eigener Cross-Tenant-Redteam-Test; Frontend blendet UI zusätzlich clientseitig aus (`vorgaenge-tabelle.tsx:41`, Nav nur Inhaber) |

### Security-Red-Team (eigener Testlauf, unabhängig vom Dev)
- **Cross-Tenant Formular/Triage-Konfiguration:** Mandant B kann Mandant A's veröffentlichtes Formular nicht lesen (404) und nicht gegen As `formular_id`/`feld_id` schreiben (404, kein Leak) — `test_cross_tenant_triage_einstellung_isoliert` PASS.
- **Cross-Tenant Vorgang/Triage:** Mandant B erhält 404 auf As Vorgang, kein Triage-Datenleck — `test_cross_tenant_vorgang_triage_kein_leak` PASS.
- **JWT-Tampering:** Payload-Manipulation (`role: Monteur → Inhaber`) bei unveränderter Signatur → 401, kein Rollen-Bypass — `test_jwt_ohne_rolle_manipulation_kein_bypass` PASS.
- **SQL-Injection via Pydantic-Bypass:** Injection-String im `wert`-Feld (`x'; DROP TABLE ...`) wird parametrisiert als Literal gespeichert, Tabelle bleibt intakt — `test_sql_injection_leistungswert` PASS.
- **RLS:** Beide neue Tabellen (`triage_einstellung`, `triage_leistungswert`) haben `ENABLE ROW LEVEL SECURITY` + `FOR ALL`-Policy auf `current_setting('app.current_mandant_id')`, Muster identisch zu bestehenden Tabellen.
- Keine weiteren Befunde (keine Secrets-Exposure, kein Rate-Limiting-relevanter neuer Endpoint, kein MinIO-Zugriff in diesem Feature).

### Edge Cases (aus Spec) — Stichprobe verifiziert
- Nicht mehr konfigurierter Leistungswert → „Nicht bewertet" statt rot geraten: PASS (`test_triage_nicht_bewertet_ohne_grundlage`).
- Fehlendes Wunschdatum bei passender Leistung → kann grün sein, kein Konflikt: PASS (`v_gruen` in `test_triage_gruen_gelb_rot_nicht_bewertet`).
- Nächster freier Termin auf/vor Wunschtermin → kein Konflikt: Code-Review bestätigt (`wunsch_datum < kapazitaet`, strikt kleiner).
- Rote Anfrage bleibt zugänglich, kein Archivieren/Löschen: Code-Review bestätigt, kein DELETE/Statuswechsel im Triage-Pfad.

### Regression
- Gesamte Backend-Suite (alle Features inkl. PROJ-3, PROJ-6, PROJ-13, PROJ-14, PROJ-22) weiterhin 285/285 grün — keine Regressionen durch die `vorgaenge`/`formulare`-Erweiterungen.
- `GET /vorgaenge` ohne Triage-Parameter unverändert (Query-Parameter rein additiv, Monteur-Pfad unverändert).

### Offene Punkte
_Keine Bugs gefunden (Critical/High/Medium/Low: 0)._

### Production-Ready
**READY** — keine Critical/High-Bugs. Empfehlung: weiter zu Deploy.

## Deployment
_To be added by /abc-deploy_
