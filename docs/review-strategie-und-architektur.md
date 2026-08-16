# Review: Produktstrategie und ImmoCRM-Wiederverwendung

**Datum:** 2026-08-15  
**Status:** Empfehlung zur Revalidierung, keine Baufreigabe  
**Geprüfte Grundlagen:** `docs/Brainstorm.md`, `docs/architektur-reuse-immocrm.md`, aktueller ImmoCRM-Quellbestand und offizielle Wettbewerberseiten

---

## 1. Entscheidung

Die Problemrichtung ist plausibel, das geplante Business OS ist aber zu groß und seine bisherige Abgrenzung inzwischen teilweise überholt.

**Empfehlung:** Noch kein Multi-Tenant-SaaS und keine Feature-Specs PROJ-1 bis PROJ-14 bauen. Zuerst einen bezahlten, weitgehend manuellen Pilot für einen engen **Anfrage-Entscheidungsassistenten** durchführen. Erst wenn dieser Pilot messbaren Nutzen und Zahlungsbereitschaft belegt, beginnt die Produktentwicklung.

Das spätere technische Grundmodell bleibt sinnvoll:

- neues Repository statt Fork von ImmoCRM;
- Next.js für Büro- und öffentliche Webflächen;
- FastAPI und Postgres;
- RLS als Mandantenschutz, sobald tatsächlich mehrere zahlende Mandanten existieren;
- nur kleine, fachlich saubere Infrastrukturteile aus ImmoCRM übernehmen.

---

## 2. Warum das bisherige Vorgehen nicht freigegeben werden sollte

### 2.1 Die angenommene Marktlücke ist kleiner geworden

Die These „moderne Handwerkersoftware beginnt erst beim Auftrag“ trifft 2026 nicht mehr allgemein zu:

| Anbieter | Anfrage und KI | Weiterer Schwerpunkt | Einstiegspreis laut Anbieter, netto |
|---|---|---|---:|
| Plancraft | PORTA nimmt Anrufe an und stellt bis zu zehn individuelle Fragen; strukturierte Anfragen | Kalkulation, Angebote, Rechnungen, Projekte | ab 47,92 € bei zweijährlicher bzw. 59,90 € bei jährlicher Zahlung; PORTA mit kleinem Gratiskontingent bzw. kostenpflichtig |
| HERO | HERO Voice erkennt Bestandskunden, Notfälle und Auftragsarten, qualifiziert und erstellt Aufgaben; HERO Command für Angebote aus Betriebsdaten ist angekündigt | sehr breites Handwerker-Betriebssystem | HERO Select ab 59 € im Jahresangebot; Voice standalone ab 69 € jährlich |
| Meisterwerk | KI-Telefonassistent qualifiziert Anfragen und legt Termine an | Einsatz- und Routenplanung, Aufträge, mobile Nutzung | 49 € inklusive drei Nutzer, Zusatzmodule separat |
| ToolTime | keine gleichwertige öffentliche Auto-Triage erkennbar | Angebote, Rechnungen, Aufmaß und Ausführung | 69 € Solo |
| Craftboxx | keine gleichwertige Anfrage- oder Angebots-KI erkennbar | Einsatzplanung, Zeit und Dokumentation | 15,99 € je Nutzer im Jahresabo |

Folge: **Telefonannahme, Anfragequalifizierung und schnelle Angebotserstellung sind allein kein belastbares Alleinstellungsmerkmal mehr.**

### 2.2 Der bisherige Core ist ein Vollprodukt, kein MVP

Der geplante Core umfasst unter anderem Mandantenverwaltung, Rollen, Branding, Posteingang, CRM, Import, Preiskatalog, Angebots-PDF, Versand, Nachfassen, Monitoring, Export, Onboarding und Compliance.

Damit müsste das Produkt vom ersten Tag an gegen breite, ausgereifte Systeme bestehen. Gleichzeitig verlangt es Migration, Einrichtung und Prozessänderung. Für ein noch unvalidiertes Problem ist das unverhältnismäßig.

### 2.3 Die schwierigsten Annahmen sind noch unbewiesen

Vor dem Bau fehlen belastbare Antworten auf diese Fragen:

1. Erhalten die Zielbetriebe genug ungeordnete Anfragen, damit Triage regelmäßig Nutzen stiftet?
2. Wollen Betriebe tatsächlich systematisch absagen oder lassen sie Anfragen bewusst unbeantwortet?
3. Pflegen sie Kapazität und wirtschaftliche Regeln zuverlässig?
4. Sind aus einer frühen Anfrage Deckungsbeitrag und Zeitbedarf ausreichend genau ableitbar?
5. Zahlen sie zusätzlich zu bestehender Handwerkersoftware mindestens einen wirtschaftlich tragfähigen Preis?

---

## 3. Verbleibende Produktchance

Die stärkste mögliche Position ist kein weiteres vollständiges Handwerker-ERP, sondern eine Entscheidungsschicht vor vorhandenen Systemen:

> **Wir helfen ausgelasteten Handwerksbetrieben zu entscheiden, welche Anfragen sie annehmen, zurückstellen oder höflich ablehnen – anhand ihrer Kapazität, Stammkundenregeln und wirtschaftlichen Vorgaben.**

### Möglicher Mehrwert gegenüber den Wettbewerbern

1. **Überlastung statt Lead-Verlust optimieren**  
   Plancraft, HERO und Meisterwerk konzentrieren sich stark auf Erreichbarkeit, Erfassung und Weiterleitung. Das neue Produkt kann den Gegenfall besetzen: Ein Betrieb hat bereits genug Arbeit und will bewusst auswählen.

2. **Annehmen, Rückfragen, Warteliste und Absagen als zusammenhängender Ablauf**  
   Nicht nur „Anfrage erfasst“, sondern eine vorbereitete Entscheidung mit passender Kundenreaktion.

3. **Kapazitäts- und Stammkundenregeln über alle Eingangskanäle**  
   Die gleiche Entscheidung unabhängig davon, ob die Anfrage per E-Mail, Formular oder Telefon kam.

4. **Nachvollziehbarkeit statt Blackbox**  
   Jede Empfehlung nennt die verwendeten Betriebsregeln und bleibt vor Versand freigabepflichtig.

5. **Ergänzung statt sofortiger Systemwechsel**  
   Ergebnisse werden zunächst an die vorhandene Handwerkersoftware oder den bestehenden Büroprozess übergeben. Dadurch entfällt die größte Einführungshürde.

### Was kein Burggraben ist

- Sprachmodell oder Textgenerierung;
- KI-Telefonassistent;
- Angebotserstellung allein;
- schöner Posteingang;
- Kalender und Terminplanung;
- allgemeines Whitelabel-Branding.

Der mögliche Schutz entsteht erst aus verlässlichen Kanalabläufen, betriebsspezifischen Entscheidungsregeln, Korrekturdaten und erfolgreichem Onboarding.

---

## 4. Empfohlener Pilot vor jedem Softwarebau

### Umfang

Der Pilot braucht keine eigene Plattform. Pro Betrieb genügen:

- Weiterleitung oder Export eingehender Anfragen;
- eine einfache Liste der Betriebsregeln;
- manuell unterstützte Einordnung in **annehmen**, **Rückfrage**, **später/Warteliste** oder **absagen**;
- vorbereitete Antwort, die der Betrieb freigibt;
- wöchentliche Auswertung.

Keine eigene Authentifizierung, Mandantenplattform, App, eigene Domain, Rechnungsfunktion, Telefon-KI oder tiefe Fremdsystemintegration.

### Stichprobe

- drei bis fünf Betriebe aus höchstens zwei ähnlichen Gewerken;
- je Betrieb mindestens 30 bis 50 reale Anfragen;
- Laufzeit vier bis sechs Wochen;
- von Beginn an bezahlt, damit nicht nur Interesse, sondern Zahlungsbereitschaft geprüft wird.

### Messgrößen

- eingesparte Bürozeit pro Woche;
- Anteil der Anfragen, bei denen der Vorschlag die Entscheidung beschleunigt;
- Anteil der Antwortentwürfe, die nur gering geändert werden;
- Zahl sauber beantworteter statt liegen gelassener Anfragen;
- Nutzung der Warteliste;
- Bereitschaft, nach dem Pilot weiter mindestens etwa 149 € monatlich plus Einrichtung zu zahlen.

### Baufreigabe

Erst bauen, wenn mindestens drei Betriebe:

- den Pilot bezahlen;
- nachweislich mehrere Stunden pro Woche sparen;
- den Ablauf über mehrere Wochen wiederholt nutzen;
- nach dem Pilot kostenpflichtig fortsetzen wollen.

Werden diese Kriterien nicht erreicht, wird kein Business OS gebaut. Dann war die Dienstleistung die günstigere Validierung.

---

## 5. Bewertung der ImmoCRM-Wiederverwendung

### Richtig

- kein Fork des bestehenden ImmoCRM;
- Immobilien-Fachlichkeit nicht in ein Mehrsegmentprodukt umbauen;
- Next.js statt Flutter Web für öffentliche Seiten und Büroanwendung;
- vorhandene Infrastruktur nicht grundsätzlich neu erfinden;
- neues Mandantenmodell nicht vom ImmoCRM übernehmen.

### Zu optimistisch

#### Route-Code ist nicht automatisch RLS-portabel

`TenantDatabaseRouter.connect()` hat laut CodeGraph 265 Aufrufer. Der Wechsel von separaten Datenbanken zu einer gemeinsamen RLS-Datenbank betrifft daher nicht nur das Schema. Betroffen sind auch:

- sichere Mandantensetzung je Transaktion;
- Hintergrundjobs und Sweeper;
- öffentliche Routen ohne angemeldeten Nutzer;
- Verbindungen nach Commit oder Rollback;
- Tests, die fehlenden oder falschen Mandantenkontext sicher abweisen.

Die vorhandene Aufrufform kann als Orientierung dienen, ist aber kein Beweis für Portabilität.

#### `email_service.py` ist kein fast unverändert übernehmbares Modul

Die Datei umfasst rund 4.500 Zeilen und mischt:

- IMAP und SMTP;
- MIME-Parsing und Anhänge;
- Konversationen;
- Kundenanlage;
- Immobilien-Interessententypen und Aufbewahrung;
- Objektzuordnung;
- IS24-Sonderlogik;
- Abwesenheitsantworten und Spamprüfung.

Übernommen werden sollten nur klar abtrennbare technische Teile wie Providerbesonderheiten, IMAP/SMTP-Verbindung, MIME-Parsing und Credential-Verschlüsselung. Die Verarbeitung eingehender Nachrichten wird für das neue Anfrageobjekt neu entworfen.

#### Auth ist Vorlage, keine 1:1-Kopie

JWT, Passwort-Hashing, TOTP und Backup-Codes sind wiederverwendbar. Die Auth-Routen selbst hängen jedoch an Master-Datenbank, Tenant-Wechsel, Mitgliedschaften, Rollen und Berechtigungstabellen. Diese Teile müssen zum neuen RLS-Modell passen und gelten deshalb als Vorlage.

### Reuse-Klassifizierung

| Einstufung | Bausteine |
|---|---|
| Direkt übernehmen, nach kleinem Test | Konfigurationshelfer, MinIO-Grundlage, Vault-/Credential-Helfer, einzelne reine Parser |
| Extrahieren und vereinfachen | IMAP/SMTP, MIME, Providerbesonderheiten, PDF-Grundlage, Advisory-Lock-/Retry-Muster |
| Als Vorlage verwenden | Auth-Abläufe, Rollen, Tenant-Settings, Erinnerungen, Terminmuster, Import-Mapping |
| Neu bauen | Anfrageobjekt, Triage, Entscheidungsregeln, RLS-Schema, Angebotskomposition, Integrationsübergabe |
| Nicht übernehmen | Immobilien-, IS24-, OpenImmo-, Exposé- und Objektlogik sowie der Monolith `main.py` |

Gemeinsame Bibliotheken zwischen ImmoCRM und Business OS sind vorerst nicht nötig. Ebenso sollte aber keine große Datei kopiert werden, deren Fehler anschließend bewusst doppelt gepflegt werden müssten.

---

## 6. Architektur nach erfolgreicher Validierung

Erst nach Baufreigabe wird die kleinste bewiesene Produktkette umgesetzt:

```text
Anfrageeingang
└── strukturierte Anfrage
    └── regelbasierter Entscheidungsvorschlag
        ├── annehmen
        ├── Rückfrage
        ├── Warteliste
        └── absagen
            └── menschliche Freigabe
                └── Antwort und Übergabe an Bestandssystem
```

### Erste Produktgrenze

Enthalten:

- E-Mail-Weiterleitung und Webformular;
- ein Anfrageobjekt;
- wenige explizite Betriebsregeln;
- Entscheidungsansicht;
- freigabepflichtige Antworten;
- einfache Übergabe per E-Mail oder Export;
- Nutzenmessung.

Nicht enthalten:

- eigene Angebots- und Rechnungswelt;
- Telefon-Sprachagent;
- Monteur-App;
- vollständiges CRM;
- individuelle Mandantendomains;
- Recruiting;
- Routenoptimierung;
- Deckungsbeitragsautomatik ohne belastbare Eingangsdaten.

Die Angebotskomposition aus eigener Preisliste wird erst ergänzt, wenn der Pilot zeigt, dass sie gegenüber vorhandenen Angeboten von Plancraft, HERO oder ToolTime einen zusätzlichen, bezahlten Nutzen liefert.

---

## 7. Rechtliche Korrekturen für spätere Anforderungen

- Die GoBD verlangt keine verbindliche Softwarezertifizierung. Zertifikate oder Testate können Auswahlhilfen sein, binden die Finanzverwaltung aber nicht.
- Für Angebote gilt nicht pauschal eine zehnjährige Aufbewahrung. Je nach Einordnung gelten unterschiedliche Fristen; Handels- und Geschäftsbriefe liegen typischerweise bei sechs Jahren, Buchungsbelege bei acht Jahren.
- Recruiting-KI ist nicht in jedem vorbereitenden Einsatz automatisch ein Hochrisikosystem. Bewertung, Ranking, Profiling oder eine materielle Beeinflussung von Personalentscheidungen bleiben dennoch bewusst außerhalb des Produkts und müssen vor Umsetzung rechtlich geprüft werden.

---

## 8. Quellen

### Produkt und Preise

- [Plancraft Preise und PORTA](https://plancraft.com/de-de/preise)
- [Plancraft: individuelle Fragen für Projektanfragen](https://plancraft.com/de-de/produktupdates/updates-im-april)
- [HERO Voice](https://hero-software.de/ai/voice)
- [HERO AI und angekündigtes HERO Command](https://hero-software.de/ai)
- [HERO Preise](https://hero-software.de/preise)
- [ToolTime Preise](https://www.tooltime.app/preise)
- [Meisterwerk Produkt und Preise](https://www.meisterwerk.app/)
- [Craftboxx Preise](https://www.craftboxx.de/preise)

### Recht

- [BMF: GoBD, Zertifizierung und Software-Testate](https://grsth.bundesfinanzministerium.de/ao/2025/Anhaenge/BMF-Schreiben-und-gleichlautende-Laendererlasse/Anhang-33/inhalt.html)
- [§ 257 HGB: Aufbewahrungsfristen](https://www.gesetze-im-internet.de/hgb/__257.html)
- [EU AI Act, Verordnung (EU) 2024/1689](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32024R1689)

---

## 9. Nächster Schritt

Kein `/abc-requirements` und kein Repository-Skelett. Als Nächstes wird ein einseitiges Pilotangebot mit Zielgruppe, Ablauf, Preis, Messgrößen und Abbruchkriterien erstellt und an drei bis fünf konkrete Betriebe verkauft.
