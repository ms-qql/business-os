# Brainstorm — Whitelabel Business OS für lokale Dienstleister

**Datum:** 2026-08-15
**Status:** Divergenz + Konvergenz abgeschlossen, bereit für `/abc-requirements`
**Technik:** Progressive Flow über 9 Domänen-Runden, 75 Ideen

---

## 1. Session-Setup

| | |
|---|---|
| **Thema** | Whitelabel Business OS für lokale Dienstleister — Core-Modul + optionale Segment-Module |
| **Pilot-Segment** | Handwerk (Elektro, SHK, Maler) |
| **Kern-Kette** | Anfrage → Qualifizierung → Vor-Ort-Termin → Angebot → Auftrag → Rechnung/Nachfassen |
| **Geschäftsmodell** | Multi-Tenant SaaS, Direktvertrieb an Handwerksbetriebe, Whitelabel = Branding je Mandant (Logo, Farben, eigene Domain) |
| **Ziel der Session** | Klare Anforderungen. Umsetzung explizit später. |
| **Ausgangslage** | Kein Erstkunde vorhanden, Branchenwissen vorhanden |
| **Energie** | Strategisch-breit, dann konvergent |
| **Gesetzt (nicht diskutiert)** | Stack: FastAPI + Postgres/RLS, MinIO, Dokploy, Next.js oder Flutter |

### Im Verlauf getroffene Entscheidungen

1. **Hebel 1 = Auto-Triage** (Idee #2) — Anfragen aussortieren und priorisieren
2. **Hebel 2 = Automatische Angebotserstellung** (Idee #5) aus eigener Preisliste
3. **Core versendet nie autonom** — nur Entwürfe, Freigabe-Klick zwingend
4. **Telefon-Mailbox-Transkription** gehört in Core (Kanal-Anbindung einfach)
5. **Sprachagent** = Premium-Modul, später
6. **Build statt Buy** (Runde 6, Weg D) — Kern selbst bauen, Standardteile zukaufen
7. **Entlastung vor Geschwindigkeit** (Runde 8) — Betriebe sind ausgelastet; Triage dient dem Auswählen und Absagen, nicht dem schnellen Zugreifen
8. **Mitarbeiterakquise als eigenes Modul** (Runde 9) — gleiche Pipeline, zweiter Objekttyp, hohe Zahlungsbereitschaft, eigener Rechtsrahmen
9. **WhatsApp raus aus Core** — WhatsApp Business API verlangt Meta-Verifizierung des Unternehmens, vorab genehmigte Nachrichtenvorlagen und ein 24-Stunden-Fenster für freie Nachrichten. Pro Mandant ein eigener Onboarding-Prozess, kein API-Key. → eigenes Modul.

---

## 2. Divergenz — 56 Ideen

### Runde 1: Betriebsalltag & Nutzer

Ausgangsbeobachtung: Der Engpass im Handwerk ist nicht die Arbeit, sondern das Büro nach Feierabend. Anfragen kommen über fünf Kanäle, Angebote entstehen um 21 Uhr, ein erheblicher Teil der Anfragen bleibt unbeantwortet, weil er unpassend ist — aber niemand hat Zeit, das zu prüfen.

**[Betrieb #1] Ein Posteingang für alle Kanäle**
_Concept:_ Telefon (Mailbox→Transkript), E-Mail, Web-Formular, WhatsApp, Portale (MyHammer/Check24) landen in einer Liste mit einheitlicher Struktur.
_Novelty:_ Nicht „CRM mit E-Mail-Anbindung", sondern: der Kanal ist egal, die Anfrage hat immer dieselben Felder.

**[Betrieb #2] Auto-Triage statt Auto-Antwort** ⭐ HEBEL 1
_Concept:_ Jede Anfrage erhält Gewerk, Dringlichkeit, geschätzten Auftragswert, Entfernung und ein Ampel-Urteil „passt / passt nicht / Rückfrage nötig".
_Novelty:_ Der Wert liegt im Aussortieren, nicht im Antworten. Ein Handwerker will 30 Anfragen auf 6 reduzieren.

**[Betrieb #3] Rückfragen-Automat**
_Concept:_ Fehlt Information (Stockwerk, Baujahr, Zählerschrank-Foto, Miete/Eigentum), fragt das System gezielt nach — mit gewerkspezifischer Fragenliste.
_Novelty:_ Die Fragenliste ist Konfiguration, kein Code. Der Betrieb pflegt seine eigenen Qualifizierungsfragen.

**[Betrieb #4] Foto-zu-Aufmaß**
_Concept:_ Kunde lädt Fotos hoch, Vision-Modell erkennt Objekte (Heizkörper, Steckdosen, Wandfläche) und schlägt Positionen vor.
_Novelty:_ Kürzt den Vor-Ort-Termin für Kleinaufträge komplett weg.

**[Betrieb #5] Angebot aus Textbaustein-Bibliothek + Preisliste** ⭐ HEBEL 2
_Concept:_ Das Modell wählt aus den *eigenen* hinterlegten Leistungspositionen und Preisen des Betriebs und formuliert nichts frei Erfundenes. Ausgabe: PDF im Betriebs-Branding.
_Novelty:_ Kein „KI schreibt Angebot", sondern KI *komponiert* aus geprüften Bausteinen. Preisfantasie ist strukturell ausgeschlossen.

**[Betrieb #6] Angebot immer als Entwurf, nie automatisch raus**
_Concept:_ Jedes Angebot braucht einen Freigabe-Klick. Der Chef sieht die Abweichung zu Standardpreisen.
_Novelty:_ Haftung. Ein automatisch versendetes Angebot ist rechtlich bindend — das ist ein Produkt-Killer, kein Feature.

**[Betrieb #7] Terminvergabe mit Fahrtwegs-Logik**
_Concept:_ Terminvorschläge berücksichtigen, wo der Monteur an dem Tag ohnehin ist. Cluster nach PLZ.
_Novelty:_ Für Handwerk ist der Kalender ein Routen-Problem, kein Zeitslot-Problem. Unterscheidet das Produkt von jedem Friseur-Tool.

**[Betrieb #8] Nachfassen als Default**
_Concept:_ Angebot raus → Reminder nach 3/7/14 Tagen, Status wandert auf „nachgefasst", dann „verloren" mit Grund.
_Novelty:_ Der größte Umsatzhebel im Handwerk. Angebote versanden, weil niemand nachfragt.

**[Betrieb #9] Zwei Oberflächen: Büro-Desktop, Monteur-Handy**
_Concept:_ Monteur sieht nur: heutige Termine, Adresse, Auftragsdetails, Fotos hochladen, Zeit erfassen, „erledigt".
_Novelty:_ Getrennte Rollen-Apps statt einer App mit Rechtefiltern. Ein Monteur mit Handschuhen bedient keine Tabelle.

**[Betrieb #10] Der Kunden-Status-Link**
_Concept:_ Endkunde erhält eine Link-Seite: „Ihre Anfrage — Status: Angebot in Arbeit / Termin am X / Monteur unterwegs".
_Novelty:_ Senkt die Anrufflut im Büro. Paketverfolgung, aber für Handwerksaufträge.

**[Betrieb #11] Migration ist das Verkaufshindernis Nr. 1**
_Concept:_ Import aus Excel, Outlook-Kontakten, bestehenden Programmen (pds, Streit, Label). Alte Kundenliste in 10 Minuten drin.
_Novelty:_ Kein Feature — ein Vertriebs-Gate. Ohne das kauft niemand.

**[Betrieb #12] Rechnung als Grenze, nicht als Ziel**
_Concept:_ Bewusst keine Buchhaltung. Stattdessen DATEV-/Lexware-Export und saubere Schnittstelle zum Steuerberater.
_Novelty:_ Das Verlockendste weglassen. Buchhaltung bedeutet GoBD-Pflicht, Zertifizierung und Haftung — das versenkt ein Solo-Projekt.

### Runde 2: KI & Automatisierung

Leitfrage: Wo darf das System *entscheiden*, wo nur *vorschlagen*, wo gar nichts tun.

**[KI #13] Vertrauensstufen statt An/Aus**
_Concept:_ Pro Automatisierung drei Stufen — beobachten (Vorschlag im Log), assistieren (Entwurf zur Freigabe), autonom (macht es selbst). Der Betrieb schiebt den Regler hoch, wenn Vertrauen wächst.
_Novelty:_ Löst das Onboarding-Problem. Niemand aktiviert an Tag 1 eine KI, die Kunden anschreibt. Das System verdient sich Rechte.

**[KI #14] Eingangsklassifizierung als strukturiertes Zwischenformat**
_Concept:_ Anfrage → JSON (Gewerk, Leistungsart, Objekt, Dringlichkeit, Adresse, Budget-Signal, Kundentyp privat/gewerblich). Alles Weitere arbeitet auf diesem JSON, nicht auf dem Rohtext.
_Novelty:_ Entkoppelt Kanal von Logik. Später austauschbares Modell bei gleicher Pipeline.

**[KI #15] Antwortentwurf im Ton des Betriebs**
_Concept:_ Betrieb hinterlegt 3–5 eigene alte Antworten; das System übernimmt Duzen/Siezen, Länge, Grußformel, Dialektfärbung.
_Novelty:_ Whitelabel geht über das Logo hinaus — die *Stimme* ist das eigentliche Branding in der Kundenkommunikation.

**[KI #16] Telefon-Mailbox → Ticket**
_Concept:_ Mailbox-Aufnahme wird transkribiert, klassifiziert, als Anfrage angelegt; Rückrufwunsch mit Zeitfenster extrahiert.
_Novelty:_ Handwerk ist telefondominiert. Wer nur E-Mail abdeckt, deckt die Hälfte nicht ab.

**[KI #17] KI-Telefonassistent als späteres Modul, nicht Core**
_Concept:_ Echtzeit-Sprachagent nimmt Anrufe an, qualifiziert, bucht Termin.
_Novelty:_ Größter Wow-Effekt, größtes Risiko (Latenz, Kosten, Fehlbuchungen, Akzeptanz älterer Kunden). Gehört bewusst hinter die Core-Linie.

**[KI #18] Kalkulations-Assistent mit Deckungsbeitrags-Warnung**
_Concept:_ Beim Angebot: Materialkosten + Stunden × Stundensatz. Warnung, wenn die Marge unter die Schwelle des Betriebs fällt.
_Novelty:_ Nicht „schneller Angebote", sondern „keine unprofitablen Angebote". Zahlungsbereitschaft ist hier höher.

**[KI #19] Lernschleife aus gewonnenen/verlorenen Angeboten**
_Concept:_ Verlorene Angebote mit Grund erfassen. Das System zeigt Muster: „Angebote mit mehr als 5 Tagen Verzug gewinnen Sie zu 12 %, unter 24 h zu 47 %."
_Novelty:_ Aus dem CRM wird ein Beratungswerkzeug. Verkauft sich als Einsicht, nicht als Software.

**[KI #20] Alles Wichtige ist überschreibbar und protokolliert**
_Concept:_ Jede KI-Ausgabe zeigt ihre Quelle (welche Preisposition, welche Regel), ist editierbar; Änderungen fließen als Korrektursignal zurück.
_Novelty:_ Nachvollziehbarkeit ist bei Angeboten kein Nice-to-have — im Streitfall muss der Chef sagen können, woher die Zahl kam.

**[KI #21] Harte Grenze: keine Preisfindung ohne Betriebsdaten**
_Concept:_ Kein Modell darf Preise schätzen. Ohne hinterlegte Preisliste kein Angebotsmodul, stattdessen geführte Ersteinrichtung der Positionen.
_Novelty:_ Bewusst eine Funktion verweigern. Erfundene Preise wären der schnellste Weg, den ersten Kunden zu verlieren.

**[KI #22] Kostenkontrolle je Mandant**
_Concept:_ Token-/Minutenbudget pro Betrieb, sichtbar im Admin, Drosselung statt Überraschungsrechnung.
_Novelty:_ Bei Flatrate-Preisen ist ein Vielnutzer sonst der Verlustbringer. Betriebswirtschaftliche Anforderung, kein Tech-Detail.

### Runde 3: Geschäftsmodell & Preis

**[Modell #23] Preis an Volumen, nicht an Nutzern**
_Concept:_ Basis-Abo plus Staffel nach Anfragevolumen statt pro Sitzplatz.
_Novelty:_ Handwerksbetriebe haben 3–15 Mitarbeiter, aber nur 1–2 Büro-Nutzer. Per-Seat verdient nichts, Volumen skaliert mit dem Nutzen.

**[Modell #24] Der Einstieg ist eine Diagnose, kein Abo**
_Concept:_ Erste Anfrage-Analyse kostenlos: Betrieb leitet 20 alte Anfragen weiter und erhält die Auswertung „so viel Umsatz lag in unbeantworteten Anfragen".
_Novelty:_ Verkauft die Diagnose vor dem Produkt. Zahlen aus dem eigenen Betrieb überzeugen stärker als jede Demo.

**[Modell #25] Einrichtungspauschale ist Pflicht, nicht optional**
_Concept:_ Einmalbetrag für Preislisten-Erfassung, Textbausteine, Kanal-Anbindung, Datenimport.
_Novelty:_ Ohne befüllte Preisliste funktioniert das Angebotsmodul nicht — die Einrichtung ist die eigentliche Wertschöpfung. Kostenlos angeboten wird sie nicht gemacht, und das Produkt scheitert stumm.

**[Modell #26] Module als Preisstufen, nicht als Kästchen**
_Concept:_ Core → Plus → Premium statt frei kombinierbarer Module.
_Novelty:_ Weniger Kombinatorik. Jede frei wählbare Kombination ist sonst ein eigener Test- und Supportfall.

**[Modell #27] Segment-Module sind Konfiguration, kein Code** ⭐ ARCHITEKTUR-KERN
_Concept:_ Was Handwerk von Friseur unterscheidet, steckt in Datensätzen: Qualifizierungsfragen, Leistungskatalog, Terminarten, Textbausteine, Pflichtfelder. Ein „Branchenpaket" ist ein Import-Bundle.
_Novelty:_ Die zentrale Architekturentscheidung des Produkts. Segmente als Code = fünf Codebasen. Segmente als Daten = ein Produkt, das ein Vertriebspartner selbst auf eine neue Branche zuschneiden kann.

**[Modell #28] Referenzbetrieb statt Marketing**
_Concept:_ Erster Kunde erhält dauerhaft günstige Konditionen gegen Referenz, Feedback und Namensnennung.
_Novelty:_ Im Handwerk läuft Vertrieb über Innungen, Kollegenempfehlung und Fachgruppen, nicht über Google Ads.

**[Modell #29] Datenexport als Verkaufsargument**
_Concept:_ Jederzeit vollständiger Export aller Kunden, Angebote und Dokumente — prominent beworben.
_Novelty:_ Handwerker sind von Software-Anbietern gebrannt. Ausstiegsfreiheit senkt die Einstiegshürde messbar.

**[Modell #30] Wachstum über den Steuerberater**
_Concept:_ Steuerberater und Handwerks-IT-Dienstleister als Empfehlungskanal, Provision auf Bestand.
_Novelty:_ Ein Multiplikator mit 40 Handwerksmandanten schlägt 40 Einzelakquisen.

### Runde 4: Betrieb, Datenschutz, Support

**[Betrieb #31] Mandantentrennung ist nicht verhandelbar**
_Concept:_ Jede Tabelle mit `mandant_id`, Row Level Security in Postgres, `mandant_id` immer aus dem Token — nie aus dem Request-Body.
_Novelty:_ Kein Feature, sondern Existenzgrundlage. Ein einziger Cross-Tenant-Leak beendet das Produkt.

**[Betrieb #32] Auftragsverarbeitungsvertrag als Produktbestandteil**
_Concept:_ AVV nach Art. 28 DSGVO, TOM-Dokumentation, Verzeichnis der Verarbeitungstätigkeiten — als fertige PDFs im Onboarding.
_Novelty:_ Jeder Betrieb braucht das rechtlich. Mitgeliefert wird es zum Verkaufsargument statt zum Verkaufshindernis.

**[Betrieb #33] KI-Verarbeitung transparent und regional**
_Concept:_ Dokumentieren, welches Modell welche Daten sieht. EU-Region oder europäischer Anbieter. Opt-out je Mandant für KI-Funktionen.
_Novelty:_ Endkundendaten (Name, Adresse, Objektfotos) gehen ins Modell — das steht im AVV und wird gefragt werden.

**[Betrieb #34] Löschkonzept von Anfang an**
_Concept:_ Aufbewahrungsfristen je Objekttyp (Angebote steuerlich 10 Jahre, verworfene Anfragen 6 Monate), automatische Löschjobs, Löschung auf Kundenwunsch.
_Novelty:_ Nachträglich in ein gewachsenes Schema eingebaut sind das Wochen. Vorne mitgedacht Stunden.

**[Betrieb #35] Support ist der Kostenblock, nicht der Server**
_Concept:_ Handwerksbetriebe rufen an statt zu ticketen, gerne um 7 Uhr. Support-Aufwand je Mandant realistisch kalkulieren und einpreisen.
_Novelty:_ Bei niedrigem Monatspreis sind zwei Support-Anrufe die Marge. Begrenzt, wie viele Kunden solo tragbar sind — eine harte Anforderung an Selbsterklärbarkeit.

**[Betrieb #36] Fehler dürfen nicht still passieren**
_Concept:_ Kanal-Abriss (Postfach nicht erreichbar, Token abgelaufen) erzeugt sichtbare Warnung im Dashboard *und* eine Mail an den Betrieb.
_Novelty:_ Die schlimmste Störung ist die unbemerkte: drei Tage keine Anfragen und niemand merkt es.

**[Betrieb #37] Ein Demo-Mandant mit realistischen Daten**
_Concept:_ Fester Vorführ-Mandant mit erfundenem Elektrobetrieb, gefüllter Historie, echten Abläufen.
_Novelty:_ Doppelnutzen — Vertriebsdemo ohne Kundendaten und Testumgebung für QA und Screenshots.

**[Betrieb #38] Selbst-Onboarding scheitert — Onboarding ist begleitet**
_Concept:_ Geführter Einrichtungsassistent plus ein Termin: Preisliste importieren, Kanal verbinden, erste Anfrage durchspielen.
_Novelty:_ Die Zielgruppe registriert sich nicht abends selbst und pflegt Textbausteine. Wer das annimmt, baut ein Produkt ohne Nutzer.

**[Betrieb #39] Zugriffsrollen minimal halten**
_Concept:_ Drei Rollen — Inhaber (alles), Büro (Anfragen, Angebote, Termine), Monteur (nur eigene Termine, keine Preise).
_Novelty:_ Monteure sollen Kundenpreise oft nicht sehen. Rollen sind hier fachlicher Wunsch, kein Sicherheits-Feigenblatt.

**[Betrieb #40] Betriebsurlaub und Notdienst**
_Concept:_ Abwesenheitsmodus mit automatischer Info an Anfragende; Notfall-Anfragen werden trotzdem markiert und weitergeleitet.
_Novelty:_ SHK und Elektro haben echte Notfälle. Ein System, das im Urlaub stumm bleibt, wird abgeschaltet statt gelobt.

### Runde 5: Failure-Modes (Reverse Brainstorming)

Frage umgedreht: *Wie sorge ich zuverlässig dafür, dass dieses Produkt scheitert?* Jede Antwort ist eine Anforderung im Negativ.

**[Fail #41] Leere Preisliste**
_Concept:_ Betrieb wird freigeschaltet, hat keine Positionen gepflegt, das Angebotsmodul erzeugt Unsinn. Nutzer schließt: „KI kann's nicht."
_Anforderung:_ Angebotsmodul bleibt gesperrt, bis N Positionen erfasst sind. Sperre mit Erklärung, nicht mit Fehlermeldung.

**[Fail #42] Ein falsches Angebot mit echtem Rechtsfolgen-Schaden**
_Concept:_ Zahlendreher im Entwurf, Chef klickt durch, 4.000-€-Auftrag für 400 €. Bindend.
_Anforderung:_ Plausibilitätsprüfung vor Freigabe (Abweichung vom Erfahrungswert, Marge unter Schwelle), Summen groß in der Freigabe-Ansicht, Angebot mit Freibleibend-Klausel und Gültigkeitsdatum.

**[Fail #43] Triage sortiert einen Großauftrag aus**
_Concept:_ Anfrage als „passt nicht" eingestuft, war aber der 30.000-€-Auftrag. Einmal reicht für Vertrauensverlust.
_Anforderung:_ Nichts wird gelöscht oder verborgen, nur sortiert. „Aussortiert" ist ein Filter, kein Papierkorb. Wöchentliche Zusammenfassung des Aussortierten.

**[Fail #44] Das Ding wird ein zweiter Posteingang**
_Concept:_ Betrieb nutzt weiter Outlook und schaut zusätzlich ins Tool. Doppelte Arbeit, Kündigung.
_Anforderung:_ Antworten müssen aus dem System heraus gehen und die Konversation dort weiterlaufen. Halbe Integration ist schlechter als keine.

**[Fail #45] Zu viele Segmente zu früh**
_Concept:_ Friseur, Arzt und Handwerk gleichzeitig. Nichts passt richtig, dreifacher Support, kein Referenzkunde.
_Anforderung:_ Ein Segment bis zum zahlenden Referenzkunden. Zweites Segment erst, wenn das Branchenpaket reine Konfiguration ist (#27).

**[Fail #46] Arztpraxen zu früh angefasst**
_Concept:_ Gesundheitsdaten sind Art.-9-DSGVO-Daten, dazu ärztliche Schweigepflicht (§ 203 StGB). KI-Verarbeitung von Patientenanliegen ist ein eigenes Rechtsprojekt.
_Anforderung:_ Arztpraxis aus der Roadmap streichen, bis Handwerk trägt. Nicht „später auch", sondern begründet vertagt.

**[Fail #47] Der Solo-Betreiber ist der Engpass**
_Concept:_ 15 Kunden, jeder ruft an, gleichzeitig Feature-Entwicklung. Entwicklung stoppt, Produkt veraltet.
_Anforderung:_ Selbstbedienung für alles Wiederkehrende (Preisliste, Textbausteine, Nutzer, Kanäle). Jede Einstellung, die nur der Betreiber ändern kann, ist künftige Support-Last.

**[Fail #48] Kanal bricht ab, keiner merkt es**
_Concept:_ OAuth-Token läuft aus, drei Tage keine Anfragen, verlorene Aufträge, Schuld beim System.
_Anforderung:_ Aktive Überwachung je Kanal, Heartbeat, Alarm an Betrieb und Betreiber (siehe #36).

**[Fail #49] KI-Kosten fressen die Marge**
_Concept:_ Ein Betrieb mit 400 Anfragen im Monat, Vision-Analysen, lange Kontexte. Flatrate wird zum Verlust.
_Anforderung:_ Verbrauch je Mandant messen und begrenzen, teure Funktionen an höhere Stufen binden.

**[Fail #50] Datenschutz-Frage im Verkaufsgespräch nicht beantwortet**
_Concept:_ „Wo liegen meine Kundendaten und wer trainiert damit?" Ohne klare Antwort ist der Termin vorbei.
_Anforderung:_ Eine Seite Klartext — Hosting-Ort, Modell-Anbieter, kein Training auf Kundendaten, AVV im Anhang.

**[Fail #51] Zu viel gebaut, bevor jemand zahlt**
_Concept:_ Neun Monate Entwicklung, dann erste Kundengespräche. Falsche Annahmen fallen zu spät auf.
_Anforderung:_ Kleinster verkaufbarer Umfang = Posteingang + Triage + Angebotsentwurf + Freigabe + Versand. Alles andere wartet auf einen Kunden, der danach fragt.

**[Fail #52] Der Chef vertraut den Entwürfen nicht und schreibt neu**
_Concept:_ Wenn ein Entwurf zu 60 % passt, ist Überarbeiten langsamer als Neuschreiben. Nutzung stirbt leise.
_Anforderung:_ Qualitätsmessung — wie oft wird ein Entwurf ohne Änderung freigegeben? Diese Quote ist die zentrale Produktkennzahl, nicht Logins und nicht Anzahl Anfragen.

### Runde 6: Buy or Build

> Hinweis: Preise und Lizenzbedingungen unten sind vor einer Entscheidung selbst zu prüfen — sie ändern sich laufend. Die Struktur der Argumente ist stabil, die Konditionen nicht.

**[Buy #53] Weg A — Fertige Whitelabel-Plattform wiederverkaufen (GoHighLevel & Co.)**
_Concept:_ Agentur-Plattform mieten, Unter-Accounts an Betriebe vergeben, eigenes Logo. Agentur-Tarif grob im dreistelligen Dollar-Bereich pro Monat; Whitelabel-Domain und App-Branding meist in höheren Stufen.
_Passt:_ Wenn in vier Wochen verkauft werden soll und der Wert in Beratung und Einrichtung liegt.
_Passt nicht:_ GoHighLevel ist für Marketing-Agenturen gebaut (Funnels, Kampagnen, Nurture-Sequenzen). Die beiden identifizierten Hebel — Triage nach Gewerk und Auftragswert (#2) und Angebotserstellung aus der eigenen Preisliste mit Margenprüfung (#5, #18, #21) — bildet es nicht ab. Man kauft genau das, was man nicht braucht, und bekommt nicht, was das Produkt ausmacht.
_Zusatzproblem:_ US-Anbieter, US-Hosting. Man wird gegenüber den Betrieben Auftragsverarbeiter, die Plattform wird Unterauftragsverarbeiter — mit Drittlandtransfer, Standardvertragsklauseln und Transfer Impact Assessment. Machbar, aber Arbeit — und im Verkaufsgespräch (#50) die schwächere Antwort.

**[Buy #54] Weg B — Open-Source-Plattform selbst hosten und erweitern**
_Kandidaten:_ ERPNext/Frappe, Odoo Community, EspoCRM, Twenty, SuiteCRM.
_Passt:_ Datenhoheit, EU-Hosting selbstverständlich, kein Anbieter kann Preise erhöhen.
_Passt nicht:_ Man erbt ein fremdes Datenmodell und dessen Weltbild. Anpassungen kämpfen gegen die Plattform, Upgrades können sie brechen. ERPNext und Odoo sind ERP-Systeme — der Handwerker sieht ein Konzernsystem mit ausgeblendeten Feldern. Die Zielgruppe (#38) verzeiht das nicht.
_Lizenzfalle:_ GPL ist bei SaaS unkritisch (kein Vertrieb). **AGPL nicht** — geänderter AGPL-Code, der als Dienst angeboten wird, verlangt Offenlegung der Änderungen. „Fair-code"-Lizenzen (z. B. n8n) schränken genau das ein, worum es hier geht: das Produkt gebrandet als Dienst weiterverkaufen. Vor jeder Komponente: Lizenz lesen, nicht das Marketing.

**[Buy #55] Weg C — Deutsche Handwerkersoftware**
_Namen:_ Plancraft, hero software, ToolTime, Craftboxx, Meisterwerk; dazu die Alteingesessenen pds, Streit, Label.
_Realität:_ Wettbewerber, keine Bausteine — Whitelabel-Wiederverkauf bietet keiner an. Relevant trotzdem: Sie belegen Markt und Zahlungsbereitschaft und zeigen die Lücke. Die meisten starten beim Auftrag; die These hier setzt davor an, beim Anfrageeingang und der Vorqualifizierung. Das ist eine verteidigbare Position.
_Aufgabe:_ Zwei Nachmittage Wettbewerbsanalyse vor der ersten Zeile Code — um die Abgrenzung in einem Satz sagen zu können.

**[Buy #56] Weg D — Kern selbst, Standardteile zukaufen** ⭐ EMPFEHLUNG
_Prinzip:_ Selbst bauen, was das Produkt *ist*. Zukaufen, was jeder hat.
_Selbst:_ Datenmodell (Anfrage, Kunde, Angebot, Termin, Auftrag), Triage-Logik, Angebotskomposition aus Preisliste, Mandanten- und Rechtekonzept, Oberfläche.
_Zugekauft:_ Zahlungsabwicklung (Stripe), E-Mail-Versand (Postmark/Brevo), Telefonie und Transkription, PDF-Erzeugung, Modell-Anbieter, Fehlerüberwachung (Sentry), Hosting.
_Warum:_ Der Aufwand steckt nicht im CRM — Kunden, Angebote, Termine sind schnell gebaut. Er steckt in Kanal-Anbindungen, Onboarding und Zuverlässigkeit. Genau die nimmt einem keine Plattform ab.

#### Der Lock-in-Test

Nicht „ist das Lock-in?", sondern **„was kostet der Ausstieg in Wochen?"** Für jede Komponente sechs Fragen:

1. **Datenhoheit** — kommen alle Daten strukturiert und vollständig heraus, ohne Aufpreis?
2. **Wem gehört der Kunde?** Laufen Vertrag und Abrechnung über dich oder über den Anbieter? Der härteste Lock-in, härter als jede Technik.
3. **Steckt die Geschäftslogik im fremden System?** Im Anbieter-Baukasten geklickte Automatisierungen sind nicht mitnehmbar. Logik im eigenen Code ist portabel.
4. **Wie viele Wochen kostet der Austausch?** E-Mail-Versender tauschen: Tage. Modell-Anbieter hinter eigener Schnittstelle: eine Woche. Plattform tauschen: Neubau.
5. **Preishoheit** — kann der Anbieter die Marge einseitig zerstören? Bei Wiederverkauf: jederzeit.
6. **Rechtsposition** — wo liegen die Daten, wer ist Unterauftragsverarbeiter, ist das den Kunden erklärbar?

**Praktische Regel:** eigenes Datenmodell in der eigenen Datenbank, alles Fremde hinter einer eigenen Schnittstelle. Dann ist jeder Zulieferer austauschbar und keiner besitzt dich. Die eine bewusst eingegangene Ausnahme ist die Datenbank selbst — Postgres ist die sicherste Wette.

#### Empfehlung Buy-or-Build

**Weg D, mit einer Nutzung von Weg A, die meist übersehen wird:** eine fertige Plattform als *Validierungs-Attrappe*, nicht als Produkt. Zwei bis drei Betriebe damit von Hand bedienen — Anfragen einsammeln, Triage manuell, Angebote manuell. Kostet ein paar hundert Euro und liefert in sechs Wochen mehr Erkenntnis über die echten Abläufe als sechs Monate Entwicklung; vor allem zeigt es, ob jemand zahlt (#24, #51). Was funktioniert, wird dann als eigenes Produkt gebaut.

Gegen reinen Wiederverkauf spricht strukturell: Als Wiederverkäufer verkauft man dasselbe wie tausend andere Agenturen. Das Handwerks-Wissen bleibt Beratungsleistung statt Vermögenswert. Als Eigenbau ist es ins Produkt eingebaut.

### Runde 7: Wettbewerb & Abgrenzung

> Hinweis: Anbieterlandschaft nach Kenntnisstand, nicht tagesaktuell recherchiert. Funktionsumfänge und Preise ändern sich schnell — vor einem Verkaufsgespräch gegenprüfen.

**[Wettbewerb #57] Lager 1 — Die Alteingesessenen**
_Wer:_ pds, Streit, Label, TopKontor/blue:solution, Winworker, Sander.
_Stärke:_ Vollständig bis zur Buchhaltung, GAEB-Ausschreibungen, DATEV, Lohn, Materialwirtschaft mit Großhändler-Anbindung. Tief verankert, Vertrieb über Fachhändler und Innungen.
_Schwäche:_ Desktop-Erbe, Bedienung aus den Neunzigern, Einführung dauert Monate, mobil schwach. Der Anfrageeingang interessiert sie nicht — sie beginnen beim bereits angelegten Vorgang.
_Konsequenz:_ Nicht der Gegner. Diese Betriebe behalten ihr System. Nebeneinander-Existenz nötig → DATEV-Export und sauberer Datenexport (#29) wichtiger als eigene Rechnungsfunktion.

**[Wettbewerb #58] Lager 2 — Die Cloud-Generation**
_Wer:_ Plancraft, hero software, ToolTime, Craftboxx, Meisterwerk, Openhandwerk, 123erfasst.
_Stärke:_ Gute Oberflächen, mobil gedacht, schnelle Angebote und Rechnungen, Zeiterfassung, gut finanziert, aggressives Marketing.
_Lücke:_ Ihr Ablauf startet, *wenn der Chef bereits entschieden hat, ein Angebot zu machen*. Wie die Anfrage hereinkam, wer sie beantwortet hat, ob sie es wert war — bei ihnen ein leeres Formularfeld.
_Warnung:_ „Angebote schneller erstellen" ist damit **kein** Alleinstellungsmerkmal. Die Abgrenzung darf nicht darauf gebaut sein.

**[Wettbewerb #59] Lager 3 — Die Portale**
_Wer:_ MyHammer, Check24 Profis, Aroundhome, Blauarbeit.
_Rolle:_ Kanal und Konkurrent zugleich. Sie liefern Anfragen und machen die Vorqualifizierung selbst, gegen Provision oder Lead-Gebühr.
_Verkaufsargument daraus:_ Der Betrieb zahlt pro Lead, oft für unpassende. „Sie zahlen für Leads — wir sorgen dafür, dass Sie die richtigen zuerst anfassen und die falschen in zwei Minuten los sind."
_Risiko:_ Als Kanal-Anbindung unzuverlässig (kein offizielles API-Versprechen) → korrekt in Premium.

**[Wettbewerb #60] Lager 4 — Der eigentliche Ist-Zustand** ⭐
_Wer:_ Outlook, Excel, Papierkalender, WhatsApp auf dem Chef-Handy, Telefonsekretariat (ebuero & Co.), das Büro der Ehefrau, der Abend ab 20 Uhr.
_Bedeutung:_ Das ist der echte Wettbewerber, nicht Plancraft. Der Betrieb vergleicht nicht „Ihr Tool gegen hero software", sondern „Ihr Tool gegen wie ich es heute mache".
_Konsequenz:_ Preisbegründung ist ein Stundenlohnvergleich (Chef-Abendstunden, Sekretariatskosten), kein Feature-Vergleich. Einstiegshürde ist Gewohnheit, nicht Konkurrenz.

**[Wettbewerb #61] Lager 5 — Die KI-Neulinge**
_Wer:_ KI-Telefonassistenten und Anfrage-Bots; im US-Markt für Home Services bereits eigene Kategorie, in Deutschland im Kommen.
_Bedeutung:_ Hier entsteht der künftige Wettbewerb — nicht bei den ERP-Anbietern. Schnell, aber dünn: nehmen Anrufe an und buchen Termine, kennen die Preisliste des Betriebs nicht.
_Konsequenz:_ Verteidigung ist nicht der Sprachagent (bekommt jeder), sondern die Verbindung von Anfrage und betriebseigener Kalkulation.

#### Was verteidigbar ist — und was nicht

**Nicht verteidigbar:** das Sprachmodell, „KI schreibt Texte", schöne Oberflächen, Angebotserstellung an sich, ein Terminkalender. Alles davon hat jeder in zwölf Monaten.

**Verteidigbar:**
1. **Die gepflegte Preis- und Textbausteinbibliothek des Betriebs** — nach sechs Monaten Nutzung mühsam nachzubauen. Wechselkosten, die durch Nutzen entstehen statt durch Datengeiselhaft (#29).
2. **Die Rückkopplung gewonnen/verloren** (#19) — wer weiß, welche Angebote dieses Betriebs gewinnen, kalkuliert besser als ein generisches Werkzeug.
3. **Kanal-Anbindungen und ihre Zuverlässigkeit** (#48) — langweilig, unsexy, kopiert niemand gern.
4. **Begleitetes Onboarding** (#38, #25) — in dieser Zielgruppe der Unterschied zwischen Nutzung und Karteileiche.

Punkte 3 und 4 sind Dienstleistung, nicht Code. In diesem Markt ist genau das der Burggraben.

#### Abgrenzungssatz — Kandidaten

**A — Geschwindigkeit:** „Wir sorgen dafür, dass Sie auf jede Kundenanfrage innerhalb einer Stunde mit einem fertigen Angebot antworten — ohne dass Sie abends am Schreibtisch sitzen."

**B — Filter:** „Wir sortieren Ihre Anfragen, bevor Sie sie lesen: welche passen, welche lohnen sich, welche können weg."

**C — Kombination (EMPFEHLUNG):** „Andere Handwerkersoftware fängt beim Auftrag an. Wir fangen bei der Anfrage an: alle Kanäle in einem Posteingang, automatisch sortiert nach Passung und Auftragswert, mit fertigem Angebotsentwurf aus Ihren eigenen Preisen — Sie prüfen und geben frei."

C grenzt im ersten Satz gegen Lager 2 ab, liefert im zweiten den konkreten Nutzen und baut das Entwurf-Prinzip (#6) als Vertrauensargument ein.

#### Die offene Kernannahme

> **Gewinnt im Handwerk wirklich, wer zuerst antwortet?**

Wenn ja: Antwortgeschwindigkeit ist das Verkaufsargument, alles andere folgt.
Wenn nein — Aufträge laufen über Empfehlung und Stammkundschaft, Geschwindigkeit ist egal — dann ist der Hebel **Entlastung** (Abendstunden zurückgewinnen) und die Preisargumentation ändert sich komplett.

Das ist die eine Frage, die die Validierungsphase beantworten muss. Alles andere ist Detail.

### Runde 8: Neuausrichtung — Entlastung statt Geschwindigkeit

**Nutzer-Entscheidung:** Handwerksbetriebe sind typischerweise sehr gut ausgelastet. Primärer Hebel ist **Entlastung**, Geschwindigkeit erst danach.

Das dreht den Zweck der Triage: nicht „schnell zugreifen", sondern **auswählen und sauber ablehnen**.

**[Entlastung #62] Die Absage ist ein Kernfeature, kein Randfall**
_Concept:_ Höflicher Absagetext mit offener Tür („aktuell ausgelastet bis KW 43, melden Sie sich gern wieder"), ein Klick, Vorgang geschlossen.
_Novelty:_ Kein Wettbewerber baut die Absage als Hauptfunktion. Für einen ausgelasteten Betrieb ist sie der häufigste Vorgang — heute der unangenehmste, weil er meist gar nicht stattfindet und die Anfrage liegen bleibt.

**[Entlastung #63] Kapazität als Eingabegröße der Triage**
_Concept:_ Betrieb pflegt grob freie Kapazität je Woche und nächsten freien Termin. Die Ampel bewertet gegen die tatsächliche Auslastung.
_Novelty:_ Bei Vollauslastung bedeutet „passt" etwas anderes als bei Leerlauf. Ohne Kapazitätsgröße bewertet das System an der Realität vorbei.

**[Entlastung #64] Auswahl nach Deckungsbeitrag, nicht nach Auftragswert**
_Concept:_ Sortierung nach erwartetem Deckungsbeitrag je Monteurstunde statt nach Auftragssumme.
_Novelty:_ Der 30.000-€-Auftrag mit sechs Wochen Bindung und 8 % Marge ist schlechter als drei Wartungsaufträge. Die Rechnung macht der Chef im Kopf — kein Tool bildet sie ab.

**[Entlastung #65] Preis statt Absage bei Überauslastung** ⭐
_Concept:_ Fachlich passend, zeitlich nicht: Angebot mit Auslastungsaufschlag statt Absage. Der Kunde entscheidet.
_Novelty:_ Verwandelt Kapazitätsknappheit in Marge statt in verlorene Anfragen. Ökonomisch der stärkste Einzelhebel im Produkt.

**[Entlastung #66] Stammkunden gehen vor**
_Concept:_ Bestandskunden werden in der Triage automatisch hochgestuft, unabhängig vom Auftragswert.
_Novelty:_ Ein ausgelasteter Betrieb lebt von Wiederholung. Ein System, das den Stammkunden hinter einen Neukunden sortiert, wird sofort abgeschaltet.

**[Entlastung #67] Warteliste mit Rückmeldung**
_Concept:_ „Passt, aber nicht jetzt" → Wiedervorlage bei freier Kapazität, automatische Rückmeldung an den Kunden.
_Novelty:_ Heute ein Zettel oder nichts. Aus abgelehnten Anfragen wird eine Pipeline für die nächste Flaute.

**[Entlastung #68] Die Kennzahl ändert sich**
_Concept:_ Nicht Antwortzeit, sondern gesparte Büro-Stunden je Woche, Anteil automatisch erledigter Anfragen, durchschnittlicher Deckungsbeitrag je Auftrag.
_Novelty:_ Was gemessen wird, wird verkauft. Der Betrieb kauft eine Abendstunde zurück.

### Runde 9: Mitarbeiterakquise als Modul

**Nutzer-Impuls:** Mitarbeiterakquise könnte ein USP sein. — Trifft zu: Fachkräftemangel ist im Handwerk der teurere Schmerz, und es ist **derselbe Ablauf** wie bei Kundenanfragen (Eingang, strukturieren, qualifizieren, antworten, terminieren, absagen). Die Maschine steht bereits, es ist ein zweiter Objekttyp.

**[Recruiting #69] Dieselbe Pipeline, zweites Objekt**
_Concept:_ Bewerbung läuft durch denselben Posteingang, dasselbe Strukturformat, dieselbe Terminlogik wie eine Kundenanfrage.
_Novelty:_ Architektonisch fast geschenkt, verkäuflich als eigenes Modul mit eigener Zahlungsbereitschaft. Bestes Aufwand-Ertrag-Verhältnis im Backlog.

**[Recruiting #70] Kurzbewerbung ohne Lebenslauf**
_Concept:_ Karriereseite im Betriebs-Branding, fünf Felder, WhatsApp oder Formular, kein PDF, kein Anschreiben.
_Novelty:_ Ein Geselle bewirbt sich vom Handy in der Mittagspause oder gar nicht. Klassische Bewerbungsprozesse filtern hier alle heraus.

**[Recruiting #71] Hier zählt Geschwindigkeit doch**
_Concept:_ Antwort in unter einer Stunde, Terminvorschlag zum Probearbeiten im selben Zug.
_Novelty:_ Umkehrung: bei Kundenanfragen ist Entlastung der Hebel, bei Bewerbern Geschwindigkeit. Gute Handwerker sind in Tagen vergeben.

**[Recruiting #72] Empfehlungsprämie eingebaut**
_Concept:_ Bestehende Mitarbeiter teilen einen personalisierten Link, Prämie wird nachverfolgt und ausgezahlt.
_Novelty:_ Wirksamster Kanal im Handwerk — heute ohne jedes Werkzeug, rein mündlich.

**[Recruiting #73] Preisargument ist ein anderes**
_Concept:_ Vergleichsgröße ist die Personalvermittler-Provision (mehrere Monatsgehälter) oder eine Stellenanzeige, nicht ein Software-Abo.
_Novelty:_ Ein Modul, das eine einzige Einstellung ermöglicht, hat sich vielfach bezahlt. Höchste Zahlungsbereitschaft im Produkt.

**[Recruiting #74] ⚠️ Rechtliche Grenze — hart**
_Concept:_ Bewerber-Screening durch KI gilt nach EU AI Act als **Hochrisiko-Anwendung** (Anhang III, Beschäftigung). Dazu AGG: automatisierte Vorauswahl, die mittelbar nach Alter, Herkunft, Geschlecht oder Behinderung sortiert, ist ein Haftungsfall — für Anbieter *und* Betrieb.
_Anforderung:_ Das Modul darf **strukturieren, antworten und terminieren — nicht bewerten, ranken oder aussortieren.** Kein Score, keine Empfehlung, keine automatische Absage. Der Betrieb entscheidet, das System schreibt nur. Bedingung der Baubarkeit, nicht Vorsicht.
_Nebeneffekt:_ Eigene Löschfristen für Bewerberdaten (Absage + Frist), strikte Trennung von Kundendaten.

**[Recruiting #75] Trotzdem nicht ins Core**
_Concept:_ Modul nach dem Referenzkunden, nicht davor.
_Novelty:_ Verlockend, weil der Schmerz größer ist — aber es verdoppelt Rechtsrahmen und Zielgruppenansprache (Chef kauft für sich vs. Chef kauft fürs Personalproblem). Erst muss der Kern tragen.

---

## 3. Konvergenz — Der Schnitt

### 3.1 Produktdefinition in einem Satz

> Ein Business OS für **ausgelastete** Handwerksbetriebe, das eingehende Kundenanfragen aus allen Kanälen einsammelt, nach Deckungsbeitrag und freier Kapazität vorsortiert, Angebotsentwürfe aus der eigenen Preisliste erzeugt und den Rest höflich absagt — der Betrieb prüft und gibt frei, das System bereitet vor.

**Abgrenzungssatz (Verkauf), nach Runde 8:**

> „Sie sind ausgelastet und sitzen trotzdem abends über Anfragen. Wir sortieren Ihre Anfragen nach dem, was sich für Sie rechnet, schreiben die Angebote aus Ihren eigenen Preisen und sagen den Rest höflich ab. Sie prüfen und geben frei."

**Verkaufte Nutzenordnung:** 1. Entlastung (Abendstunden zurück) → 2. bessere Auftragsauswahl (Marge) → 3. Geschwindigkeit (nachgelagert).

### 3.2 Vier Töpfe

#### CORE — kleinster verkaufbarer Umfang (V1)

Begründung je Zeile: ohne dieses Teil ist das Versprechen nicht einlösbar.

| Baustein | Warum unverzichtbar |
|---|---|
| Mandanten, Auth, 3 Rollen, RLS | Existenzgrundlage (#31, #39) |
| Branding je Mandant (Logo, Farben, Absender, Domain) | Das „Whitelabel" im Produktnamen |
| Posteingang: E-Mail + Web-Formular | Ohne Eingang kein Produkt (#1) |
| Einheitliches Anfrage-Objekt (strukturiertes JSON) | Entkoppelt Kanal von Logik (#14) |
| **Auto-Triage mit Ampel** | Hebel 1 (#2, #43) |
| Kapazitätsangabe je Woche als Triage-Eingang | Ohne Auslastung bewertet die Ampel an der Realität vorbei (#63) |
| **Absage-Funktion mit Textbausteinen** | Häufigster Vorgang eines ausgelasteten Betriebs (#62) |
| Stammkunden-Vorrang in der Sortierung | Sonst wird das System abgeschaltet (#66) |
| Kunden-/Kontaktverwaltung + Import (CSV/Outlook) | Vertriebs-Gate (#11) |
| Leistungskatalog & Preisliste | Voraussetzung für alles Weitere (#21, #41) |
| **Angebotsentwurf aus Preisliste** | Hebel 2 (#5) |
| Freigabe-Ansicht + PDF im Branding + Versand | Haftung, Entwurf-Prinzip (#6, #42) |
| Antwort aus dem System, Konversations-Verlauf | Sonst zweiter Posteingang (#44) |
| Nachfassen 3/7/14 Tage + Verloren-Grund | Größter Umsatzhebel, billig zu bauen (#8) |
| Kanal-Überwachung + Alarm | Stille Fehler sind tödlich (#36, #48) |
| Einrichtungsassistent | Onboarding entscheidet über Nutzung (#38) |
| Demo-Mandant | Vertrieb + QA (#37) |
| Datenexport (vollständig) | Verkaufsargument + Lock-in-Antwort (#29) |
| DSGVO-Paket: AVV, TOM, Löschkonzept, KI-Transparenzseite | Verkaufsvoraussetzung (#32, #33, #34, #50) |
| Verbrauchsmessung je Mandant | Margenschutz (#22, #49) |
| Kennzahl: Entwurf-ohne-Änderung-Quote | Die Produktkennzahl (#52) |

#### CORE V1.1 — direkt danach, noch vor „Plus"

- Terminverwaltung (einfach, ohne Routen) + Kalender-Sync
- Telefon-Mailbox → Transkript → Anfrage (#16)
- Rückfragen-Automat mit gewerkspezifischer Fragenliste (#3)
- Kunden-Status-Link (#10)
- Monteur-Ansicht mobil, ohne Preise (#9, #39)
- Abwesenheits-/Notdienstmodus (#40)
- Ton-des-Betriebs für Antwortentwürfe (#15)

#### PLUS

- Sortierung nach Deckungsbeitrag je Monteurstunde (#64)
- Auslastungsaufschlag statt Absage (#65)
- Warteliste mit automatischer Rückmeldung bei freier Kapazität (#67)
- Deckungsbeitrags-Warnung & Kalkulationsassistent (#18)
- Auswertung & Lernschleife gewonnen/verloren (#19)
- Auftrags- und Zeiterfassung
- DATEV-/Lexware-Export (#12)
- Vertrauensstufen-Regler für Automatisierungen (#13)

#### PREMIUM

- WhatsApp Business API als Kanal (eigener Onboarding-Prozess je Mandant)
- KI-Sprachagent für Anrufannahme (#17)
- Routen-/Fahrtwegs-Optimierung für Termine (#7)
- Foto-zu-Aufmaß per Vision-Modell (#4)
- Portal-Anbindungen (MyHammer, Check24)

#### MODUL: MITARBEITERAKQUISE (nach dem Referenzkunden)

Eigenes verkaufbares Modul, nutzt die Core-Pipeline mit zweitem Objekttyp (#69).

- Karriereseite im Betriebs-Branding + Kurzbewerbung ohne Lebenslauf (#70)
- Bewerbung als Objekt im gemeinsamen Posteingang
- Antwort- und Terminvorschlag in unter einer Stunde (#71) — hier gilt Geschwindigkeit
- Empfehlungsprämie mit personalisiertem Mitarbeiter-Link (#72)
- Eigene Löschfristen, strikte Trennung von Kundendaten

**Harte Designgrenze (#74):** Bewerber-Screening durch KI ist EU-AI-Act-Hochrisiko (Anhang III, Beschäftigung), dazu AGG-Haftung. Das Modul darf strukturieren, antworten und terminieren — **nicht bewerten, ranken, scoren oder automatisch absagen.** Entscheidung immer beim Betrieb.

#### BEWUSST NICHT — mit Begründung

| Nicht gebaut | Grund |
|---|---|
| Buchhaltung / Rechnungswesen | GoBD, Zertifizierung, Haftung — versenkt ein Solo-Projekt (#12) |
| Arztpraxis-Segment | Art. 9 DSGVO + § 203 StGB, eigenes Rechtsprojekt (#46) |
| Autonomer Angebotsversand im Core | Rechtlich bindend (#6, #42) |
| Preisschätzung ohne Betriebsdaten | Schnellster Weg, den ersten Kunden zu verlieren (#21) |
| Reseller-/Agentur-Hierarchie | Verdoppelt Mandantenmodell, kein Bedarf im Direktvertrieb |
| Zweites Segment vor dem Referenzkunden | (#45) |
| Freie Modul-Kombinationen | Kombinatorik in Test und Support (#26) |

### 3.3 Vorschlag Feature-Backlog (`features/INDEX.md`)

Reihenfolge ist Abhängigkeitsreihenfolge, nicht Wichtigkeit.

| ID | Feature | Topf | Hängt ab von |
|---|---|---|---|
| PROJ-1 | Mandanten, Auth, Rollen, RLS-Fundament | Core | — |
| PROJ-2 | Mandanten-Branding (Logo, Farben, Absender, Domain) | Core | PROJ-1 |
| PROJ-3 | Anfrage-Datenmodell + Web-Formular als erster Kanal | Core | PROJ-1 |
| PROJ-4 | E-Mail-Kanal (Empfang, Zuordnung, Verlauf) | Core | PROJ-3 |
| PROJ-5 | Auto-Triage: Klassifizierung, Ampel, Filteransichten | Core | PROJ-3 |
| PROJ-6 | Kundenverwaltung + Datenimport | Core | PROJ-1 |
| PROJ-7 | Leistungskatalog & Preisliste + geführte Ersterfassung | Core | PROJ-1 |
| PROJ-8 | Angebotsentwurf aus Preisliste (Komposition, Quellenanzeige) | Core | PROJ-5, PROJ-7 |
| PROJ-9 | Freigabe, Plausibilitätsprüfung, PDF, Versand | Core | PROJ-8 |
| PROJ-10 | Nachfass-Automatik + Verloren-Gründe | Core | PROJ-9 |
| PROJ-11 | Kanal-Überwachung & Alarmierung | Core | PROJ-4 |
| PROJ-12 | Einrichtungsassistent + Demo-Mandant | Core | PROJ-7 |
| PROJ-13 | Datenexport + DSGVO-Paket (AVV, TOM, Löschjobs) | Core | PROJ-1 |
| PROJ-14 | Verbrauchsmessung & Budgetgrenzen je Mandant | Core | PROJ-5 |
| PROJ-15 | Terminverwaltung + Kalender-Sync | V1.1 | PROJ-6 |
| PROJ-16 | Telefon-Mailbox → Transkript → Anfrage | V1.1 | PROJ-3 |
| PROJ-17 | Rückfragen-Automat (gewerkspezifische Fragenlisten) | V1.1 | PROJ-5 |
| PROJ-18 | Kunden-Status-Link | V1.1 | PROJ-15 |
| PROJ-19 | Monteur-Ansicht mobil | V1.1 | PROJ-15 |
| PROJ-20 | Branchenpaket als Konfigurations-Bundle (Import/Export) | Architektur | PROJ-7, PROJ-17 |
| PROJ-21 | Kapazitätsplanung als Triage-Eingang | Core | PROJ-5 |
| PROJ-22 | Absage-Funktion mit Textbausteinen + Wiedervorlage | Core | PROJ-5 |
| PROJ-23 | Deckungsbeitrags-Sortierung + Auslastungsaufschlag | Plus | PROJ-21, PROJ-8 |
| PROJ-24 | Modul Mitarbeiterakquise (Karriereseite, Kurzbewerbung, Terminierung) | Modul | PROJ-15, PROJ-20 |

**PROJ-21 und PROJ-22 gehören ins Core** und sind aus Runde 8 nachgezogen — ohne sie adressiert das Produkt einen Betrieb, den es nicht gibt (den unausgelasteten).

**PROJ-20 ist strategisch das wichtigste Ticket der Liste.** Es entscheidet, ob das Produkt jemals ein zweites Segment bedienen kann, ohne eine zweite Codebasis zu erzeugen (#27). Es sollte konzeptionell ab PROJ-7 mitgedacht und spätestens vor dem zweiten Segment umgesetzt werden.

### 3.4 Kennzahlen

**Produktqualität — Freigabe-ohne-Änderung-Quote** (#52)
Anteil der Angebots- und Antwortentwürfe, die der Betrieb unverändert freigibt. Unter ~50 % ist das Produkt langsamer als Handarbeit und stirbt leise.

**Verkaufter Nutzen — Entlastungskennzahlen** (#68)
- Gesparte Büro-Stunden je Woche
- Anteil der Anfragen, die ohne Zutun des Chefs erledigt sind (Absage, Rückfrage, Warteliste)
- Durchschnittlicher Deckungsbeitrag je angenommenem Auftrag

Antwortzeit ist ausdrücklich **keine** Leitkennzahl mehr — außer im Recruiting-Modul (#71).

---

## 4. Offene Entscheidungen vor `/abc-requirements`

1. ~~Buy or Build~~ — **entschieden: BUILD** (Weg D, #56). Kern selbst, Standardteile zugekauft, alles Fremde hinter eigener Schnittstelle. Offen bleibt nur, ob eine manuelle Validierungsphase mit 2–3 Betrieben vorgeschaltet wird (Empfehlung: ja, aber ohne gekaufte Plattform — Posteingang und Triage von Hand).
2. **Frontend:** Next.js oder Flutter. Empfehlung Next.js — Web-only, SEO für Marketing-Seite, Monteur-Ansicht als PWA reicht.
3. **Modell-Anbieter und Region** — bestimmt die Antwort auf die Datenschutzfrage im Verkaufsgespräch (#33, #50).
4. **E-Mail-Empfang:** IMAP-Anbindung des bestehenden Postfachs oder eigene Adresse mit Weiterleitung? Beeinflusst #44 erheblich.
5. **Telefonie-Anbieter** für Mailbox-Transkription.
6. **Preispunkt und Staffelgrenzen** (#23, #25).
7. **Rechtsform, AVV-Vorlage, Auftragsverarbeitungs-Kette** — vor dem ersten zahlenden Kunden geklärt.
8. **Produktname und Marke.**
9. **Abgrenzungssatz festlegen** — Kandidat C aus Runde 7 bestätigen oder schärfen. Voraussetzung: Wettbewerbsanalyse mit tagesaktuellen Daten gegenprüfen (#55, #58).
10. ~~Kernannahme Geschwindigkeit vs. Entlastung~~ — **entschieden: Entlastung zuerst, Geschwindigkeit nachgelagert** (Runde 8). Betriebe sind typischerweise gut ausgelastet.
11. **Kapazitätsmodell:** Wie grob darf die Kapazitätsangabe sein, damit sie gepflegt wird? (Wochenstunden je Gewerk? Nur „nächster freier Termin"?) Zu fein = wird nicht gepflegt, zu grob = Triage nutzlos (#63).
12. **Recruiting-Modul:** vor oder nach dem zweiten Segment? Zahlungsbereitschaft ist höher (#73), Rechtsrahmen aber eigenständig (#74).

---

## 5. Empfohlene Reihenfolge

1. Wettbewerbsanalyse + Abgrenzungssatz (2 Nachmittage)
2. Offene Entscheidungen 2–5 festlegen (Technikwahl)
3. Validierungsphase mit 2–3 Betrieben, manuell (6 Wochen) — parallel dazu:
4. `/abc-requirements` für PROJ-1 bis PROJ-5 (Fundament + Hebel 1)
5. `/abc-architecture` für den Schnitt Anfrage-Objekt ↔ Triage ↔ Branchenpaket (PROJ-20 mitdenken)
6. Bau PROJ-1 … PROJ-14 = kleinster verkaufbarer Umfang
7. Referenzbetrieb gewinnen (#28), dann V1.1

---

_Erzeugt mit `/abc-brainstorm`. Nächster Schritt: `/abc-requirements`._
