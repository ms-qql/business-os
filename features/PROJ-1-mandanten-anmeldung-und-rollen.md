# PROJ-1: Mandanten, Anmeldung und Rollen

## Status: Architected
**Created:** 2026-08-16

## Dependencies
- None

## Reuse aus ImmoCRM
- Passwort-Hashing, JWT und Audit-Logging als Vorlage; TOTP folgt in V2.
- Neu: gemeinsames Postgres-Schema mit RLS statt separater Datenbank je Mandant.

## User Stories
- Als Inhaber möchte ich mich sicher anmelden, um nur meinen Betrieb zu sehen.
- Als Inhaber möchte ich Büro- und Monteurkonten anlegen, um Arbeit gezielt zu verteilen.
- Als Monteur möchte ich keine Preise oder fremden Termine sehen.
- Als Betreiber möchte ich einen neuen Betrieb mit einem Inhaber anlegen.

## Acceptance Criteria
- [ ] Jede geschäftliche Tabelle ist einem Mandanten zugeordnet; ein Request kann niemals Daten eines anderen Mandanten lesen oder ändern.
- [ ] Anmeldung, Abmeldung und Passwortzurücksetzen sind möglich; Fehlermeldungen verraten nicht, ob eine E-Mail-Adresse existiert.
- [ ] Nach fünf fehlgeschlagenen Anmeldeversuchen innerhalb von 15 Minuten werden weitere Versuche für dieselbe Kombination aus Konto und Herkunft gedrosselt; die Fehlermeldung bleibt einheitlich.
- [ ] Die festen Rollen sind Inhaber, Büro und Monteur; Rechte sind nicht frei konfigurierbar.
- [ ] Inhaber verwalten Nutzer ihres Betriebs; sie können den eigenen letzten aktiven Inhaber nicht deaktivieren.
- [ ] Neue Betriebsnutzer setzen ihr Passwort ausschließlich über einen kurzlebigen, einmal verwendbaren Einladungslink.
- [ ] Monteure sehen ausschließlich ihnen zugewiesene Termine und zugehörige Vorgänge; Preis- und Rechnungsdaten sind ausgeblendet.
- [ ] Anmeldung, Rollenänderung und fehlgeschlagene Anmeldung werden protokolliert.

## Edge Cases
- Deaktivierte Nutzer verlieren bestehende Sitzungen.
- Ein Nutzer mit Mitgliedschaft in mehreren Betrieben ist in V1 nicht erlaubt.
- Ein abgelaufener oder manipuliert wirkender Zugriffstoken liefert „Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.“
- Ein Aufruf ohne Mandantenkontext wird abgewiesen, nicht mit einem Standardmandanten beantwortet.

## Technical Requirements
- Security: Mandantenkontext ausschließlich aus der authentifizierten Sitzung; RLS erzwingt die Trennung zusätzlich.
- Browser Support: aktuelle Chrome-, Firefox- und Safari-Versionen.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-16 · **Stack:** Next.js 16 + FastAPI + PostgreSQL (RLS) · **Branch:** dev

### Ziel und Umfang

PROJ-1 schafft die Sicherheits- und Zugriffsgrundlage für alle folgenden
Funktionen. Sie umfasst Mandanten, Anmeldung, feste Rollen, Nutzerverwaltung,
Sitzungen, Einladungen, Passwortzurücksetzung und Audit-Protokolle. Dateien,
Echtzeit, TOTP und frei konfigurierbare Rechte gehören nicht zu diesem Feature.

### Komponentenstruktur

```text
Anmeldebereich
├── Anmeldeformular
├── Passwort-vergessen-Formular
├── Passwort-zurücksetzen-Formular
└── Sitzungsablauf-Hinweis

Angemeldete Betriebszentrale
├── AppShell
│   ├── Rollenabhängige Navigation
│   └── Konto-Menü mit Abmeldung
├── Startseite
└── Nutzerverwaltung (nur Inhaber)
    ├── Nutzerliste
    ├── Nutzer einladen/bearbeiten
    └── Deaktivieren-Bestätigung

Betreiberbereich
└── Betrieb mit erstem Inhaber anlegen
```

Der Betreiberbereich ist keine Mandantenansicht und bleibt nur für den
Plattformbetreiber erreichbar. Er verwendet einen getrennten Zugang und ist
nicht eine vierte Betriebsrolle. Monteure erhalten keine Preis- oder
Rechnungsnavigation; spätere Termin- und Vorgangsansichten begrenzen die Daten
zusätzlich auf ihre Zuweisungen.

### Datenmodell

- **Mandant:** ein SHK-Betrieb mit eindeutiger Kennung und aktivem Status.
- **Nutzer:** gehört in V1 genau einem Mandanten an; speichert Name,
  E-Mail-Adresse, Passwortnachweis, Rolle und Aktiv-Status.
- **Rolle:** genau eine der festen Rollen `Inhaber`, `Büro` oder `Monteur`.
  Es gibt keine frei editierbaren Rechte oder Mehrfachrollen.
- **Sitzung:** der serverseitige, maßgebliche Nachweis eines gültigen Logins.
  Ein kurzlebiges signiertes Zugriffstoken verweist darauf; jeder Request prüft
  zusätzlich, ob die Sitzung aktiv ist. So verlieren deaktivierte Nutzer sofort
  den Zugriff, auch vor Ablauf ihres Tokens.
- **Einladung:** kurzlebiger, einmal verwendbarer Nachweis für einen neuen
  Betriebsnutzer. Er setzt damit selbst sein Passwort; ein Inhaber kennt oder
  übermittelt kein Startpasswort.
- **Passwortzurücksetzung:** kurzlebiger, einmal verwendbarer Nachweis; die
  Antwort beim Anfordern bleibt für bekannte und unbekannte E-Mail-Adressen
  gleich.
- **Plattformbetreiber:** eigene Betreiberidentität außerhalb der
  Mandantennutzer und Rollen. Ihr Zugriff kann keinen Mandantenkontext
  übernehmen oder in eine Betriebsrolle umgewandelt werden.
- **Audit-Ereignis:** unveränderbarer Eintrag für erfolgreiche und fehlgeschlagene
  Anmeldungen sowie Rollenänderungen, mit Zeitpunkt, Auslöser und betroffenem
  Mandanten.

Alle heutigen und zukünftigen Geschäftsdaten tragen eine Mandantenkennung.
PostgreSQL-RLS begrenzt jede Datenabfrage auf den Mandanten der authentifizierten
Sitzung. Ohne gesetzten Mandantenkontext wird der Zugriff abgewiesen.
Der API-Dienst setzt diesen Kontext pro Datenbanktransaktion über
`SET LOCAL app.current_mandant_id`; der Wert kommt ausschließlich aus der
geprüften Sitzung.

### API-Form

- `POST /auth/login` → Sitzung für gültige Zugangsdaten eröffnen.
- `POST /auth/logout` → aktuelle Sitzung beenden.
- `POST /auth/invitations/accept` → Einladung einlösen und eigenes Passwort
  setzen.
- `POST /auth/password-reset` → Passwortzurücksetzung anfordern, ohne die
  Existenz der E-Mail-Adresse preiszugeben.
- `POST /auth/password-reset/confirm` → Passwort mit gültigem Einmalnachweis
  ändern und alte Sitzungen beenden.
- `GET /auth/me` → angemeldeten Nutzer, Rolle und Mandantenkontext liefern.
- `GET /users` → Nutzer des eigenen Betriebs auflisten (nur Inhaber).
- `POST /users` → Nutzer im eigenen Betrieb einladen (nur Inhaber); versendet
  den Einladungslink über den transaktionalen E-Mail-Versand.
- `PATCH /users/{id}` → Rolle oder Aktiv-Status eines Betriebsnutzers ändern
  (nur Inhaber); der letzte aktive Inhaber bleibt geschützt.
- `POST /operator/auth/login` und `POST /operator/auth/logout` → getrennte
  Betreiber-Sitzung öffnen bzw. beenden.
- `POST /admin/mandanten` → Betrieb samt erstem Inhaber anlegen, ausschließlich
  mit einer Betreiber-Sitzung.

Alle Betriebs-Endpunkte lesen den Mandanten ausschließlich aus der Sitzung;
eine Mandantenkennung im Browser-Aufruf wird nicht vertraut. Die späteren
Termin- und Vorgangs-Endpunkte übernehmen denselben Kontext und prüfen für
Monteure zusätzlich die Zuweisung.

### Plattformbetreiber-Zugang

Betreiberidentitäten, Betreiber-Sitzungen und ihre Login-Endpunkte sind von
Mandantennutzern getrennt. Betreiber-Tokens tragen eine eigene Zielgruppe und
werden nur an `/operator`- und `/admin`-Endpunkten akzeptiert; sie sind für
Betriebs-Endpunkte ungültig. Umgekehrt können Betriebs-Tokens niemals einen
Betreiber-Endpunkt aufrufen. So entsteht keine vierte Rolle und kein Weg, eine
normale Mandantensitzung zu erhöhen.

### Technische Entscheidungen

- **Next.js 16 statt Flutter Web:** folgt der Projektentscheidung und bedient
  angemeldete sowie spätere öffentliche Webflächen in einem System. Die
  Monteuransicht bleibt zunächst eine mobile Web/PWA-Ansicht.
- **FastAPI als API-Grenze:** trennt Browseroberfläche und Geschäftsdaten klar;
  die nachfolgenden Features nutzen dieselbe Authentifizierung und denselben
  Mandantenkontext.
- **Gemeinsames PostgreSQL-Schema mit RLS:** die Datenbank verhindert
  Mandantenlecks auch dann, wenn eine Anwendungsroute einen Filter vergisst.
  Der Mandantenwert wird je Transaktion gesetzt und nach ihrem Ende verworfen.
- **Kurzlebige Zugriffstoken mit serverseitiger Sitzungsprüfung:** JWTs sind
  nicht rein zustandslos; die aktive Sitzung bleibt bei jedem Request die
  Autorität. Dadurch wirken Abmeldung und Deaktivierung sofort.
- **Argon2-Passwortnachweise und Einmalnachweise:** Passwörter und
  Einladungs- oder Zurücksetzungslinks werden nicht im Klartext gespeichert.
  Wiederverwendung orientiert sich an den Auth- und Audit-Abläufen aus ImmoCRM,
  nicht an dessen Datenbank-pro-Mandant-Modell.
- **Drosselung statt Kontosperre:** fünf Fehlversuche in 15 Minuten werden pro
  Konto-Herkunfts-Kombination gedrosselt. Das bremst Angriffe, ohne dass ein
  Angreifer ein fremdes Konto dauerhaft sperren kann.
- **Einladungsablauf statt Startpasswort:** neue Nutzer setzen ihr Passwort
  selbst über einen Einmal-Link. Der ohnehin nötige transaktionale
  E-Mail-Versand wird dafür wiederverwendet.
- **TOTP erst in V2:** hält das P0-Fundament klein; Passwortschutz,
  Drosselung, Sitzungswiderruf, RLS und Audit sind für V1 verbindlich.
- **Kein MinIO in PROJ-1:** Authentifizierung und Rollen brauchen keine Dateien.
  Objekt- und Dokumentenspeicher beginnt erst mit PROJ-2/PROJ-3.
- **Keine Echtzeit-Verbindung:** Rollen- und Sitzungsänderungen werden beim
  nächsten API-Aufruf durchgesetzt; das hält die Grundlage klein und sicher.

### Abhängigkeiten

- **Next.js 16, Tailwind und shadcn/ui:** Weboberfläche und zugängliche Formulare.
- **FastAPI:** Authentifizierungs- und Nutzer-API.
- **PostgreSQL mit RLS:** Mandantentrennung auf Datenbankebene.
- **Argon2-Passwortbibliothek und JWT-Bibliothek:** sichere Passwortnachweise
  und signierte Zugriffstoken.
- **Drosselungsdienst:** begrenzt fehlgeschlagene Anmeldungen nach Konto und
  Herkunft.
- **Transaktionaler E-Mail-Versand:** Einladungen und Passwortzurücksetzung;
  die konkrete Zustellungsanbindung wird als schlanke Konfiguration festgelegt
  und nicht mit PROJ-4s vollständiger Inbox gekoppelt.

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
