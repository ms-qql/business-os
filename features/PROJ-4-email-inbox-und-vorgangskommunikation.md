# PROJ-4: E-Mail-Inbox und Vorgangskommunikation

## Status: Architected
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — geschützter Mandanten- und Nutzerkontext.
- Requires: PROJ-3 — Kunden, Vorgänge und Dokumente.

## Reuse aus ImmoCRM
- IMAP/SMTP-Verbindung, MIME-Parsing, Anhänge, Polling und Fehlerprotokoll extrahieren; Immobilienzuordnung und Monolith nicht übernehmen.

## User Stories
- Als Büro möchte ich E-Mail-Anfragen in derselben Inbox wie Webanfragen sehen.
- Als Inhaber möchte ich aus einem Vorgang antworten, damit kein zweiter Posteingang entsteht.
- Als Büro möchte ich erkennen, wenn die Postfachanbindung gestört ist.

## Acceptance Criteria
- [ ] Ein Inhaber kann ein Betriebspostfach verbinden und Empfang sowie Versand vor dem Speichern testen.
- [ ] Neue E-Mails werden als neuer Vorgang oder als Nachricht am passenden bestehenden Vorgang abgelegt; Anhänge werden mitgespeichert.
- [ ] Büro und Inhaber können eine E-Mail im Vorgang schreiben, prüfen und senden; gesendete Nachricht und Versandzeit erscheinen im Verlauf.
- [ ] Antworten auf eine gesendete E-Mail werden demselben Vorgang zugeordnet, sofern eine eindeutige Thread-Zuordnung möglich ist.
- [ ] Bei nicht erreichbarem Postfach zeigt die Inbox eine sichtbare Warnung „E-Mail-Abruf fehlgeschlagen. Bitte Verbindung prüfen.“
- [ ] Nur Inhaber und Büro dürfen externe E-Mails senden.

## Edge Cases
- Unbekannte Absender werden als neuer Vorgang angelegt; bekannte Absender werden nicht blind mit einem beliebigen alten Vorgang verknüpft.
- Nicht unterstützte oder gefährliche Anhänge werden nicht ausgeführt und mit „Anhang konnte nicht verarbeitet werden.“ markiert.
- Eine E-Mail ohne Text, aber mit Anhang, wird dennoch verarbeitet.
- Doppelt abgeholte Nachrichten werden anhand stabiler Mail-Kennung nicht erneut angelegt.

## Technical Requirements
- Security: Zugangsdaten verschlüsselt speichern; HTML-E-Mail-Inhalte vor Anzeige bereinigen.
- Reliability: Polling-Fehler protokollieren und je Konto sichtbar machen.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-17 · **Stack:** Next.js 16 (App Router, Tailwind, shadcn/ui) + FastAPI + Postgres (RLS) + MinIO · **Branch:** specs/PROJ-4-email-inbox-und-vorgangskommunikation

### A) Komponentenstruktur (Next.js)
```
VorgangDetailPage
└── VorgangDetail (nextjs_app/components/vorgaenge/vorgang-detail.tsx)
    ├── VorgangChronik            (bestehend)
    ├── VorgangDokumente          (bestehend)
    └── VorgangEmail              (neu, nach Dokumente eingehängt)
        ├── EmailThread           (Liste gesendet/empfangen, Anhang-Chips)
        ├── EmailComposer         (nur sichtbar wenn darfSchreiben)
        └── PostfachWarnung       (Banner "E-Mail-Abruf fehlgeschlagen…")

InboxPage
├── PostfachWarnung
├── InboxFilter (zugeordnet / nicht zugeordnet)
├── EmailInboxListe
└── EmailNachrichtDetail (Vorgang zuordnen oder neu anlegen)

EinstellungenPage
└── PostfachEinstellungen (neu)
    ├── PostfachForm (IMAP/SMTP Host, Port, User, Passwort)
    └── TestVerbindungButton (Empfang + Versand vor Speichern testen; nur Inhaber)
```

### B) Datenmodell (Klartext)
- **email_konto** (ein aktives Konto pro Mandant, mandant-scoped, RLS wie bestehende Tabellen): IMAP/SMTP Host, Port, Benutzername, Passwort (verschlüsselt), TLS-Flag, `letzter_abruf_status` (ok/fehler), `letzter_abruf_fehler_text`, `letzter_abruf_at`.
- **email_thread**: mandant-scoped, mit optionalem `vorgang_id` und `kunde_id`. Neue, noch nicht sicher zuordenbare E-Mails bleiben damit sichtbar in der Inbox, ohne einem Vorgang zugeordnet zu sein.
- **email_nachricht**: gehört zu einem Thread, Richtung (eingehend/ausgehend), Absender, Empfänger, Betreff, Text (bereinigtes HTML + Plaintext), `message_id`/`in_reply_to`/`references` (RFC-Header für Thread-Zuordnung), `stabile_mail_kennung` (Unique-Constraint pro Mandant gegen doppeltes Abholen), Zeitstempel, sendender Nutzer (bei ausgehend).
- **email_anhang**: gehört zu `email_nachricht`, gleiches Muster wie Vorgangs-Dokumente — `object_key` in MinIO (`email/{mandant_id}/{thread_id}/{uuid4()}.{ext}`), Dateiname, Content-Type (per Magic Bytes gesnifft, nie Client-Angabe vertraut), Größe.
- Historie: jede Zustellung/jeder Versand erzeugt einen `add_historie`-Eintrag (`email_empfangen` / `email_gesendet`), gleiches Muster wie bestehende Vorgangs-Events.

### C) API-Shape (nur Endpunkte, kein Code)
```
- GET    /email-konto              → aktuelle Postfach-Konfiguration des Mandanten (ohne Passwort im Klartext)
- PUT    /email-konto              → Postfach speichern/aktualisieren (nur Inhaber)
- POST   /email-konto/test         → Empfang + Versand testen, ohne zu speichern
- GET    /email/inbox              → paginierte Inbox, Filter und Verbindungsstatus
- GET    /email/nachrichten/{id}   → Nachricht samt bereinigtem Inhalt und Anhängen
- POST   /email/nachrichten/{id}/zuordnen → einem vorhandenen Vorgang zuordnen
- POST   /email/nachrichten/{id}/vorgang → neuen Vorgang aus Nachricht anlegen
- GET    /vorgaenge/{id}/emails    → Thread eines Vorgangs (nur Büro und Inhaber)
- POST   /vorgaenge/{id}/emails    → E-Mail verfassen + senden (nur Inhaber, Büro)
- GET    /vorgaenge/{id}/emails/{email_id}/anhaenge/{anhang_id}/download → presigned URL

Alle Endpunkte: JWT Pflicht, mandant_id aus Token. Postfach konfigurieren/testen ist Inhaber-only; Zuordnen und Senden sind Büro/Inhaber. Monteure erhalten weder Inbox noch externe E-Mail-Inhalte.
```

### D) Tech-Entscheidungen (Begründung)
- **Kein neuer Scheduler-Dependency:** Es existiert im Repo keinerlei Job-Queue/Scheduler (kein Celery/APScheduler). Ein Dokploy-Cron startet den internen Abruf periodisch. Das hält die Abruflogik von öffentlich erreichbaren Nutzer-APIs fern und passt zum bestehenden Request/Response-Stil.
- **Zugangsdaten-Verschlüsselung:** neue, kleine Fernet-Verschlüsselung (symmetrisch) mit Schlüssel aus Server-Env (`EMAIL_CREDENTIALS_KEY`), analog zu den bereits vorhandenen Secrets in `config.py`. Kein KMS — für diesen Umfang ausreichend, DSGVO-Anforderung "verschlüsselt speichern" ist damit erfüllt.
- **Zuordnungs-Regel (dreistufig, deckt AC2 + Edge Cases ab):** (1) Treffer über `In-Reply-To`/`References`/gespeicherte Thread-Kennung → automatisch am bestehenden Vorgang abgelegt. (2) Kein Treffer, aber Absender-E-Mail an keinen `Kunde` bekannt → automatisch neuer Vorgang (erfüllt AC2 "neuer Vorgang" + Edge Case "unbekannte Absender werden als neuer Vorgang angelegt"). (3) Kein Thread-Treffer, aber Absender bekannt (mehrere/keine eindeutig zuordenbaren offenen Vorgänge) → Nachricht bleibt unzugeordnet in der Inbox, manuelle Zuordnung über `/email/nachrichten/{id}/zuordnen` oder `/vorgang` (erfüllt Edge Case "bekannte Absender werden nicht blind mit einem beliebigen alten Vorgang verknüpft"). Nur Fall (3) braucht die Inbox-Triage-UI — Fälle (1) und (2) laufen vollautomatisch beim Poll.
- **Duplikaterkennung:** `stabile_mail_kennung` (Message-ID) als Unique-Constraint pro Mandant statt Zeitstempel-Heuristik — robust gegen erneuten Poll derselben Mail.
- **HTML-Sanitizing:** eingehende HTML-Mails vor Anzeige serverseitig bereinigen (Allow-List Tags/Attribute), damit kein Script-/Tracking-Payload im Frontend landet.
- **Anhänge:** gleiches MinIO-Muster wie Vorgangs-Dokumente (Content-Type-Sniffing, presigned Download) — aber mit eigenem Thread-Pfad und eigener Sicherheitsprüfung, weil die bestehende Dokumentfunktion nur Bilder und PDFs akzeptiert.

### E) Abhängigkeiten (neue Pakete)
- Backend: `imaplib`, `email` und `smtplib` aus der Python-Standardbibliothek; `cryptography` für Fernet-Verschlüsselung und `bleach` für HTML-Bereinigung.
- Frontend: keine neuen Pakete — bestehende shadcn/ui-Komponenten (Card, Alert, Textarea, Button) reichen.

## Architecture Review (abc-review-architecture)
**Reviewed:** 2026-08-17 · **Verdict:** Architected

Hinweis: Die Tech-Design-Sektion wurde nach dem ersten Review-Durchlauf konkurrierend erweitert
(email_thread/InboxPage-Triage-Konzept ergänzt, Commit `bfc4bc3`). Dieses Review bewertet den
aktuellen, erweiterten Stand — nicht die ursprüngliche Fassung.

### Checklist
- [x] Component structure — `VorgangEmail` (Vorgang-Detail), `InboxPage` (nicht zugeordnete Nachrichten), `PostfachEinstellungen` decken alle drei Flows aus den User Stories ab, kein Konflikt mit bestehenden Komponenten.
- [x] Data model — `mandant_id` auf allen vier neuen Tabellen (`email_konto`, `email_thread`, `email_nachricht`, `email_anhang`), RLS-Muster wie bestehende Tabellen (mandant_id-first-arg-Konvention, `set_config` in `db.py`).
- [x] API shape — jeder AC hat einen Endpoint: Verbinden+Testen → `PUT/POST /email-konto(/test)`; Ablage neuer Mails → Poll (intern) + `GET /email/inbox`, `/zuordnen`, `/vorgang`; Antwort schreiben/senden → `POST /vorgaenge/{id}/emails`; Warnbanner → `letzter_abruf_status` auf `GET /email-konto`; Rollen-Restriktion → `require_role`.
- [x] Tech decisions — Zuordnungs-Regel während dieses Reviews präzisiert (siehe „Autonom behoben"), alle übrigen Entscheidungen bereits begründet.
- [x] Dependencies — stdlib bevorzugt (`imaplib`/`email`/`smtplib`), `cryptography` und `bleach` als einzige echte Neuzugänge, klar benannt.
- [x] Branch field — `specs/PROJ-4-email-inbox-und-vorgangskommunikation` (existiert bereits, aktiver Branch).
- [x] Conflict-free — CodeGraph-Exploration fand keine bestehenden Routen/Tabellen zu E-Mail/Postfach; keine Namenskollision.
- [x] Acceptance-criteria coverage — alle 6 AC + alle 4 Edge Cases auf mind. einen Endpoint/eine Komponente gemappt.

### Owner-/Schreibpfad-Check (abc-coordinate Overlay)
- `email_konto`: Owner/Schreiber = Inhaber über `PUT /email-konto` (Tech Design engt gegenüber AC auf Inhaber-only ein — AC verlangt nur "ein Inhaber kann verbinden", keine Aussage zu Büro; keine Verletzung). Voraussetzungs-Lesepfad: `GET /email-konto` — vorhanden.
- `email_thread`/`email_nachricht` (eingehend): Schreiber = interner Poll-Prozess. Voraussetzung: `Kunde.email`-Lookup + offene Vorgänge des Kunden — im Tech Design jetzt als dreistufige Zuordnungs-Regel präzisiert (siehe Tech-Entscheidungen).
- `email_nachricht` (ausgehend): Schreiber = Büro/Inhaber über `POST /vorgaenge/{id}/emails`. Voraussetzungs-Lesepfad: `GET /vorgaenge/{id}` — bestehender Endpoint, kein neuer Lesepfad nötig.
- Inbox-Triage (`/email/nachrichten/{id}/zuordnen`, `/vorgang`): Schreiber = Büro/Inhaber (gleiche Rollen wie Vorgangs-Schreibzugriff). Voraussetzungs-Lesepfad: `GET /email/inbox` (Liste unzugeordneter Nachrichten) — vorhanden.
- `email_anhang`: kein eigener Schreibpfad — entsteht mit der zugehörigen `email_nachricht`. Lesepfad: Download-Endpoint mit presigned URL, gleiches Muster wie `vorgaenge`-Dokumente.

### Autonom behoben
- Zuordnungs-Regel in „Tech-Entscheidungen" auf drei explizite Fälle präzisiert (Thread-Treffer → auto; unbekannter Absender → auto neuer Vorgang; bekannter Absender ohne Thread-Treffer → manuelle Inbox-Triage). Ohne diese Präzisierung stand die Inbox-Triage-UI im Widerspruch zu AC2 ("werden ... abgelegt" = automatisch); mit der Drei-Fälle-Regel decken sich Tech Design, AC2 und beide einschlägigen Edge Cases exakt — rein technische Klärung aus Spec + Codebase ableitbar, keine neue Produktentscheidung nötig.

### Offene Fragen (falls Blocked)
- Keine.

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
