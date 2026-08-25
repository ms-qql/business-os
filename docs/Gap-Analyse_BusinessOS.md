# Gap-Analyse: BusinessOS PRD & INDEX vs. Ent1Pro & FastMove

**Stand:** 2026-08-23
**Verglichene Dokumente:**
- `PRD.md` und `INDEX.md` (BusinessOS, Ist-Stand)
- `Brainstorm 2.md` (BusinessOS, Vorstufe zum PRD)
- `Ent1Pro_PRD.md` (Wettbewerber, Entrümpelung/Haushaltsauflösung, aus Website + Admin-Screenshots rekonstruiert)
- `FastMove_PRD.md` (Wettbewerber, Umzugsunternehmen, aus Landingpages + Produkttour rekonstruiert)

**Hinweis:** Ent1Pro- und FastMove-PRDs sind selbst rekonstruierte Dokumente mit offenen Punkten (z. B. FastMove ohne Preisseite). Die dort dokumentierten Funktionen sind Marketing-/Screenshot-Belege, keine geprüfte Spezifikation — als Vergleichsmaßstab für "was Kunden in dieser Kategorie erwarten" aber gut belastbar.

---

## 0. Wichtigster Befund zuerst: Piloten-Mismatch

Deine Nachricht sagt: *"Es soll ein übergreifendes CRM- und Webseiten-System sein, welches für viele Betriebe genutzt werden soll. Ein Entrümpelungsservice wird ein Pilot sein."*

Das aktuelle `PRD.md` sagt etwas anderes: Titel **"Business OS für kleine SHK-Betriebe"**, Vision, Zielgruppe, Produktversprechen und die komplette Roadmap sind durchgängig auf SHK-Service zugeschnitten ("Geführte SHK-Website", Entscheidungstabelle "Startsegment: SHK-Service"). Entrümpelung taucht in `PRD.md` und `INDEX.md` **kein einziges Mal** auf. `INDEX.md` zeigt zudem, dass PROJ-1 bis PROJ-8 sowie PROJ-12 bereits **Deployed** sind — also SHK-spezifisch gebaut, nicht als konfigurierbares Branchenpaket.

Das ist keine Kleinigkeit, weil die zentrale Architekturentscheidung aus dem Brainstorm — *"Segment-Module sind Konfiguration, kein Code"* (#27), verankert als PROJ-20 *"Branchenpaket als Konfigurations-Bundle"* — im PRD nur als eine Zeile unter P1 auftaucht ("Branchenpakete: weitere Gewerke als konfigurierte Vorlage") und **ohne jede Spezifikation, ohne INDEX-Ticket, ohne Zeitpunkt vor dem zweiten Segment**. Wenn Entrümpelung jetzt der Pilot wird, ist genau diese Architektur die Voraussetzung dafür — nicht ein Nice-to-have für später.

Zwei Wege, das aufzulösen (Entscheidung nötig, siehe Abschnitt 6):

1. **Entrümpelung ersetzt SHK als V1-Pilot.** Dann müssen Vision, Zielgruppe, Produktversprechen und Roadmap in `PRD.md` neu geschrieben werden — nicht nur ergänzt. Die bereits deployten SHK-spezifischen Teile (Website-Formular, Textbausteine) müssten geprüft werden, was davon SHK-hart-codiert ist.
2. **SHK bleibt V1, Entrümpelung wird der Beweis für die Branchenpaket-Architektur (zweites Segment).** Dann muss PROJ-20 vorgezogen werden, *bevor* Entrümpelung als Pilot startet — sonst entsteht laut Brainstorm selbst Fail #45 ("Zu viele Segmente zu früh").

Beide Wege sind machbar, aber das PRD muss explizit sagen, welcher gilt. Aktuell tut es das nicht.

> **Entscheidung (2026-08-23):** Weder noch — **Doppel-Pilot**. Das PRD wird von Anfang an branchenneutral geschrieben; SHK und Entrümpelung werden ab V1 als zwei gleichzeitig bediente Branchenpaket-Konfigurationen behandelt, nicht als Nachfolge oder Vorrang. Das bedeutet für Schritt 2 konkret: PROJ-20 (Branchenpaket als Konfigurations-Bundle) rückt von P1 auf P0 vor und wird Voraussetzung, nicht Nebenprodukt, für die restliche V1-Roadmap. Vision, Zielgruppe und Produktversprechen im PRD müssen branchenneutral umformuliert werden (weg von "SHK-Betriebe", hin zu "Handwerks- und Dienstleistungsbetriebe" o. ä.), und die bereits deployten SHK-spezifischen Teile (v. a. PROJ-2 Website/Formular) müssen darauf geprüft werden, was davon hart auf SHK codiert ist und ins Konfigurationsmodell wandern muss.

---

## 1. Inhaltliche Lücken

### 1.1 Kernhebel aus dem Brainstorm fehlen im PRD komplett

Der Brainstorm hat zwei explizite Hebel benannt und mit ⭐ markiert: **Auto-Triage** (Hebel 1, Idee #2) und **automatische Angebotserstellung** (Hebel 2, Idee #5). Hebel 2 ist im PRD als "Angebote und PDF-Versand" (P0) vertreten. **Hebel 1 — Auto-Triage — kommt in `PRD.md` und `INDEX.md` nicht vor.** Ebenso fehlen, obwohl in Runde 8 des Brainstorms explizit ins Core-Paket aufgenommen:

| Aus Brainstorm (Core, #62–#66) | Im PRD.md vorhanden? |
|---|---|
| Auto-Triage mit Ampel (#2, #43) | Nein |
| Kapazitätsangabe als Triage-Eingang (#63) | Nein |
| Absage-Funktion mit Textbausteinen (#62) | Nein |
| Stammkunden-Vorrang (#66) | Nein |
| Freigabe-ohne-Änderung-Quote als Nordstar-Metrik (#52) | Nein — "Erfolgsmessung" hat 4 andere Metriken, keine davon misst Entwurfsqualität |

Das ist die größte fachliche Lücke unabhängig vom Piloten-Thema: Ohne Triage ist "Entlastung statt Geschwindigkeit" (die im Brainstorm explizit als Neuausrichtung beschlossene Positionierung, Runde 8) im PRD nicht mehr eingelöst — das Produktversprechen im PRD ("weniger verlorene Anfragen, weniger Büro nach Feierabend") setzt Triage eigentlich voraus, aber die Roadmap liefert sie nicht. Weder Ent1Pro noch FastMove haben ein Triage-/Ampel-Konzept — das wäre also weiterhin ein Alleinstellungsmerkmal, aber nur, wenn es im PRD auftaucht.

**Interessant für die Entrümpelung-Pilotierung:** Ent1Pro (der direkte Entrümpelung-Wettbewerber) hat *kein* Triage/Ampel-Feature — sortiert nicht nach Passung/Deckungsbeitrag. Das bestätigt, dass Auto-Triage weiterhin ein valider Differenzierer wäre, gerade im Piloten-Segment.

### 1.2 Branchenspezifische Datenerfassung fehlt als Konzept

Beide Wettbewerber lösen "wie kommt die Branche ins System" konkret, aber unterschiedlich:

- **Ent1Pro:** KI-gestützter Form-Builder — Freitext rein, Formularfelder raus, mit 12 Feldtypen, Mehrstufigkeit, 3 Einbindungsvarianten (Link/iframe/Script).
- **FastMove:** Raumbasierte Inventaraufnahme (Zimmer → Objekte → Menge → automatische Volumenberechnung).

Das BusinessOS-PRD hat "Anfrage-Datenmodell + Web-Formular" (PROJ-3 in Brainstorm-Liste) und "Rückfragen-Automat mit gewerkspezifischer Fragenliste" (V1.1), aber nirgends spezifiziert, *wie* ein Formular oder eine Objekterfassung pro Branche konfiguriert wird, wer es pflegt (Betreiber vs. Betrieb vs. KI-Assistent) und in welchem Format (Feldtypen, Validierung, Embed-Optionen). Für Entrümpelung ist "m²-Fläche → Sofortpreis" (Ent1Pro) ein sehr konkretes Muster, das im BusinessOS-PRD keine Entsprechung hat — die "Schnellkalkulation" fehlt komplett; PRD kennt nur "Angebote aus Positionen", nicht "Sofortpreis aus einer Kennzahl".

**Empfehlung für Schritt 2:** Ein eigener Abschnitt "Formular- und Kalkulationskonfiguration je Branchenpaket" mit mindestens: Feldtypen-Katalog, Mehrstufigkeit, Einbindungsvarianten, Verknüpfung zur Preisliste (m²/m³/Pauschale/Position), und wer diese Konfiguration pflegen darf.

### 1.3 Angebote: Status-Tracking und E-Signatur fehlen

FastMove trackt pro Angebot, ob es geöffnet/angenommen/mit Rückfrage versehen wurde, und bietet Online-Signatur direkt im System. Das BusinessOS-PRD hat nur zeitbasiertes Nachfassen (3/7/14 Tage) ohne echten Lesestatus — das ist strukturell schwächer, weil "nachfassen nach 3 Tagen" bei einem bereits angenommenen, aber noch nicht rückgemeldeten Angebot unnötig nervt. E-Signatur ist im BusinessOS-PRD nirgends erwähnt (auch nicht als Nicht-Ziel) — sollte zumindest bewusst vertagt werden statt implizit zu fehlen, besonders weil größere Aufträge (Umzug, Haushaltsauflösung) genau davon profitieren würden.

### 1.4 DSGVO-Paket ist im PRD nur eine Überschrift, bei Ent1Pro ein Produktbestandteil

Das BusinessOS-PRD nennt unter Rahmenbedingungen "Datenschutz nach DSGVO: Mandantentrennung, Zugriff nach Rolle, transparente Verarbeitung, Lösch- und Exportmöglichkeit" und in der Roadmap (P1) "Datenschutz, Datenexport und Aufbewahrung". Ent1Pro liefert dagegen konkret vor: automatisch geführtes Verarbeitungsverzeichnis (Art. 30, druckbar, mit Rechtsgrundlage/Speicherdauer je Verarbeitungstätigkeit), AVV-Template-Generator, DPIA-Unterstützung, Self-Service-Portal für Betroffenenrechte (Art. 15/17/20), Audit-Log (Admin-Zugriffe, 365 Tage), Feldverschlüsselung sensibler Daten (AES-256-GCM). Da DSGVO im BusinessOS-PRD explizit als Rahmenbedingung *und* als P0-Verkaufsargument in Runde 4 des Brainstorms (#32–#34, #50) auftaucht, ist die fehlende Tiefe hier ein Risiko: "Wo liegen meine Kundendaten?" (Fail #50) bleibt unbeantwortet, solange PROJ-11 ("Datenschutz, Datenexport und Aufbewahrung", P1, noch Proposed) nicht konkretisiert ist.

**Konkrete Lücke:** Kein automatisch geführtes Verarbeitungsverzeichnis, kein AVV-Generator, kein Audit-Log, keine Aussage zu Feldverschlüsselung — alles vier bei Ent1Pro Standard, alle vier im BusinessOS-PRD nicht spezifiziert.

### 1.5 Kunden-Status-Link ist aus dem PRD verschwunden

Brainstorm-Idee #10 ("Paketverfolgung für Handwerksaufträge") wurde in der Konvergenz explizit in CORE V1.1 aufgenommen (Abschnitt 3.2) und als PROJ-18 gelistet. Im aktuellen `PRD.md` und `INDEX.md` taucht sie nirgends mehr auf — auch nicht als P1/P2-Punkt. FastMove hat zwar keinen identischen Kundenlink, aber die "Status-Tracking"-Idee bei Angeboten zeigt, dass Endkunden-Transparenz in dieser Produktkategorie erwartet wird. Sollte entweder bewusst gestrichen (mit Begründung) oder wieder aufgenommen werden.

### 1.6 CSV-/Buchhaltungs-Export fehlt

Beide Wettbewerber positionieren sich explizit *nicht* als Buchhaltungssoftware, liefern aber beide einen einfachen CSV-Export mit Kompatibilitätsangabe zu DATEV/lexoffice/sevDesk (Ent1Pro) bzw. kündigen zumindest Berichte/Reporting-Module an (FastMove). Das BusinessOS-PRD schließt Buchhaltung/DATEV-Integration explizit als Nicht-Ziel aus — das ist richtig für *Integration*, sagt aber nichts zu einem simplen *Export*. Für Steuerberater-Übergabe (in Runde 4 als Vertriebskanal identifiziert, #30) ist ein CSV-Export der niedrigschwelligste Baustein und fehlt komplett im PRD.

### 1.7 Kanalüberwachung/Alarmierung ist im PRD verwässert

Brainstorm Fail #36/#48 macht "stille Fehler" (Postfach nicht erreichbar, Token abgelaufen) zum expliziten Core-Requirement mit Dashboard-Warnung *und* E-Mail-Alarm. Im PRD.md taucht das nur implizit unter "E-Mail-Inbox und Antwort" auf, ohne eigene Zeile für Monitoring/Alarmierung. INDEX.md hat dafür ebenfalls kein eigenes Ticket. Sollte als eigener Punkt (mind. als Akzeptanzkriterium von PROJ-4) sichtbar gemacht werden.

### 1.8 Wettbewerbspositionierung fehlt im PRD

Runde 7 des Brainstorms hat sehr bewusst herausgearbeitet, was verteidigbar ist (gepflegte Preis-/Textbausteinbibliothek, Rückkopplung gewonnen/verloren, Kanalzuverlässigkeit, begleitetes Onboarding) und einen Abgrenzungssatz formuliert ("Andere Handwerkersoftware fängt beim Auftrag an. Wir fangen bei der Anfrage an…"). Davon ist im PRD nichts übernommen. Das ist strukturell auffällig, weil sowohl Ent1Pro als auch FastMove in ihren (rekonstruierten) PRDs jeweils eine Abgrenzung kommunizieren ("kein Lead-Generator" bzw. Kernthese "drei Probleme hängen zusammen") — das BusinessOS-PRD hat keine Entsprechung, obwohl die Vorarbeit dazu bereits geleistet wurde.

---

## 2. Strukturelle Lücken

### 2.1 PRD.md ↔ INDEX.md sind nicht deckungsgleich

- PRD.md-Roadmap hat 16 Zeilen (8× P0, 5× P1, 3× P2), INDEX.md hat 12 PROJ-Einträge. Für P1 "KI-Assistenz" und "Branchenpakete" sowie für alle drei P2-Punkte existiert **kein PROJ-Ticket** — sie sind in der Roadmap versprochen, aber im Tracking-Dokument nicht vorhanden.
- PRD.md-Roadmap hat keine ID-Spalte; Zuordnung zu INDEX-PROJ-IDs ist nur über Feature-Namen möglich und teils uneindeutig (z. B. PRD-Zeile "Mobile Monteuransicht und Automationen" entspricht zwei getrennten INDEX-Einträgen, PROJ-9 und PROJ-10).
- Der PROJ-Nummernkreis in `Brainstorm 2.md` (PROJ-1 … PROJ-24, inkl. Auto-Triage, Absage-Funktion, Recruiting-Modul) und der in `INDEX.md` (PROJ-1 … PROJ-12) sind **unterschiedliche Nummerierungen mit teils gleichen IDs für andere Inhalte** (z. B. Brainstorm-PROJ-5 = "Auto-Triage: Klassifizierung, Ampel, Filteransichten", INDEX-PROJ-5 = "Angebote: Positionen, PDF, Freigabe und Versand"). Das ist verwirrend, wenn beide Dokumente nebeneinander referenziert werden — spätestens beim Anlegen neuer Tickets sollte klar sein, welcher Nummernkreis der gültige ist.

### 2.2 INDEX.md: Spalte "ImmoCRM-Reuse" wird zweckentfremdet

Bei PROJ-3, PROJ-6, PROJ-8 stehen in der Spalte "ImmoCRM-Reuse" keine Reuse-Angaben, sondern Deployment-Status, Versionsnummern und QA-Ergebnisse (z. B. "Deployed 2026-08-17, v0.1.2 · biz.app.msce.info; QA bestanden 6/6 AC…"). Das ist wertvolle Information, aber am falschen Ort — sie gehört in eine eigene Spalte (z. B. "Deployment/QA-Status"), sonst wird die Spalte für ihren eigentlichen Zweck (Wiederverwendungsgrad aus ImmoCRM, siehe `PRD.md` Abschnitt "Wiederverwendungsentscheidung") unbrauchbar, sobald ein Feature deployed ist.

### 2.3 Fehlende Abschnitte gegenüber der Wettbewerbs-PRD-Struktur

Beide Wettbewerbs-PRDs (obwohl rekonstruiert) haben eine vollständigere Dokumentstruktur als `PRD.md`:

| Abschnitt | Ent1Pro/FastMove | BusinessOS PRD.md |
|---|---|---|
| Technische Rahmenbedingungen (Stack, Hosting, Security) | Ja, eigener Abschnitt | Nein — Stack-Entscheidungen (FastAPI/Postgres/RLS, MinIO, Dokploy, Next.js) stehen nur im Brainstorm, nicht im PRD |
| Preis-/Bereitstellungsmodell | Ja (bei FastMove als Lücke markiert, bei Ent1Pro vollständig) | Nicht vorhanden — evtl. bewusst, da internes PRD, aber Trial-/Onboarding-Flow hat Produktauswirkung |
| Wettbewerbsvergleich/Abgrenzung | Ja, beide | Nein (siehe 1.8) |
| Offene Punkte/Risiken (itemisiert) | Ja, beide, mit nummerierter Liste | Nur indirekt über "Aus vorigem Brainstorm bewusst vertagt" — kein laufendes Risiko-Log |
| Versionierung/Changelog | Ja (Ent1Pro nennt v2.4.1) | Nein — PRD.md hat nur "Stand: 2026-08-16", INDEX.md dagegen Versionsnummern (v0.1.2 … v0.1.10) ohne Rückbezug zum PRD |
| Quellenanhang/Nachvollziehbarkeit | Ja, beide | Entfällt (BusinessOS-PRD ist Primärquelle, kein Rekonstruktionsdokument) |

### 2.4 Branchenpaket-Architektur ist strukturell unterrepräsentiert

Der Brainstorm bezeichnet PROJ-20 ("Branchenpaket als Konfigurations-Bundle") explizit als *"strategisch das wichtigste Ticket der Liste"*. Im PRD.md ist die entsprechende Zeile ("Branchenpakete: weitere Gewerke als konfigurierte Vorlage statt eigener Anwendung") eine von fünf P1-Zeilen unter vielen — keine eigene Sektion, kein Verweis auf die Lock-in-/Architektur-Überlegungen aus Brainstorm Runde 6, kein INDEX-Ticket. Angesichts des jetzt zweiten Piloten (Entrümpelung) sollte das eine eigene PRD-Sektion werden, nicht eine Roadmap-Zeile.

### 2.5 Nordstar-Metrik fehlt in "Erfolgsmessung"

`PRD.md` Abschnitt "Erfolgsmessung" hat vier Kennzahlen (Vollständigkeitsquote Webanfragen, Onboarding-Erfolg, 5-Minuten-Angebot, Sichtbarkeit am Vorgang). Der Brainstorm identifiziert dagegen explizit die **Freigabe-ohne-Änderung-Quote** als *"die zentrale Produktkennzahl, nicht Logins und nicht Anzahl Anfragen"* (#52) sowie Entlastungskennzahlen (gesparte Büro-Stunden, Anteil automatisch erledigter Anfragen, Deckungsbeitrag je Auftrag, #68). Keine davon ist in PRD.md übernommen — die dortigen Metriken sind alle Prozess-Vollständigkeitsmetriken, keine Qualitäts- oder Entlastungsmetriken.

---

## 3. UI-Vorschlag für die App

### 3.1 Ausgangslage aus den Screenshots

**Ent1Pro** (siehe Dashboard, Kunden, Anfragen, Formularerstellung): klassisches SaaS-Admin-Layout — linke Sidebar mit Gruppen (Übersicht/Module/Planung/Support), KPI-Kacheln oben, Datentabellen mit Filter-Pills und Paginierung, Badges für Status/Quelle, Split-Panel-Formulare (links Konfiguration, rechts Einbindung/Vorschau), Onboarding-Hinweisbanner bei fehlenden Voraussetzungen ("Claude API Key fehlt"), Accessibility-Controls (A-/A+, Dark Mode) direkt in der Topbar, ein durchgängiger runder Floating-Action-Button unten rechts.

**FastMove** (siehe Kundenliste, Projektübersicht, Projektdetail): reduzierter, heller, weniger dichte Sidebar (nur 7 Punkte), Projekt als Tab-Struktur (Kundendaten/Beladeort/Entladeort/Service), Raum-Karten als Kanban-artige Kacheln mit Objektanzahl, Status als einfaches Dropdown-Feld statt Badge-System, Consent-Toggle direkt im Datensatz.

Beide sind für **eine** Branche gebaut. BusinessOS muss dasselbe Aufgabenspektrum abdecken, aber mandantenfähig, markenneutral im Kern und über ein Branchenpaket konfigurierbar sein — das ist der Hauptunterschied zur UI-Gestaltung.

### 3.2 Leitprinzipien

1. **Der Posteingang ist die Startseite, nicht das Dashboard.** Das Produktversprechen ist "keine verlorene Anfrage" — Büro-Nutzer sollten beim Einloggen zuerst die neuen/offenen Anfragen sehen (mit Ampel/Triage-Status, falls Abschnitt 1.1 umgesetzt wird), nicht KPI-Kacheln. Ent1Pro zeigt das Dashboard zuerst; für BusinessOS ist das aus Produktsicht die falsche Reihenfolge.
2. **Der Vorgang ist die Klammer, nicht die einzelnen Module.** Statt getrennter Top-Level-Module für Kunden/Angebote/Rechnungen (Ent1Pro-Muster) sollte ein Vorgang eine Detailseite mit Tabs sein (FastMove-Muster, aber generalisiert): Übersicht, Kommunikation (E-Mail-Verlauf inkl. Antwortentwurf), Angebot, Termin, Rechnung, Dokumente. Das verhindert Fail #44 ("zweiter Posteingang") strukturell, weil alles am Vorgang hängt statt in Parallelmodulen zu leben.
3. **Progressive Freischaltung statt Fehlermeldung.** Ent1Pros Muster "Modul gesperrt/Hinweisbanner, wenn Voraussetzung fehlt" (Claude-Key-Banner) ist genau die richtige Antwort auf Fail #41 ("leere Preisliste") — als generelles UI-Pattern übernehmen: Angebotsmodul bleibt sichtbar, aber mit Erklärbanner gesperrt, bis N Preislistenpositionen erfasst sind.
4. **Whitelabel auch im Backend, nicht nur auf der öffentlichen Website.** Weder PRD.md noch Brainstorm klären, ob die Büro-/Inhaber-Oberfläche selbst das Branding des Betriebs trägt (Logo/Farbe in der Sidebar) oder ein neutrales "BusinessOS" zeigt. Ent1Pro und FastMove zeigen jeweils ihre eigene Marke im Admin-Bereich — für ein Whitelabel-Produkt ist das vermutlich der falsche Ansatz. Empfehlung: Sidebar-Header zeigt Betriebslogo + -name, ein kleiner "Powered by BusinessOS"-Hinweis unten. Das ist eine offene Entscheidung, die ins PRD gehört (siehe Abschnitt 4).
5. **Drei getrennte Erlebnisse, nicht eine Oberfläche mit Rechtefiltern** — deckt sich mit Brainstorm-Idee #9 und den bereits definierten Rollen.

### 3.3 Rollen- und Navigationsstruktur

**Inhaber (Desktop, volle Ansicht):**
Sidebar-Gruppen wie bei Ent1Pro, aber mit Posteingang an erster Stelle:
`Posteingang` (Anfragen, alle Kanäle, mit Ampel) → `Vorgänge` (Kanban: Neu/Qualifiziert/Angebot/Termin/Erledigt/Abgesagt) → `Kunden` → `Preisliste & Textbausteine` → `Team` → `Auswertung` (Freigabe-Quote, Entlastungskennzahlen, Umsatz) → `Einstellungen` (Branding, Kanäle, Kapazität, DSGVO-Center).
Dashboard entfällt als eigener Menüpunkt zugunsten einer kompakten Kennzahlenzeile oben auf der Posteingang-Seite (KPI-Kacheln wie bei Ent1Pro, aber reduziert auf: offene Anfragen, Angebote unterwegs, Termine heute/morgen, überfällige Rechnungen).

**Büro (Desktop, Arbeitsansicht):**
Gleiche Struktur wie Inhaber, ohne `Auswertung` (oder nur eingeschränkt) und ohne Umsatzzahlen in der Preisliste, falls der Betrieb das so möchte — Rechtekonfiguration wie in PRD.md Rollen-Abschnitt bereits vorgesehen.

**Monteur (Mobile/PWA):**
Kein Sidebar-Menü, eine Ein-Spalten-Ansicht: Terminkarten gruppiert nach Heute/Morgen (direkt Ent1Pro-Dashboard-Widget-Muster übernehmen — das funktioniert bereits gut), pro Termin: Adresse, Kontakt, Checkliste, Foto-Upload, "Erledigt"-Button. Keine Preise sichtbar (PRD-Anforderung bereits vorhanden, UI muss das konsequent umsetzen — auch keine Preisspalten in irgendeiner Monteur-Ansicht der Preisliste, da Monteure dort keinen Zugriff haben).

**Kunde (öffentlich, kein Login):**
Zwei öffentliche Oberflächen: die konfigurierbare Landingpage/Anfrageformular (bereits in PRD.md abgedeckt) und — falls Abschnitt 1.5 wieder aufgenommen wird — eine schlanke Status-Trackingseite im Betriebs-Branding ("Ihre Anfrage — Status: Angebot in Arbeit").

### 3.4 Vorgang-Detailseite (Kernbildschirm, neu ggü. beiden Wettbewerbern)

Empfohlene Tab-Struktur, angelehnt an FastMoves Projekt-Tabs, aber branchenneutral:

| Tab | Inhalt |
|---|---|
| Übersicht | Stammdaten, Status (Ampel + Textstatus), Kapazitäts-/Terminbezug, Quelle (Kanal-Badge wie bei Ent1Pro) |
| Kommunikation | E-Mail-Verlauf im Vorgang, Antwortentwürfe zur Freigabe, Absage-Textbausteine |
| Angebot | Positionen aus Preisliste, PDF-Vorschau, Freigabe-Button, Status (Entwurf/versendet/geöffnet/angenommen/abgelehnt) |
| Termin | Terminvorschlag/-bestätigung, Zuweisung an Team-Mitglied |
| Rechnung | PDF-Rechnung, Zahlungsstatus |
| Dokumente | Fotos, Anhänge, branchenspezifische Zusatzobjekte (z. B. Fundstücke bei Entrümpelung, Rauminventar bei Umzug) — dieser Tab ist der Erweiterungspunkt für Branchenpakete |

### 3.5 Designsystem-Grundzüge

- **Statusfarben/Ampel** als durchgängiges System: Grün/Gelb/Rot für Triage, konsistent auch für Angebotsstatus und Rechnungsstatus (überfällig = Rot, wie bereits bei Ent1Pro für "Überfällig"-Kachel zu sehen).
- **Ein Akzentton pro Mandant**, neutrale Grautöne im Rest der Oberfläche (verhindert Konflikt zwischen Systemfarbe und Betriebs-Branding).
- **Datentabellen** mit Filter-Pills nach Quelle/Status (Ent1Pro-Muster gut übertragbar), Paginierung konfigurierbar, Kanban umschaltbar wo sinnvoll (Vorgänge, nicht Kunden).
- **Barrierefreiheit:** Schriftgrößen-Toggle (A-/A+) wie bei Ent1Pro sinnvoll übernehmen — Zielgruppe (Inhaber 40+, oft ohne Software-Routine) profitiert davon konkret.
- **Empty-/Gate-States** als eigenes wiederverwendbares Komponentenmuster (siehe 3.2, Punkt 3).
- **Formular-/Konfigurationseditor** im Split-Panel-Muster (links Einstellungen, rechts Einbindung/Vorschau) wie Ent1Pros Formularerstellung — passt gut zum begleiteten Onboarding-Assistenten.

### 3.6 Was bewusst nicht übernommen werden sollte

- Ent1Pros KI-Freitext-Formulargenerator ("Beschreibe in Worten…") ist ein Nice-to-have, aber kein Kernpfad — passt eher zu P1 "KI-Assistenz", nicht zu V1.
- FastMoves Team-Konto-Modell ohne granulare Rollen ist schwächer als die bereits im BusinessOS-PRD festgelegten drei Rollen — hier ist BusinessOS klar im Vorteil und sollte das nicht verwässern.
- Reine KPI-Dashboard-Startseite (Ent1Pro) widerspricht Prinzip 1 (Posteingang zuerst) — nicht übernehmen.

---

## 4. Offene Entscheidungen, die vor Schritt 2 geklärt werden sollten

1. ~~**Pilot-Frage (Abschnitt 0)**~~ — **entschieden: Doppel-Pilot.** SHK und Entrümpelung laufen ab V1 parallel als zwei Branchenpaket-Konfigurationen; PROJ-20 rückt von P1 auf P0.
2. Soll Auto-Triage (Hebel 1) wieder ins Core-Paket aufgenommen werden, oder ist das ein bewusster Verzicht, der ins PRD als Nicht-Ziel/vertagt gehört?
3. Trägt die Büro-/Inhaber-Oberfläche das Branding des Betriebs oder eine neutrale BusinessOS-Marke?
4. Wird ein einfacher CSV-Export (ohne DATEV-Integration) Teil von V1, angesichts des Steuerberater-Vertriebskanals?
5. Welcher PROJ-Nummernkreis gilt künftig — der aus `Brainstorm 2.md` oder der aus `INDEX.md`? (Beide weiterzuführen erzeugt Verwechslungsgefahr.)

---

## 5. Empfehlung für Schritt 2 (PRD-Ergänzung)

Priorisierter Vorschlag, in welcher Reihenfolge die Lücken ins PRD eingearbeitet werden sollten:

1. Doppel-Piloten-Entscheidung in Vision, Zielgruppe, Produktversprechen und Entscheidungstabelle umsetzen — branchenneutrale Formulierung statt SHK-spezifisch (Abschnitt 0).
2. Branchenpaket-Architektur als eigene PRD-Sektion mit Datenmodell-Grundzügen ausarbeiten und PROJ-20 von P1 auf P0 vorziehen (Abschnitt 1.2, 2.4).
3. Auto-Triage + Kapazität + Absage-Funktion entweder ins Core-Roadmap zurückholen oder explizit vertagen (Abschnitt 1.1).
4. DSGVO-Sektion konkretisieren: Verarbeitungsverzeichnis, AVV-Generator, Audit-Log, Feldverschlüsselung als benannte Anforderungen statt Sammelbegriff (Abschnitt 1.4).
5. UI-Abschnitt (Abschnitt 3 dieses Dokuments) als neue PRD-Sektion "Oberflächenkonzept" aufnehmen.
6. INDEX.md bereinigen: fehlende PROJ-Tickets für P1/P2 ergänzen, "ImmoCRM-Reuse"-Spalte von Status-Infos befreien, ID-Spalte in PRD-Roadmap-Tabelle ergänzen.
7. Erfolgsmessung um Freigabe-ohne-Änderung-Quote und Entlastungskennzahlen erweitern (Abschnitt 2.5).
8. Kunden-Status-Link, CSV-Export, Angebots-Statustracking als bewusste Entscheidungen (aufnehmen oder explizit als Nicht-Ziel begründen) dokumentieren (Abschnitte 1.3, 1.5, 1.6).
