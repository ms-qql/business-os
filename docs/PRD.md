# PRD — Business OS für SHK- und Entrümpelungsbetriebe (Doppel-Pilot)

**Status:** In Überarbeitung — ergänzt um Branchenpaket-Architektur, Oberflächenkonzept, Formular-Baukasten und Gewerke-Kalkulationskonzept
**Stand:** 2026-08-23 (v3, Ergänzung zu v2)
**Änderungsanlass:** Vergleich mit den Wettbewerbsprodukten ENT1PRO (Entrümpelung) und FastMove (Umzug) sowie Entscheidung für einen Doppel-Piloten SHK + Entrümpelung. Details der Analyse: `Gap-Analyse_BusinessOS.md`. v3 ergänzt das **Gewerk** als zentrale, branchenneutrale Kalkulationseinheit für Angebote — destilliert aus einer produktiven Handwerker-Software (Screenshot-Auswertung) und damit Auflösung des bisherigen Platzhalters „Kalkulationsdetails folgen separat" bei PROJ-5. Details: `Kalkulation_und_Angebotserstellung.md`, neues Ticket PROJ-22.

## Vision

Business OS ist eine geführte Website plus einfache Betriebszentrale für inhabergeführte Service- und Handwerksbetriebe mit ein bis drei (SHK) bzw. wenigen Mitarbeitern (Entrümpelung/Haushaltsauflösung). Eine Web- oder E-Mail-Anfrage wird ohne Medienbruch zu Kunde, Projekt, Angebot oder Termin und schließlich zu einer PDF-Rechnung.

Das Produkt gewinnt nicht über ERP-Breite, sondern über einen verständlichen Ablauf: weniger verlorene Anfragen, weniger Büro nach Feierabend und ein professioneller Auftritt, der in wenigen Tagen eingerichtet ist. Was den Betrieb von SHK zu Entrümpelung (und später zu weiteren Branchen) unterscheidet, steckt **in Konfiguration** — Formulare, Preislisten, Textbausteine, Objekttypen —, **nicht in einer zweiten Codebasis.**

## Zielgruppe

Primär: Inhabergeführte SHK-Servicebetriebe **und** Entrümpelungs-/Haushaltsauflösungs-/Räumungsunternehmen mit 1–5 Mitarbeitern, wenig bestehender Branchensoftware und einer veralteten oder fehlenden Website. Sie arbeiten tagsüber beim Kunden bzw. auf der Baustelle/im Objekt, bearbeiten Anfragen abends und nutzen häufig Telefon, E-Mail, WhatsApp, Papier oder Excel parallel.

Sekundär: Bürokräfte und Monteure/Mitarbeiter derselben Betriebe. Bürokräfte pflegen Projekte und Dokumente; Monteure/Team-Mitglieder sehen nur ihre eigenen Termine und Auftragsinformationen auf dem Mobilgerät, ohne Preise.

**Warum zwei Piloten gleichzeitig statt nacheinander:** SHK und Entrümpelung teilen denselben Kernablauf (Anfrage → Qualifizierung → Angebot → Termin → Rechnung), unterscheiden sich aber deutlich in den Objekten, die dabei erfasst werden (Heizkessel/Zählerschrank bei SHK vs. Zimmer/Fundstücke bei Entrümpelung). Genau dieser Unterschied ist der Belastungstest für die Branchenpaket-Architektur (siehe unten). Ein einzelner Pilot hätte diesen Test nicht bestanden, weil er die Konfigurierbarkeit nie fordert.

## Produktversprechen

> Website, Anfragen und Büroarbeit in einem einfachen Ablauf — für Service- und Handwerksbetriebe, die keine weitere komplizierte Branchensoftware wollen.

## Entscheidungen

| Bereich | Festlegung |
|---|---|
| Startsegmente | SHK-Service **und** Entrümpelung/Haushaltsauflösung als Doppel-Pilot, beide als Branchenpaket-Konfiguration auf derselben Codebasis |
| Branchenpaket-Architektur | Formulare, Preislisten, Textbausteine und branchenspezifische Objekttypen sind Konfiguration, nicht Code; ab V1 Voraussetzung, nicht Nachrüstung (siehe Abschnitt „Branchenpaket-Konfiguration") |
| Kalkulationseinheit | Das **Gewerk** (vorkalkulierte, wiederverwendbare Leistungseinheit aus Lohn/Material/Fremdleistung mit Zuschlägen) ist die zentrale, branchenneutrale Kalkulationseinheit für Angebote; branchenspezifisch ist nur der Gewerke-Katalog, nicht die Mechanik (siehe Abschnitt „Gewerke: Kalkulationseinheit für Angebote") |
| Formular-Erstellung | Baukasten mit festem Feldtypen-Katalog; Betrieb/Admin vergibt Bezeichnungen, Optionen und Komplexitätsstufe je Formular — **keine KI-Generierung** (bewusste Abgrenzung zu ENT1PRO, siehe Abschnitt „Formular-Baukasten") |
| Oberflächenstruktur | Fixe Hauptnavigation: Dashboard, Kunden, Anfragen, Angebote, Projekte, Termine, Rechnungen, Admin (Webseite / Vorlage / Onboarding), Einstellungen — siehe Abschnitt „Oberflächenkonzept" |
| Auslieferung der Website | Je Mandant konfigurierbare Landingpage aus freigegebenen Sektionen |
| Eingangskanäle V1 | Website-Formular und E-Mail |
| Rollen | Inhaber, Büro, Monteur/Team |
| Mandantenmodell | Multi-Tenant mit strikt getrennten Betriebsdaten |
| Rechnungen | PDF-Rechnung; keine Buchhaltung und keine E-Rechnung in V1 |
| Kommunikation | Entwürfe werden stets durch Menschen freigegeben |
| Produktfokus | Website-first: Anfrage zum Auftrag, nicht vollständiges ERP |

## Oberflächenkonzept

Die App hat eine fixe Hauptnavigation (identisch für SHK und Entrümpelung, nur die Inhalte darunter sind branchenspezifisch konfiguriert):

| Modul | Zweck | Rollen-Sichtbarkeit |
|---|---|---|
| **Dashboard** | Kennzahlenüberblick: neue Anfragen, offene Angebote, Termine heute/morgen, offene/überfällige Rechnungen, Umsatz | Inhaber, Büro (eingeschränkt) |
| **Kunden** | Kundenliste und -detail: Kontaktdaten, Quelle/Kanal, Historie, aktive/gelöschte Kunden | Inhaber, Büro |
| **Anfragen** | Posteingang aller Kanäle (Website-Formular, E-Mail), Status NEU/gelesen/bearbeitet, Übernahme zu Kunde + Projekt | Inhaber, Büro |
| **Angebote** | Liste aller Angebote projektübergreifend, Status Entwurf/freigegeben/versendet/angenommen/abgelehnt, PDF-Versand | Inhaber, Büro |
| **Projekte** | Das verbindende Objekt: ein Projekt je Vorgang, mit Bezug zu Ursprungs-Anfrage, Kunde, Angebot(en), Termin(en), Rechnung und branchenspezifischen Dokumenten/Objekten | Inhaber, Büro |
| **Termine** | Kalender-/Listenansicht aller Termine, Tages-/Wochenansicht, Zuweisung an Team-Mitglied | Inhaber, Büro; Monteur nur eigene Termine |
| **Rechnungen** | Liste aller Rechnungen, PDF, Zahlungsstatus offen/bezahlt/überfällig | Inhaber, Büro |
| **Admin → Webseite** | Branding (Logo, Farben, Absenderadresse, Domain), Landingpage-Sektionen | Inhaber |
| **Admin → Vorlage** | Formular-Baukasten, Textbausteine (Antworten, Absagen), Angebots-/Rechnungsvorlagen, Preisliste je Branchenpaket | Inhaber, Büro (eingeschränkt) |
| **Admin → Onboarding** | Geführter Einrichtungsassistent, Demo-Mandant, Einrichtungs-Checkliste | Inhaber |
| **Einstellungen** | Nutzer & Rollen, Kanäle (E-Mail-Postfach), Kapazität, Benachrichtigungen, DSGVO-Center, Verbrauchsgrenzen | Inhaber |

**Warum „Projekte" als eigenes Modul und trotzdem globale Listen für Kunden/Anfragen/Angebote/Termine/Rechnungen:** Die einzelnen Listen sind bewusst als *gefilterte Sichten auf denselben Datenbestand* zu verstehen, nicht als getrennte Silos — jedes Angebot, jeder Termin und jede Rechnung hängt an genau einem Projekt. Das Projekt selbst ist als Detailseite mit Reitern gedacht (Übersicht, Kommunikation, Angebot, Termin, Rechnung, Dokumente), damit ein Vorgang an einer Stelle vollständig nachvollziehbar bleibt und kein zweiter Posteingang entsteht (siehe Gap-Analyse, Abschnitt 3.4). Die globalen Module (Angebote, Termine, Rechnungen) dienen der schnellen, projektübergreifenden Arbeit — „alle offenen Angebote diese Woche" — nicht als eigenständige Datenmodelle.

Monteur/Team-Mitglieder erhalten keine eigene Navigation aus obiger Liste, sondern eine reduzierte mobile Ansicht: Terminkarten für Heute/Morgen mit Adresse, Checkliste, Foto-Upload und „Erledigt"-Button, ohne Preise. Der Kunde erhält keine Login-Oberfläche, nur die öffentliche Website mit Anfrageformular (Status-Trackingseite ist im Backlog, siehe Roadmap PROJ-17).

## Formular-Baukasten

Der frühere Roadmap-Punkt „Anfrageformular" wird zum eigenständigen Feature **Formular-Baukasten** (unter Admin → Vorlage). Vorbild ist strukturell ENT1PRO (fester Feldtypen-Katalog, Mehrstufigkeit, mehrere Einbindungsvarianten), **bewusst ohne** dessen KI-Freitext-Generator:

- **Fester Feldtypen-Katalog** (Produkt-/Codeseite, nicht erweiterbar durch den Betrieb): Text, mehrzeiliger Text, Auswahl/Dropdown, Kachel-Auswahl, Radio-Buttons, Mengenfeld/Zahl, Datum, Datei-/Foto-Upload, Adressfeld, Consent/Datenschutz-Zustimmung.
- **Baukasten-Editor statt KI-Prompt:** Der Betrieb (bzw. im Onboarding der Betreiber) fügt Felder aus dem Katalog per Klick hinzu und konfiguriert je Feld: **Bezeichnung/Label**, Pflichtfeld ja/nein, Hilfetext, und bei Auswahl-/Radio-/Kachel-Feldern die **Optionsliste** (Werte + Bezeichnungen). Es wird kein Text generiert oder interpretiert — jede Ausgabe ist das direkte Ergebnis der Konfiguration.
- **Komplexitätsstufe je Formular:** „Einfach" zeigt nur Pflichtfelder, „Erweitert" zusätzlich optionale Zusatzfelder — steuerbar pro Formular, nicht global. Das erlaubt kurze Formulare für eilige Anfragen und ausführliche für komplexe Aufträge, ohne zwei Formulare pflegen zu müssen.
- **Branchenpaket-Vorlagen:** SHK und Entrümpelung erhalten je ein vorkonfiguriertes Startformular (Feldtypen + branchentypische Bezeichnungen/Optionen bereits befüllt, z. B. „Heizkessel/Boiler/Therme" bei SHK vs. „Kühlschrank/Sofa/Umzugskartons" bei Entrümpelung). Der Betrieb passt Bezeichnungen und Optionen an, ohne bei null zu starten (löst Fail „leeres Formular schreckt ab").
- **Mehrstufigkeit** mit Fortschrittsanzeige, beliebig viele Schritte.
- **Drei Einbindungsvarianten:** Direktlink, iframe-Embed, JS-Snippet (Kompatibilität mit gängigen Website-Baukästen).
- **Spam-Schutz:** Honeypot, Rate-Limit, Zeit-Validierung.
- **Automatische Übernahme:** jede abgeschlossene Anfrage wird zu Kunde + Anfrage im Anfragen-Modul; bei Bestätigung Umwandlung in Projekt.
- **Verknüpfung zur Kalkulation:** Optionsfelder (z. B. Mengenangaben, Flächen, Objektlisten) werden mit einem **Gewerk** passender Einheit verknüpft (siehe Abschnitt „Gewerke: Kalkulationseinheit für Angebote"). Beispiel: Formularfeld „Fläche in m²" bei Entrümpelung zeigt auf ein Gewerk mit Verkaufspreis je m² und erzeugt daraus automatisch eine vorausgefüllte Angebotsposition — das löst den in der Gap-Analyse (Abschnitt 1.2) vermerkten Fail „Schnellkalkulation fehlt" auf. Der frühere Platzhalter „Details liefert der Betrieb separat nach" ist damit aufgelöst, siehe PROJ-22 und `Kalkulation_und_Angebotserstellung.md`.

**Bewusste Abgrenzung zu ENT1PRO:** Kein Claude-API-Key-Setup, keine Generierungskosten pro Formular, keine Abhängigkeit von KI-Verfügbarkeit für einen Kernprozess — dafür muss der Betrieb (unterstützt durch die Branchenpaket-Vorlage) die Felder aktiv zusammenstellen statt sie generieren zu lassen. Diese Abwägung gehört als Nicht-Ziel ergänzt (siehe unten).

## Branchenpaket-Konfiguration

Ehemals Roadmap-Punkt „Branchenpakete" (P1), jetzt wegen des Doppel-Piloten auf **P0** vorgezogen. Ein Branchenpaket bündelt für eine Branche (SHK, Entrümpelung, später weitere):

- Formular-Baukasten-Vorlage (Feldbezeichnungen, Optionen, Komplexitätsvoreinstellung)
- Preisliste-Grundstruktur (Positionsarten, Einheiten — Detailkalkulation folgt separat)
- Textbaustein-Sätze (Antwort-/Absagevorlagen im Ton der Branche)
- Branchenspezifische Projekt-Zusatzobjekte (z. B. Fundstücke-Dokumentation bei Entrümpelung; bei SHK ggf. Anlagen-/Gerätedaten) als konfigurierbarer Dokumente-Reiter im Projekt

Was **Code** bleibt: Feldtypen-Katalog, Datenmodell (Kunde/Anfrage/Projekt/Angebot/Termin/Rechnung), Freigabe-Workflow, Mandantentrennung. Was **Konfiguration** wird: alles, was ein Betrieb ohne Produkt-Update ändern können muss, um ein zweites Branchenpaket zu bedienen. Diese Trennlinie ist die Voraussetzung dafür, dass Entrümpelung als zweiter Pilot nicht zu einer zweiten Codebasis führt (Lock-in-Test aus dem Brainstorm, Runde 6).

## Gewerke: Kalkulationseinheit für Angebote

Ehemals der unspezifizierte Platzhalter „Verknüpfung zur Kalkulation" im Formular-Baukasten (siehe oben) und die Roadmap-Notiz „Kalkulationsdetails folgen separat" bei PROJ-5. Beides wird durch ein einziges, branchenneutrales Konzept aufgelöst: das **Gewerk**.

Ein Gewerk ist eine wiederverwendbare, vorkalkulierte Leistungseinheit mit fester oder je Bezugseinheit berechneter Preisangabe. Ein Gewerk wird **einmal** angelegt und legt fest, was zu seiner Erbringung nötig ist:

- wie viel **Arbeitszeit** (Lohn, nach Qualifikationsstufe)
- welches **Material**
- welche **sonstigen/externen Kosten** (Fremdleistung, Geräte, Entsorgung …)

anfallen — jeweils mit Menge, Einheit und Einkaufspreis, plus einem Zuschlagssatz je Kostenart, der automatisch den Verkaufspreis ergibt. Beim Erstellen eines Angebots wird ein Gewerk als fertige Position gezogen, statt Lohn, Material und Preis für jeden Auftrag neu zusammenzustellen.

**Beispiele:**

| Branche | Gewerk | Einheit/Bezugsgröße |
|---|---|---|
| SHK | „Waschbecken komplett einbauen" | Stk. (Festpreis aus Lohnzeit + Material) |
| SHK | „Heizkörper tauschen" | Stk. |
| Entrümpelung | „Wohnung entrümpeln" | Preis pro m² Wohnfläche |
| Entrümpelung | „Container stellen & entsorgen" | Preis pro Container (z. B. 5 m³) |

Der entscheidende Punkt: **das Gewerk als Konzept — Kopfdaten, Kostenzeilen je Kostenart, Zuschlagsrechnung, Ergebnis als Angebotsposition — ist branchenneutraler Code.** Branchenspezifisch ist ausschließlich, *welche* Gewerke mit *welchen* Preisen, Arbeitsschritten und Bezugsgrößen vorbefüllt sind. SHK und Entrümpelung unterscheiden sich hier nicht in der Mechanik, sondern nur im Katalog — dieselbe Trennlinie wie beim Formular-Baukasten und der Branchenpaket-Konfiguration oben, hier auf die Kalkulation angewendet.

Damit lässt sich auch die Formular-Kalkulations-Verknüpfung konkret auflösen: Ein Formularfeld mit passender Bezugsgröße (z. B. „Fläche in m²") wird direkt an ein Gewerk mit derselben Einheit gekoppelt; aus einer abgeschlossenen Anfrage lässt sich damit automatisch eine vorausgefüllte Angebotsposition erzeugen, ohne dass ein KI-Freitext-Generator (bewusst ausgeschlossen, siehe Formular-Baukasten) nötig wäre.

**Ausdrücklich nicht Teil des Gewerk-Konzepts** (konsistent mit den Nicht-Zielen): Nachkalkulation als Soll-Ist-Vergleich, GAEB-/Datanorm-Import von Gewerk-Vorlagen, freie Erweiterung der Kostenarten durch den Betrieb.

Details zu Datenmodell, Kostenarten, Zuschlagslogik und branchenspezifischen Beispiel-Gewerken (SHK und Entrümpelung): siehe `Kalkulation_und_Angebotserstellung.md` und Ticket PROJ-22.

## Roadmap

| ID | Priorität | Feature | Ziel |
|---|---|---|---|
| PROJ-1 | P0 | Mandanten, Anmeldung und Rollen | Betriebsdaten und Ansichten sicher trennen |
| PROJ-14 | P0 | Branchenpaket-Konfiguration | Beim Onboarding einmalig SHK oder Entrümpelung wählen und versionierte Produktvorlagen in den Mandanten kopieren — Voraussetzung für Doppel-Pilot |
| PROJ-2 | P0 | Geführte Website und Branding | Betrieb veröffentlichen, Branchenpaket-Landingpage |
| PROJ-13 | P0 | Formular-Baukasten | Anfrageformulare ohne KI aus festem Feldtypen-Katalog konfigurieren |
| PROJ-3 | P0 | Kunden, Projekte und Dokumente | Anfrage, Kunde, Projekt, Status, Historie und Anhänge zentral führen |
| PROJ-4 | P0 | E-Mail-Inbox und Antwort | E-Mail-Anfragen und freigegebene Antworten im selben Projekt führen |
| PROJ-5 | P0 | Angebote und PDF-Versand | Einfache Positionen in ein prüfbares Angebot überführen |
| PROJ-22 | P0 | Gewerke: Kalkulationseinheiten für Angebote | Lohn/Material/Fremdleistung mit Zuschlägen zu wiederverwendbaren Leistungseinheiten bündeln; löst „Kalkulationsdetails folgen separat" auf, siehe Abschnitt „Gewerke" |
| PROJ-6 | P0 | Einfache Terminplanung | Termin einem Team-Mitglied zuordnen |
| PROJ-8 | P0 | PDF-Rechnungen | Rechnung aus erledigtem Projekt erstellen und ablegen |
| PROJ-7 | P0 | Begleitetes Onboarding | Betrieb, Branding, Postfach und Preisliste startklar einrichten, inkl. Testdurchstich vor Livegang |
| PROJ-15 | P0 (Vorschlag) | Auto-Triage mit Ampel | Anfragen nach Passung/Dringlichkeit/Kapazität vorsortieren — Reaktivierung aus Brainstorm „Hebel 1", der in v1 des PRD verlorenging; **zu bestätigen** |
| PROJ-9 | P1 | Mobile Monteuransicht und Automationen | Aufträge mobil abschließen sowie Erinnerungen auslösen |
| PROJ-10 | P1 | Erinnerungen und Statusautomationen | Nachfassen ohne Zutun des Büros |
| PROJ-11 | P1 | Datenschutz, Datenexport und Aufbewahrung | Jetzt konkretisiert: Verarbeitungsverzeichnis (Art. 30), AVV-Generator, Self-Service-Portal (Art. 15/17/20), Audit-Log, Feldverschlüsselung sensibler Daten |
| PROJ-16 | P1 | KI-Assistenz | Zusammenfassungen, Klassifizierung und Textentwürfe mit Freigabe |
| PROJ-12 | P1 | Freier Website-Baukasten und Landingpage | Hochwertige, modular konfigurierbare Startseite |
| PROJ-23 | P1 | Dedizierter Bildspeicher und WebP-Optimierung | Neue Landingpage-Sektionsbilder von ImmoCRM trennen und komprimiert als WebP ausliefern |
| PROJ-17 | P1 | Kunden-Status-Link | Öffentliche Statusseite für Endkunden — wiederaufgenommen aus Brainstorm #10, war im PRD v1 verlorengegangen |
| PROJ-18 | P1 (Vorschlag) | CSV-Export für Buchhaltung | Export kompatibel zu DATEV/lexoffice/sevDesk — aus Wettbewerbsvergleich ergänzt, Priorität zu bestätigen |
| PROJ-19 | P2 (offen) | Angebots-Statustracking & optionale E-Signatur | Geöffnet/angenommen-Status, digitale Unterschrift — aus FastMove-Vergleich, unentschieden, nicht spezifiziert |
| PROJ-20 | P2 | E-Rechnungen | Strukturierte Rechnungsformate ergänzen |
| PROJ-21 | P2 | Telefonie, Routen, Kundenportal | Nur bei belegtem Kundenbedarf |

## Erfolgsmessung

- Mindestens 80 % der Webanfragen werden vollständig als Projekt angelegt.
- Ein Betrieb kann seine Website und den ersten Anfragefluss in einem begleiteten Termin produktiv nutzen.
- Der Inhaber kann aus einer vollständigen Anfrage in höchstens fünf Minuten ein Angebot oder einen Termin vorbereiten.
- Jede E-Mail-Antwort, jedes Angebot und jeder Termin bleibt am zugehörigen Projekt sichtbar.
- **Freigabe-ohne-Änderung-Quote:** Anteil der Angebots- und Antwortentwürfe, die unverändert freigegeben werden — Kennzahl für Entwurfsqualität, ergänzt nach Brainstorm-Befund, dass sie „die zentrale Produktkennzahl" ist, nicht Login-/Anfragezahlen.
- Beide Piloten (SHK und Entrümpelung) erreichen die obigen Werte unabhängig voneinander — Nachweis, dass die Branchenpaket-Konfiguration trägt.

## Rahmenbedingungen

- Deutschsprachiges, mobiles Webprodukt; öffentliche Seiten müssen suchmaschinenfreundlich sein.
- Datenschutz nach DSGVO: Mandantentrennung, Zugriff nach Rolle, transparente Verarbeitung, Lösch- und Exportmöglichkeit. Konkretisierung siehe PROJ-11.
- Persönliches Onboarding ist Teil des Angebots; Selbstkonfiguration ist kein V1-Erfolgsmaßstab.
- Der Baukasten bleibt auf freigegebene, responsive Sektionstypen begrenzt; kein freies HTML oder individuelles Seitenlayout — gilt sowohl für die öffentliche Website als auch für den Formular-Baukasten (fester Feldtypen-Katalog, keine freie Formularlogik).

## Nicht-Ziele

- Lager, Materialwirtschaft, Lohn, Finanzbuchhaltung, DATEV-Integration (Volleinbindung) und komplexe Nachkalkulation.
- GAEB, Großhändler-Integration, Routenoptimierung und Offline-Synchronisierung.
- Freie Rollen- und Rechteverwaltung, mehrstufige Unternehmenshierarchien oder Agentur-/Reseller-Modell.
- Autonom versendete Angebote, Rechnungen oder Kundenantworten.
- **KI-generierte Formularerstellung** (bewusste Abgrenzung zu ENT1PRO — der Formular-Baukasten ist konfigurationsbasiert, siehe oben).
- WhatsApp, Sprachagent, Recruiting und weitere Gewerke vor bestätigtem Bedarf.

## Aus vorigem Brainstorm bewusst vertagt

Warteliste, Deckungsbeitrags-Sortierung, Auslastungsaufschlag statt Absage, Telefon-Transkription, Vertrauensstufen-Regler und Recruiting-Modul bleiben wertvolle spätere Optionen. Sie sind nicht Teil dieser PRD-Ergänzung, weil der Doppel-Pilot zunächst den durchgehenden Grundfluss über zwei Branchen beweisen muss. **Auto-Triage (PROJ-15)** ist die eine Ausnahme, die aus dem Brainstorm zurückgeholt wird, weil sie im PRD v1 versehentlich verlorenging, nicht bewusst vertagt wurde.

## Wiederverwendungsentscheidung

ImmoCRM liefert technische Vorlagen für E-Mail, Dateien, Zugangsdaten, Erinnerungen und Termine. Das neue Produkt übernimmt keine Immobilienlogik, Flutter-Oberflächen oder das separate Datenbank-Mandantenmodell. Details: [Reuse-Audit](reuse-audit-immocrm.md).

Die Übernahme verändert vor allem die Umsetzung, nicht den Kundenfluss: PROJ-4, PROJ-6, PROJ-7 und spätere Erinnerungen starten mit bewährten technischen Bausteinen. Die fachlich differenzierenden Teile — Website, Anfrage-/Projektmodell, Branchenpaket-Konfiguration, Angebote und Rechnungen — werden bewusst neu spezifiziert.
