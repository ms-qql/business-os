# E2E Smoke Report — PROJ-4 (E-Mail-Inbox und Vorgangskommunikation)

**Datum:** 2026-08-18
**Stack:** lokaler Docker-Compose-Build (`bizos-db`/`bizos-backend`/`bizos-frontend`), Backend `:18000`, Frontend `:13000` (Host-Portmapping nur für diesen Testlauf, Ports 8000/3000 auf dem VPS anderweitig belegt)
**Tester:** QA Engineer (AI), Playwright gegen echten Next.js-DOM (kein CanvasKit-Problem wie bei Flutter — reale Selektoren funktionieren)

## Browser-Smoke (Playwright, Chromium)

| Status | Test | Detail |
|---|---|---|
| ✅ PASS | login-render-mobile (375px) | HTTP 200 |
| ✅ PASS | login-render-tablet (768px) | HTTP 200 |
| ✅ PASS | login-render-laptop (1024px) | HTTP 200 |
| ✅ PASS | login-render-desktop (1440px) | HTTP 200 |
| ✅ PASS | login-flow (echter Login mit Inhaber-Account) | → `/startseite` |
| ✅ PASS | postfach-einstellungen-render | IMAP/SMTP-Formular inkl. getrennter `imap_tls`/`smtp_tls`-Checkboxen korrekt gerendert (BUG-1-Fix visuell bestätigt) |
| ✅ PASS | email-inbox-render | Inbox rendert, Filter „Nicht zugeordnet/Zugeordnet" vorhanden |
| ✅ PASS | AC-5 Warnbanner | Nach simuliertem Poll-Fehler erscheint exakt „E-Mail-Abruf fehlgeschlagen. Bitte Verbindung prüfen." |

Console-/Page-Errors: **keine**.

## API-Matrix (live gegen laufenden Stack)

| Test | Erwartet | Ergebnis |
|---|---|---|
| `GET /email-konto` ohne Token | 401 | ✅ 401 |
| `GET /email/inbox` ohne Token | 401 | ✅ 401 |
| `GET /email-konto` mit ungültigem Token | 401 | ✅ 401 |
| `GET /email-konto` vor erster Konfiguration | 404 „kein Postfach verbunden" | ✅ 404 (erwartetes Verhalten, kein Bug) |
| `POST /internal/email/poll` ohne Secret | 403 | ✅ 403 |
| `PUT /email-konto` mit Passwörtern (initial) | 200, Passwort nicht im Response | ✅ 200, `imap_passwort`/`smtp_passwort` fehlen in Response |
| `PUT /email-konto` erneut ohne Passwörter (BUG-1-Retest) | 200, bestehendes Passwort bleibt | ✅ 200 (kein 422 mehr) |
| `imap_tls`/`smtp_tls` getrennt übertragen (BUG-1-Retest) | beide Felder unabhängig steuerbar | ✅ bestätigt (imap_tls=false, smtp_tls=true korrekt persistiert) |
| `POST /internal/email/poll` mit korrektem Secret, ungültigem IMAP-Host | `letzter_abruf_status=fehler` + Fehlertext | ✅ bestätigt, Frontend zeigt Banner |

## Was nicht live getestet wurde (Limitation)

- **Kein echter IMAP/SMTP-Server verfügbar** → AC-2 (E-Mail ablegen), AC-3 (Senden), AC-4 (Thread-Zuordnung) und BUG-5 (Tracking-Pixel-Sperre) wurden **nicht** end-to-end gegen einen echten Mailserver getestet. Diese Pfade sind durch die grüne Backend-Testsuite (101 pytest, inkl. Zuordnungs-, Dedupe- und Sanitize-Tests mit gemockten IMAP/SMTP-Clients) abgedeckt — siehe `features/PROJ-4-*.md`, Abschnitt „QA Test Results".
- Rollen-Matrix Monteur (darf keine E-Mail-Daten sehen) wurde **nicht** live nachgestellt (Einladungs-Flow bräuchte E-Mail-Zustellung) — abgedeckt durch bestehende pytest-Rollentests (`require_role`-Guards code-verifiziert).
- Rate-Limiting/Login-Lockout nicht Teil dieses PROJ-4-fokussierten Laufs.

## Bugs

Keine neuen Bugs gefunden. BUG-1 und BUG-5 (Code-Ebene) aus vorherigem QA-Zyklus visuell/live re-bestätigt.

## Fazit

PROJ-4 Browser- und Live-API-Smoke: **bestanden**. Zusammen mit der bereits grünen automatisierten Suite (101 Backend-Tests, Frontend Jest/Typecheck/Build) und der bekannten Limitation (keine echte Mailserver-Verbindung in dieser Umgebung) bleibt die Produktionsfreigabe **YES** unverändert.
