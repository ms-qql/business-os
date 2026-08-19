# Schwarm-Lessons-Learned

Lebendes Dokument über den mehrstufigen Koordinator-Schwarm-Ansatz
(Coordinator → Product Architect → Frontend/Backend Developer → QA → Deploy)
bei business_os. Ergänzt `docs/koordination-probleme.md` (Befundbericht aus dem
ersten Lauf, PROJ-1) um den zweiten Lauf (PROJ-2) und die daraus gezogenen
Konsequenzen für künftige Läufe.

---

## Verbindliche Nutzer-Vorgaben ab jetzt (2026-08-17)

1. **Freigabe-Gate verschoben.** Im Schwarm-Modus (Koordinator orchestriert ein
   Feature Ende-zu-Ende) übernimmt der Koordinator die Freigaberolle des
   Nutzers für Spec → Architektur → Frontend/Backend → QA. Der Nutzer wird
   **erst am Deploy-Gate** eingebunden.
2. **QA fixt statt nur zu dokumentieren.** Critical/High/Medium-Bugs aus der
   QA-Phase lässt der Koordinator selbst durch die Spezialisten fixen und neu
   verifizieren (Fix-Retest-Loop), ohne Nutzer-Rückfrage. Nur Low-Bugs bleiben
   dokumentiert, ungefixt.
3. **Gilt nur für Schwarm-Läufe.** Ruft der Nutzer einen `/abc-*`-Skill
   direkt und einzeln auf (ohne Koordinator-Kontext), gelten dessen normale
   Human-in-the-Loop-Checkpoints unverändert.
4. **Offen, noch nicht umgesetzt:** Frontend- und Backend-Entwicklung sollen im
   Schwarm-Modus in **eigenen Terminal-Sessions** mit eigenem Agenten-Set
   laufen (wie in `.claude/rules/agents/*.md` beschrieben) — nicht als
   Task/Subagent innerhalb der Koordinator-Session. Siehe „Abweichung vom
   Zielbild" unten.

---

## Lauf 2 (PROJ-2): Was besser lief als Lauf 1

Bezogen auf die P1–P7-Befunde aus `koordination-probleme.md` (Lauf 1, PROJ-1):

- **P4 (Vertrag zu grob für Feldnamen)** — diesmal explizit adressiert: QA hat
  Frontend- (`nextjs_app/lib/api/public.ts`, `website-settings.ts`) und
  Backend-Schemas (`backend/app/features/website/schemas.py`) Feld für Feld
  gegeneinander geprüft, nicht nur den Prosa-Vertrag gelesen. Ergebnis: exakte
  Übereinstimmung, keine Laufzeit-Mismatches wie in Lauf 1.
- **P7 (vier Statusquellen laufen auseinander)** — Write-then-verify auf
  `features/INDEX.md` und Spec-Header wurde bei jedem Übergang konsequent
  durchgezogen; keine Divergenz beobachtet.
- **Unabhängige Verifikation statt Selbstauskunft (P3 partiell behoben)** —
  beim Fix-Retest von SEC-1 hat der QA-Agent nicht nur den Dev-Test gelesen,
  sondern einen eigenen Angriffsversuch geschrieben und ausgeführt (inkl.
  Canary-String-Grep gegen das Client-Bundle, um ein Secret-Leak
  auszuschließen). Das ist der Verifikationsstandard, den wir beibehalten
  sollten.

## Lauf 2 (PROJ-2): Was noch fehlt / neu auffiel

### Abweichung vom Zielbild (Nutzer-Punkt 4 oben)

Frontend, Backend, QA und alle Bugfixes liefen als `Agent`-Tool-Subagents
**innerhalb derselben Koordinator-Session**, nicht als eigene Terminal-Sessions
mit eigenem Rollen-Prompt (`frontend-dev.md`, `backend-dev.md`,
`qa-engineer.md`) wie im README (`.claude/rules/agents/README.md`)
vorgesehen. Funktional lief es (klare Auftragsbriefings, Ergebnisse kamen
sauber zurück), aber es ist nicht das vom Nutzer gewünschte
Isolationsmodell — vermutlich, weil aus der Koordinator-Session heraus kein
Mechanismus genutzt wurde, um echte Peer-Terminal-Sessions zu öffnen und zu
adressieren (vgl. P1/P2 aus Lauf 1: Koordinator hatte dort keinen
Dispatch-Kanal zu Peer-Sessions). Zu klären: welches Werkzeug/welcher
Mechanismus in dieser Umgebung tatsächlich neue, eigenständige Terminal-Sessions
für Frontend/Backend öffnen kann, die der Koordinator dann wie in
`README.md` beschrieben anschreibt statt sie als Subagent zu spawnen.

### P6 (Testbeleg trägt nicht) — in neuer Form wieder aufgetaucht

Lauf 1: pytest lief gegen SQLite statt Postgres, RLS ungetestet. Lauf 2: alle
automatisierten Tests (Backend `pytest`, Frontend `tsc`/`next build`) waren
grün und QA hat sie mehrfach verifiziert — trotzdem brach die Produktion an
drei Stellen, die kein Test abdeckte:

1. **`python-multipart` fehlte in `requirements.txt`** — im
   Dashboard-Conda-Env transitiv über ein anderes Paket vorhanden, in einem
   sauberen Container-Build nicht. Lokale/QA-Testumgebung ≠ Produktions-Image.
2. **`APP_HOST` nicht durch `docker-compose.yml` durchgereicht** — Next.js-
   Middleware-Routing-Logik, die kein Unit-/Integrationstest je mit einem
   echten fremden Hostnamen aufgerufen hat.
3. **`INTERNAL_PROXY_SECRET` nicht gesetzt** — der reale Next.js→Backend-
   Rewrite-Pfad mit echten HTTP-Headern wurde nie end-to-end getestet;
   pytest prüft die Backend-Logik direkt bzw. über `TestClient`, nie die
   tatsächliche Proxy-Kette. Zusätzlich verschleiert: die zuerst getestete
   Domain (die interne App-Domain) durchläuft diesen Code-Pfad gar nicht
   (Bypass über `APP_HOSTS`), sodass der Fehler erst bei der ersten echten
   Mandanten-Domain sichtbar wurde.

**Muster:** Alle drei Lücken liegen an der Grenze zwischen „Code ist korrekt"
und „Deploy-Infrastruktur transportiert das Ergebnis korrekt". Dev-Env,
Testumgebung und Produktions-Container liefen mit unterschiedlichen
Abhängigkeiten/Umgebungsvariablen, ohne dass ein Gate das automatisch
aufgedeckt hätte. QA hat inhaltlich sauber gegen die Spec getestet — aber
nicht gegen einen sauberen, produktionsnahen Container-Build mit exakt den
Env-Vars, die Dokploy tatsächlich setzt.

**Fixrichtung für künftige Läufe:** Vor dem Deploy-Gate einen echten
`docker compose build` (nicht nur `pytest`/`npm run build`) lokal/CI gegen ein
Env-File mit allen in `.env.example` gelisteten Variablen laufen lassen —
das hätte den `python-multipart`-Crash sofort gefangen (Container startet gar
nicht). Für `APP_HOST`/`INTERNAL_PROXY_SECRET` bräuchte es einen echten
End-to-End-Smoke-Test gegen eine zweite, nicht-App-Domain — das ist im
`abc-deploy`-Skill als Schritt 9 vorgesehen, wurde aber in diesem Lauf erst
nach dem Deploy und nur reaktiv (durch den Nutzer gemeldet) durchgeführt statt
proaktiv als Teil des Deploy-Checklists.

### Neue Erkenntnis: „Approved"/"Deployed" ist keine Garantie für Nutzbarkeit

Nach QA-Freigabe und erfolgreichem `git push` folgten **drei** weitere
Incident-Runden (fehlende Dependency, fehlendes Domain-Routing-Env,
fehlendes Proxy-Secret) plus eine echte Scope-Lücke (Domain-Zuweisung war
gar nicht baubar — kein Schreibpfad existierte). Der `abc-deploy`-Skill kennt
zwar Rollback und eine Gotchas-Tabelle, aber keinen strukturierten
Post-Deploy-Vorfall-Loop innerhalb desselben Laufs. In dieser Session wurde
das improvisiert (Diagnose → Fix-Agent → Push, mehrfach wiederholt). Für
künftige Läufe wäre ein leichtgewichtiger „Incident"-Modus sinnvoll, der
genau diesen Diagnose-Fix-Verify-Push-Zyklus als benannten Schritt kennt,
statt dass der Koordinator ihn jedes Mal neu improvisiert.

### Neue Erkenntnis: Produktentscheidung fehlte im Tech Design

Die Domain-Zuweisung (wer darf einem Mandanten welche öffentliche Domain
geben) war im Tech Design nur als Datenmodell-Feld beschrieben, nie als
Verantwortlichkeit/Workflow geklärt. Das fiel erst auf, als der Nutzer nach
dem Deploy fragte „welche URL hat die öffentliche Website". Das ist keine
Vertragsverletzung (der Vertrag hat dazu geschwiegen), aber eine Lücke, die
`/abc-architecture` oder `/abc-review-architecture` hätte auffangen sollen,
bevor QA/Deploy erreicht wird — QA prüft gegen Akzeptanzkriterien, aber „wer
weist eine Domain zu" stand in keinem Akzeptanzkriterium.

### Token/Auth für Schwarm-Sessions

Nutzer musste einmalig ein Token generieren, damit Sessions laufen konnten
(vgl. P1 aus Lauf 1: Koordinator-Session hatte keinen eigenen Kanal/Token).
Unklar, ob das dauerhaft gilt oder pro Lauf wiederholt werden muss — aus
Koordinator-Sicht nicht prüfbar. **Offene Frage an den Nutzer/die
Infrastruktur**, nicht durch diese Session lösbar.

---

## Zusammenfassung: was für Lauf 3 zu tun war (Stand nach Lauf 2)

1. Mechanismus klären, mit dem der Koordinator echte Peer-Terminal-Sessions
   für Frontend/Backend öffnet (statt Agent-Subagents in der eigenen Session).
2. Deploy-Checkliste um einen echten `docker compose build` gegen
   vollständiges `.env.example`-Set ergänzen, VOR dem Push.
3. Deploy-Skill um einen benannten Post-Deploy-Smoke-Test gegen eine
   zweite (Nicht-App-)Domain ergänzen, wenn das Feature Domain-Routing
   einführt — nicht erst reaktiv nach Nutzer-Meldung.
4. `/abc-architecture` / `/abc-review-architecture` prüfen lassen, ob jede
   im Datenmodell genannte Entität auch einen klaren Schreibpfad/Owner hat,
   nicht nur einen Lesepfad.
5. Swarm-Freigabe-Gate wie oben festgelegt: Koordinator entscheidet bis QA
   inklusive Fix-Loop, Nutzer erst am Deploy-Gate.

**Umgesetzt in Lauf 3 (im aktuellen `abc-coordinate`-Skill):** Punkt 2
(Pre-Deploy-Build-Gate als eigener Schritt 6) und Punkt 4 (Owner-Check als
Architektur-Zusatzschritt) sind jetzt fester Bestandteil des Skills. Punkt 1
(echte Peer-Sessions) ist weiterhin **nicht** gelöst — siehe unten, diesmal
mit konkreterem Befund statt nur der offenen Frage.

---

## Lauf 3 (PROJ-3): Was gut lief

- **Vertrag-zuerst hat gehalten.** Architektur legte API-Vertrag +
  Schreib-Owner-Tabelle fest; Backend/Frontend liefen parallel dagegen.
  Am Ende nur 1 Konflikt (Feldnamen-Drift), kein Deadlock.
- **Fix-Retest-Loop ohne Nutzer-Eingriff funktionierte wie vorgesehen.**
  Backend-Crash (kaputter Import) → mit File:Line-Beleg zurückgewiesen →
  gefixt → grün. QA-Bug (BUG-1) genauso: gefixt → nur der Bug retestet,
  nicht die ganze Suite neu.
- **Unabhängige Verifikation durch den Koordinator zahlte sich aus.** Ein
  Agent meldete „grün"; der Koordinator ließ `pytest`/`docker compose build`
  trotzdem selbst laufen und deckte damit einen Bruch auf, der im
  Agent-Report (vor dessen Crash) nicht sichtbar gewesen wäre.
- **Neu in Lauf 3: Pre-Deploy-Build-Gate** (`docker compose build` gegen
  volle `.env.example`) lief als eigener Schritt vor `abc-deploy` — genau
  wie aus Lauf 2 abgeleitet. Fing diesmal nichts, aber der Schritt selbst
  ist jetzt etabliert.
- **QA als Subagent in der Koordinator-Session ist unproblematisch**, weil
  gleiches Modell wie der Koordinator selbst — anders als bei
  Frontend/Backend (siehe unten). Der Fix-Verify-Zyklus über QA lief sauber
  und sollte so bleiben.
- **Deploy-Gate beim Menschen hat gehalten** — kein Schritt Richtung
  main/push ohne explizite Nutzer-Ansage.

## Lauf 3 (PROJ-3): Neue/bestätigte Lücken

### 1. Branch-Rückfrage nach der Architektur-Phase (neu, Nutzer-Punkt)

Der Nutzer wurde nach `/abc-architecture` gefragt, welchen Branch er nehmen
möchte (Feature-Branch vs. `dev` vs. `main`) — das ist im Schwarm-Modus eine
unnötige Rückfrage. Für einen Koordinations-Schwarm-Lauf ist die sauberste
Trennung **immer ein dedizierter Feature-Branch** (`specs/PROJ-X-…`); es gibt
in diesem Modus keinen Grund, `dev` oder `main` zur Wahl zu stellen. Der
`abc-coordinate`-Skill sollte das **festlegen statt fragen** — die
Branch-Wahl aus `abc-architecture`/`abc-deploy` (Step 2.5) ist für den
Einzel-Skill-Aufruf richtig, aber im Coordinate-Overlay ein
Freigabe-Punkt zu viel.

### 2. Frontend/Backend als teure Subagents im selben (Claude-)Kontingent — größtes Problem

Frontend- und Backend-Entwicklung liefen als `Agent`-Subagents **innerhalb
der Koordinator-Session**, mit demselben (Claude-)Modell und demselben
API-Token-Kontingent wie der Koordinator. Konkret beobachtet:

- Zwei parallele Subagents haben in Summe so viel vom Kontingent verbraucht,
  dass beide **gleichzeitig am Session-Limit** hingen und mit
  „terminated early" abbrachen (Backend mitten in einer fehlerhaften
  Vertrags-Umschreibung, Frontend mitten in der Nacharbeit).
- Es gibt in diesem Setup **keine güstigere/andere Modell-Klasse** für
  Frontend/Backend als für den Koordinator selbst — anders als vom Nutzer
  gewünscht (Wunsch: Frontend/Backend auf einem billigeren, nicht-Claude-
  Agenten laufen lassen können, Koordinator bleibt Claude).
- Nutzer-Beobachtung: der Wechsel zwischen Unterprojekten „3" und „3.1" hat
  funktioniert (`SendMessage`/Resume auf eine bestehende Session), aber ein
  Wechsel zu **neuen**, separaten Sessions/Agenten für Frontend/Backend nicht
  (bzw. wurde im Zweifel gar nicht erst versucht). Hypothese des Nutzers:
  das Werkzeug kann zwischen **bestehenden** Sessions hin- und herschalten
  (`SendMessage` an eine laufende/pausierte Session), aber **keine neue
  Session mit anderem Agenten/Modell** aus der Koordinator-Session heraus
  öffnen. Falls das zutrifft: Frontend- und Backend-Agent müssten **zu
  Beginn des Laufs** (z. B. in Step 4 des Skills, vor dem ersten Dispatch)
  bereits als eigene, dauerhafte Sessions angelegt werden — mit jeweils
  eigenem Rollen-Kontext und ggf. eigenem (günstigeren) Modell —, statt sie
  bei Bedarf per `Agent`-Tool aus der Koordinator-Session heraus zu spawnen.
  Das deckt sich mit der seit Lauf 2 offenen Isolationslücke (Punkt 1 oben),
  liefert jetzt aber eine konkretere Fixrichtung: **vorab angelegte,
  langlebige Peer-Sessions statt Spawn-on-demand.**
- Klarstellung zu „Unterprojekte 3/3.1 wurden angelegt, aber nicht
  genutzt": der Koordinator-Kontext kannte offenbar eine Struktur für
  mehrere Unterprojekte/Sessions, hat davon aber nur zwei IDs (`3`, `3.1`)
  tatsächlich bespielt statt je eine pro Rolle (Architektur, Backend,
  Frontend, QA) konsequent durchzuziehen. Architecture Review lief ebenso
  wie QA direkt im Koordinator statt in einer eigenen Unterprojekt-Session.

### 3. Architecture Review lief im Koordinator, nicht als eigene Rolle

Analog zu Punkt 2, aber weniger kritisch (keine Kontingent-Explosion, weil
kein separater Build/Testlauf nötig war): `/abc-review-architecture` wurde
faktisch vom Koordinator selbst statt von einer Product-Architect-Rolle in
eigener Session ausgeführt. Gleiches Muster wie QA — dort aber bewusst als
„so lassen" bewertet (Punkt „Was gut lief"), weil kein Modell-/Kosten-
Unterschied besteht. Für Architecture Review gilt das vermutlich genauso,
sollte aber im Rahmen der Session-Vorab-Anlage (Punkt 2) konsistent
mitgedacht werden, statt weiter implizit im Koordinator zu laufen.

---

## Zusammenfassung: was für Lauf 4 zu tun ist

1. **Branch-Wahl im Coordinate-Overlay festlegen, nicht erfragen.** Nach
   `/abc-architecture` im Schwarm-Modus immer einen dedizierten
   Feature-Branch (`specs/PROJ-X-…`) verwenden — keine `AskUserQuestion` zu
   `main`/`dev`/Feature-Branch, das ist ein Einzel-Skill-Feature.
2. **Frontend-/Backend-/(optional Architecture-Review-)Sessions vorab
   anlegen, nicht on-demand spawnen.** Klären, ob das verwendete
   Session-Werkzeug tatsächlich nur zwischen bestehenden Sessions
   umschalten kann (nicht neue mit anderem Agenten/Modell öffnen) — falls
   ja, den Skill so umbauen, dass er in einem frühen Schritt (vor dem
   ersten Dispatch an Frontend/Backend) die benötigten Peer-Sessions mit
   je eigenem Rollen-Kontext **einmalig** erzeugt und danach nur noch per
   Resume/`SendMessage` anspricht.
3. **Günstigeres/anderes Modell für Frontend/Backend ermöglichen.** Sobald
   (2) gelöst ist: prüfen, ob die vorab angelegten Peer-Sessions mit einem
   anderen (günstigeren, nicht zwingend Claude-)Agenten konfiguriert werden
   können, damit Frontend-/Backend-Arbeit nicht mehr das
   Koordinator-Kontingent mitverbraucht. QA und Architecture Review dürfen
   weiter im teureren/gleichen Modell wie der Koordinator laufen — dort
   kein beobachteter Schaden.
4. Weiterhin offen aus Lauf 2: Domain-/Schreibpfad-Lücken früh im
   Owner-Check fangen (siehe Ergänzung — inzwischen im Skill, aber
   `GET /users`-artige **abhängige Lesepfade** wurden vom Owner-Check nicht
   erfasst, nur Schreibpfade; für Lauf 4 den Owner-Check um „wer *liest*,
   was zum Schreiben gebraucht wird" erweitern).
5. Rollback-Pfad aus `abc-deploy` mindestens einmal bewusst durchspielen
   (bisher in keinem Lauf nötig/getestet gewesen).
