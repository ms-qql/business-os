# Kalkulation & Angebotserstellung — Gewerke als Kalkulationseinheit (Vertiefung zu PROJ-5 / PROJ-22)

**Status:** Entwurf zur Einarbeitung in `PRD.md` / `INDEX.md`
**Stand:** 2026-08-23
**Anlass:** Screenshots einer produktiven Handwerker-Software (Firma "SHK Schlüter", SHK-Betrieb, generische Branchensoftware für viele Gewerke gleichzeitig) — ausgewertet auf das für BusinessOS Relevante.
**Füllt:** `PRD.md`, Abschnitt „Formular-Baukasten", Punkt „Verknüpfung zur Kalkulation (Platzhalter) … Details zur Kalkulationslogik liefert der Betrieb separat nach" sowie die Roadmap-Zeile zu PROJ-5 „Kalkulationsdetails folgen separat". In `PRD.md`/`INDEX.md` als **PROJ-22** und Abschnitt „Gewerke: Kalkulationseinheit für Angebote" verankert.
**Kernbefund dieser Version:** Das **Gewerk** — eine einmal angelegte, vorkalkulierte Leistungseinheit aus Lohn/Material/Sonstigem mit Festpreis oder Preis je Bezugseinheit (z. B. „Waschbecken komplett einbauen" als Stückpreis, „Wohnung entrümpeln" als Preis pro m²) — ist der durchgängige, branchenneutrale Kern dieser Spezifikation. Branchenspezifisch ist ausschließlich der Katalog an Gewerken, nicht das Prinzip.

---

## 0. Ausgangslage und Abgrenzung

Die ausgewertete Software ist eine vollwertige Handwerker-Branchensoftware für **alle** Gewerke (Dachdecker, Fliesen, Garten-/Landschaftsbau, Maler, Sanitär/Heizung, Trockenbau, Zimmerer …) mit entsprechender Tiefe: GAEB-/Datanorm-Import, Nachkalkulation mit Soll-Ist-Vergleich je Kostenart, Mahnwesen mit Verzugszinsen, Abschlagsrechnungen, freie Berichts-/Checklisten-Baukästen. Das ist für BusinessOS bewusst zu viel — die Nicht-Ziele in `PRD.md` schließen GAEB, Großhändler-Integration, Materialwirtschaft/Lager und „komplexe Nachkalkulation" ausdrücklich aus.

**Explizit nicht übernommen** aus den Screenshots:
- GAEB-/Excel-/Datanorm-Import für Stammdaten (Screenshot „Materialien importieren")
- Nachkalkulation als Soll-Ist-Dashboard mit Fortschritts-% je Kostenart (Screenshot „Nachkalkulation" mit Kostenarten-Balkendiagramm)
- Mahnwesen mit Verzugszinsen/Mahngebühr als V1-Feature (siehe Abschnitt 6 — als Backlog vorgemerkt, nicht spezifiziert)
- Freier Berichts-/Checklisten-Baukasten (eigenständiges Feature, eher Anknüpfungspunkt für PROJ-9 „Mobile Monteuransicht" als für PROJ-5)
- Eigenes Firmen-E-Mail-Konto zum Versand verbinden (Redundanz zu PROJ-4/PROJ-7, dort bereits spezifiziert)

**Übernommen** ist die Substanz von vier Bereichen, die für den Angebotsprozess unverzichtbar sind und im PRD bislang nur als Platzhalter standen: Angebotsstruktur, das **Gewerk** als Kalkulationseinheit (Abschnitt 2, zentraler Befund dieser Runde), Gewerke-/Materialkatalog als Stammdaten (Abschnitt 3), Text- und E-Mail-Vorlagen je Dokumenttyp. Diese Bereiche werden unten branchenneutral spezifiziert (Abschnitte 1–6) und anschließend als zwei Branchenpaket-Vorlagen ausdekliniert: **SHK** (Abschnitt 7) und **Entrümpelung** (Abschnitt 8, das zweite Pilotmodul) — jeweils als Katalog konkreter Gewerke, nicht als eigene Mechanik.

---

## 1. Angebots-/Dokumentstruktur (Code, branchenneutral)

Ein Angebot besteht aus einer Kopfzeile (Empfänger, Ansprechperson, Datum, Betreff, Leistungsort — bereits durch PROJ-3-Datenmodell gedeckt) und einem Positionsteil aus vier Bausteintypen:

| Baustein | Zweck |
|---|---|
| **Text** | Freier Absatz, z. B. Anfangs-/Schlusstext oder Zwischenerklärung |
| **Titel** | Gruppiert nachfolgende Positionen zu einem Abschnitt (z. B. „Bad EG") mit eigener Zwischensumme; mehrere Titel sind möglich |
| **Position** | Eine Angebotszeile: Menge, Einheit, Kurzbeschreibung, optional ausklappbarer Langtext, Einzelpreis, Gesamtpreis |
| **Bild** | Referenzfoto/Produktbild innerhalb einer Position oder frei im Dokument |

Am Ende jedes Angebots steht ein Summenblock: Nettosumme → zzgl. USt (Satz aus Positionen abgeleitet) → Bruttosumme, mit manueller Override-Möglichkeit ("Preis anpassen") für Fälle, in denen ein Pauschalpreis vom kalkulierten Wert abweichen soll. Umfasst ein Angebot mehrere Titel, wird auf der letzten Seite automatisch eine Zusammenfassung „Übersicht der Titel" mit Titel-Zwischensummen erzeugt.

**Empfohlene Ergänzung (neu, nicht nur Übernahme):** Ein automatisch berechneter und ausgewiesener **Lohnkostenanteil** („Der Lohnkostenanteil beträgt X €, die darin enthaltene Umsatzsteuer beträgt Y €") direkt im Angebots-/Rechnungstext. Das ist für Privatkunden steuerlich relevant (§35a EStG, Handwerkerleistungen) und für SHK der Regelfall — Aufwand ist gering, da er sich direkt aus der Kalkulationslogik in Abschnitt 2 ergibt (Summe aller Lohn-Kostenanteile über alle Positionen).

---

## 2. Das Gewerk: Kalkulationseinheit für Angebotspositionen (Code: Rechenregeln — Konfiguration: Sätze)

Der zentrale Baustein hinter jeder kalkulierten Angebotsposition ist das **Gewerk**: eine wiederverwendbare, einmal angelegte Leistungseinheit, die festlegt, was zu ihrer Erbringung nötig ist — wie viel **Arbeitszeit**, welches **Material**, welche **sonstigen/externen Kosten** — und daraus einen Preis errechnet. Statt bei jedem Auftrag Lohn, Material und Preis neu zusammenzustellen, wird ein bestehendes Gewerk als fertige Position ins Angebot gezogen und höchstens in der Menge angepasst.

Beispiel SHK: das Gewerk „Waschbecken komplett einbauen" hat einen festen Stückpreis, der sich aus einer festgelegten Lohnzeit (z. B. 2 Std. Geselle) plus den benötigten Materialpositionen (Waschbecken, Armatur, Sifon, Befestigung) ergibt. Beispiel Entrümpelung: das Gewerk „Wohnung entrümpeln" hat keinen Stückpreis, sondern einen **Preis pro m² Wohnfläche**; das Gewerk „Container stellen & entsorgen" einen **Preis pro Container** (z. B. 5 m³) — dieselbe Mechanik, andere Bezugsgröße. Welche Gewerke es gibt und wie sie bepreist sind, ist Sache des Branchenpakets (Abschnitte 7–8); *dass* ein Gewerk aus Kostenzeilen mit Zuschlägen besteht, ist Code.

Ein Gewerk kann auf zwei Arten kalkuliert werden:

- **Einheitspreiskalkulation** — Kosten werden pro Bezugseinheit (m, m², Stk., Std., Container …) hinterlegt und mit der im Angebot eingegebenen Menge multipliziert.
- **Gesamtpreiskalkulation** — Kosten werden einmalig für das gesamte Gewerk hinterlegt (z. B. Pauschalen wie Baustelleneinrichtung).

In beiden Fällen setzt sich der Einkaufspreis (EK) eines Gewerks aus einer oder mehreren **Kostenzeilen** zusammen. Jede Kostenzeile hat eine **Kostenart**:

| Kostenart | Beispiel | Übliche Einheit |
|---|---|---|
| Lohn | Arbeitszeit nach Qualifikationsstufe | Minuten oder Stunden |
| Material | Einzelartikel aus dem Materialkatalog | Stk., m, m², Liter … |
| Fremdleistung | Zugekaufte Leistung (Subunternehmer, Entsorgung, Container) | Pauschale oder Einheit |
| Sonstiges/Geräte | Gerätemiete, Maschineneinsatz | Pauschale oder Einheit |

Für jede Kostenart gilt ein **Zuschlagssatz in %** (Betriebs-Standardwert, pro Gewerk überschreibbar), der auf die EK-Summe dieser Kostenart aufgeschlagen wird und den Verkaufspreis (VK) ergibt: `VK = EK + (EK × Zuschlag%)`. Die Summe aller VK-Kostenarten ergibt den Gewerkpreis; daraus errechnet sich automatisch auch ein effektiver Gesamt-Zuschlagssatz. Aus der Summe der Lohn-Minuten aller Gewerke eines Angebots lässt sich zusätzlich die kalkulierte Bearbeitungszeit ableiten — ein direkter Anknüpfungspunkt für PROJ-6 (Terminplanung: Dauer eines Termins aus dem Angebot vorschlagen, statt sie manuell zu schätzen).

**Bewusst nicht übernommen:** ein Nachkalkulations-Dashboard, das erfasste Ist-Kosten den kalkulierten Soll-Kosten je Kostenart gegenüberstellt. Das wäre ein eigenständiges, deutlich größeres Feature (Zeit-/Materialerfassung je Auftrag, Soll-Ist-Reporting) und widerspricht dem Nicht-Ziel „komplexe Nachkalkulation".

---

## 3. Stammdaten: Gewerke- und Materialkatalog

Damit nicht jedes Gewerk von Hand neu kalkuliert werden muss, pflegt der Betrieb eine Preisliste aus zwei Katalogtypen — der **Gewerke-Katalog** ist dabei die eigentliche Preisliste, der Materialkatalog liefert ihm nur die Zutaten:

- **Materialkatalog** — Einzelartikel mit Artikelnummer (optional), Einheit, Kurzbeschreibung, optionalem Langtext, EK, Zuschlag% und daraus berechnetem VK. Wird von Gewerken als Kostenzeile referenziert.
- **Gewerke-Katalog** (in der Quellsoftware „Leistungen" genannt) — die vorkalkulierten Gewerke selbst: Kurz- und Langtext, Bezugseinheit, ihre Kostenzeilen (Lohn/Material/Sonstiges, siehe Abschnitt 2) und der daraus berechnete Preis. Das ist die Ebene, die als fertige Position ins Angebot gezogen wird.

Beide Kataloge sind in **Ordnern/Kategorien** organisiert. Diese Ordnerstruktur ist genau die Stelle, an der ein Branchenpaket (PROJ-14) greift: SHK und Entrümpelung erhalten unterschiedliche, vorbefüllte Kategorien und Beispiel-Gewerke (siehe Abschnitte 7–8), der Betrieb passt Bezeichnungen, Mengen und Preise an, ohne bei null zu starten — dasselbe Prinzip, das `PRD.md` bereits für den Formular-Baukasten festlegt.

Eine Sonderkategorie **Lohnarbeiten** enthält feste Kostenzeilen-Bausteine je Qualifikationsstufe (z. B. Meister, Geselle/Facharbeiter, Lehrling, Helfer) mit hinterlegtem Stundensatz und Standard-Zuschlag — diese werden in praktisch jedem Gewerk mit Lohnanteil als Kostenzeile wiederverwendet, ohne selbst ein eigenständiges Gewerk zu sein (Ausnahme: reine Stundenlohnarbeit ohne Material, siehe Abschnitt 7 — dort ist der Lohnsatz selbst das Gewerk).

**Import:** Aus den Screenshots übernommen wird nur das Prinzip „Position aus einem bestehenden Angebot als Gewerk in den Katalog übernehmen" (spart Doppelerfassung bei wiederkehrenden Leistungen). **Nicht übernommen:** Import aus GAEB-, Datanorm- oder Großhändler-Exportdateien — das ist laut Nicht-Ziele bewusst außerhalb des Produkts.

---

## 4. Text- und E-Mail-Vorlagen je Dokumenttyp

Jeder Dokumenttyp bekommt einen Standard-Anfangstext und einen oder mehrere Standard-Schlusstext-Blöcke, die beim Erstellen automatisch eingefügt und vom Betrieb frei bearbeitet oder deaktiviert werden können. Für BusinessOS V1 sind mindestens **Angebot**, **Auftragsbestätigung** und **Rechnung** relevant (Kostenvoranschlag, Lieferschein, Abschlagsrechnung, Schlussrechnung und Gutschrift sind Dokumenttypen, die es in der Quellsoftware zusätzlich gibt, im BusinessOS-PRD aber noch nicht als eigene Module vorgesehen sind — siehe Abschnitt 6).

**Branchenneutrale Standardtexte** (direkt aus den Screenshots übernommen, bewusst allgemein gehalten und für beide Branchenpakete geeignet):

| Dokumenttyp | Anfangstext | Schlusstext |
|---|---|---|
| Angebot | „Anbei senden wir Ihnen das angeforderte Angebot. Dieses lautet wie folgt:" | „Für Rückfragen zu diesem Angebot stehen wir Ihnen gerne zur Verfügung. Falls Ihnen das Angebot zusagt, senden Sie es bitte unterschrieben zurück. Das Angebot hat eine Gültigkeit von 30 Tagen." + Unterschriftsfeld (Ort, Datum, Unterschrift Auftraggeber) |
| Auftragsbestätigung | „Hiermit bestätigen wir den von Ihnen erteilten Auftrag. Dieser lautet wie folgt:" | „Für Rückfragen zum Auftrag stehen wir Ihnen gerne zur Verfügung." |
| Rechnung | „Wir danken Ihnen für den erteilten Auftrag und berechnen Ihnen wie folgt:" | „Sofern nicht anders angegeben, entspricht das Liefer-/Leistungsdatum dem Rechnungsdatum. Für Rückfragen stehen wir Ihnen gerne zur Verfügung." + „Die gesetzliche Aufbewahrungspflicht gemäß §14b UStG beträgt für Privatpersonen 2 Jahre und für Unternehmen 10 Jahre." |

Zusätzlich ein Skonto-/Zahlungsziel-Satz am Ende des Angebots (z. B. „Nach Rechnungsstellung gewähren wir 2 % Skonto bei Zahlung innerhalb von 7 Tagen. Ohne Abzug beträgt das Zahlungsziel 14 Tage.") sowie der in Abschnitt 1 vorgeschlagene Lohnkostenanteil-Satz.

**E-Mail-Vorlage** je Dokumenttyp, mit denselben Platzhaltern, die PROJ-4 (E-Mail-Inbox) ohnehin für Antwortentwürfe braucht:

```
{{anrede}}

wie vereinbart [das Angebot / die Auftragsbestätigung / die Rechnung] mit der Nummer {{dokumentenNummer}}.

Mit freundlichen Grüßen
{{name}}
```

Platzhalter: `{{anrede}}` (aus dem Dokument abgeleitete Anrede), `{{dokumentenNummer}}`, `{{name}}` (interne Ansprechperson). Absender ist standardmäßig eine Produktadresse; ein eigenes E-Mail-Konto zu verbinden ist bereits über PROJ-4/PROJ-7 abgedeckt und wird hier nicht doppelt spezifiziert.

---

## 5. Layout/Briefpapier (Wiederverwendung aus PROJ-2)

Die PDF-Erzeugung braucht kein eigenständiges neues Layout-Feature: Logo, Akzentfarbe und Kontaktdaten kommen direkt aus dem Branding, das PROJ-2 bereits im Onboarding erfasst („automatisches Layout aus den Unternehmensdaten"). Zusätzlich sinnvoll und mit sehr geringem Aufwand: eine Fußzeile mit Seitenzahl und optionaler Produktkennzeichnung („Erstellt mit …"). Ob diese Kennzeichnung standardmäßig sichtbar ist, hängt von der in der Gap-Analyse offen gelassenen Whitelabel-Frage ab (Abschnitt 3.2, Punkt 4 dort) und sollte dort mitentschieden, nicht hier separat festgelegt werden.

---

## 6. Zahlungsbedingungen — V1 schlank, Rest Backlog

**V1 (einfach, geringer Aufwand):** Zahlungsziel in Tagen und optionaler Skontosatz als globale Betriebseinstellung, die automatisch in den Schlusstext von Angebot und Rechnung einfließt (siehe Abschnitt 4).

**Bewusst als Backlog vorgemerkt, nicht in dieser Spezifikation ausgearbeitet** (im Einklang mit dem Nicht-Ziel „Finanzbuchhaltung"):
- Mahnwesen mit gestuften Mahnungen (Zahlungserinnerung → 1. Mahnung → 2. Mahnung), Verzugszinsen und Mahngebühr je Stufe
- Abschlagsrechnungen (kumulativ oder nicht-kumulativ) — setzt ohnehin voraus, dass Rechnungen (PROJ-8) über die einfache PDF-Einzelrechnung aus V1 hinausgehen

Diese zwei Punkte gehören, falls priorisiert, als eigene Roadmap-Zeilen ins PRD (z. B. unter PROJ-8-Erweiterung oder als neues Ticket), nicht implizit in PROJ-5.

---

## 7. Branchenpaket SHK — Gewerke-Vorlage

**Kategorien im Gewerke-/Materialkatalog (Vorschlag zur Vorbefüllung):**

| Kategorie | Typische Gewerke | Übliche Zuschläge |
|---|---|---|
| Lohnarbeiten | Meister/Vorarbeiter, Geselle/Facharbeiter, Azubi/Lehrling, Helfer — je Std. (reines Lohn-Gewerk, kein Material) | einheitlich ca. 20 % |
| Sanitär | „Waschbecken komplett einbauen", „WC/Dusche komplett einbauen", Rohrsanierung (Trink-/Abwasser) je m, Entkalkung | Lohn ca. 10 %, Material ca. 15–20 % |
| Heizung | Kessel-/Thermentausch, Heizkörper tauschen, Thermostatventil tauschen | Lohn ca. 10 %, Material ca. 15–20 % |
| Bad-Sanierung | Abbruch Altbestand, Fliesenarbeiten je m², Vorwandinstallation | Lohn ca. 10 %, Material ca. 15–20 % |
| Kleinteile & Material | Pauschale für Nägel, Dübel, Dichtmaterial, Kleinbefestigung | 0–10 % (oft Pauschale ohne Aufschlag) |
| Sonstige Pauschalen | Regiekosten, Baustelleneinrichtung, Anfahrt | Gesamtpreiskalkulation, kein separater Zuschlag nötig |

Beispiel-Gewerk „Waschbecken komplett einbauen" (Einheitspreiskalkulation, Bezugsgröße Stk.): Kostenzeile Lohn — 2 Std. Geselle à 41 €; Kostenzeilen Material — Waschbecken, Armatur, Sifon, Befestigungsmaterial aus dem Materialkatalog. Zuschlag Lohn ca. 10 %, Material ca. 15–20 %, Summe ergibt den Stückpreis, der als eine einzige Position ins Angebot wandert.

**Beispiel-Lohnsätze** (aus den Screenshots, als Startwerte übernehmbar): Meister/Vorarbeiter 58 €/Std., Geselle/Facharbeiter 41 €/Std., Lehrling 30 €/Std., Helfer 25 €/Std. — jeweils zzgl. 20 % Zuschlag zum Stunden-VK.

**Beispiel-Anfangstext (SHK-Ton, Angebot):** „Anbei senden wir Ihnen das angeforderte Angebot für die Arbeiten an Ihrer Anlage. Dieses lautet wie folgt:"

**Beispiel-E-Mail:** „{{anrede}} wie vereinbart das Angebot mit der Nummer {{dokumentenNummer}} für Ihre Sanitär-/Heizungsarbeiten. Mit freundlichen Grüßen {{name}}"

---

## 8. Branchenpaket Entrümpelung — Gewerke-Vorlage (zweites Modul)

**Kategorien im Gewerke-/Materialkatalog (Vorschlag zur Vorbefüllung):**

| Kategorie | Typische Gewerke | Hinweis |
|---|---|---|
| Lohnarbeiten | Kolonnenleiter, Helfer — je Std. oder Tagessatz (reines Lohn-Gewerk) | analog SHK, andere Sätze |
| Entsorgung | „Container stellen & entsorgen" (Preis pro Container, z. B. 5 m³), Sperrmüll/Tonne, Sondermüll-Zuschlag, Elektroschrott | meist Fremdleistung (Entsorgerpreis + Zuschlag) |
| Transport | Fahrzeuggröße/-typ, Kilometerpauschale | Fremdleistung oder Sonstiges |
| Zuschläge | Etagenzuschlag ohne Aufzug, Halteverbotszone einrichten, Express/kurzfristig | eigene Gewerke, meist Gesamtpreiskalkulation |
| Endreinigung | Besenreine Übergabe, Grundreinigung | Lohn + ggf. Material (Reinigungsmittel) |
| Wertanrechnung | Ankauf/Anrechnung verwertbarer Gegenstände | **negative Position** — siehe unten |
| Pauschalen | „Wohnung entrümpeln" (Preis pro m² Wohn-/Objektfläche) | Schnellkalkulation, siehe unten |

Beispiel-Gewerk „Wohnung entrümpeln" (Einheitspreiskalkulation, Bezugsgröße m² Wohnfläche): Kostenzeile Lohn — X Minuten Helfer je m²; Kostenzeile Fremdleistung — anteilige Entsorgungskosten je m²; Zuschlag je Kostenart wie in Abschnitt 2. Beispiel-Gewerk „Container stellen & entsorgen" (Gesamtpreiskalkulation, Bezugsgröße Container): Kostenzeile Fremdleistung — Containerstellung + Entsorgung als Pauschale, Kostenzeile Lohn — Beladezeit. Beide zeigen, dass dasselbe Gewerk-Prinzip aus Abschnitt 2 ohne Änderung an der Mechanik auf branchentypisch ganz andere Bezugsgrößen passt.

**Technische Anforderung:** Wertanrechnung setzt voraus, dass eine Position einen **negativen** Preis haben kann (Menge × Einzelpreis < 0), damit sie die Angebotssumme mindert statt sie zu erhöhen. Das ist eine kleine, aber notwendige Ergänzung an der Gewerk-/Positions-Rechenlogik aus Abschnitt 1/2.

**Anknüpfung an die Gap-Analyse:** Die Kategorie „Pauschalen" mit dem Gewerk „Wohnung entrümpeln" (Preis pro m² Wohnfläche) ist genau das Muster, das die Gap-Analyse unter 1.2 als fehlende „Schnellkalkulation" (Sofortpreis aus einer Kennzahl, Vorbild Ent1Pro: „m²-Fläche → Sofortpreis") beschreibt. Ein Formularfeld „Fläche in m²" kann direkt an dieses Gewerk gekoppelt werden (siehe `PRD.md`, Abschnitt „Gewerke: Kalkulationseinheit für Angebote") und liefert damit automatisch eine vorausgefüllte Angebotsposition — ohne eigene Rechenlogik im Formular-Baukasten.

**Beispiel-Anfangstext (Entrümpelungston, Angebot):** „Anbei senden wir Ihnen das angeforderte Angebot für die Räumung/Entrümpelung Ihres Objekts. Dieses lautet wie folgt:"

**Beispiel-Schlusstext-Ergänzung:** „Der genannte Preis versteht sich als Festpreis auf Basis der Besichtigung/Ihrer Angaben. Sollten sich vor Ort abweichende Mengen ergeben, sprechen wir dies vorab mit Ihnen ab."

**Beispiel-E-Mail:** „{{anrede}} wie vereinbart das Angebot mit der Nummer {{dokumentenNummer}} für die Räumung Ihres Objekts. Mit freundlichen Grüßen {{name}}"

---

## 9. Was Code bleibt, was Branchenpaket-Konfiguration wird

| Bereich | Code (produktweit) | Konfiguration (je Branchenpaket) |
|---|---|---|
| Bausteintypen (Text/Titel/Position/Bild) | ✓ | — |
| Summen-/Steuerlogik, Lohnkostenanteil-Berechnung | ✓ | — |
| **Gewerk-Datenmodell** (Kopf, Kostenzeilen, Kostenarten, Zuschlagsrechnung, Einheitspreis vs. Gesamtpreis) | ✓ | — |
| Gewerke-/Materialkatalog (Ordner-Datenmodell) | ✓ | Welche Kategorien, welche Gewerke, mit welchen Preisen/Bezugsgrößen befüllt sind |
| Dokumenttypen (Angebot/Auftragsbestätigung/Rechnung) und ihr Textvorlagen-Mechanismus | ✓ | Anfangs-/Schlusstexte, E-Mail-Texte |
| PDF-/Briefpapier-Erzeugung | ✓ (Wiederverwendung PROJ-2) | Logo/Farbe (bereits über Branding) |
| Negative Positionen (Wertanrechnung) | ✓ (Rechenregel) | Ob/wo genutzt, ist Branchensache |

Diese Trennlinie folgt exakt dem in `PRD.md` bereits festgelegten Prinzip für die Branchenpaket-Architektur (PROJ-14) und dem Formular-Baukasten — hier nur auf Angebotskalkulation angewendet.

---

## 10. Offene Punkte für den Betrieb

1. Soll der Lohnkostenanteil-Ausweis (Abschnitt 1) in V1 verpflichtend für jedes Angebot/jede Rechnung erzeugt werden, oder als optionale Einstellung je Dokumenttyp?
2. Zahlungsziel/Skonto in V1 (Abschnitt 6) — reicht die schlanke globale Einstellung, oder wird pro Kunde/Angebot ein abweichender Wert gebraucht?
3. Mahnwesen und Abschlagsrechnungen (Abschnitt 6) — bewusst vertagt lassen oder als neues Ticket mit Zielpriorität aufnehmen?
4. Negative Positionen/Wertanrechnung (Abschnitt 8) — nur für Entrümpelung freischalten oder produktweit erlauben (z. B. Rabattzeilen bei SHK)?
5. `PRD.md` und `INDEX.md` sind bereits ergänzt (Abschnitt „Gewerke: Kalkulationseinheit für Angebote", Ticket PROJ-22) — offen ist noch, ob PROJ-22 vor oder nach PROJ-6 (Terminplanung) gebaut wird, da die Lohnminuten-Ableitung aus Abschnitt 2 die Terminschätzung verbessern könnte, aber keine Abhängigkeit dorthin ist.
