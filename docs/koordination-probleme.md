# Koordination PROJ-79: Befundbericht für einen grundsätzlichen Fix

**Erstellt:** 2026-08-16 · **Anlass:** Feature-Koordination PROJ-1 (business_os)
· **Beobachtungszeitraum:** ein Lauf mit Paketen 1.1 (Backend) und 1.2 (Frontend)

Alle Punkte sind an diesem einen Lauf beobachtet, nicht hypothetisch. Reihenfolge
nach Wurzeltiefe: P1 ist die Ursache, P2–P7 sind, was daraus folgt oder daneben
liegt.

---

## P1 — Der Koordinator hat keinen Kanal zum Dispatcher

**Befund.** Die Koordinator-Session kann das Repo lesen und Peer-Sessions
anschreiben. Sonst nichts. Die Jupiter-API liegt hinter `auth_gate`
(`jupiter/backend/app/main.py:437`); ohne Token antwortet sie 401
(`jupiter/backend/app/deps.py:65`). Paket-Sessions bekommen ein Token injiziert
(im UI als `TOK="eyJhbGci…"` sichtbar), die Koordinator-Session nicht.

**Folge.** Der Koordinator darf urteilen, aber nicht handeln: kein Dispatch, kein
Retry (`POST /coordinator/features/{id}/decision`, `action:"retry"`), kein
Zurückziehen eines falschen Beacons. Die Rolle hat kein Werkzeug. Rückweisungen
enden als Text im Chat und müssen von Hand weitergereicht werden.

**Fixrichtung.** Der Koordinator-Session ein eigenes, eng geschnittenes Token
injizieren — Rechte nur für die Endpunkte, die er tatsächlich braucht
(`feature_plan`, `feature_dispatch`, `decision`, `package_complete`, Lesen des
Feature-Runs). Kein Vollzugriff auf das Nutzerkonto.

---

## P2 — Paket-Zuordnung ist unsichtbar

**Befund.** `ListAgents` liefert Session-Namen, keine Paket-IDs. Innerhalb von
Minuten verschwand `business-os-e6` und `jupiter-0f` wurde zu `jupiter-f6`
(gleicher tmux-Pane, Neustart).

**Folge.** Die Rückweisung für 1.2 ging als Broadcast an alle erreichbaren
Sessions, weil nicht feststellbar war, welche das Paket hält. Eine der drei war
zum Sendezeitpunkt bereits tot — möglicherweise die richtige.

**Fixrichtung.** Adressierung über die Paket-ID (`PROJ-1.2`), nicht über den
Session-Namen. Der Dispatcher kennt die Zuordnung bereits; sie muss dem
Koordinator sichtbar sein und Session-Neustarts überleben.

---

## P3 — Der Beacon ist Selbstauskunft ohne Gate

**Befund.** Paket 1.2 meldete `erfolgreich` mit der Begründung „`next build` grün
(10 Routen, TypeScript ok)" — bei sieben Vertragsbrüchen (siehe P4 und
`features/PROJ-1-mandanten-anmeldung-und-rollen.md:212`). Die Prüfung durch den
Koordinator läuft *nach* dem Beacon und kann ihn nicht entwerten.

**Folge.** Ein Paket definiert seinen Erfolgsbegriff selbst. Nachgelagerte
Pakete bauen auf einem Status auf, den niemand verifiziert hat.

**Fixrichtung.** Beacon bedeutet „fertig zur Prüfung". Der Paketstatus springt
erst durch die Koordinator-Abnahme auf erfolgreich. Der Koordinator braucht
dafür Schreibrecht auf den Status (folgt aus P1).

---

## P4 — Der Vertrag ist zu grob für das, was er entscheiden soll

**Befund.** § „API-Form" der Feature-Spec nennt Pfade und Semantik, aber keine
Feldnamen. Am Übergang 1.1 → 1.2 brachen daraufhin sechs Stellen:

| Stelle | Backend (abgenommen) | Frontend (geliefert) |
|---|---|---|
| `POST /auth/login` | `{access_token, token_type}` | liest `data.user` → `undefined` |
| `GET /auth/me` | `{id, name, role, …}` | erwartet `user_id`, `rolle`, `mandant_name` |
| `GET /users` | `{…, role, status}` | erwartet `rolle`, `aktiv: boolean` |
| `POST /users` | `{name, email, role}` | sendet `rolle` → 422 |
| `PATCH /users/{id}` | `{role?, status?}` | sendet `{rolle?, aktiv?}` → 422 |
| `POST /admin/mandanten` | `{name, owner_name, owner_email}` | sendet `{firmenname, inhaber_*}` → 422 |
| Rollenwert | `"Buero"` | `"Büro"` (Umlaut) → Validierung schlägt fehl |

**Folge.** Alles kompiliert sauber und scheitert erst zur Laufzeit. `next build`
konnte das nicht sehen — daher der falsche Erfolgs-Beacon aus P3. Diese
Fehlerklasse entsteht systematisch, nicht durch Unachtsamkeit.

**Fixrichtung.** Das Vertragsartefakt sollte der OpenAPI-Export des Backends
sein, gegen den das Frontend generiert oder mindestens geprüft wird. Prosa-Verträge
taugen für Semantik und Sicherheitsregeln, nicht für Feldnamen.

---

## P5 — Ein ungültiges Folgepaket reißt ein fertiges mit

**Befund.** Paket 1.2 war als `engine:"claude"` mit `model:"opencode-go/hy3"`
angelegt. Diese Kombination lehnt `manager.py:1688` ab — das Modell gehört zur
generischen CLI-Engine, nicht zu Claude (`is_claude` prüft gegen `VALID_MODELS`,
sonst greift `profile.valid_model()`). Als 1.1 fertig meldete, rief
`package_complete` intern `_schedule` für 1.2 auf, das warf.

**Folge.** 1.1 stand als `failed` da, obwohl sein Code vollständig und getestet
war. Der Fehler des Nachfolgers wurde dem Vorgänger zugerechnet.

**Fixrichtung.** Erfolg eines Pakets darf nicht an der Startbarkeit des nächsten
hängen — `package_complete` persistiert, `_schedule` scheitert separat.
Zusätzlich: Engine/Modell-Kombination beim Anlegen validieren, nicht erst beim
Start.

---

## P6 — Der Testbeleg trägt nicht

**Befund.** 18/18 Tests grün, aber gegen `SqliteEngine` (`backend/app/db.py`).
Die RLS-Policies aus `backend/sql/001_init.sql` laufen dabei nie.

**Folge.** Akzeptanzkriterium 1 (Mandantentrennung, „ein Request kann niemals
Daten eines anderen Mandanten lesen") ist unbelegt, sieht aber belegt aus. Die
Isolation ist nur auf App-Ebene geprüft — genau die Schicht, gegen die RLS
absichern soll.

**Fixrichtung.** Sicherheitskritische Tests gegen dieselbe Engine wie in
Produktion. Eine Test-Engine, die eine Sicherheitsschicht stillschweigend
überspringt, ist gefährlicher als kein Test.

---

## P7 — Vier Statusquellen, die auseinanderlaufen

**Befund.** `features/INDEX.md`, der Spec-Header, der Jupiter-Paketstatus und der
Beacon widersprachen sich im Lauf gegenseitig.

**Fixrichtung.** Eine führende Quelle festlegen, die übrigen daraus ableiten.

---

## Sachstand PROJ-1 bei Abbruch

- **1.1 Backend** — inhaltlich in Ordnung, vom Koordinator geprüft: 11/11
  Vertragsendpunkte verdrahtet, 18/18 Tests selbst gefahren. Offen: die
  RLS-Lücke aus P6.
- **1.2 Frontend** — sieben offene Punkte, unverändert auf Platte. Vollständige
  Fixliste: `features/PROJ-1-mandanten-anmeldung-und-rollen.md:212` (enthält die
  drei Struktur-Punkte; die vier Format-Brüche aus P4 sind dort noch **nicht**
  nachgetragen, sie stehen nur in diesem Bericht).
- **1.3–1.5** — nie gestartet.
