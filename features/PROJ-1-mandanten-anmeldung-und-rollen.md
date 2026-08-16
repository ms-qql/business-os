# PROJ-1: Mandanten, Anmeldung und Rollen

## Status: In Review
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

## Implementierungsstand

### Paket 1.1 — Backend (abgenommen 2026-08-16)
Alle 11 Endpunkte aus § „API-Form" im Repo vorhanden und verdrahtet
(`backend/app/main.py` bindet auth-, users-, operator- und admin-Router ein):

| Vertrag | Datei |
|---|---|
| `POST /auth/login\|logout\|invitations/accept\|password-reset\|password-reset/confirm`, `GET /auth/me` | `backend/app/features/auth/routes.py` |
| `GET\|POST /users`, `PATCH /users/{id}` | `backend/app/features/users/routes.py` |
| `POST /operator/auth/login\|logout`, `POST /admin/mandanten` | `backend/app/features/operator/routes.py` |

- Schema + RLS: `backend/sql/001_init.sql`; `SET LOCAL app.current_mandant_id`
  über `PostgresEngine` in `backend/app/db.py`.
- Argon2 + JWT mit getrennter Business-/Operator-Audience: `backend/app/security.py`.
- Tests: 18/18 grün (`backend/tests/`, verifiziert im Koordinator-Lauf).
- **Offene Einschränkung:** die Testsuite läuft gegen `SqliteEngine`; die
  RLS-Policies aus `001_init.sql` werden dabei nicht ausgeführt. Die
  Mandantentrennung ist damit nur auf App-Ebene belegt, nicht auf DB-Ebene.
  QA muss die Isolationstests zusätzlich gegen Postgres fahren.

### Paket 1.2 — Frontend (zurückgewiesen 2026-08-16)
Geliefert: Anmeldebereich, AppShell, Startseite, Nutzerverwaltung,
Betrieb-anlegen-Formular, API-Clients (`nextjs_app/`). Drei Verstöße gegen
§ „Plattformbetreiber-Zugang" bzw. gegen Akzeptanzkriterien — Nacharbeit nötig:

1. **Betreiberbereich liegt im Mandanten-Shell.**
   `app/(app)/betrieb-anlegen/page.tsx` ruft `/admin/mandanten` über
   `apiFetch` auf, das laut `lib/api/client.ts:17` den Business-Token aus
   `lib/session.ts` sendet. Der Vertrag verlangt: Betreiber-Token tragen eine
   eigene Zielgruppe, Betriebs-Token sind an `/admin` ungültig. Der Aufruf
   scheitert zwangsläufig. Der Betreiberbereich braucht eine eigene
   Route-Group ausserhalb `(app)` und einen getrennten Token-Speicher.
2. **Kein Betreiber-Login.** `POST /operator/auth/login` und
   `/operator/auth/logout` werden nirgends aufgerufen; eine Betreiber-Sitzung
   ist gar nicht herstellbar. `lib/api/operator.ts` deckt nur
   `/admin/mandanten` ab.
3. **Einladungsannahme fehlt.** `POST /auth/invitations/accept` wird nirgends
   aufgerufen, es gibt keine Seite zum Einlösen des Einladungslinks. Damit ist
   das Akzeptanzkriterium „Neue Betriebsnutzer setzen ihr Passwort
   ausschliesslich über einen kurzlebigen, einmal verwendbaren
   Einladungslink" nicht erfüllt — eingeladene Nutzer kommen nicht ins System.

Nachrangig: `router.push("/startseite")` nach Betriebsanlage führt den
Betreiber in eine Mandantenansicht, die er nicht hat.

### Offene Pakete
- 1.2 Nacharbeit (siehe oben).
- 1.3–1.5 noch nicht gestartet.

## Frontend-Implementierung (abc-frontend)
**Erstellt:** 2026-08-16 · **Stack:** Next.js 16 (App Router) + Tailwind v4 + shadcn-Stil-Komponenten.

Das Frontend liegt in `nextjs_app/`. Es deckt den Anmeldebereich und die
angemeldete Betriebszentrale aus dem Tech-Design ab:

- `app/(auth)/login` — Anmeldeformular (E-Mail + Passwort, Fehler verraten
  keine E-Mail-Existenz).
- `app/(auth)/passwort-vergessen` — Reset anfordern (einheitliche Antwort).
- `app/(auth)/passwort-zuruecksetzen` — Passwort mit Einmal-Token setzen.
- `app/sitzung-abgelaufen` — Hinweis bei abgelaufenem/ungültigem Token.
- `app/(app)/layout` — AppShell mit rollenabhängiger Navigation (Inhaber sieht
  Nutzerverwaltung + Betrieb-anlegen; Büro/Monteur nur Startseite) und
  Konto-Menü mit Abmeldung.
- `app/(app)/startseite` — Begrüßung + rollenbasierte Karten (Monteur sieht
  „nur eigene Termine").
- `app/(app)/nutzerverwaltung` — Nutzerliste, Einladen, Rolle ändern,
  Aktiv/Inaktiv; Schutz des letzten aktiven Inhabers (Client + Server).
- `app/(app)/betrieb-anlegen` — Betrieb samt erstem Inhaber anlegen
  (Operator-Endpunkt `/admin/mandanten`).

API-Anbindung über `lib/api/*` (fetch-Wrapper mit Bearer-Token aus
`lib/session`), Theme-Tokens in `lib/theme/tokens.ts` (AppColors-Äquivalent).
Texte durchgängig Deutsch. Backend-Endpunkte folgen dem Tech-Design
(PROJ-1.1); das Frontend ist gegen deren Vertrag geschrieben.

## QA Test Results
**Geprüft:** 2026-08-16 · Umfang: Backend (`backend/`) vollständig, Frontend (`nextjs_app/`) Codeprüfung gegen § „Plattformbetreiber-Zugang" der 1.2-Nacharbeit.

### Automatisierte Tests
- `conda run -n Dashboard --no-capture-output python -m pytest backend/tests -q` → **18/18 grün**.
- Deckt ab: Login/Logout, Drosselung, Tenant-Isolation (`test_isolation.py`), Operator-Token-Ablehnung auf Business-Endpunkten, Rollen-/Statusänderung, Audit-Log.

### Akzeptanzkriterien
| # | Kriterium | Ergebnis |
|---|---|---|
| 1 | Jede Tabelle mandantengebunden; kein Cross-Tenant-Zugriff | **Teilweise** — App-Ebene bestanden (`test_tenant_sees_only_own_users`, `test_tenant_cannot_patch_other_tenant_user`). DB-Ebene (RLS aus `001_init.sql`) **nicht verifizierbar**: Testsuite läuft gegen `SqliteEngine`, in dieser Umgebung ist kein Postgres erreichbar (`psql`/`pg_lsclusters` fehlen). Bereits als offene Einschränkung in Paket 1.1 vermerkt. |
| 2 | Login/Logout/Reset ohne E-Mail-Enumeration | ✅ Bestanden — `request_password_reset` antwortet identisch für bekannte/unbekannte Adressen (`auth/service.py:66`). |
| 3 | Drosselung nach 5 Fehlversuchen/15 Min je Konto+Herkunft | ✅ Bestanden — `login()` prüft `count_recent_failures` vor Passwortvergleich. |
| 4 | Feste Rollen Inhaber/Büro/Monteur, nicht frei konfigurierbar | ✅ Bestanden (Schema + Tests). |
| 5 | Inhaber verwalten Nutzer, letzter aktive Inhaber geschützt | ✅ Backend bestanden (Test vorhanden). Frontend-Schutz laut Implementierungsstand vorhanden, nicht erneut manuell geprüft. |
| 6 | Neue Nutzer setzen Passwort nur über Einladungslink | ❌ **Fehlgeschlagen** — Backend-Endpunkt `POST /auth/invitations/accept` korrekt implementiert, aber es existiert **keine Frontend-Seite**, die ihn aufruft (`nextjs_app/app` enthält keine `invitat*`-Route). Eingeladene Nutzer können ihr Konto nicht aktivieren. Bereits in Paket 1.2 als Bug #3 dokumentiert — weiterhin offen. |
| 7 | Monteure sehen nur eigene Termine, keine Preise | — Nicht prüfbar in PROJ-1: Termin-/Vorgangsdaten gehören zu späteren Features (PROJ-3/6). Rollenbasierte Navigation im Frontend vorhanden. |
| 8 | Login, Rollenänderung, Fehlversuch protokolliert | ✅ Bestanden — `repo.audit(...)` bei allen relevanten Pfaden, Test vorhanden. |

### Bugs (aus Codeprüfung, deckungsgleich mit bereits dokumentierter 1.2-Zurückweisung — weiterhin ungefixt)
1. **Kritisch — Betreiberbereich im Mandanten-Shell.** `nextjs_app/app/(app)/betrieb-anlegen/page.tsx` ruft `/admin/mandanten` über `apiFetch` (`lib/api/client.ts`) auf, das den Business-Token aus `lib/session.ts` sendet. Laut Vertrag sind Betriebs-Token an `/admin` ungültig (bestätigt durch Backend-Test `test_operator_token_rejected_on_business_endpoint` — die Umkehrung gilt ebenso). Der Aufruf schlägt fehl.
2. **Kritisch — kein Betreiber-Login im Frontend.** `POST /operator/auth/login` wird nirgends aufgerufen; `lib/api/operator.ts` deckt nur `/admin/mandanten` ab. Eine Betreiber-Sitzung ist über die UI nicht herstellbar.
3. **Hoch — Einladungsannahme fehlt.** Siehe AC #6 oben. Blockiert das komplette Onboarding neuer Betriebsnutzer.

Keine neuen Bugs über die bereits dokumentierten hinaus gefunden; Backend ist stabil und deckt alle prüfbaren Kriterien ab.

### Security-Hinweise
- Operator- vs. Business-Token-Trennung serverseitig verifiziert (separate Audience, Test vorhanden).
- Passwort-Reset widerruft alle Sitzungen des Nutzers (`revoke_user_sessions`) — verhindert Session-Fixation nach Kompromittierung.
- RLS-Verifikation auf DB-Ebene bleibt offen (siehe AC #1) — muss vor Deploy gegen echtes Postgres nachgeholt werden.

### Produktionsreife: **NEIN**
Zwei kritische und ein hoher Bug (alle aus Paket 1.2) sind ungefixt und blockieren zentrale Akzeptanzkriterien (Einladungs-Onboarding, Betreiberbereich). Backend ist bereit; Frontend-Nacharbeit aus 1.2 muss zuerst erfolgen.

**Nächster Schritt:** Frontend-Nacharbeit (Paket 1.2) beheben lassen, danach `/abc-qa` erneut für die betroffenen Kriterien.

### Re-Check 2026-08-16 (zweiter Lauf, `/abc-qa 1`)
- `conda run -n Dashboard --no-capture-output python -m pytest backend/tests -q` → weiterhin **18/18 grün**, keine Regression.
- Codeprüfung `nextjs_app/`: Paket-1.2-Nacharbeit noch nicht erfolgt.
  - `app/(app)/betrieb-anlegen/page.tsx` weiterhin unter `(app)`, ruft `createBetrieb` → `apiFetch("/admin/mandanten")` mit Business-Token (`lib/api/operator.ts`, `lib/api/client.ts`). Bug 1 **weiterhin offen**.
  - Kein `operator`-Login im Frontend; `lib/api/operator.ts` deckt nur `/admin/mandanten` ab. Bug 2 **weiterhin offen**.
  - Kein `invitat*`-Route unter `app/`. Bug 3 **weiterhin offen**.
- Keine neuen Bugs. Status bleibt **NEIN / In Review** — unverändert seit dem ersten Lauf, da keine Nacharbeit committet wurde.

### Fix 2026-08-16 (Paket 1.2 Nacharbeit)
Alle drei Bugs aus der 1.2-Zurückweisung behoben:
1. **Betreiberbereich getrennt.** `betrieb-anlegen` liegt jetzt unter einer eigenen Route-Group `app/(operator)/` mit eigenem Layout-Guard; Aufrufe laufen über `operatorApiFetch` (`lib/api/client.ts`), das den getrennten Betreiber-Token aus `lib/session.ts` (`bo_operator_access_token`) sendet, nie den Business-Token.
2. **Betreiber-Login ergänzt.** `app/(operator)/operator-login/page.tsx` ruft `POST /operator/auth/login` auf (`lib/api/operator.ts: operatorLogin`); `operatorLogout` ruft `/operator/auth/logout`.
3. **Einladungsannahme ergänzt.** `app/(auth)/einladung/page.tsx` ruft `POST /auth/invitations/accept` (`lib/api/auth.ts: acceptInvitation`) und leitet danach zu `/login`.

Zusätzlich beim Fix gefunden und mitbehoben: `lib/api/operator.ts` sendete für `POST /admin/mandanten` falsche Feldnamen (`firmenname`/`inhaber_name`/`inhaber_email` statt der vom Backend erwarteten `name`/`owner_name`/`owner_email`, siehe `backend/app/features/operator/schemas.py`) — Anlage wäre immer mit 422 gescheitert. Jetzt korrekt.

Nebenbei: `betrieb`-Navigationseintrag aus `NAV_RECHTE.Inhaber` und der AppShell-Navigation entfernt — der Betreiberbereich ist keine Mandantenansicht und gehört nicht in die Inhaber-Navigation (§ „Plattformbetreiber-Zugang").

Verifiziert: `npx tsc --noEmit` und `npx next build` fehlerfrei. Backend-Tests unverändert 18/18 grün (reiner Frontend-Fix).

**Nächster Schritt:** `/abc-qa 1` erneut laufen lassen, um AC #6 und die Bugs #1–3 als bestanden zu bestätigen (inkl. manueller Browser-Prüfung, da hier nur Code-Review + Build-Verifikation erfolgte).

### Re-Check 2026-08-16 (dritter Lauf, `/abc-qa 1`, End-to-End über HTTP)
Backend läuft (kein Postgres in dieser Umgebung erreichbar) mit `SqliteEngine`
im echten `uvicorn`-Prozess, seeded mit Betreiber. Die exakten Aufrufe aus
`nextjs_app/lib/api/operator.ts` und `lib/api/auth.ts` wurden 1:1 per `curl`
gegen laufende Endpunkte nachgestellt (Vertrag statt Browser-Klick, da keine
Display/Playwright-Session in diesem Lauf aufgesetzt wurde):

| Schritt | Ergebnis |
|---|---|
| `POST /operator/auth/login` (Payload wie `operatorLogin`) | ✅ `200`, Token mit `aud=operator` |
| `POST /admin/mandanten` mit Business-/Fremdtoken | ✅ `401` — Trennung hält |
| `POST /admin/mandanten` mit `{name, owner_name, owner_email}` (Payload wie `createBetrieb` nach Feldnamen-Fix) | ✅ `201`, korrekt angelegt — vorheriger Feldnamen-Bug bestätigt behoben |
| `POST /auth/invitations/accept` mit Einladungstoken + 20-stelligem Passwort (Payload wie `acceptInvitation`) | ✅ `{"ok":true}` |
| `POST /auth/login` mit dem neu gesetzten Passwort | ✅ `200`, Business-Token erhalten — AC #6 bestätigt erfüllt |
| Einladungstoken zweites Mal einlösen | ✅ `422` — Einmal-Verwendung hält |

`npx tsc --noEmit` und `npx next build` weiterhin fehlerfrei. Backend-Testsuite
weiterhin 18/18 grün, keine Regression.

**Nicht in diesem Lauf geprüft:** echter Browser-Klickpfad (Playwright/Chrome)
über die drei neuen/verschobenen Seiten (`(operator)/operator-login`,
`(operator)/betrieb-anlegen`, `(auth)/einladung`) sowie RLS auf echter
Postgres-Instanz — beides weiterhin offen wegen fehlender Postgres-Instanz in
dieser Umgebung (siehe frühere Einschränkung in Paket 1.1).

### Aktualisierte Akzeptanzkriterien
| # | Kriterium | Ergebnis |
|---|---|---|
| 6 | Neue Nutzer setzen Passwort nur über Einladungslink | ✅ **Bestanden** (Frontend-Seite vorhanden + End-to-End-Vertrag verifiziert) |

### Bugs — Status
1. Betreiberbereich im Mandanten-Shell → **behoben, verifiziert**
2. Kein Betreiber-Login → **behoben, verifiziert**
3. Einladungsannahme fehlt → **behoben, verifiziert**
(Zusatzfund Feldnamen-Mismatch `/admin/mandanten` → **behoben, verifiziert**)

Keine offenen Critical/High-Bugs aus der 1.2-Nacharbeit mehr. Verbleibende
offene Einschränkung: RLS-Verifikation auf echter Postgres-Instanz (AC #1,
seit Paket 1.1 bekannt, nicht durch diesen Fix berührt).

### Produktionsreife: **JA, mit Einschränkung**
Alle Critical/High-Bugs aus Paket 1.2 sind gefixt und end-to-end verifiziert.
Einzige verbleibende offene Prüfung ist AC #1 auf DB-Ebene (RLS gegen echtes
Postgres) — das ist eine Infrastruktur-Lücke dieser Dev-Umgebung, kein
Code-Bug, muss aber vor Produktivbetrieb nachgeholt werden.

**Nächster Schritt:** Status auf **Approved** setzen; vor `/abc-deploy` die
RLS-Policies einmal gegen eine echte Postgres-Instanz laufen lassen.

## Deployment
_To be added by /deploy_
