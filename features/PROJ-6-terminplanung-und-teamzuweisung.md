# PROJ-6: Terminplanung und Teamzuweisung

## Status: Approved
**Created:** 2026-08-16
**Last Updated:** 2026-08-18

## Dependencies
- Requires: PROJ-3 — Vorgang und zugehörige Adresse.
- Requires: PROJ-1 — Rollen (Inhaber, Büro, Monteur) und Mandantenkontext.

## Reuse aus ImmoCRM
- Kalenderfenster und Verfügbarkeitsverhalten dienen als Vorlage; Makler-, Besichtigungs- und Buchungslogik wird nicht übernommen.

## Datenmodell-Hinweis (Abgrenzung zu PROJ-3)
PROJ-3 hat bereits ein minimales `vorgang.zugewiesener_nutzer_id` (eine Monteur-Zuweisung auf **Vorgangsebene**, ohne Kalender). PROJ-6 fügt eine **eigenständige 1:n-Struktur auf Terminebene** hinzu: ein `Termin` verweist auf genau einen Vorgang und kann über eine `termin_zuweisung`-Tabelle einem oder mehreren Monteuren zugeordnet werden. Diese Termin-Zuweisung konkurriert nicht mit `vorgang.zugewiesener_nutzer_id`; beide Felder bleiben bestehen und bedienen unterschiedliche Ebenen (Vorgang vs. einzelner Termin). Die PROJ-3-Architektur note ("PROJ-6 legt keine zweite, konkurrierende Datenstruktur an") bezieht sich ausschließlich auf die Vorgangszuweisung und ist damit erfüllt.

## User Stories
- Als Büro möchte ich einen Vorgang als Termin planen und einem oder mehreren Teammitgliedern zuweisen, damit klar ist, wer wann wo ist.
- Als Monteur möchte ich meine eigenen Termine mit Adresse, Kontakt, Anliegen und freigegebenen Anhängen sehen, damit ich meinem Einsatz vorbereitet bin.
- Als Inhaber möchte ich die Termine des kleinen Teams im Tag- und Wochenüberblick sehen, damit ich Auslastung und Lücken erkenne.
- Als Büro möchte ich auf einen Blick sehen, wenn zwei Termine desselben Monteurs sich überschneiden, damit keine Doppelbelegung übersehen wird.

## Acceptance Criteria
- [x] **AC-1 (Anlage/Änderung/Absage):** Büro und Inhaber können einen Termin mit Pflichtfeldern Beginn und Ende, optionaler Adresse, Notiz und einem oder mehreren Teammitgliedern (Rolle `Monteur` im eigenen Mandanten) anlegen, ändern oder absagen. Ein Termin ohne zugewiesenes Teammitglied ist zulässig (Warnung, kein Block).
- [x] **AC-2 (Kalenderansicht):** Die Kalenderansicht stellt pro Teammitglied eine Spalte (Woche) bzw. Zeile (Tag) dar und deckt Tag- und Wochenansicht für maximal drei aktive Teammitglieder ab. Sind mehr als drei Monteure im Mandanten aktiv, kann der Betrachter die angezeigten Monteure per Auswahl auf bis zu drei begrenzen (Standard: zuletzt zugewiesene).
- [x] **AC-3 (Vorgangsbezug):** Ein Termin verweist auf genau einen Vorgang (`termin.vorgang_id`, FK `ON DELETE RESTRICT`); ein Vorgang kann mehrere Termine haben. Ein Termin ohne gültigen, dem Mandanten gehörenden Vorgang wird mit `422` abgelehnt.
- [x] **AC-4 (Konfliktwarnung, nicht-blockierend):** Beim Anlegen oder Verschieben wird für jedes zugewiesene Teammitglied geprüft, ob es im selben Zeitfenster (`neuer_beginn < anderer_ende` UND `neuer_ende > anderer_beginn`) bereits einen nicht-abgesagten Termin hat. Ist das der Fall, wird der Termin **trotzdem gespeichert**, die Antwort enthält `konflikt: true` (Liste der betroffenen Teammitglieder), und die Oberfläche markiert die Überschneidung rot. Die Prüfung gilt nur pro Teammitglied, nicht mandantenübergreifend.
- [x] **AC-5 (Monteursicht):** Monteure sehen ausschließlich Termine, denen sie zugewiesen sind. Sichtbar sind Adresse, Kontakt, Anliegen und freigegebene Anhänge; Preis- und Rechnungsdaten sind ausgeblendet. Ein Monteur kann keine Termine anlegen, ändern oder absagen (Schreibzugriff verweigert mit `403`).
- [x] **AC-6 (Statuswechsel):** Das Anlegen eines nicht-abgesagten Termins setzt den Vorgang auf „Termin geplant“. Wird der letzte nicht-abgesagte Termin eines Vorgangs abgesagt und existiert kein weiterer offener Termin, wird der Vorgangsstatus auf seinen vorherigen Wert zurückgesetzt; die Rücksetzung wird in der Vorgangshistorie dokumentiert. Bleibt ein weiterer offener Termin bestehen, bleibt der Status „Termin geplant“.
- [x] **AC-7 (Validierung):** Beginn und Ende sind Pflichtfelder; es gilt `ende > beginn`. Verletzungen führen zu `422`. Alle Zeitangaben werden einheitlich als Zeitzone `Europa/Berlin` interpretiert und gespeichert.

## Edge Cases
- Termin ohne vollständige Adresse ist erlaubt, aber als „Adresse offen" markiert; die Adresse kann die Objektadresse des Vorgangskunden oder Freitext sein.
- Eine Absage entfernt den Termin nicht aus der Historie; ein abgesagter Termin wird in der Kalenderansicht ausgegraut dargestellt und bleibt in der Vorgangshistorie nachvollziehbar.
- Deaktivierte Nutzer können einem Termin nicht neu zugewiesen werden; bestehende Zuweisungen bleiben nachvollziehbar (der Termin bleibt sichtbar, die Zuweisung ist als inaktiv gekennzeichnet).
- Zeitzonen werden für alle Termine einheitlich als Europa/Berlin behandelt; eine Überschneidungsprüfung vergleicht stets in derselben Zeitzone.
- Ein Termin mit Beginn in der Vergangenheit ist anlegbar (kein Hartblock); die Ansicht markiert vergangene Termine als „vergangen".
- Die Konfliktprüfung (AC-4) greift nur bei nicht-abgesagten Terminen desselben Teammitglieds; abgesagte Termine erzeugen keinen Konflikt.
- Löschen eines Vorgangs mit bestehenden Terminen ist über die FK-Regel (`ON DELETE RESTRICT`) auf Datenbankebene blockiert, solange Termine auf ihn verweisen (entspricht der Löschsperrenlogik aus PROJ-3).

## Technical Requirements
- Mobile: Tagesansicht ist ab 375 px bedienbar (Monteuransicht primär mobil).
- Performance: Wochenansicht lädt nur den sichtbaren Zeitraum (kein vollständiges Jahr im Speicher).
- Security: Schreibende Endpunkte (`POST/PATCH/DELETE` Termin, Termin-Zuweisung) tragen `require_role("Buero","Inhaber")`; Monteur-Lesezugriff wird serverseitig auf zugewiesene Termine begrenzt (analog PROJ-3-Muster, `403` bei fremdem Termin). Mandantentrennung über `mandant_id` + RLS wie in PROJ-1/PROJ-3.

---

<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
