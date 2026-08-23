# PROJ-12: Freier Website-Baukasten und hochwertige Landingpage

## Status: Deployed
**Created:** 2026-08-21
**Last Updated:** 2026-08-21

## Dependencies
- Requires: PROJ-1 — Mandant und Inhaberzugriff.
- Requires: PROJ-2 — öffentliche Website, Branding, Bildspeicher und vollständiges Anfrageformular.

## Ziel

Die bisher starre, textarme SHK-Startseite wird durch eine hochwertige, lange
Landingpage nach dem visuellen Aufbau der Referenz `entrümpelungsexpress`
ersetzt. Inhaber stellen sie aus freigegebenen Sektionstypen selbst zusammen,
ohne Layout oder HTML bearbeiten zu müssen.

## User Stories
- Als Inhaber möchte ich Sektionen hinzufügen, löschen und sortieren, damit meine Startseite den Betrieb passend präsentiert.
- Als Inhaber möchte ich für jede Sektion Überschriften, Texte, Handlungsaufrufe und Bilder pflegen, damit Inhalte und Fotos austauschbar sind.
- Als Inhaber möchte ich ein Hero-Bild und ein Kurzformular im sichtbaren Einstieg pflegen, damit Interessenten schnell eine Anfrage beginnen können.
- Als Interessent möchte ich eine übersichtliche, vertrauenswürdige und mobil nutzbare Landingpage sehen, damit ich Leistungen, Ablauf und Kontakt ohne Suche verstehe.
- Als Interessent möchte ich meine Kontaktdaten im Kurzformular eingeben und danach direkt im bestehenden Anfrageformular weitermachen, damit ich eine vollständige Anfrage absenden kann.

## Acceptance Criteria
- [ ] Die öffentliche Startseite folgt dem Referenzaufbau mit Kopfbereich, Hero mit Hintergrundfoto und Kurzformular, Über-uns-/Bildsektion, Leistungsübersicht, Vertrauens-/Qualitätssektion, Ablauf, Kennzahlen, FAQ, Kontakt sowie Abschluss-CTA und Footer.
- [ ] Inhaber können eine Sektion aus den vorgegebenen Typen Hero, Text mit Bild, Leistungen, Kennzahlen, Ablauf, FAQ, Kontakt und CTA hinzufügen, entfernen, ein- oder ausblenden und frei sortieren.
- [ ] Jede Sektion zeigt nur ihre passenden Eingabefelder; alle Textfelder erlauben leere, kurze und lange Inhalte, ohne Überlauf, abgeschnittenen Text oder überlappende Bedienelemente auf Desktop und ab 375 px Breite.
- [ ] Bilder können für Hero- und Bildsektionen hochgeladen, ersetzt und entfernt werden; ohne Bild bleibt jede Sektion als gestaltete Textvariante nutzbar.
- [ ] Das Hero enthält ein Kurzformular mit Name und mindestens einem Kontaktweg; nach gültiger Eingabe werden die Werte an das vorhandene vollständige Anfrageformular übergeben.
- [ ] Die Eingaben des Kurzformulars werden erst durch das bestehende vollständige Formular als Anfrage gespeichert; ein Abbruch erzeugt keinen Vorgang.
- [ ] Die Leistungssektion verwendet die in PROJ-2 gepflegten aktiven Leistungen und zeigt bei keiner aktiven Leistung eine editierbare, neutrale Leerzustandsvariante statt eines defekten Rasters.
- [ ] FAQ, Kennzahlen, Ablaufkarten und Leistungs-/Kontakt-CTAs sind je Sektion konfigurierbar und verlinken ausschließlich auf vorhandene öffentliche Seiten oder den Anfrage-Flow.
- [ ] Öffentliche Inhalte und hochgeladene Bilder sind ausschließlich über die Domain des zugehörigen Mandanten sichtbar; Inhaber können nur ihre eigenen Baukasteninhalte bearbeiten.
- [ ] Alle Eingabefelder, Bildaktionen, Reihenfolge-Aktionen und das Kurzformular sind per Tastatur bedienbar, haben deutsche Beschriftungen und verständliche Fehlermeldungen.

## Edge Cases
- Ein versehentlich gelöschter oder ausgeblendeter Hero lässt die Startseite mit den verbleibenden sichtbaren Sektionen nutzbar; es gibt keinen leeren oder fehlerhaften Seitenzustand.
- Sehr lange Überschriften, Fließtexte, CTA-Texte oder Leistungsnamen umbrechen responsiv und behalten ausreichende Abstände.
- Ein Bild-Upload, der die bestehenden Größen- oder Formatgrenzen nicht erfüllt, wird mit deutscher Meldung abgewiesen und ersetzt das bisherige Bild nicht.
- Wird ein Bild entfernt oder fehlt es, erscheinen weder ein defektes Bildsymbol noch eine Lücke, die die Lesereihenfolge stört.
- Enthält das Kurzformular weder Telefonnummer noch E-Mail, wird es nicht weitergeleitet und erklärt, dass mindestens ein Kontaktweg erforderlich ist.
- Nicht mehr vorhandene, deaktivierte oder fremde Leistungsseiten werden weder als Karte noch als Link veröffentlicht.
- Das Anordnen von Sektionen bei paralleler Bearbeitung speichert keinen fremden Mandanteninhalt und zeigt bei einem Speicherkonflikt eine verständliche deutsche Meldung.

## Nicht-Ziele
- Kein frei eingegebenes HTML, CSS, JavaScript oder individuelles Pixel-Layout.
- Kein Angebotsrechner und keine Speicherung unvollständiger Kurzformular-Eingaben.
- Keine freien neuen Seitentypen außerhalb der vorgegebenen Sektionen; diese werden bei nachgewiesenem Bedarf ergänzt.

## Technical Requirements
- Security: Bild- und Inhaltszugriffe bleiben mandantenisoliert; der Kurzformular-Übergang darf keine Kontaktdaten in URL-Parametern preisgeben.
- Accessibility: Sichtbare Fokuszustände, ausreichende Kontraste, semantische Überschriften und Alternativtexte für Inhaltsbilder.
- Mobile: Die vollständige Startseite ist ab 375 px Breite ohne horizontales Scrollen nutzbar.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-21 · **Stack:** Next.js 16/shadcn-artige UI, FastAPI, PostgreSQL raw SQL + RLS, MinIO, Dokploy · **Branch:** main

### Ausgangspunkt und Grenze

PROJ-2 liefert bereits hostbasiertes öffentliches Routing, `website_settings`,
aktive `leistungsseite`-Einträge, MinIO-Bildspeicher und das vollständige
Anfrageformular. PROJ-12 ersetzt nur dessen starre Startseite durch eine
konfigurierbare Startseite. Leistungsdetailseiten, Anfrage-Submit, Domain,
Branding und Kontaktstammdaten bleiben ihre bestehenden Verantwortlichkeiten.

Der Baukasten ist absichtlich kein allgemeines CMS: feste Sektionstypen,
validierte Feldformen und feste CTA-Ziele. Kein HTML, CSS, JavaScript, freie
URLs oder neues Seitensystem.

### Flächen und Komponenten

```text
Öffentliche Betriebsdomain
└── Landingpage
    ├── Kopfbereich (bestehendes Logo, Navigation, Kontakt)
    ├── sichtbare, sortierte Baukasten-Sektionen
    │   ├── Hero mit Hintergrundbild und Kurzformular
    │   ├── Text mit Bild
    │   ├── Leistungen (bestehende aktive Leistungen)
    │   ├── Kennzahlen
    │   ├── Ablauf
    │   ├── FAQ
    │   ├── Kontakt
    │   └── Abschluss-CTA
    └── bestehender Footer

Angemeldete Betriebszentrale, nur Rolle Inhaber
└── Website-Einstellungen / Landingpage
    ├── Vorschau
    ├── Sektionsliste: hinzufügen, ein-/ausblenden, Reihenfolge, löschen
    ├── typenbezogener Editor
    ├── Bildaktion für Hero und Text-mit-Bild
    └── Konflikthinweis mit Neu-laden-Aktion

Bestehender Anfrage-Flow
└── vollständiges Anfrageformular, mit vorausgefülltem Name/Kontaktweg
```

Die öffentliche Renderer-Komponente kennt jeden erlaubten Typ explizit. Sie
ignoriert unbekannte oder unsichtbare Sektionen sicher. Texte umbrechen;
Bildbereiche haben eine gleichwertige Textvariante. Mobile Layouts sind ab
375 px einspaltig, Bild-/Textabschnitte wechseln dort nicht die Lesereihenfolge.

### Datenmodell, Ownership und Lesepfade

Alle neuen Tabellen tragen `mandant_id`, referenzieren den Mandanten und
erhalten RLS `FOR ALL` auf `current_setting('app.current_mandant_id')`. FastAPI
setzt diesen Kontext aus dem JWT für Inhaber-Endpunkte. Jede Repository-Query
filtert zusätzlich `mandant_id`. Öffentliche Lesewege lösen den Mandanten wie
PROJ-2 ausschließlich über die aktive angefragte Domain auf; die vorhandene
gezielte `SECURITY DEFINER`-Domainauflösung ist der einzige Zugriff vor einem
Mandantenkontext.

| Entität | Inhalt | Schreiber / Owner | nötige Lesepfade |
|---|---|---|---|
| `website_landingpage` (neu) | genau eine Startseite je Mandant: `id`, `mandant_id`, `version`, Zeitstempel | `POST /website-builder/startseite/initialisieren`, nur Inhaber; erstellt idempotent die Defaultseite. Jede Sektionsmutation erhöht `version`. | `GET /website-builder/startseite` für den Inhaber-Editor; Bestandteil von `GET /public/site` für die Betriebsdomain. |
| `website_section` (neu) | `id`, `mandant_id`, `landingpage_id`, Typ, sichtbarer Status, Position, typenvalidierter Inhalt, Zeitstempel | nur Inhaber über `POST/PATCH/DELETE /website-builder/sections*` und Reihenfolge-Endpunkt. | Builder-GET für Bearbeitung/Vorschau; `GET /public/site` liefert ausschließlich sichtbare Sektionen derselben Domain. |
| `website_section_bild` (neu) | ein optionaler MinIO-Objektpfad und Alt-Text je Hero-/Text-mit-Bild-Sektion | nur Inhaber mit `POST/DELETE /website-builder/sections/{id}/bild`; Upload ersetzt erst nach erfolgreicher Prüfung den alten Verweis. | Builder-GET zeigt eine kurzlebige Vorschau-URL; `GET /public/site` liefert nur für seine sichtbare Sektion eine kurzlebige Lese-URL und Alt-Text. |
| `website_settings` (bestehend) | Firmenname, Logo, Farbe, Telefon, E-Mail, Adresse, Öffnungszeiten, Über-uns | bestehendes `PATCH /website-settings` und `POST /website-settings/logo`, nur Inhaber. PROJ-12 schreibt diese Entität nicht. | bestehendes `GET /website-settings` vor dem Builder; `GET /public/site` für Kopf, Kontakt und Fallback-Inhalte. |
| `leistungsseite` (bestehend) | aktive Leistung, Titel, Kurzbeschreibung, Detailinhalt | bestehendes `PATCH /website-settings` durch Inhaber. PROJ-12 schreibt sie nicht. | bestehendes `GET /website-settings` vor Leistungsbearbeitung; `GET /public/site` liest nur aktive Leistungen für den Typ Leistungen; `GET /public/leistungen/{slug}` liest nur aktive Leistung derselben Domain. |
| `website_domains` (bestehend) | aktive Domain-Mandant-Zuordnung | ausschließlich Onboarding-Veröffentlichung, nicht der Baukasten. | Domainauflösung vor jedem öffentlichen `GET /public/*`; `GET /website-settings` zeigt Status im Editor. |
| `anfrage` und `anfragebild` (bestehend) | vollständige Anfrage und optionale Bilder des Interessenten | ausschließlich bestehendes `POST /public/anfragen` sowie dessen Upload-Pfad; der Baukasten schreibt beides nie direkt. | bestehendes Anfrageformular liest nur die flüchtige Kurzformular-Vorbelegung; die Betriebszentrale liest Anfragen über ihre bestehenden Vorgangs-/Anfragepfade. |
| Kurzformular-Übergabe (kein DB-Datensatz) | Name und mindestens Telefon oder E-Mail, nur temporär im Browser | Hero-Kurzformular schreibt nach Validierung nur in `sessionStorage`, hostgebunden; wird beim finalen Anfrage-Senden oder Abbruch gelöscht. | bestehendes `/site/anfrage` liest einmalig zum Vorbefüllen. Die bestehende `POST /public/anfragen` bleibt alleiniger Schreiber von `anfrage` und erzeugt bei Abbruch nichts. |

`website_section.inhalt` bleibt ein strukturiertes JSON-Feld, wird aber je Typ
durch Pydantic-Varianten serverseitig geprüft: Hero (Titel, Text, CTA), Text
mit Bild (Titel, Text), Leistungen (Titel, Einleitung, CTA), Kennzahlen
(Titel, Wert/Label-Paare), Ablauf (Titel, Schritt-Paare), FAQ (Titel,
Frage/Antwort-Paare), Kontakt (Titel, Einleitung, CTA) und CTA (Titel, Text,
CTA). CTA-Ziele sind nur `anfrage`, `leistungen` oder `kontakt`; der Renderer
bildet diese auf vorhandene öffentliche Pfade bzw. Anker ab. Damit existiert
kein unprüfbarer Linkpfad. Der Leistungs-Typ speichert keine Leistungs-IDs:
er zeigt immer die aktuelle, aktive Liste und seinen editierbaren neutralen
Leerzustand, wenn sie leer ist.

Die Initialisierung erzeugt die in den Akzeptanzkriterien genannten acht
Sektionen mit neutralen Defaulttexten und sichtbarem Status. Ein gelöschtes
oder ausgeblendetes Hero ist zulässig; mindestens eine sichtbare Sektion wird
nicht erzwungen. Die öffentliche Seite bleibt mit Header/Footer und den
verbleibenden sichtbaren Sektionen nutzbar.

### API-Contracts

Alle Builder-Endpunkte verlangen Bearer-JWT und `require_role("Inhaber")`.
`mandant_id` kommt ausschließlich aus dem serverseitig aufgelösten Nutzerkontext
(Session-Lookup zum JWT `sub`, `deps.py:get_current_user`), nie aus
Request-Body, Pfad oder Query.

- `GET /website-builder/startseite` liefert eigene Landingpage, alle Sektionen,
  Bildvorschauen und `version`; der Landingpage-Screen ruft ihn vor jeder
  Bearbeitung und nach einem Konflikt ab.
- `POST /website-builder/startseite/initialisieren` erzeugt die Defaultseite
  samt acht Defaultsektionen nur, falls noch keine existiert; wiederholter
  Aufruf liefert den bestehenden Zustand.
- `POST /website-builder/sections` fügt eine erlaubte Sektion am Ende hinzu;
  Request enthält nur `type` und erwartete `version`.
- `PATCH /website-builder/sections/{section_id}` ändert nur passende
  Text-/Listenfelder und `visible`; Request enthält erwartete `version`.
- `PUT /website-builder/sections/reihenfolge` nimmt die vollständige,
  duplikatfreie Liste der vorhandenen Sektions-IDs und erwartete `version`.
- `DELETE /website-builder/sections/{section_id}` entfernt Sektion und ihren
  Bildverweis; der zugehörige MinIO-Objektpfad wird mitgelöscht. Request trägt
  erwartete `version`.
- `POST /website-builder/sections/{section_id}/bild` nimmt ein Bild und
  Alt-Text für erlaubte Bildtypen an; gleiche bestehende Bildprüfung wie Logo
  (Format/Magic Bytes, Größenlimit) und erwartete `version`.
- `DELETE /website-builder/sections/{section_id}/bild` entfernt Bildverweis
  und Objekt, lässt die Textvariante der Sektion intakt; erwartete `version`.
- `GET /public/site` erweitert den bestehenden Public-Site-Contract um
  `sections` in sortierter Renderer-Form. Keine unsichtbare Sektion, kein
  Objektpfad, keine fremde/fehlende/inaktive Leistung.

Jede erfolgreiche Mutation liefert den vollständigen aktuellen Builder-Zustand
mit neuer `version`. Stimmt die erwartete Version nicht, liefert sie `409` mit
deutscher Konfliktmeldung und unverändertem Serverzustand. Der Editor verwirft
keine lokale Eingabe still; er bietet Neu-laden an. Das verhindert verlorene
Reihenfolgenänderungen bei paralleler Bearbeitung, ohne Echtzeit-Infrastruktur.

### Entscheidungen

- **Next.js statt Flutter:** Das Repository hat bereits eine Next.js-16-
  Oberfläche und die öffentliche Domain-Umschreibung in `nextjs_app/proxy.ts`.
  Eine zweite Frontend-Technologie würde den bestehenden Ablauf verdoppeln.
- **Eine Startseite, Tabellen für Struktur und Bild:** Sektionen müssen
  sortierbar, sichtbar und sicher löschbar sein; ein einzelnes Freitextfeld in
  `website_settings` könnte weder diese Regeln noch Bild-Lebenszyklus sauber
  abbilden.
- **Strukturierte Inhalte statt HTML:** Erfüllt Gestaltungsfreiheit innerhalb
  freigegebener Bausteine und schließt XSS, kaputte Layouts und fremde URLs an
  der Ursache aus.
- **Bilddateien in MinIO, nur Pfade in PostgreSQL:** folgt Logo-/Anfragebild-
  Muster; Datenbank bleibt für Daten, MinIO für Binärdateien. Öffentliche
  URLs sind kurzlebig und werden erst nach Domain-/Sektionsprüfung erzeugt.
- **Öffentlicher Mandant allein aus Hostname:** folgt `GET /public/site` und
  verhindert, dass ein Browser fremde Baukasteninhalte per ID abruft.
- **Kurzformular nur Browser-Übergabe:** keine neue PII-Tabelle und keine
  Kontaktwerte in URL-Parametern. Erst das vorhandene vollständige Formular
  kann eine Anfrage und damit einen Vorgang anlegen.
- **Optimistic Locking mit Page-Version:** kleinster belastbarer Schutz gegen
  parallele Sortierung; keine WebSockets, Sperrlisten oder Entwürfe nötig.

### Abhängigkeiten und Migration

- Keine neuen Frontend- oder Backend-Pakete. Vorhandene Next.js-,
  react-hook-form/Zod-, FastAPI/Pydantic- und MinIO-Muster reichen aus.
- Neue idempotente raw-SQL-Datei `backend/sql/010_website_landingpage.sql`
  nach bestehender `backend/sql/002_website.sql`-Konvention: drei Tabellen,
  Fremdschlüssel, eindeutige `(mandant_id, landingpage_id, position)`- bzw.
  Bildbeziehung, RLS-Policies und Lesereihenfolge-Index. Kein Alembic.
- Die bestehende `PublicSite`-Antwort ist rückwärtskompatibel zu erweitern;
  die aktuelle statische Startseiten-Renderer-Route wird erst durch den neuen
  Sektionsrenderer ersetzt, wenn `sections` geliefert wird.
- Dokploy behält die bestehende Next.js/FastAPI/MinIO-Auslieferung. Für die
  neue öffentliche Bildanzeige sind keine offenen MinIO-Buckets nötig.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-21 · **Verdict:** Architected

### Checklist
- [x] Component structure — Öffentliche Landingpage und Inhaber-Editor klar getrennt, jeder Sektionstyp explizit benannt, kein "irgendeine UI hier".
- [x] Data model — alle drei neuen Tabellen mit `mandant_id`, RLS `FOR ALL` auf `current_setting('app.current_mandant_id')`, Feldtypen je Sektionstyp über Pydantic-Varianten geprüft.
- [x] API shape — jeder Endpunkt mit Methode, Pfad, Rolle (`require_role("Inhaber")`); Akzeptanzkriterien-Abgleich zeigt jeden AC mit Endpoint-/Komponenten-Heimat.
- [x] Owner-Check — jede Entität in der Tabelle hat genau einen benannten Schreibpfad (neu: `/website-builder/*`; bestehend: `/website-settings`, `/public/anfragen` — PROJ-12 schreibt sie explizit nicht).
- [x] Lesepfad-Check — jeder Owner-Pfad hat dokumentierte Voraussetzungs-Lesepfade (z. B. Builder-GET vor jeder Mutation wegen `version`; Leistungen-Sektion braucht keinen Auswahl-Read, da sie immer die aktuelle aktive Liste zeigt statt IDs zu speichern).
- [x] Tech decisions — alle sieben Entscheidungen mit Begründung, nicht nur Auswahl.
- [x] Dependencies — keine neuen Pakete; gegen Code verifiziert.
- [x] Branch field — vorhanden (`main`).
- [x] Conflict-free — CodeGraph-Cross-Check: keine Kollision mit `website_landingpage`, `website_section`, `website_section_bild` oder `/website-builder/*`; nächste freie Migrationsdatei `010_website_landingpage.sql` kollidiert nicht mit 001–009.
- [x] Acceptance-criteria coverage — alle 10 ACs auf mind. einen Endpoint/eine Komponente abgebildet (Sektionstypen, Bild-Upload/-Entfernen, Kurzformular-Übergabe, Leistungs-Leerzustand, CTA-Ziele, Domain-Isolation, Versionskonflikt).

### CodeGraph-Cross-Check (Explore-Agent, gegen echten Code)
1. `GET /public/site` existiert (`routes.py:37`); `sections`-Feld fehlt im Schema noch — das ist erwartete neue Arbeit, kein Designfehler.
2. Domain-Auflösung über `website_domains` + SECURITY DEFINER existiert (`002_website.sql`, `repository.py:25`, Hostname-Härtung `routes.py:21-32`).
3. Bestehende Endpunkte `GET/PATCH /website-settings`, `POST /website-settings/logo`, `POST /public/anfragen`, `GET /public/leistungen/{slug}` alle vorhanden.
4. `nextjs_app/proxy.ts` Host-Rewrite existiert (Zeilen 29-46).
5. Bild-Validierung (Magic Bytes, Größenlimit) existiert als Helper `service.py:41-53`, wiederverwendbar für Sektionsbilder (neue Größenkonstante plausibel, kein Blocker).
6. `require_role("Inhaber")` existiert (`deps.py:87-93`), bereits mehrfach genutzt.
7. **Korrigiert:** `mandant_id` kam in der Spec-Formulierung fälschlich direkt "aus dem Token" — tatsächlich löst `deps.py:get_current_user` sie über Session-Lookup zum JWT-`sub` auf. Sicherheitseigenschaft (nie aus Client-Eingabe) bleibt unverändert; Formulierung in Sektion API-Contracts korrigiert.
8. Raw-SQL-Migrationskonvention (`backend/sql/0XX_*.sql`, kein Alembic) exakt wie behauptet, 001–009 vorhanden.

### Autonom behoben
- API-Contracts-Absatz präzisiert: `mandant_id`-Herkunft korrekt als serverseitiger Session-Lookup statt direkter JWT-Claim beschrieben (kein Sicherheits-, nur ein Genauigkeitsfehler).

### Offene Fragen
Keine. Owner- und Lesepfad-Check für jede Entität bestanden, keine Code-Kollisionen, keine offene Produktentscheidung.

## QA Test Results
**Getestet:** 2026-08-21 · **Tester:** jupiter-qa · **Verdict: READY** (keine Critical/High-Bugs)

### Akzeptanzkriterien
| # | Kriterium | Status |
|---|---|---|
| 1 | Öffentliche Startseite folgt Referenzaufbau (Kopf, Hero+Kurzformular, Über-uns, Leistungen, Ablauf, Kennzahlen, FAQ, Kontakt, CTA, Footer) | ✅ PASS — `section-renderer.tsx` deckt alle 8 Typen; `GET /public/site` liefert sie sortiert/sichtbar (eigener curl-Test gegen echte Postgres+RLS bestätigt) |
| 2 | Inhaber: Sektionen hinzufügen/entfernen/ein-ausblenden/sortieren | ✅ PASS — 8 Endpunkte, `page.tsx` UI vollständig (Pfeile hoch/runter, Löschen mit Bestätigung, Sichtbar-Checkbox); pytest deckt add/delete/reihenfolge |
| 3 | Sektion zeigt nur passende Felder; Textfelder ohne Überlauf 375px–Desktop | ✅ PASS (Code-Review) — `SectionEditor`/`InhaltFelder` sind typendiskriminiert; Renderer nutzt `whitespace-pre-wrap`, responsive Grid-Klassen (`sm:`/`md:`/`lg:`) durchgängig. **Browser-Viewport-Screenshot nicht möglich** (siehe Limitation) |
| 4 | Bild-Upload/-Ersetzen/-Entfernen für Hero/Text-mit-Bild, Textvariante ohne Bild nutzbar | ✅ PASS — eigener pytest-Redteam-Lauf + Dev-Tests bestätigen Upload/Delete/Ablehnung Nicht-Bild-Typ; Renderer zeigt "Kein Bild hinterlegt"-Fallback |
| 5 | Hero-Kurzformular (Name + mind. 1 Kontaktweg) übergibt an Anfrageformular | ✅ PASS (Code-Review) — `speichereKurzformular`/`liesKurzformular` via sessionStorage, `AnfragePage` übernimmt Vorgabe als defaultValues |
| 6 | Kurzformular erzeugt selbst keine Anfrage; Abbruch erzeugt keinen Vorgang | ✅ PASS — sessionStorage wird nur clientseitig gehalten, kein Backend-Schreibpfad vor `POST /public/anfragen` |
| 7 | Leistungssektion nutzt aktive PROJ-2-Leistungen, editierbarer Leerzustand bei 0 aktiven | ✅ PASS — eigener Live-Test: Testmandant mit 0 aktiven Leistungen liefert `leistungen: []`; Renderer zeigt neutralen Leerzustand mit Telefon/E-Mail-Fallback statt defektem Raster |
| 8 | FAQ/Kennzahlen/Ablauf/CTAs konfigurierbar, CTA-Ziele nur anfrage/leistungen/kontakt | ✅ PASS — Pydantic-`Literal`-Diskriminator erzwingt das serverseitig; eigener Redteam-Versuch mit `cta_typ: "javascript:alert(1)"` → 422 |
| 9 | Öffentliche Inhalte/Bilder nur über zugehörige Mandantendomain; Inhaber nur eigene Inhalte | ✅ PASS — eigener Redteam: Cross-Tenant PATCH/DELETE/Bild-Upload auf fremde Section → alle 404, Ziel-Section unverändert; öffentliche Sites per Host isoliert (eigener Live-Test mit 2 Domains) |
| 10 | Tastaturbedienbar, deutsche Beschriftungen, verständliche Fehlermeldungen | ✅ PASS (Code-Review) — native `<button>`/`<input>`/`<select>` mit `aria-label` je Zeile/Aktion, alle sichtbaren Texte deutsch, 409-Konfliktmeldung deutsch geprüft |

### Edge Cases (Code-Review, nicht alle live browser-verifizierbar)
- Gelöschtes/ausgeblendetes Hero → Seite bleibt mit Rest-Sektionen nutzbar: ✅ (kein "mind. 1 sichtbar"-Zwang im Code, Renderer ignoriert fehlende Typen sicher)
- Lange Texte umbrechen responsiv: ✅ Code (`whitespace-pre-wrap`, keine fixen Höhen) — visuell nicht verifizierbar (Limitation)
- Bild-Upload-Ablehnung bei falschem Format/Größe: ✅ PASS (pytest: `test_upload_bild_rejects_non_image`, deutsche Meldungen im Service)
- Fehlendes Bild kein Broken-Icon: ✅ Code — bedingtes Rendering, kein `<img>` ohne `bild.url`
- Kurzformular ohne Telefon/E-Mail wird abgelehnt: ✅ Code (`HeroKurzformular.onSubmit`-Validierung + deutsche Fehlermeldung)
- Inaktive/fremde Leistungen nie veröffentlicht: ✅ PASS — `list_active_leistungen` filtert serverseitig, kein IDs-Speichern im Sektionstyp
- Reihenfolge-Konflikt bei paralleler Bearbeitung → 409 deutsch, kein fremder Mandanteninhalt gespeichert: ✅ PASS (pytest `test_add_section_wrong_version_is_409` + eigener Redteam-Test)

### Security-Redteam (eigener, unabhängiger Testlauf)
11 selbst geschriebene Angriffstests (nicht die Dev-Tests) gegen laufende pytest-Fixture-API, alle 11 bestanden:
- Cross-Tenant PATCH/DELETE/Bild-Upload auf fremde Section → 404, keine Datenänderung
- Kein Token → 401; Nicht-Inhaber-Rolle (Buero) → 403
- Extra-Body-Feld `mandant_id` im Request wird ignoriert (Server liest `mandant_id` ausschließlich aus Session-Lookup, nie aus Body)
- CTA-Ziel außerhalb des Enums (`javascript:alert(1)`) → 422 (Pydantic Literal)
- SQLi-Payload im `type`-Feld → 422 (Pydantic Literal, kein Query-String-Interpolationspfad)
- HTML/Script im Textfeld wird als reiner String gespeichert (kein serverseitiges Escaping nötig — React escaped beim Rendern automatisch; keine `dangerouslySetInnerHTML`-Stelle im Renderer gefunden)
- Öffentliche Sites zweier Mandanten über unterschiedliche Hosts liefern getrennte Inhalte
- Veraltete `version` → 409 mit deutscher Konfliktmeldung, Serverzustand unverändert

Zusätzlich Live-Verifikation gegen echte PostgreSQL 16 (Docker) mit angewendeten RLS-Policies (nicht nur die SQLite-Testsuite): Initialisierung, Cross-Tenant-Isolation und `GET /public/site` mit `sections` bestätigt funktionsfähig unter echtem RLS.

### Regressionstest
- Backend: `backend/.venv/bin/python -m pytest` → **217 passed**, keine Fehlschläge (inkl. 18 Website-Builder-Tests des Dev + Kern-Domänen Kunden/Vorgänge/Rechnungen/Termine/Angebote/Onboarding/E-Mail unverändert grün).
- Next.js: `tsc --noEmit` exit 0, `next build` exit 0 (alle Routen inkl. `/website-builder` und `/site` kompilieren, keine neuen Warnungen).

### Bugs
Keine Critical/High/Medium-Bugs gefunden. Keine Low-Bugs dokumentiert.

### Limitation (ehrlich vermerkt, siehe abc-qa-e2e §6/§10)
Der Browser-Tool-Daemon (agent-browser/Chromium headless) in dieser Umgebung hing bei jedem `browser_navigate`-Versuch (Timeout nach 60s, verwaiste Chrome-Subprozesse). Trotz Neuinstallation (`npx agent-browser install --with-deps`) und mehrfachem Retry keine funktionierende Navigation möglich — **kein Hermes/Umgebungsproblem des Features**, sondern ein Tooling-Defekt in dieser QA-Session. Als Ersatz: Live-API-Smoke gegen echten uvicorn-Prozess + echte PostgreSQL 16 (Docker) mit angewendeten RLS-Migrationen, SSR-HTML-Abruf (`curl` gegen `next start`-Build) zur Bestätigung, dass die Seite ohne Serverfehler rendert, und Code-Review der responsiven Klassen für AC3/Edge-Cases. Empfehlung: vor dem nächsten Browser-E2E-Lauf `agent-browser`-Daemon neu starten oder Playwright direkt nutzen.

Hinweis: `backend/sql/009_rechnungen.sql` (PROJ-8, nicht PROJ-12) hat einen vorbestehenden zirkulären FK-Bug (`rechnung.fassung_id → rechnung_fassung`, aber `rechnung_fassung` wird erst danach angelegt) — fällt nur beim frischen `apply_migrations.py`-Lauf auf leerer DB auf (pytest nutzt SQLite-Fixtures, nicht betroffen). Nicht PROJ-12-Scope, hier nur zur Kenntnisnahme dokumentiert; separates Ticket empfohlen.

### Nachtest Bugfix 2026-08-23 — Bild-URL im Editor (Produktion gemeldet)

**Bug:** Nach erfolgreichem Bild-Upload im Sektion-Editor (`POST /website-builder/sections/{id}/bild` → 200 OK) lieferte die Antwort eine rohe MinIO-Presigned-URL (Port 9000, `https://…:9000/...`) statt der proxied App-HTTPS-URL. Browser: `net::ERR_SSL_PROTOCOL_ERROR`, Bild blieb im Editor unsichtbar. Ursache: `_public_bild()` in `backend/app/features/website/builder_service.py:56` (Rückgabepfad für `get_builder_state` → Upload/Patch/Delete-Response) wurde vom Fix in 9645d3d ("Serve section images through app HTTPS") **nicht** mit erfasst — nur `public_sections()` (Zeile 252, öffentliche Landingpage `/public/site`) war bereits korrekt.

**Fix:** `_public_bild()` liefert jetzt ebenfalls `f"/public/sections/{section['id']}/bild"` statt `storage_mod.storage.presigned_get_url(...)` — identisches Muster wie der bereits gefixte Pfad.

**Test:**
- Bestehender Test `test_upload_and_delete_section_bild` (`backend/tests/features/website/test_website_builder.py:212`) asserte bisher explizit die kaputte URL (`.startswith("memory://")`, die Storage-Test-Doubles-URL) — der Bug war damit im Test selbst als "erwartet" festgeschrieben und wurde deshalb nicht gefangen. Assertion korrigiert auf `== f"/public/sections/{hero['id']}/bild"`.
- `test_public_section_bild_uses_same_origin_url` (bereits vorhanden, Zeile 239) deckt den öffentlichen Pfad weiterhin ab — unverändert grün, keine Regression durch den Fix.
- Volle Backend-Suite (`conda run -n Dashboard --no-capture-output python -m pytest backend/`): **alle Tests grün**, keine Regression.

**Nicht getestet (Scope-Lücke, vorbestehend, nicht durch diesen Fix verursacht):** Format-Coverage nur PNG + Non-Image-Rejection; kein expliziter Test für JPEG/GIF/WEBP-Upload trotz `_sniff_image_ext`-Unterstützung aller vier Formate. Browser-Live-Test (Drag&Drop, visuelle Anzeige) nicht durchgeführt — kein Browser-Tool in dieser Session verfügbar; Backend-Contract-Test + Code-Review als Ersatz. Empfehlung: nach Deploy einmal manuell im Browser bestätigen (Bild hochladen, Editor-Vorschau + öffentliche Landingpage prüfen).

**Bug-Schwere:** High (Kernfunktion Bild-Upload im Editor de facto unbenutzbar) — behoben, keine offenen Critical/High-Bugs.

**Production-Ready:** JA, für diesen Fix. Vor Redeploy empfohlen: WebP-Konvertierung/Optimierung als separates Feature aufnehmen (aktuell kein Resize/Kompression — vom Nutzer als "später" eingestuft, nicht Teil dieses Fixes).

## Deployment
**Production URL:** https://bizos.app.msce.info
**Deployed:** 2026-08-22 · **Version:** 0.1.9

- Frontend rebuilt from `main` after the section-switch editor fix.
- Production smoke test: `/website-builder` and `/api/health` return 200.
- Browser smoke test pending: hard-refresh, then switch through all section types.
