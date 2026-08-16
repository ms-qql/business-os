# Architektur-Entscheidung: ImmoCRM-Wiederverwendung für das Handwerker Business OS

**Erstellt:** 2026-08-15 · **Autor:** Solution Architect (`/abc-architecture`)
**Status:** Freigegeben · **Branch:** main (business_os ist noch kein Git-Repo, nur `docs/`)
**Entschieden am 2026-08-15:** Frontend = **Next.js 16** (App Router, TypeScript, Tailwind + shadcn/ui, Motion), Monteur-Ansicht zunächst als PWA. Folge: keine Frontend-Code-Ernte aus ImmoCRM — die Ernte betrifft ausschließlich das Backend.
**Grundlagen:** `docs/Brainstorm.md` (Business OS), Codebasis `/home/dev/projects/immo-crm`

---

## 1. Entscheidung in einem Satz

> **Neues Repo, aber kein Neubau von Null: Infrastruktur aus ImmoCRM wird gezielt geerntet („Harvest"), die Immobilien-Fachlichkeit bleibt zurück.**
> Kein Fork, kein Umbau der bestehenden App, kein zweites Segment in derselben Codebasis.

Begründung kurz: Ein Fork schleppt ~60 % Immobilien-Domäne mit, die nie gebraucht wird (Exposé, IS24, ImmoCheck, OpenImmo). Ein echter Neubau wirft dagegen ~6–9 Monate gehärtete Infrastruktur weg, die im Business OS **wortgleich** wieder gebraucht wird — vor allem die E-Mail-Pipeline, Auth mit 2FA, Mandanten-Branding und die Hintergrund-Daemons.

---

## 2. Was ImmoCRM heute ist (Bestandsaufnahme)

| Bereich | Stand |
|---|---|
| Backend | FastAPI, rohes SQL über `psycopg`, ~35 Route-Module + 30 Services |
| Frontend | Flutter Web (`lib/`), Riverpod, go_router, **eigene Widget-Bibliothek — kein `shadcn_flutter`** |
| Mandantenmodell | **Datenbank pro Mandant.** Master-DB (Auth, `tenants`, Audit) + je Mandant eine eigene DB; `TenantDatabaseRouter` löst `tenant_id → database_url` mit 5-Minuten-Cache auf |
| RLS | **nicht vorhanden** — Fachtabellen haben bewusst gar keine `tenant_id`-Spalte (`schema.py`: „no tenant_id columns") |
| Schema | `db/migrations/*.sql` (22 Dateien) + `backend/app/schema.py` (1.500 Zeilen Schema-Bootstrap im Code) |
| Dateien | MinIO über `storage.py` (boto3), Presigned URLs |
| Reife | 130+ Feature-Specs, 44 Flutter-Tests, laufende Produktion |

**Zwei Altlasten, die nicht mitkommen dürfen:**
1. `backend/app/main.py` = **7.614 Zeilen** mit 69 direkt eingehängten Endpunkten neben 33 Routern.
2. Einzelne Route-Dateien mit 60–106 KB (`expose.py`, `is24_sync.py`, `import_export.py`) — nicht mehr review-fähig.

---

## 3. Der harte Bruch: Mandantentrennung

Das ist die einzige Stelle, an der Business OS **strukturell anders** sein muss.

| | ImmoCRM | Business OS (laut Brainstorm #31) |
|---|---|---|
| Modell | eine Postgres-DB je Mandant | eine DB, `mandant_id` je Zeile, Row Level Security |
| Isolation | maximal (physisch getrennt) | stark (Datenbank-Ebene, nicht Anwendungs-Ebene) |
| Kosten je Mandant | eine DB — bei Neon billig, auf einem Dokploy-VPS teuer | nahe null |
| Migration | 1 Migration × N Mandanten, N wächst | 1 Migration, fertig |
| Onboarding | DB anlegen, Schema initialisieren, URL eintragen | Zeile in `mandanten` einfügen |

**Empfehlung: RLS-Modell für Business OS.** Zielgruppe sind viele kleine Handwerksbetriebe zu niedrigem Monatspreis auf selbstgehostetem Dokploy-Postgres — DB-pro-Mandant skaliert dort weder betrieblich (#47: der Solo-Betreiber ist der Engpass) noch preislich.

**Der Glücksfall dabei:** Weil ImmoCRM-Fachtabellen *keine* `tenant_id`-Spalte haben, enthalten die 191 Datenbankzugriffe in den Route-Modulen **keine Mandanten-Filter im SQL**. Genau so muss Code unter RLS aussehen — der Filter kommt aus der Policy. Konsequenz:

- **Route-Code ist portabel**, wenn der Verbindungs-Kontextmanager dieselbe Signatur behält und statt einer anderen DB ein `SET LOCAL app.current_mandant_id` setzt.
- **Schema-DDL ist nicht portabel**: jede Fachtabelle braucht neu `mandant_id` + Policy + Index.

Das ist die zentrale technische Erkenntnis dieser Prüfung: Der Wechsel des Mandantenmodells kostet die *Schema-Schicht*, nicht die *Anwendungs-Schicht*.

---

## 4. Was übernommen wird — bewertet

### Klasse A — nahezu 1:1 übernehmen (höchster Hebel)

| Baustein aus ImmoCRM | Deckt im Business OS ab | Anpassung |
|---|---|---|
| `backend/app/auth/*` — JWT, Refresh, TOTP-2FA, Backup-Codes, Passwort-Policy, `require_permission`, Audit-Log (~1.500 Zeilen) | **PROJ-1** Mandanten, Auth, Rollen | Rollen umbenennen (Inhaber/Büro/Monteur, #39), `tenant_id` → `mandant_id` |
| `services/email_service.py` — IMAP-Empfang, SMTP-Versand, Zugangsdaten-Verschlüsselung, MIME-Parsing, Anhänge, Thread-/Konversations-Zuordnung | **PROJ-4** E-Mail-Kanal, **#44** Antwort aus dem System | Transport- und Parsing-Schicht übernehmen, ImmoCRM-Zuordnungslogik (Objekt/Interessent) durch Anfrage-Zuordnung ersetzen |
| `routes/email_sync_errors.py` + Sweeper-Fehlerpfade | **PROJ-11** Kanal-Überwachung, **#36/#48** stille Fehler | fast unverändert |
| `services/reminders.py` + `reminder_sweeper.py` — generisch über `entity_type`/`entity_id` gebaut | **PROJ-10** Nachfassen 3/7/14 Tage | Entitätstypen austauschen |
| `routes/tenant_settings.py` — Logo-Upload nach MinIO, Farben, Absender, Einstellungs-JSON | **PROJ-2** Mandanten-Branding (Whitelabel) | Feldliste erweitern (eigene Domain) |
| `storage.py`, `config.py`, `vault.py` — MinIO, Settings, Credential-Verschlüsselung | Querschnitt | unverändert |
| `services/ai_service.py` — inkl. **PII-Scrubber** vor dem Modellaufruf und Mandanten-Opt-out für KI | **#21/#33/#50** KI-Transparenz, DSGVO-Antwort im Verkaufsgespräch | Prompts neu, Struktur bleibt |
| Sweeper-Muster (Hintergrund-Thread, Advisory-Lock je Mandant, Backoff-Retry) | alle Automatiken: Triage, Nachfassen, Löschjobs | Lock-Schlüssel auf `mandant_id` |

### Klasse B — als Vorlage/Muster, nicht als Datei

| Baustein | Nutzung im Business OS |
|---|---|
| `routes/templates.py` + `services/anrede.py` (Textbausteine, Platzhalter-Rendering, Du/Sie-Anrede) | **#62** Absagetexte, **#15** Ton des Betriebs — Datenmodell passt, Platzhalter neu |
| `routes/import_export.py` (CSV/Excel-Import mit Feld-Mapping) | **PROJ-6/#11** Kundenimport aus Excel/Outlook — Mapping-Mechanik übernehmen, 80 KB Immobilien-Mapping nicht |
| `routes/appointments.py`, `appointment_types.py`, `calendar_feed.py` (inkl. ICS-Feed) | **PROJ-15** Terminverwaltung + Kalender-Sync — grob 60–70 % Struktur |
| `templates/expose_pdf.html` + PDF-Erzeugung im Mandanten-Branding | **PROJ-9** Angebots-PDF im Betriebs-Branding — Pipeline übernehmen, Inhalt neu |
| `routes/support.py`, Support-Widget, Tooltip-Hilfe | **#35** Support ist der Kostenblock |
| `routes/tasks.py`, `documents.py`, `audit.py` | Querschnitt |

### Klasse C — bleibt zurück (Immobilien-Domäne, ~60 % des Backend-Volumens)

`expose.py` (106 KB), `immoscout.py`/`is24_*` (~230 KB), `immocheck*` (~75 KB), `openimmo_parser.py`, `property_*`, `bookings.py`, `viewing_invitations.py`, `client_alias_rematch*`, `import_export.py`-Feldwerke.

### Klasse D — bewusst **nicht** übernehmen (Architekturschulden)

- `main.py` als Monolith mit Inline-Endpunkten → im Business OS gilt: `main.py` hängt nur Router ein, Route-Dateien < 500 Zeilen.
- `schema.py` als 1.500-Zeilen-Schema-im-Code → im Business OS ausschließlich versionierte SQL-Migrationen.
- `TenantDatabaseRouter` als DB-pro-Mandant → ersetzt durch RLS-Adapter mit gleicher Aufrufform.
- Fehlende Pydantic-Schemas: ImmoCRM nimmt in vielen Routen rohe `dict[str, Any]`-Bodies. Business OS validiert alles über Pydantic v2 (Projektkonvention).

---

## 5. Frontend — Next.js vs. Flutter im Detail

Brainstorm-Punkt 2 ist offen und entscheidet den Frontend-Anteil dieser Analyse. Die Frage ist nicht „welches Framework ist besser", sondern: **wie viel des Business OS ist öffentlich zugängliche Web-Fläche, und wie viel ist angemeldete Anwendung?** Daran hängt alles Weitere.

### 5.1 Der entscheidende Punkt: der öffentliche Anteil ist groß

Aus dem Brainstorm ergeben sich diese Flächen, die **ohne Login, von Fremden, oft vom Handy** aufgerufen werden:

| Fläche | Herkunft | Wer ruft auf |
|---|---|---|
| Web-Formular als erster Anfragekanal | **PROJ-3 (Core)** | Endkunde, eingebettet auf der Website des Betriebs |
| Kunden-Status-Link („Ihre Anfrage — Status …") | #10, PROJ-18 | Endkunde, per SMS/Mail auf dem Handy |
| Angebots-Ansicht/-Annahme durch den Endkunden | PROJ-9-Umfeld | Endkunde |
| Karriereseite + Kurzbewerbung ohne Lebenslauf | #70, PROJ-24 | Bewerber, „vom Handy in der Mittagspause" |
| Empfehlungs-Link für Mitarbeiter | #72 | Bewerber |
| Rechtsseiten: Datenschutz, AVV-Info, **KI-Transparenzseite** | #32, #33, #50 | Interessent im Verkaufsgespräch |
| Marketing-/Produktseite des Business OS selbst | Vertrieb | Google, Interessent |
| Je Mandant eigene Domain (Whitelabel) | Core-Tabelle „Branding je Mandant … Domain" | alle obigen, unter fremder Domain |

Das ist kein Randbereich — das sind sieben bis acht Oberflächen, davon zwei im Core (PROJ-3, Rechtsseiten) und die tragenden Teile des Recruiting-Moduls.

**Und genau hier liefert ImmoCRM den empirischen Beleg:** Dort ist das Frontend Flutter — trotzdem sind *alle* öffentlichen Seiten als servergerenderte Jinja-Templates im FastAPI-Backend gebaut: `expose.html` (25 KB), `expose_pdf.html`, `expose_provision.html`, `expose_thanks.html`, `listing.html`, `legal_agb.html`, `legal_datenschutz.html`, `legal_widerruf.html`, ausgeliefert über `HTMLResponse`-Routen in `expose.py`. Die Flutter-App konnte den öffentlichen Teil nicht übernehmen, also ist ein **zweites Frontend im Backend** entstanden.

Mit Flutter im Business OS passiert dasselbe noch einmal — nur mit mehr Flächen: zwei Technologien, zwei Styling-Systeme, zwei Stellen, an denen das Mandanten-Branding (Logo, Farben, Domain) korrekt umgesetzt sein muss, zwei Test-Wege. Mit Next.js ist es ein System: öffentliche Routen servergerendert, angemeldeter Bereich als Client-Anwendung, gleiche Komponenten, gleiche Tokens, gleiches Branding-Objekt.

### 5.2 Ladezeit und Zielgruppe

Der Endkunde des Handwerkers klickt einen Status-Link auf dem Handy im Mobilfunknetz. Der Bewerber öffnet die Karriereseite in der Mittagspause und bricht bei Verzögerung ab (#70 ist genau darauf ausgelegt: fünf Felder, kein PDF).

- Flutter Web liefert eine Anwendung aus (Engine + App-Bundle) — je nach Renderer ein Vielfaches einer HTML-Seite und mit sichtbarem Leerbildschirm bis zum ersten Frame. Für eine Fünf-Felder-Bewerbung ist das strukturell das falsche Format.
- Next.js liefert für dieselbe Seite HTML aus, das sofort sichtbar ist.

Dazu kommt: **Flutter Web ist nicht indexierbar.** Für Marketing-Seite und Karriereseite (Handwerker suchen Personal auch über Google) ist das ein harter Ausschluss, für den Kunden-Status-Link egal.

### 5.3 Was ImmoCRM auf der Flutter-Seite konkret kostet

Aus der Codebasis, nicht aus dem Lehrbuch:

- **Kein `shadcn_flutter`.** ImmoCRM hat eine eigene Widget-Sammlung (`lib/core/widgets/`: Sidebar, Topbar, StatCard, SearchableDropdown, AppTextField …). Wer sie erbt, verstößt gegen die Projektkonvention „shadcn first" und pflegt eine zweite, undokumentierte Komponentenbibliothek. Wer sie nicht erbt, verliert den größten Teil der behaupteten Ersparnis.
- **`google_fonts` in 70 Dateien** (`GoogleFonts.plusJakartaSans…`). Dieses Paket lädt Schriften zur Laufzeit vom Google-CDN — das verstößt gegen die DSGVO-Regel des Projekts (Schriften nur über Bunny Fonts oder selbst gehostet). Für ein Produkt, dessen Verkaufsargument teilweise Datenschutz ist (#50), muss das ohnehin ersetzt werden.
- **HTML-Brücken als Dauerthema.** Für Mail-Inhalte nutzt ImmoCRM `HtmlElementView`-iframes (`mail_body_iframe_web.dart`, `email_detail_iframe_web.dart`) und musste `pointer_interceptor` einbauen, weil Klicks in Dialogen vom darüberliegenden iframe verschluckt wurden (siehe Kommentar in `pubspec.yaml`, PROJ-39). Das Business OS zeigt genauso E-Mail-Verläufe an (#44) — dieselbe Brücke, dieselben Randfälle.
- **Web-spezifische Doppel-Dateien** (`token_storage_web.dart` / `_stub.dart`, `browser_http_client_web.dart` / `_stub.dart`) als Preis dafür, dass eine Mehrplattform-Technologie im Browser läuft.

Realistische Ersparnis bei Flutter, ehrlich gerechnet: `lib/core/auth/` (Auth-Provider, Token-Storage), API-Client-Muster, `permission_gate`, `app_shell` — **2–4 Wochen**, davon ein Teil sofort wieder ausgegeben für Font-Umstellung und Widget-Bereinigung.

### 5.4 Das einzige echte Flutter-Argument: die Monteur-Ansicht

#9/PROJ-19: „Ein Monteur mit Handschuhen bedient keine Tabelle." Heute Termine, Adresse, Fotos hochladen, Zeit erfassen, „erledigt".

Für Flutter spricht dort: echte App-Store-Builds, robuste Kamera-Anbindung, verlässliche Offline-Fähigkeit im Keller oder Neubau ohne Empfang, Push ohne Umwege.

Dagegen sprechen drei Dinge:
1. **PROJ-19 ist V1.1, nicht Core.** Die Framework-Wahl für das gesamte Produkt an einem Feature auszurichten, das nach dem Referenzkunden kommt, dreht die Prioritäten um.
2. Der Funktionsumfang der Monteur-Ansicht ist klein und mit einer PWA erreichbar: Kamera-Upload über Datei-Eingabe, Offline-Cache über Service Worker, Startbildschirm-Symbol. Push auf iOS ist nur nach „Zum Home-Bildschirm" verfügbar — bei einer Handvoll eigener Monteure je Betrieb ist das eine Onboarding-Zeile, kein Blocker.
3. Falls die Monteur-App später doch nativ sein muss, ist sie **eine separate, kleine App** gegen dieselbe API — nicht der Grund, das Büro-Frontend in Flutter zu bauen. Genau das entspricht #9: „getrennte Rollen-Apps statt einer App mit Rechtefiltern".

### 5.5 Entwicklungstempo und vorhandenes Werkzeug

- **Eigene UI-Pipeline passt zu React.** Die vorhandenen Skills `ui-redesign`, `ui-template-ingest`, `ui-mockup-export`, `ui-images-fill` erzeugen und verwalten **React/Tailwind**-Bausteine in einer Block-Registry. Für Marketing-Seite, Karriereseite und Rechtsseiten des Business OS ist das direkt verwendbar. Für Flutter ist davon nichts nutzbar.
- **shadcn/ui-Ökosystem** deckt Tabelle, Formular, Dialog, Command-Palette, Datepicker fertig ab; Zod + react-hook-form ist für ein formularlastiges Produkt (Preisliste, Angebotspositionen, Qualifizierungsfragen) der kürzere Weg.
- **Gegenrechnung, ehrlich:** `/abc-frontend` und die Agent-Rules `frontend-dev.md` sind heute **rein Flutter** formuliert. Next.js kostet eine Anpassung dieser beiden Dateien. Die globale Projektkonstitution kennt Next.js dagegen bereits als gleichwertige Option inklusive `nextjs_app/`-Layout — der Rahmen steht also, nur die Skill-Texte fehlen. Aufwand: überschaubar, aber real und vor PROJ-1 einzuplanen.

### 5.6 Gegenüberstellung

| Kriterium | Next.js 16 | Flutter Web |
|---|---|---|
| Öffentliche Seiten (7–8 Flächen) | nativ, ein System | zweites Frontend nötig (Beleg: ImmoCRM-Jinja) |
| SEO Marketing + Karriereseite | ja | nein |
| Erstladezeit Handy/Mobilfunk | gering | Anwendungs-Bundle |
| Whitelabel-Domain je Mandant | Host-basiertes Routing in einer Schicht | App + zweite Schicht separat |
| Code-Ernte aus ImmoCRM | keine | 2–4 Wochen, mit Altlasten |
| Monteur-Ansicht | PWA (ausreichend), nativ später separat | stärker |
| Vorhandene UI-Skills/Block-Registry | direkt nutzbar | nicht nutzbar |
| shadcn-Konvention des Projekts | shadcn/ui, sofort | `shadcn_flutter` — in ImmoCRM nicht vorhanden |
| Anpassung von Skills/Agent-Rules | nötig (`abc-frontend`, `frontend-dev.md`) | keine |
| Schriften/DSGVO | Bunny Fonts direkt | ImmoCRM-Theme hängt an `google_fonts` (CDN) — muss ersetzt werden |

### 5.7 Empfehlung — **entschieden am 2026-08-15: Next.js 16**

**Next.js 16, App Router, Tailwind + shadcn/ui — Monteur-Ansicht zunächst als PWA.** Die 2–4 Wochen Flutter-Ernte sind der einzige Vorteil und werden von einem zweiten Frontend für den öffentlichen Bereich mehr als aufgefressen; ImmoCRM zeigt genau diesen Verlauf bereits im Bestand.

**Flutter wäre die richtige Wahl, wenn** die Monteur-App mit Offline-Betrieb schon im Core stünde statt in V1.1, oder wenn der öffentliche Anteil auf eine einzige Seite zusammenschmelzen würde. Beides trifft laut Brainstorm nicht zu.

---

## 6. Warum nicht die Alternativen

**Fork von ImmoCRM und umbauen.** Klingt schnell, ist die teuerste Variante: Man löscht wochenlang fremde Fachlichkeit aus 7.600 Zeilen `main.py` und einem verflochtenen Schema, ohne je zu wissen, ob man fertig ist. Jede zurückgelassene Immobilien-Tabelle ist künftige Verwirrung und Support-Last. Zusätzlich zieht ein Fork das falsche Mandantenmodell mit — genau die Entscheidung, die man neu treffen will.

**ImmoCRM zum Multi-Segment-Produkt ausbauen** (Handwerk als zweites Segment in derselben Codebasis). Widerspricht #27 und #45 direkt: Segmente sollen Konfiguration sein, nicht Code — und ImmoCRM ist als Immobilien-Code gebaut, nicht als Konfigurationsträger. Zusätzlich gefährdet jeder Umbau ein laufendes, zahlendes Produkt.

**Komplett von Null.** Vertretbar, aber teuer ohne Gegenwert: Die E-Mail-Pipeline (IMAP, SMTP, MIME, Anhänge, Zugangsdaten-Verschlüsselung, Fehlerbehandlung, Wiederanlauf) ist mehrere Monate Arbeit und in ImmoCRM produktionsbewährt. Sie noch einmal zu schreiben schafft keinen einzigen neuen Produktvorteil — und **#51 warnt ausdrücklich davor, vor dem ersten zahlenden Kunden zu viel zu bauen.**

---

## 7. Grobe Wirkung auf den Backlog

| Business-OS-Ticket | Herkunft | Ersparnis |
|---|---|---|
| PROJ-1 Auth/Rollen/RLS | Klasse A + neues RLS-Fundament | hoch |
| PROJ-2 Branding | Klasse A | sehr hoch |
| PROJ-3 Anfrage-Datenmodell | neu (Kern des Produkts) | keine |
| PROJ-4 E-Mail-Kanal | Klasse A | **sehr hoch** |
| PROJ-5 Auto-Triage | neu (Kern, Hebel 1) | keine |
| PROJ-6 Kunden + Import | Klasse B | mittel |
| PROJ-7 Preisliste | neu (Kern, Hebel 2) | keine |
| PROJ-8/9 Angebot + PDF | PDF-Pipeline aus Klasse B, Komposition neu | mittel |
| PROJ-10 Nachfassen | Klasse A | hoch |
| PROJ-11 Kanal-Überwachung | Klasse A | hoch |
| PROJ-12/13/14 Onboarding, DSGVO, Verbrauch | teils Klasse A/B | mittel |
| PROJ-15 Termine | Klasse B | mittel |

**Muster:** Genau die Tickets, die das Produkt *ausmachen* (Anfrage-Objekt, Triage, Preisliste, Angebotskomposition — #56 „Selbst bauen, was das Produkt ist"), sind Neubau. Alles, was jedes SaaS hat, kommt geerntet. Das ist die gewünschte Aufteilung, kein Zufall.

---

## 8. Erntetechnik (wie konkret)

1. Neues Repo `business_os` mit sauberem Skelett gemäß Projektstruktur; Git initialisieren.
2. **Kopieren, nicht submodulen, nicht als Bibliothek teilen.** Eine geteilte Bibliothek koppelt zwei Produkte mit unterschiedlichem Mandantenmodell und unterschiedlicher Release-Kadenz — jeder Fehler wird ein Doppelrisiko. Kopie ist hier die billigere Wahrheit.
3. Reihenfolge der Ernte: `config`/`storage`/`vault` → `auth` → RLS-Adapter mit gleicher Aufrufform wie `TenantDatabaseRouter.connect()` → `tenant_settings`/Branding → E-Mail-Transport → Sweeper-Muster.
4. Jede geerntete Datei bekommt beim Übernehmen: Pydantic-Schema, Umbenennung `tenant` → `mandant`, Aufteilung falls > 500 Zeilen.
5. Rückfluss-Kanal einplanen: Fixes, die beide Produkte betreffen (z. B. E-Mail-Parsing), werden bewusst **zweimal** gepflegt — das ist der Preis der Entkopplung und billiger als die Kopplung.

---

## 9. Offene Punkte, die diese Entscheidung berühren

1. ~~Frontend Next.js vs. Flutter~~ — **entschieden: Next.js 16** (2026-08-15). Damit keine Flutter-Ernte. **Folgeaufgaben, vor PROJ-1 einzuplanen:**
   - `/home/dev/tools/Hal/09_Skills/abc-frontend/SKILL.md` ist rein Flutter formuliert → Next.js-Variante nötig (eigener Skill oder Framework-Weiche im Master).
   - `/home/dev/.claude/rules/agents/frontend-dev.md` ebenso (Flutter/Riverpod/`AppColors`) → auf Next.js/Tailwind/shadcn-ui umschreiben.
   - Projektstruktur `nextjs_app/` gemäß globaler Konstitution anlegen; Schriften über Bunny Fonts, nie Google-CDN.
   - Öffentliche Flächen (siehe 5.1) von Anfang an als servergerenderte Routen planen, nicht nachträglich.
2. **E-Mail-Empfang: IMAP am Bestandspostfach oder eigene Adresse mit Weiterleitung** (Brainstorm-Punkt 4). ImmoCRM kann IMAP produktiv — das spricht dafür, den geerbten Weg zu nehmen und die Weiterleitungs-Variante nur als Fallback zu führen.
3. **Modell-Anbieter/Region** (Brainstorm-Punkt 3): ImmoCRM nutzt OpenAI mit vorgeschaltetem PII-Scrubber. Für den Verkaufs-Einwand (#50) prüfen, ob EU-Region oder europäischer Anbieter nötig ist.
4. Business OS hat noch **keine `features/INDEX.md` und keine Specs** — der Brainstorm schlägt PROJ-1…PROJ-24 vor, geschrieben ist noch nichts. Vor `/abc-architecture` je Feature muss `/abc-requirements` laufen.

---

## 10. Empfohlener nächster Schritt

`/abc-requirements` im Init-Modus für `business_os` — PRD + `features/INDEX.md` aus `docs/Brainstorm.md` anlegen, dann Specs für PROJ-1 bis PROJ-5. Diese Datei ist die Grundlage für den Tech-Design-Abschnitt von PROJ-1 (Mandanten/Auth/RLS), weil dort das Mandantenmodell endgültig festgeschrieben wird.
