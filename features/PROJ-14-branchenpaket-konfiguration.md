# PROJ-14: Branchenpaket-Konfiguration

## Status: Architected
**Created:** 2026-08-24
**Last Updated:** 2026-08-24

## Dependencies
- Requires: PROJ-1 — Mandanten, Anmeldung und Rollen für die mandantensichere Zuordnung des Branchenpakets.
- Coordinates with: PROJ-7 — das Onboarding erfragt und speichert die einmalige Branchenwahl.
- Coordinates with: PROJ-13 — erhält die kopierten Formular-Startvorlagen.
- Coordinates with: PROJ-22 — erhält die kopierten Gewerke-, Material- und Textvorlagen.

## Ziel

Beim Onboarding erhält jeder Betrieb genau ein vom Produktteam gepflegtes Branchenpaket: SHK oder Entrümpelung. Das Paket liefert passende Startinhalte für Formulare, Preislisten, Textbausteine und Dokumentkategorien. Diese Inhalte werden in den Mandanten kopiert und danach ausschließlich dort bearbeitet; spätere Produktvorlagen verändern keinen bestehenden Betrieb.

## User Stories

- Als Inhaber möchte ich im Onboarding SHK oder Entrümpelung auswählen, damit mein Betrieb nicht mit leeren Formularen, Katalogen und Texten startet.
- Als Inhaber möchte ich nach der Einrichtung die übernommenen Inhalte im eigenen Mandanten anpassen, damit Begriffe, Preise und Texte zu meinem Betrieb passen.
- Als Büro-Mitarbeiter möchte ich nur die für meinen Betrieb übernommenen Vorlagen sehen, damit ich nicht versehentlich mit fachfremden Inhalten arbeite.
- Als Produktteam möchte ich die zwei Standardpakete mit dem Produkt ausliefern, damit neue Betriebe eine geprüfte, einheitliche Ausgangsbasis erhalten.
- Als Inhaber möchte ich erkennen, welches Paket beim Onboarding gewählt wurde, damit die fachliche Ausgangslage nachvollziehbar bleibt.

## Acceptance Criteria

- [ ] Das Onboarding bietet genau die Branchenpakete „SHK" und „Entrümpelung" mit verständlicher deutscher Beschreibung; die Auswahl ist vor Abschluss erforderlich.
- [ ] Nach erfolgreichem Onboarding ist das gewählte Paket am Mandanten gespeichert und für Inhaber sowie Büro sichtbar, aber nicht durch diese Rollen änderbar.
- [ ] Die Paketübernahme legt für den neuen Mandanten eine eigene Kopie der passenden Formular-Startvorlage, Kategorien und Beispiel-Gewerke/Materialien sowie Angebots-, Rechnungs- und E-Mail-Textbausteine an.
- [ ] SHK-Startinhalte enthalten mindestens typische Sanitär-/Heizungsbegriffe; Entrümpelungs-Startinhalte mindestens Fläche, Entsorgung, Transport und Wertanrechnung als fachliche Ausgangsbasis.
- [ ] Übernommene Inhalte sind mandantenbezogen in den jeweils zuständigen Modulen bearbeitbar; Änderungen eines Betriebs sind für keinen anderen Betrieb sichtbar.
- [ ] Produktupdates mit neuen oder geänderten Paketvorlagen ändern weder bestehende Mandantendaten noch historische Formulare, Angebote oder Dokumente.
- [ ] Neue Betriebe erhalten ausschließlich die zum Zeitpunkt ihres Onboardings ausgelieferte Fassung ihres gewählten Pakets; eine zentrale Pflegeoberfläche für Betriebe oder interne Betreiber ist nicht Teil von V1.
- [ ] Alle Paketnamen, Beschreibungen und sichtbaren Startinhalte sind auf Deutsch und in der Onboarding-Ansicht ab 375 px Breite ohne horizontales Scrollen nutzbar.

## Edge Cases

- Bricht das Onboarding vor der Paketübernahme ab, ist kein Paket und kein unvollständiger Vorlagenbestand im Mandanten sichtbar.
- Schlägt das Kopieren eines Bestandteils fehl, wird das Onboarding nicht als abgeschlossen markiert und es bleibt kein teilweise übernommener Paketbestand zurück.
- Existieren im Zielmandanten bereits Inhalte, wird keine Paketübernahme erneut gestartet und nichts überschrieben.
- Wird ein Paket später im Produkt korrigiert oder erweitert, behalten bereits eingerichtete Betriebe unverändert ihre eigene Kopie.
- Fehlende oder ungültige Startinhalte eines ausgelieferten Pakets verhindern dessen Auswahl mit einer verständlichen deutschen Meldung; der Mandant wird nicht eingerichtet.
- Ein Benutzer eines anderen Mandanten kann weder Paketzuordnung noch kopierte Vorlagen eines fremden Betriebs abrufen oder verändern.

## Nicht-Ziele

- Kein Wechsel des Branchenpakets nach abgeschlossenem Onboarding.
- Keine gleichzeitige Nutzung mehrerer Pakete je Mandant.
- Keine Paketverwaltung oder eigenen Paketdefinitionen durch Betriebe oder interne Betreiber.
- Keine automatische oder manuelle Übernahme späterer Paketupdates in bestehende Mandanten.
- Keine neue Branchenmechanik; Formulare, Kataloge, Texte und Dokumente bleiben die jeweiligen bestehenden Fachmodule.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-24 · **Stack:** Next.js 16/shadcn-artige UI, FastAPI, PostgreSQL raw SQL + RLS, MinIO, Dokploy · **Branch:** main

### Ausgangspunkt und kleinste vollständige Lösung

Das Produkt hat bereits zwei Formular-Startvorlagen (`shk`, `entruempelung`),
den mandantenbezogenen Formulardraft samt Publish-Snapshots sowie eine
mandantenbezogene Preisliste. Die aktuelle Onboarding-Checkliste enthält sieben
berechnete Schritte und veröffentlicht erst nach einer serverseitigen Prüfung.
PROJ-14 ergänzt genau einen Pflichtschritt und einen einmaligen, atomaren
Übernahmevorgang. Es baut weder einen Paket-Editor noch eine dritte
Frontend-Technologie.

Die beiden Pakete sind versionierte, mit dem Release ausgelieferte
Produktkataloge im Backend, keine mandantenlesbaren Datenbankzeilen und keine
Betreiber-Oberfläche. Ein Katalog hat eine feste Kennung (`shk` oder
`entruempelung`), eine deutsche Bezeichnung/Beschreibung, eine Release-Version
und nur die Startdaten, die die vorhandenen bzw. von PROJ-22 vorgesehenen
Fachmodule verstehen. Das ist absichtlich die kleinste Lösung: neue
Produktvorlagen gelten ausschließlich für spätere Übernahmen.

### Flächen und Komponenten

```text
Angemeldete Betriebszentrale, nur Inhaber
└── Begleitetes Onboarding
    ├── bestehende Fortschrittsliste
    ├── neuer Pflichtschritt „Branchenpaket“
    │   └── Wahlkarten SHK / Entrümpelung (Beschreibung, keine Preisangaben)
    ├── Übernahme-Bestätigung mit deutscher Fehleranzeige
    └── bestehendes Veröffentlichen-Gate

Betriebszentrale, Inhaber und Büro
├── bestehende Formularliste/-editor: übernommene Formularvorlage bearbeiten
├── bestehender Katalog: übernommene Startpositionen sehen/bearbeiten
└── künftige PROJ-22-Flächen: Kategorien, Gewerke, Material und Textvorlagen

Backend
└── Branchenpaket-Orchestrierung
    ├── prüft ausgelieferten Katalog vollständig
    ├── kopiert alle Zielinhalte in genau einen Mandanten
    └── schreibt Zuordnung erst mit erfolgreichem Gesamtvorgang
```

Die Wahlkarten sind auf 375 px untereinander angeordnet; Bezeichnung,
Beschreibung, Auswahl- und Fehlermeldungen sind deutsch. Büro sieht die
schreibgeschützte Paketbezeichnung ausschließlich über Betriebsinformation,
nicht auf der Inhaber-only-Onboarding-Seite und nicht die Übernahmeaktion.

### Datenmodell, Owner und Lesepfade

Neue untergeordnete Mandantenentitäten tragen `mandant_id`; die bestehende
Entität `mandanten` wird per eigener ID-Policy begrenzt. RLS begrenzt beide
Varianten auf `current_setting('app.current_mandant_id')`; FastAPI bezieht den
Mandanten serverseitig aus dem Sitzungs-Lookup zum JWT-`sub`
(`backend/app/deps.py:52-84`) und jede Repository-Abfrage filtert zusätzlich
nach `mandant_id`. `mandant_id`, Paketkennung und Paketversion sind nie
Client-Eingaben für einen Schreibpfad.

| Entität | Inhalt | Schreiber / Owner | nötige Lesepfade |
|---|---|---|---|
| Produktkatalog `BranchenpaketVorlage` (Release-Artefakt, keine DB-Tabelle) | feste Kennung, deutsche Beschreibung, Version und validierte Seed-Daten für SHK/Entrümpelung | Produktentwicklung beim Release; keine Runtime-API und keine Betreiber-/Betriebsoberfläche in V1 | `GET /onboarding/branchenpakete` liest nur Kennung, Namen und Beschreibungen für die Inhaber-Wahl; der Übernahme-Endpunkt liest den vollständigen Katalog serverintern. |
| `mandanten` (bestehend, erweitert) | unveränderliche `branchenpaket_kennung`, `branchenpaket_version`, `branchenpaket_uebernommen_am` | ausschließlich `POST /onboarding/branchenpaket-uebernehmen`, Rolle Inhaber, einmalig; bestehende Mandantenerstellung schreibt diese Felder nicht | `GET /onboarding` vor und nach Übernahme für den Pflichtschritt; `GET /auth/me` bzw. ein schlanker Betriebsinfo-Lesepfad für Inhaber/Büro, bevor die Paketinfo angezeigt wird. |
| `leistungsseite` / Website-Leistungsseiten (bestehend) | mandanteneigene Leistungsseiten als Startinhalt des gewählten Branchenpakets; SHK und Entrümpelung haben getrennte Katalogeinträge | initial ausschließlich `POST /onboarding/branchenpaket-uebernehmen` im atomaren Paketvorgang; danach ausschließlich bestehendes `PATCH /website-settings`, Rolle Inhaber. `GET /website-settings` erzeugt bei Bedarf nur Website-Einstellungen, aber keine Leistungsseiten und ist kein Seed-Owner. | Inhaber lädt `GET /website-settings` vor Anzeige oder Bearbeitung und vor `PATCH /website-settings`. Öffentliche Website nutzt unverändert `GET /public/site` für die Liste und `GET /public/leistungen/{slug}` für eine aktive Seite. |
| `formular`, `formular_schritt`, `formular_feld`, `formular_option` (bestehend) | eigenständige Kopie einer passenden Startformularstruktur; keine Referenz auf Produktkatalog | normal: bestehende Formular-Editor-Endpunkte durch Inhaber/Büro; initial: ausschließlich die Paketübernahme als derselbe atomare Vorgang | `GET /formulare` vor Formularauswahl; `GET /formulare/{id}` vor Edit/Publish. Der Übernahme-Status zählt als Erfolg erst, wenn die Kopie vollständig angelegt ist. Öffentliche Leser nutzen weiter nur veröffentlichte `formular_version` per bestehender Domainauflösung. |
| `formular_version` (bestehend) | unveränderlicher Publish-Snapshot einer später vom Betrieb veröffentlichten Kopie | ausschließlich bestehendes `POST /formulare/{id}/veroeffentlichen`, Inhaber/Büro; Paketübernahme schreibt keinen öffentlichen Snapshot | `GET /formulare/{id}` vor dem Publish; öffentliche Leser verwenden den bestehenden Hostname- und `public_id`-Lesepfad. |
| `preisliste` (bestehend, bis PROJ-22 abgelöst/angebunden) | mandanteneigene Beispielpositionen als kurzfristiger Katalog-Seed | normal: `POST /katalog/positionen`, CSV-Import und Delete, derzeit Inhaber; initial: Paketübernahme atomar | `GET /katalog` vor Bearbeitung/Anzeige und zur Validierung, dass keine vorherigen Inhalte existieren. |
| PROJ-22-Katalogentitäten: Kategorien, Gewerke, Materialien und Kostenzeilen (neu in PROJ-22) | branchenabhängige Startkategorien und Beispiel-Gewerke/Materialien; Entrümpelung enthält Fläche, Entsorgung, Transport und Wertanrechnung | ihre späteren PROJ-22-CRUD-Endpunkte durch Inhaber/Büro; initial Paketübernahme als alleiniger Seed-Owner | jeweilige PROJ-22-Listen vor Zuweisung/Bearbeitung. PROJ-14 reserviert keine eigene parallele Katalogmechanik und wartet auf die finalen Entitätsnamen/Contracts von PROJ-22. |
| PROJ-22-Textvorlagen (neu) | Angebots-, Auftragsbestätigungs-, Rechnungs- und E-Mail-Anfangs/Schlusstexte als mandanteneigene Kopie | ihr späterer PROJ-22-Textvorlagen-Editor; initial Paketübernahme atomar | jeweilige Textvorlagen-Listen vor Dokumenterstellung und vor Edit. Bestehende Angebote/Rechnungen bleiben unverändert; die Übernahme schreibt keine historischen Belege oder Snapshots. |

**Invariante:** Existiert bereits eine Paketkennung am Mandanten **oder**
existiert irgendein Zielinhalt aus der Übernahme, antwortet der Übernahmeweg mit
`409`, schreibt nichts und überschreibt nie Betriebseingaben. Der Katalog wird
vor Beginn vollständig validiert. Jede Zielschreiboperation läuft in einer
einzigen Datenbanktransaktion mit gesetztem Mandantenkontext; Fehler führen zum
Rollback aller Kopien und der Mandantenfelder. MinIO ist in V1 nicht beteiligt,
weil Paketdaten keine Binärdateien enthalten.

**Bestehende Website-Seed-Korrektur:** Der heutige Lazy-Pfad
`website/service.py:_get_or_create_settings` darf keine globale SHK-Liste mehr
in `leistungsseite` schreiben. Er bleibt ausschließlich Owner der leeren
`website_settings`-Zeile. Die Leistungsseiten-Kataloge gehören vollständig zu
den beiden `BranchenpaketVorlage`-Einträgen und werden nur durch die erfolgreiche
Paketübernahme geschrieben. Damit kann ein Entrümpelungs-Mandant weder beim
Öffnen von `GET /website-settings` noch beim öffentlichen Seitenaufruf
SHK-Leistungsseiten erhalten.

### API-Contracts

Alle geschützten Routen verlangen Bearer-JWT. `Inhaber` ist die einzige Rolle,
die wählen oder übernehmen kann. `Buero` darf nur die gespeicherte Kennung und
die ihm ohnehin zugänglichen kopierten Fachinhalte lesen/bearbeiten; `Monteur`
erhält keine Paket- oder Editorroute. Die vorhandene Rollenprüfung folgt
`require_role` (`backend/app/deps.py:87-93`).

- `GET /onboarding/branchenpakete` liefert genau zwei deutsche, nicht
  veränderbare Wahloptionen `{kennung, name, beschreibung}`. Inhaber-Wahlkarte
  ruft ihn vor der Auswahl; keine Versions- oder Seed-Details im Browser.
- `POST /onboarding/branchenpaket-uebernehmen` nimmt nur `kennung` (`shk` oder
  `entruempelung`) an. Es prüft Rolle, fehlende frühere Übernahme, leeren
  Zielbestand und die vollständige ausgelieferte Vorlage; dann kopiert es
  atomar und liefert `kennung`, `name`, `version`, `uebernommen_am` sowie den
  aktualisierten Onboarding-Status. Ungültiger/defekter Katalog: `422` mit
  deutscher Meldung. Bereits übernommenes/nicht leeres Ziel: `409`.
- `GET /onboarding` erweitert den bestehenden Status um den Pflichtschritt
  `branchenpaket` und die schreibgeschützte Paketinfo. Der Schritt ist nur nach
  erfolgreicher Übernahme `erledigt`; vorab wird keine Wahl persistent
  gespeichert.
- `GET /website-settings` und `PATCH /website-settings` behalten ihren
  bestehenden Inhaber-Contract für Lesen bzw. spätere Bearbeitung der kopierten
  Leistungsseiten. Sie nehmen keine Paketkennung an und lösen keine globale
  Default-Befüllung aus. Der Paketübernahmeweg ist der einzige Initialschreiber.
- `POST /onboarding/veroeffentlichen` bleibt der einzige Publish-Weg. Seine
  bestehende Pflichtprüfung behandelt `branchenpaket` zusätzlich als Gate und
  aktiviert keine Domain, solange die Paketübernahme fehlt. Es startet keine
  stillschweigende Kopie.
- `GET /auth/me` wird rückwärtskompatibel um die schreibgeschützte
  Paketkennzeichnung erweitert, damit Inhaber/Büro sie ohne Zugriff auf die
  Inhaber-only-Onboarding-Seite sehen. Alternativ darf ein bestehender
  Betriebsinfo-Contract dieselben drei Felder liefern; genau einer dieser
  Lesepfade wird bei Umsetzung gewählt, nicht beide.

Bestehende `GET/POST/PATCH /formulare*`, `GET/POST/DELETE /katalog*` und die
späteren PROJ-22-Contracts bleiben Eigentümer der fachlichen Bearbeitung. Sie
erhalten keine `branchenpaket`-Parameter und keine Logik, die Produktvorlagen
nachlädt.

### Reihenfolge und Abhängigkeiten

1. Paketkatalog inkl. deutscher Inhalte und Validierungsregeln mit der
   vorhandenen Formularvorlagenstruktur und `leistungsseite` abstimmen. Er
   enthält je Paket eigene Leistungsseiten: SHK-Sanitär-/Heizungsbegriffe;
   Entrümpelung mindestens Fläche, Entsorgung, Transport und Wertanrechnung.
   Die globale SHK-Konstante im Website-Lazy-Pfad entfällt; die Website-Seed-
   Daten werden nur aus dem gewählten Katalog übernommen.
2. Raw-SQL-Migration nach `012_website_section_images.sql`: drei nullable
   Paket-Metadatenfelder auf `mandanten`; keine neue Mandanten-Tabelle. Die
   bestehende RLS-Policy für `mandanten` schützt sie bereits.
3. Onboarding-Status, Wahl-/Übernahme-Contracts und atomare Orchestrierung
   ergänzen. Die Orchestrierung nutzt die vorhandene Formular-Seed-Struktur
   (`formulare/service.py:85-124`), aber nicht den öffentlichen bzw. normalen
   Formular-POST als HTTP-Call.
4. Next.js-Onboarding um Wahlkarten und Statusanzeige ergänzen; nur vorhandene
   shadcn-artige Komponenten und API-Client-Muster nutzen.
5. PROJ-22 liefert seine Katalog-/Textvorlagenentitäten. Bis dahin übergibt
   PROJ-14 nur die bereits existierende Formular-Kopie/Preisliste; die finale
   Paketübernahme darf erst die vollständige, in diesem Dokument verlangte
   Modulmenge aktivieren, wenn PROJ-22-Zielschreiber existieren. Keine
   Schatten-Tabellen oder temporären Textvorlagen in PROJ-14.

### Entscheidungen (ADRs)

- **ADR-14-1: Release-Katalog statt Paketverwaltung.** Zwei feste Pakete und
  kein Betreiber-UI erfüllen V1. Neue Katalogversionen ändern keinen alten
  Mandanten, weil nur der Übernahmezeitpunkt kopiert und an `mandanten`
  protokolliert wird.
- **ADR-14-2: Kopie, keine Referenz.** Betriebsvorlagen einschließlich
  Website-Leistungsseiten bleiben editierbar und Produktänderungen können weder
  fremde Daten noch historische Formular-/Dokument-Snapshots verändern. Es gibt
  keinen branchenunabhängigen Website-Seed; die gewählte Vorlage ist alleiniger
  Initialschreiber der Leistungsseiten.
- **ADR-14-3: Eine atomare Orchestrierung.** Modulübergreifende Seeds ohne
  gemeinsame Transaktion würden unbrauchbare Teilbestände erzeugen. Eine
  Übernahme ist ganz erfolgreich oder nicht sichtbar.
- **ADR-14-4: Wahl erst beim Übernehmen persistent machen.** Abgebrochene
  Onboarding-Sitzungen hinterlassen weder eine Paketzuordnung noch Seed-Daten.
  Die Browser-Auswahl ist bis zur Bestätigung nur UI-Zustand.
- **ADR-14-5: Next.js weiterverwenden.** Das Repository enthält bereits die
  Next.js-16-Onboarding-Seite und keinen Flutter-Client. Eine Flutter-Fläche
  wäre Doppelpflege.
- **ADR-14-6: Kein MinIO.** Startinhalte sind Struktur und Text; Binärspeicher
  wäre zusätzlicher, nicht verlangter Lebenszyklus.
- **ADR-14-7: RLS plus Repository-Filter.** Der Mandantenkontext kommt nie vom
  Client. RLS begrenzt Datenbankzugriff zusätzlich zur expliziten
  `mandant_id`-Abfrage und verhindert mandantenübergreifende Paket-/Seed-Zugriffe.

### Abhängigkeiten und Auslieferung

- Keine neuen Pakete: Next.js/React, vorhandene shadcn-artige UI, FastAPI,
  Pydantic und raw SQL reichen aus.
- Neue idempotente raw-SQL-Datei `backend/sql/013_branchenpakete.sql`; kein
  Alembic. Sie erweitert nur `mandanten` und braucht keine MinIO- oder Dokploy-
  Konfiguration.
- Dokploy liefert Backend und bestehendes Next.js gemeinsam aus. Paketkatalog
  reist mit dem Backend-Release; `branchenpaket_version` ist deshalb die
  nachvollziehbare Releasefassung eines neuen Betriebs.
- PROJ-22 ist eine fachliche Blocker-Abhängigkeit für Kategorien, Gewerke,
  Materialien und Textvorlagen. Implementierung darf den End-to-End-
  Übernahme-Endpunkt nicht vor den dort definierten Zielentitäten als
  „vollständig“ ausliefern.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-24 (Re-Review) · **Verdict:** Architected

### Checklist
- [x] Owner-Check — `leistungsseite` hat expliziten Initial-Owner `POST /onboarding/branchenpaket-uebernehmen` und späteren Owner `PATCH /website-settings`, Rolle Inhaber.
- [x] Lesepfad-Check — `GET /website-settings` (Inhaber, `routes.py:76`), `GET /public/site` (`routes.py:38`), `GET /public/leistungen/{slug}` (`routes.py:43`) existieren real und passen zum Contract.
- [x] Code-Korrektur verifiziert — `website/service.py:64-69 _get_or_create_settings` ruft aktuell unbedingt `repo.seed_leistungen(mandant_id, SEED_LEISTUNGEN)` mit globaler SHK-Liste (`service.py:15-21`); Korrektur im Dokument benennt exakt diesen Pfad und die richtige Zielarchitektur (Seed nur aus gewähltem Branchenpaket, `create_default_settings` bleibt alleiniger Owner der leeren Zeile). Kein Widerspruch zum Code.
- [x] Repository-Ebene — `repository.py:76-82 create_default_settings` legt nur die leere `website_settings`-Zeile an, `repository.py:131 seed_leistungen` ist die Stelle, die künftig ausschließlich vom Paketübernahme-Pfad aufgerufen werden darf.
- [x] API-Contract konsistent — `settings_router` erzwingt `require_role("Inhaber")` auf GET/PATCH (`routes.py:76,82`), passt zu Doku-Aussage.
- [x] Migrationsreihenfolge — `013_branchenpakete.sql` nach `012_website_section_images.sql` korrekt (aktuell letzte reale Migration).
- [x] Referenzierte Formular-Seed-Struktur — `formulare/service.py:85 create_formular`, `:96 _seed_template` existieren (Doku-Referenz 85-124 im Rahmen).
- [x] ADR-14-2 — Konsistent mit Code: kein branchenunabhängiger Seed vorhanden/vorgesehen nach Korrektur.

### CodeGraph-Cross-Check
Direkt gegen Code verifiziert (kein Explore-Agent nötig, Umfang klein genug für direkte Prüfung): `website/service.py`, `website/routes.py`, `website/repository.py`, `onboarding/service.py`, `onboarding/repository.py`, `onboarding/routes.py`, `sql/`. Keine Diskrepanzen zur Tech-Design-Behauptung gefunden.

### Autonom behoben
- Keine Änderungen nötig — Korrektur aus der Vorrunde war bereits vollständig und korrekt.

### Offene Fragen
- Keine.

## Deployment
_To be added by /abc-deploy_
