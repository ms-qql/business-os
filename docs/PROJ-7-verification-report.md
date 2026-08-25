# Verifikationsbericht PROJ-7 Tech Design vs. Code

**1. GET/PATCH /website-settings, POST /website-settings/logo — JA**
`backend/app/features/website/routes.py:69-89`: `GET ""` (L69), `PATCH ""` (L74), `POST "/logo"` (L84), Router-Prefix `/website-settings` (L11). Service/Repo vorhanden (`service.py`, `repository.py`).

**2. PATCH aktiviert Domain automatisch beim Speichern — JA (bestätigt Design-Aussage)**
`service.py:187-192`: wenn `domain` gesetzt, wird `_validate_hostname` + Kollisionscheck aufgerufen, dann `repo.upsert_domain(mandant_id, hostname)`. `repository.py:52-55` (Update-Fall) und `:57-60` (Insert-Fall) setzen **immer `status = 'aktiv'`** — hart codiert, kein separater Aktivierungsschritt. Feld: `website_domains.status` (Spalte `hostname`/`status`, `sql/002_website.sql:20-26`).

**3. GET/PUT /email-konto + POST /email-konto/test — JA**
`backend/app/features/email/routes.py:23-36`: `GET "/email-konto"` (L23), `PUT "/email-konto"` (L28), `POST "/email-konto/test"` (L33). Verschlüsselung via `encrypt_secret`/`decrypt_secret` aus `app.crypto` (`service.py:6,33,35`). Test-Endpoint nimmt `EmailKontoTest`-Payload (nicht gespeicherte Eingabedaten) — unverbindlicher Verbindungstest bestätigt.

**4. Tabelle `website_domains` mit global eindeutigem hostname + Status — JA**
`sql/002_website.sql:20-26`: `hostname TEXT NOT NULL UNIQUE`, `status TEXT ... CHECK (status IN ('aktiv','inaktiv'))`.

**5. Tabelle `email_konto` existiert, `konfiguration_version` fehlt — TEILWEISE (Tabelle ja, Spalte nein — wie Design will)**
`sql/004_email.sql:7-25`: keine Spalte `konfiguration_version`. Design-Erweiterung ist tatsächlich neu.

**6. Tabelle `vorgang` mit kunde/objekt-Referenzen, `ist_test` fehlt — TEILWEISE (Tabelle ja, Spalte nein — wie Design will)**
`sql/003_kunden_vorgaenge.sql:31-47`: `kunde_id`, `objekt_id` vorhanden, keine `ist_test`-Spalte.

**7. RLS-Muster — JA**
Jede mandantengebundene Tabelle: `mandant_id UUID NOT NULL REFERENCES mandanten(id)`, RLS-Policy `FOR ALL USING (mandant_id = current_setting('app.current_mandant_id')::uuid)` (z.B. `sql/002_website.sql:89-90`, `003_kunden_vorgaenge.sql:93-106`, `004_email.sql:81-88`). Server setzt Kontext serverseitig: `backend/app/db.py:58,79,96` — `SELECT set_config('app.current_mandant_id', %s::text, true)`. mandant_id kommt aus JWT/Session (`deps.py:74,80-84` — `session["mandant_id"]`), nicht vom Client.

**8. Rollen Inhaber/Büro/Monteur — JA**
`require_role(*roles)` in `deps.py:87-93` als FastAPI-Dependency. Verwendung z.B. `website/routes.py:70,76,86` (`require_role("Inhaber")`), `email/routes.py:14-15` (`require_role("Buero","Inhaber")`, `require_role("Inhaber")`). 28 Dateien referenzieren die Rollen.

**(a) Routen-Konflikte neue Endpunkte:** Kein Konflikt — Suche nach `/onboarding` im sichtbaren Repo-Code ergab 0 Treffer; existiert nur in der Spec-Markdown selbst. Kein bestehender `onboarding`-Router.

**(b) RLS-Muster:** siehe Punkt 7, Referenzdatei `backend/app/db.py:58/79/96` + jede `sql/*.sql`-Migration.

**(c) Raw SQL vs. ORM:** Raw SQL bestätigt — `db.engine.query(...)`/`db.engine.command(...)` mit `%s`-Parametern (z.B. `website/repository.py:19-29,34-39,52-60`), kein ORM (kein SQLAlchemy-Model o.ä. gefunden).

**(d) Kollision PATCH/Domain:** Ja, direkte Kollision — `PATCH /website-settings` setzt bei jeder übergebenen `domain` automatisch `website_domains.status='aktiv'` (`repository.py:53,59`). Das neue Design (`PUT /onboarding/domain` nur speichert, `POST /onboarding/veroeffentlichen` aktiviert separat) erfordert, dass die bestehende Auto-Aktivierung in `update_website_settings`/`upsert_domain` entfernt oder umgangen wird — sonst würde der alte Pfad weiterhin sofort aktivieren.
