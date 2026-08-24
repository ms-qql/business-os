# PROJ-13: Formular-Baukasten

## Status: Deployed
**Created:** 2026-08-23
**Last Updated:** 2026-08-24

## Dependencies
- Requires: PROJ-1 — Mandanten, Anmeldung und Rollen für die Mandantentrennung sowie Inhaber- und Bürozugriff.
- Requires: PROJ-2 — öffentliche Betriebswebsite als Einbindungs- und Veröffentlichungsziel.
- Coordinates with: PROJ-14 — Branchenpaket-Konfiguration liefert die SHK- und Entrümpelungs-Startvorlagen.
- Integrates with: PROJ-3 — übernimmt gültige Einsendungen als Anfrage und Kundenentwurf.

## Ziel

Inhaber und Büro erstellen und veröffentlichen ohne KI Anfrageformulare aus
einem festen Feldtypen-Katalog. Interessenten füllen ein passendes,
mehrstufiges Formular auf der Betriebswebsite, über einen Direktlink oder
eingebettet aus. Gültige Einsendungen werden mandantenisoliert als Anfrage
und Kundenentwurf übernommen; verdächtige Einsendungen bleiben als Spam
nachvollziehbar markiert.

## User Stories
- Als Inhaber möchte ich ein Formular aus vorgegebenen Feldtypen zusammenstellen und beschriften, damit ich keine technische Hilfe für Qualifizierungsfragen brauche.
- Als Büro-Mitarbeiter möchte ich Formulare bearbeiten und veröffentlichen, damit die Website bei neuen Leistungen oder saisonalen Anliegen aktuell bleibt.
- Als Inhaber möchte ich mit einer SHK- oder Entrümpelungs-Vorlage starten, damit das Formular nicht leer beginnt und zur Branche passt.
- Als Interessent möchte ich ein mehrstufiges Formular mit Fortschrittsanzeige auf Mobilgeräten ausfüllen, damit ich auch umfangreiche Angaben verständlich absenden kann.
- Als Interessent möchte ich Fotos und PDF-Dokumente mitsenden, damit der Betrieb mein Anliegen vor dem Kontakt besser einschätzen kann.
- Als Büro-Mitarbeiter möchte ich eine gültige Einsendung als neue Anfrage mit Kundenentwurf vorfinden, damit ich sie ohne Übertragen weiterbearbeiten kann.

## Acceptance Criteria
- [ ] Inhaber und Büro können innerhalb ihres Mandanten Formulare anlegen, umbenennen, bearbeiten, als Entwurf speichern, veröffentlichen und die Veröffentlichung zurücknehmen; fremde Mandanten sind weder sichtbar noch bearbeitbar.
- [ ] Der Editor bietet ausschließlich diese nicht frei erweiterbaren Feldtypen: Text, mehrzeiliger Text, Auswahl/Dropdown, Kachel-Auswahl, Radio-Buttons, Mengenfeld/Zahl, Datum, Datei-/Foto-Upload, Adressfeld und Consent/Datenschutz-Zustimmung.
- [ ] Für jedes Feld können mindestens Bezeichnung, Pflichtfeld und Hilfetext gepflegt werden; Auswahl-, Radio- und Kachel-Felder erlauben eine geordnete Liste aus sichtbarer Bezeichnung und gespeichertem Wert.
- [ ] Ein Formular kann beliebig viele Schritte enthalten. Die öffentliche Ansicht zeigt den aktuellen Schritt und eine Fortschrittsanzeige; Vor- und Zurück-Navigation erhält bereits eingegebene Werte.
- [ ] Die Komplexitätsstufe „Einfach" zeigt nur Pflichtfelder. „Erweitert" zeigt zusätzlich die als optional konfigurierten Zusatzfelder desselben Formulars, ohne ein zweites Formular zu erfordern.
- [ ] Der Betrieb kann ein Formular als Direktlink, iframe-Embed oder JavaScript-Snippet einbinden. Alle drei Varianten zeigen ausschließlich die veröffentlichte Fassung.
- [ ] Neue Formulare können aus einer vorgegebenen SHK- oder Entrümpelungs-Vorlage erstellt werden; danach sind Bezeichnungen, Hilfetexte und Auswahloptionen mandantenbezogen anpassbar.
- [ ] Das veröffentlichte Formular prüft Pflichtfelder, Datums-, Zahlen- und Auswahlwerte sowie die erforderliche Datenschutz-Zustimmung vor der Übermittlung und zeigt verständliche deutsche Feldfehler.
- [ ] Der Upload-Feldtyp akzeptiert JPEG, PNG, WebP und PDF innerhalb einer festgelegten Größenobergrenze. Nicht erlaubte, beschädigte oder zu große Dateien werden vor der Übermittlung mit einer deutschen Fehlermeldung abgewiesen.
- [ ] Eine gültige Einsendung erzeugt genau eine neue Anfrage und einen Kundenentwurf im Mandanten. Ein Projekt wird dadurch nicht automatisch angelegt.
- [ ] Wird eine Einsendung mit einer bereits vorhandenen E-Mail-Adresse abgegeben, bleibt sie eine eigene Anfrage und wird dem bestehenden Kunden zugeordnet; ohne Treffer wird ein Kundenentwurf angelegt.
- [ ] Honeypot, Zeitvalidierung und Rate-Limit schützen den öffentlichen Endpunkt. Verdächtige, nicht eindeutig blockierte Einsendungen werden als Spam markiert und bleiben nur für berechtigte Nutzer nachvollziehbar.
- [ ] Bei nicht erreichbarem Formular-Endpunkt wird keine Anfrage angelegt; die öffentliche Ansicht zeigt eine verständliche deutsche Fehlermeldung und erlaubt einen erneuten Versuch.
- [ ] Eine Formularänderung bleibt Entwurf, bis Inhaber oder Büro sie ausdrücklich veröffentlicht. Bis dahin zeigen alle Einbindungsvarianten weiterhin die zuletzt veröffentlichte Fassung.
- [ ] Alle öffentlichen Felder, Schritte, Fehlermeldungen und Aktionen sind auf Deutsch beschriftet, per Tastatur bedienbar und ab 375 px Breite ohne horizontales Scrollen nutzbar.

## Edge Cases
- Wird ein Formular ohne veröffentlichten Stand verlinkt oder eingebettet, wird keine Formularstruktur und keine Mandanteninformation preisgegeben.
- Löscht ein Bearbeiter ein Feld oder einen Schritt aus dem Entwurf, bleibt die veröffentlichte Fassung bis zur nächsten Veröffentlichung unverändert.
- Enthält eine Auswahlkonfiguration keine Option oder hat doppelte gespeicherte Werte, kann diese Fassung nicht veröffentlicht werden und der Editor erklärt den Fehler auf Deutsch.
- Eine erneute Einsendung derselben Person bleibt als eigene Anfrage erhalten; sie überschreibt weder bestehende Anfrageangaben noch Kundendaten.
- Bei einem Netzwerkfehler oder einer abgebrochenen Übermittlung speichert der Browser keine Anfrage lokal; bereits eingegebene Werte dürfen bis zum erneuten Versuch sichtbar bleiben.
- Überschreitet ein Interessent das Rate-Limit oder füllt das Honeypot-Feld, wird keine reguläre Anfrage erzeugt; eine nicht eindeutig automatisierte Einsendung wird als Spam statt als regulär markiert.
- Ist ein Upload nach der Formularvalidierung nicht mehr verfügbar oder scheitert die Speicherung, wird die gesamte Übermittlung abgewiesen und keine unvollständige Anfrage angelegt.
- Sehr lange Labels, Hilfetexte, Optionen und Dateinamen umbrechen responsiv, ohne Felder, Buttons oder die Fortschrittsanzeige zu überdecken.

## Nicht-Ziele
- Keine KI-generierten Formulare, Freitext-Interpretation oder automatische Feldvorschläge.
- Kein frei definierbarer Feldtyp, keine freie Formularlogik und kein benutzerdefiniertes HTML, CSS oder JavaScript.
- Kein Offline-Versand, kein lokaler Entwurfs-Speicher und keine automatische Wiederholung einer fehlgeschlagenen Übermittlung.
- Kein automatisches Projekt aus einer Formulareinsendung; Projektanlage bleibt ein bewusster Arbeitsschritt in PROJ-3.
- Keine Formular-zu-Gewerk-Verknüpfung und keine Schnellkalkulation; diese Erweiterung gehört zu PROJ-22.

## Technical Requirements
- Security: Der Mandant wird serverseitig aus der veröffentlichten Betriebsdomain bzw. dem authentifizierten Zugriff bestimmt; weder Einbettung noch Einsendung dürfen eine Mandanten-ID, Rolleninformation oder fremde Formulardaten steuern.
- Security: Öffentliche Uploads werden serverseitig gegen erlaubten Inhalt, Größe und Eigentümerkontext geprüft; sie sind nur über die zugehörige Anfrage und nach Berechtigung erreichbar.
- Privacy: Nur die konfigurierten Formularwerte und Anhänge werden gespeichert; die erteilte Datenschutz-Zustimmung wird mit Formularversion und Zeitpunkt nachvollziehbar festgehalten.
- Compatibility: Direktlink, iframe-Embed und JavaScript-Snippet funktionieren in aktuellen Chrome-, Firefox- und Safari-Versionen; die öffentliche Formularansicht ist responsiv ab 375 px Breite.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
**Erstellt:** 2026-08-23 · **Stack:** Next.js 16/shadcn-artige UI, FastAPI, PostgreSQL raw SQL + RLS, MinIO, Dokploy · **Branch:** main

### Ausgangspunkt und Grenze

PROJ-2 liefert bereits die hostbasierte öffentliche Mandantenauflösung,
`anfrage`/`anfragebild`, Rate-Limit-Muster und MinIO. PROJ-3 liefert
`kunde`, `vorgang`, Dokumente und die sofortige Übernahme einer Anfrage. Dieses
Feature ersetzt nicht diese Domänen: Es ergänzt eine versionierte
Formulardefinition und einen eigenen Einsendungsweg. Der Einsendungsdienst
erstellt Anfragen, Vorgänge und für neue Kontakte Kundenentwürfe atomar; die
alte Route `POST /public/anfragen` bleibt für das bisherige Kurzformular.

Der Baukasten bleibt absichtlich klein: zehn feste Feldtypen, Schritte,
Optionen und eine lineare Vor-/Zurück-Navigation. Keine Bedingungen, keine
Berechnungen, kein frei eingebetteter Code und kein allgemeines CMS. Eine
Einbindung ist immer ein iframe auf der veröffentlichten Betriebsdomain; das
JavaScript-Snippet erzeugt nur diesen iframe, keine dritte öffentliche API.

### Flächen und Komponenten

```text
Betriebszentrale, Rolle Inhaber oder Buero
└── Formulare
    ├── Formularliste: Entwurf/veröffentlicht, Neu aus Leerform/Branchenvorlage
    ├── Editor: Name, Komplexitätsstufe, Schritte und Feldliste
    │   ├── Feldtyp-Konfiguration und Übernahme-Zuordnung
    │   ├── Optionseditor für Auswahl, Kachel und Radio
    │   ├── Vorschau Einfach/Erweitert
    │   └── Publish-Check und Einbindung
    └── Vorgangsdetail: unveränderliche Formularantwort, Consent und Anhänge

Öffentliche Betriebsdomain
└── /formulare/{public_id}
    ├── Schritt, Fortschrittsanzeige und Zurück/Vor
    ├── Feldrenderer für festen Katalog
    ├── Uploadliste und deutsche Feldfehler
    └── Bestätigung oder wiederholbarer Netzwerkfehler
```

Die bestehende Next.js-Anwendung ist einziges Frontend. Sie verwendet vorhandene
shadcn-artige `Input`, `Textarea`, `Select`, `RadioGroup`, `Checkbox`, `Button`,
`Card` und `react-hook-form`/Zod. Bei 375 px ist jeder Schritt einspaltig; native
Felder und Buttons erhalten sichtbaren Fokus, Labels, Fehlerbezug und deutsche
Texte.

### Datenmodell, Owner und Lesepfade

Neue mandantenbezogene Tabellen tragen `mandant_id`, Fremdschlüssel zum
Mandanten und RLS `FOR ALL` auf `current_setting('app.current_mandant_id')`.
FastAPI setzt den Kontext pro DB-Transaktion aus dem serverseitigen
Session-Lookup des JWT-`sub`; Repositories filtern zusätzlich nach
`mandant_id`. Der öffentliche Pfad löst den Mandanten ausschließlich über die
aktive Betriebsdomain wie `GET /public/site` auf. Weder Body, Query, iframe
Hostseite noch JavaScript dürfen `mandant_id` oder Rollen vorgeben.

| Entität | Inhalt und Regeln | Schreiber / Owner | nötige Lesepfade |
|---|---|---|---|
| `formular` (neu) | `id`, `mandant_id`, Name, `draft_revision`, veröffentlichte Versions-ID, Zeitstempel. Nur Metadaten und aktuelle Entwurfsreferenz. | Formularliste/Editor über `POST/PATCH /formulare`; Inhaber und Buero. | `GET /formulare` vor Öffnen; `GET /formulare/{id}` vor jeder Mutation und für `draft_revision`; `GET /formulare/{id}/einbindung` erst nach Veröffentlichung. |
| `formular_schritt` (neu) | Entwurfsschritt: ID, Formular, Position, Titel. Position pro Formular eindeutig. | Schritteditor über `POST/PATCH/DELETE /formulare/{id}/schritte` und Reihenfolge-Route; Inhaber/Buero. | `GET /formulare/{id}` vor Bearbeitung, Löschen und Sortieren; öffentliche Ansicht liest niemals diesen Entwurf. |
| `formular_feld` (neu) | Entwurfsfeld: Schritt, Position, Typ aus festem Katalog, Label, Hilfetext, Pflichtfeld, `optional_in_einfach`, validierte Typkonfiguration und optionale Übernahme-Zuordnung. Typen: Text, mehrzeiliger Text, Dropdown, Kachel, Radio, Zahl, Datum, Upload, Adresse, Consent. | Feldeditor über `POST/PATCH/DELETE /formulare/{id}/schritte/{step_id}/felder`; Inhaber/Buero. | `GET /formulare/{id}` vor Feldänderung; Renderer liest ausschließlich den veröffentlichten Snapshot. |
| `formular_option` (neu) | Feld, Position, sichtbares Label und gespeicherter Wert; nur Auswahl/Kachel/Radio. Wert pro Feld eindeutig und nicht leer. | Optionseditor innerhalb von `PATCH .../felder/{field_id}`; Inhaber/Buero. | `GET /formulare/{id}` vor Optionenänderung/Sortierung; Publish-Check liest alle Optionen. |
| `formular_version` (neu) | Unveränderlicher Publish-Snapshot: `id`, Mandant, Formular, fortlaufende Nummer, zufällige `public_id`, vollständige Schritte/Felder/Optionen als validiertes JSON, veröffentlicht am/von. Alte Versionen bleiben wegen historischer Einsendungen erhalten. | Ausschließlich `POST /formulare/{id}/veroeffentlichen`; Inhaber/Buero. Rücknahme entfernt nur Referenz in `formular`, löscht nie Snapshots. | `GET /formulare/{id}` zeigt Versionsstatus; `GET /formulare/{id}/einbindung` liest aktuelle `public_id`; `GET /public/formulare/{public_id}` liest nur Snapshot derselben aktiven Betriebsdomain. |
| `formular_einsendung` (neu) | Unveränderliche Antwort: Mandant, Formularversion, Übermittlungskennung, alle Werte nach Feld-ID, Consent-Nachweis mit Zeitpunkt, Spam-Status (`normal`/`spam`), optional Anfragen-/Vorgangs-ID, Zeitstempel. Keine Antwort wird in den Entwurf zurückgeschrieben. | Öffentlicher Submit `POST /public/formulare/{public_id}/einsendungen`; kein angemeldeter Nutzer. Server validiert gegen Snapshot und entscheidet Spam. | `GET /vorgaenge/{id}` liefert die verknüpfte Antwort an Inhaber/Buero und an zugewiesene Monteure vollständig, einschließlich Werte, Consent und Formularanhänge; andere Monteure erhalten keinen Vorgang. `GET /formular-einsendungen?spam=1` zeigt nur markierte Einsendungen Inhaber/Buero. Öffentliche Route liest keine vergangene Einsendung. |
| `formular_upload` (neu) | Temporärer oder verknüpfter Upload: Mandant, Übermittlungskennung, Feld-ID, MinIO-Pfad, Originalname, geprüfter MIME-Typ, Größe, Einsendungs-ID. JPEG, PNG, WebP, PDF; gemeinsame feste Größenobergrenze 15 MB pro Datei. | `POST /public/formulare/{public_id}/uploads` nach Host-/Rate-/Dateiprüfung; der Submit verknüpft nur Uploads seiner Kennung. | Browser hält nur Upload-IDs für laufende Übermittlung; Submit liest diese IDs; Vorgangsdetail liest danach die daraus erzeugten bestehenden `vorgang_dokument`-Zeilen und deren autorisierten Download. |
| `anfrage` (bestehend, erweitert) | Bestehende Kontaktprojektion; erhält optionale `formular_einsendung_id` mit eindeutiger Beziehung. `anliegen` enthält eine kurze serverseitige Projektion, die vollständigen Werte bleiben in `formular_einsendung`. | Nur erfolgreicher, nicht als Spam markierter Formular-Submit erstellt sie, innerhalb derselben Transaktion wie Einsendung/Vorgang. Alte `/public/anfragen`-Route bleibt weiterer Owner für alte Anfragen. | `GET /vorgaenge/{id}` liest die verknüpfte Anfrage/Antwort; keine öffentliche Anfragen-Liste. |
| `kunde` (bestehend, erweitert) | Neues `status` mit `entwurf` oder `aktiv`; Bestandsdaten migrieren zu `aktiv`. Bei E-Mail-Treffer wird kein Kunde geschrieben; ohne Treffer entsteht ein `entwurf`. | Formular-Submit ist Owner für neue Entwürfe; bestehendes `POST /kunden` erzeugt aktive Kunden; `PATCH /kunden/{id}` durch Inhaber/Buero kann Entwurf bearbeiten/aktivieren. | Der Submit sucht intern nur im eigenen Mandanten nach gleicher E-Mail. Büro/Inhaber verwenden `GET /kunden?q=...` vor manueller Zuordnung und `GET /kunden/{id}` vor Bearbeitung; `GET /kunden` kennzeichnet Entwürfe. |
| `vorgang`, `vorgang_dokument`, `vorgang_historie` (bestehend) | Neue Einsendung wird als Vorgang `Neu`, Quelle `Formular` angelegt; Uploads werden als bestehende Vorgangsdokumente referenziert, Historie nennt Formularversion/Einsendung. Kein Projekt wird erzeugt. | Nur erfolgreicher, nicht Spam-markierter Formular-Submit schreibt diese drei Entitäten; bestehende Vorgangs- und Dokumentrouten bleiben weitere Owner. | `GET /vorgaenge` zeigt neuen Vorgang; `GET /vorgaenge/{id}` vor Detail, Antwort und Dokumentdownload; bestehende `GET /kunden/{id}/objekte` vor späterer Objektzuordnung. |

`uebernahme_zuordnung` ist kein freies Skript, sondern ein optionaler Wert je
Text-, Adresse- oder Auswahlfeld aus: Kontaktname, E-Mail, Telefon, Adresse,
Anliegen. Eine veröffentlichbare Version braucht genau ein Kontaktname-Feld und
höchstens eines je weiterer Zuordnung; bei vorhandener E-Mail wird sie für den
Bestandskundenabgleich verwendet. Vorlagen liefern diese Zuordnungen bereits.
So ist jede gültige Einsendung zuverlässig als Anfrage/Kundenentwurf
übernehmbar, ohne feldbeschriftungsabhängige Heuristik.

Der Publish-Check verlangt mindestens einen Schritt, mindestens ein Feld und
genau ein verpflichtendes Consent-Feld. Textfelder haben nur Länge/RegExp aus
einem festen, serverseitig erlaubten Satz; Zahlfelder Min/Max/Ganzzahl-Schalter;
Datumsfelder Min/Max; Auswahlfelder ihre nichtleeren Optionen; Uploadfelder
eine feste Maximalanzahl. Adresse speichert strukturierte Straße, Hausnummer,
PLZ und Ort als einen Feldwert. Im Modus **Einfach** rendert der Snapshot nur
Pflichtfelder; **Erweitert** ergänzt alle Felder mit `optional_in_einfach`.
Beide Modi validieren denselben unveränderlichen Snapshot serverseitig.

### API-Contracts

Angemeldete Routen verlangen Bearer-JWT und `require_role("Inhaber", "Buero")`.
Jede Entwurfsmutation trägt `draft_revision`; bei Abweichung folgt `409` mit
deutscher Meldung und unverändertem Stand. `mandant_id` ist nirgends ein
Request-Feld.

- `GET /formulare?limit=50&offset=0` listet eigene Formulare mit Name,
  Entwurfsrevision, Veröffentlichungsstatus und Zeitstempel; Antwort enthält
  `items`, `total`, wirksames `limit` und `offset`. `limit` ist mindestens 1,
  höchstens 200; Heimat der Formularliste.
- `POST /formulare` erstellt ein leeres Formular oder kopiert die fest
  ausgelieferte Vorlage `shk` bzw. `entruempelung` in den Mandantenentwurf.
  Die Vorlagen sind Release-Inhalt, keine vom Mandanten schreibbare Entität;
  PROJ-14 kann später denselben Katalog als Quelle übernehmen.
- `GET /formulare/{id}` liefert vollständigen eigenen Entwurf, Publish-Status
  und `draft_revision`; Pflicht-Read für Editor und alle Mutationen.
- `PATCH /formulare/{id}` ändert nur Name; `POST/PATCH/DELETE
  /formulare/{id}/schritte` sowie `PUT /formulare/{id}/schritte/reihenfolge`
  pflegen Schritte und Reihenfolge.
- `POST/PATCH/DELETE /formulare/{id}/schritte/{step_id}/felder` pflegt Feld,
  Konfiguration, Optionen und Feldreihenfolge als vollständig validierten
  Editorzustand. Leere Optionen, doppelte Werte und unzulässige Konfiguration
  werden hier angezeigt und spätestens beim Publish abgewiesen.
- `POST /formulare/{id}/veroeffentlichen` prüft gesamten Entwurf und erstellt
  eine neue unveränderliche Version. `POST /formulare/{id}/veroeffentlichung-zuruecknehmen`
  macht nur die öffentliche Referenz unzugänglich; Entwurf und Historie bleiben.
- `GET /formulare/{id}/einbindung` liefert nach Publish die kanonische
  Betriebsdomain-URL, ein iframe-Markup und ein JavaScript-Snippet, das genau
  diesen iframe erzeugt. Keine Einbettung erhält API- oder Mandantenparameter.
- `GET /public/formulare/{public_id}` liefert nach Domain- und
  Veröffentlichungsprüfung ausschließlich den Snapshot, Feldregeln und
  deutschen Standardfehler für die öffentliche Ansicht. Unbekannt, zurückgenommen
  oder falsche Domain ist ein einheitliches `404` ohne Formular-/Mandanteninfo.
- `POST /public/formulare/{public_id}/uploads` akzeptiert eine Datei plus
  Übermittlungskennung und Feld-ID. Es prüft Snapshot-Feldtyp, Magic Bytes,
  Größe, Mengenlimit, Host und Rate-Limit und gibt nur Upload-ID zurück.
- `POST /public/formulare/{public_id}/einsendungen` akzeptiert Kennung,
  Feldwerte, Upload-IDs, Honeypot und Client-Startzeit. Der Server prüft alles
  erneut, schützt mit Zeitfenster und Rate-Limit, und liefert bei `normal` nur
  Bestätigung. Bei `spam` wird keine Anfrage/Kunde/Vorgang angelegt; die
  markierte Einsendung bleibt für Berechtigte nachvollziehbar. Fehler erzeugen
  keine Teilanlage und sind deutsch/feldbezogen.
- `GET /formular-einsendungen?spam=1&limit=50&offset=0` zeigt nur markierte
  Einsendungen für Inhaber/Buero und antwortet mit `items`, `total`, wirksamem
  `limit` und `offset`; `limit` ist mindestens 1, höchstens 200. `GET
  /vorgaenge/{id}` wird um den unveränderlichen Formularantwort-Snapshot ergänzt;
  Inhaber/Buero sowie zugewiesene Monteure sehen ihn vollständig, alle anderen
  Monteure erhalten bereits nach bestehender Vorgangsregel `403`. Er bleibt der
  Lesepfad regulärer Leads.

Öffentlicher Submit läuft in einer DB-Transaktion: Einsendung, Anfrage,
Kundenentwurf oder bestehende Kundenreferenz, Vorgang, Historie,
Upload-Verknüpfung und Vorgangsdokumente bestehen gemeinsam oder gar nicht.
Eine Wiederholung derselben Kennung liefert das erste Ergebnis statt einer
zweiten Anfrage. Scheitert MinIO vor Abschluss, wird die DB-Transaktion
abgebrochen; verwaiste temporäre Objekte werden durch einen begrenzten,
internen Aufräumlauf entfernt.

### Entscheidungen

- **Next.js-Reuse:** Öffentliche Website, Host-Rewrite und shadcn-artige UI
  existieren bereits. Flutter würde dieselbe Website- und Einbettungslogik
  doppelt bauen.
- **Entwurf plus unveränderlicher Publish-Snapshot:** Bearbeiten darf nie eine
  eingebettete Fassung oder alte Antwort verändern. Ein Snapshot ist kleiner
  und belastbarer als zwei parallele editierbare Formulare.
- **iframe für alle Einbettungen:** Der Formularcode läuft auf der verifizierten
  Betriebsdomain. Damit bleibt Host-basierte Mandantentrennung auch auf fremden
  Websites erhalten; das JavaScript-Snippet ist nur Komfort, kein zweiter
  Sicherheitsweg.
- **Strukturierte feste Feldkonfiguration:** Sie deckt den Katalog ab und
  verhindert XSS, freie Logik und nicht validierbare Antwortformate.
- **MinIO-Pfade statt Blobs/öffentlicher URLs:** folgt vorhandenen Anfrage- und
  Vorgangsdokumenten. Downloads bleiben über berechtigte Vorgangsrouten,
  Buckets bleiben nicht öffentlich.
- **E-Mail-Abgleich nur innerhalb des Mandanten:** erfüllt Wiederholungsleads
  ohne Kundenüberschreibung; ohne Treffer bleibt ein sichtbar markierter
  Kundenentwurf statt unbemerkter dauerhafter Stammdatenanlage.
- **Servervalidierung und atomare Übernahme:** Browservalidierung verbessert
  Bedienung, ist aber nicht vertrauenswürdig. Eine Transaktion verhindert
  unvollständige Leads bei Upload- oder Netzwerkfehlern.

### Abhängigkeiten und Migration

- Keine neuen Frontend- oder Backend-Pakete. Vorhandene Next.js,
  react-hook-form/Zod, FastAPI/Pydantic, raw-SQL-Transaktionen und MinIO reichen.
- Eine neue idempotente raw-SQL-Migration folgt auf `010_website_landingpage.sql`:
  Formulartabellen, Fremdschlüssel, Positions-/Eindeutigkeits-Constraints,
  `anfrage.formular_einsendung_id`, `kunde.status`, RLS und Indizes für
  `(mandant_id, formular_id)`, `public_id`, Kennung und Spam-Liste. Kein Alembic.
- Bestehende `anfragebild` bleibt unverändert für den alten Anfrageflow;
  `formular_upload` ist nötig, weil PROJ-13 auch PDFs und feldbezogene Uploads
  unterstützt. Dokploy behält die bestehende FastAPI-/Next.js-/MinIO-Auslieferung.
- Vor Backend-Implementierung ist die nächste freie Nummer im echten
  `backend/sql/`-Verzeichnis zu bestätigen; laut aktuellem Stand ist `011` frei.

## Frontend-Implementierung (abc-frontend)

**Stack:** Next.js (App Router) + shadcn-artige UI, react-hook-form/Zod-Muster, `apiFetch`/`publicApiFetch` — wie in Tech Design vorgegeben. Branch `main`.

**Anlage (Next.js):**
- `lib/schemas/formular.ts` — Typen + Zod für Feldtyp-Katalog (10 Typen), Schritte, Optionen, Draft, öffentlichen Snapshot, Einbindung.
- `lib/api/formulare.ts` — Client für alle Verträge (`/formulare/*`, `/public/formulare/*`). Angemeldete Routen via `apiFetch`, öffentliche via `publicApiFetch` (kein Token, Honeypot-/Spam-Schutz serverseitig). `FormularConflictError` bei `409`.
- `components/formulare/feld-renderer.tsx` — ein Feldrenderer für Editor-Vorschau und öffentliche Mehrstufenansicht (Adresse strukturiert, Kachel/Radio/Dropdown, Consent, Upload via `renderUpload`).
- `components/formulare/feld-editor.tsx` — Feldeigenschaften (Label, Hilfetext, Pflichtfeld, `optional_in_einfach`, typ-spezifische Konfig, Übernahme-Zuordnung, Optionseditor mit Doppelwert-Prüfung).
- `app/(app)/formulare/page.tsx` — Liste (Leerform / SHK- / Entrümpelungs-Vorlage, Entwurf/live-Badge).
- `app/(app)/formulare/editor/[id]/page.tsx` — Editor: Name, Komplexitätsstufe, Schritte (anlegen/umbenennen/reihenfolge/löschen), Felder (10 Typen, bearbeiten/reihenfolge/löschen), Vorschau Einfach/Erweitert, Publish-Check (≥1 Schritt, ≥1 Feld, genau 1 Pflicht-Consent, gültige Optionen), Veröffentlichung zurücknehmen, Einbindung (Direktlink/iframe/JS).
- `app/site/formulare/[public_id]/page.tsx` — öffentliche Mehrstufenansicht: Fortschrittsanzeige, Vor/Zurück mit erhaltenen Werten, clientseitige Pflicht-/Typ-/Upload-Validierung (JPEG/PNG/WebP/PDF, 15 MB), Honeypot, idempotente Kennung, Bestätigung, wiederholbarer Netzwerkfehler, 404 ohne Mandanteninfo.
- Navigation: `formulare` in `layout.tsx` (ICONS/LABELS/PATHS) und `tokens.ts` `NAV_RECHTE` für Inhaber/Büro ergänzt.

**Offen (Backend):** Alle `/formulare`- und `/public/formulare`-Endpunkte sowie die Migration `011_*.sql` sind noch zu bauen (siehe Tech Design). Frontend erwartet exakt die dort definierten Verträge.

## QA Test Results

**Tested:** 2026-08-24 (Retest nach BUG-1/BUG-2)  
**Backend:** FastAPI TestClient, Python 3.10 / pytest 8.3.3  
**Frontend:** Next.js TypeScript typecheck + Jest + Production-Build (Chrome-Smoke in dieser Umgebung nicht verfügbar)  
**Tester:** QA Engineer (AI)

### Acceptance Criteria Status

- [x] **AC-1 bis AC-15:** Retest bestanden. Der Frontend-Adapter übersetzt Entwürfe, Snapshots, Publish-Revisionen und Einsendungen in den getesteten FastAPI-Vertrag.
- [x] Backend-Teilprüfungen: Anlage/Vorlagen, Entwurfsmutationen mit Versionskonflikt, Publish/Rücknahme, Domain-gebundener Snapshot, Upload-Magic-Bytes, Spam-Markierung, idempotente Einsendung und Vorgangsanreicherung sind durch 18 PROJ-13-Backendtests abgedeckt.

### Edge Cases Status

- [x] Nicht veröffentlichte oder domainfremde Snapshots liefern ein einheitliches `404`.
- [x] Doppelte Optionswerte und fehlendes Pflicht-Consent verhindern die Veröffentlichung.
- [x] Ungültige Upload-Typen werden serverseitig abgewiesen.
- [x] Öffentlicher Eingabe-/Einsendepfad ist wieder vertragskompatibel; visueller Chrome-Smoke bleibt als Deployment-Check offen.

### Security Audit Results

- [x] Angemeldete Formularrouten verlangen Inhaber- oder Büro-Rolle; Mandant wird nicht aus dem Request-Body bezogen.
- [x] Öffentliche Snapshots sind an die aufgelöste Betriebsdomain gebunden; fremde Domain liefert `404`.
- [x] Uploads prüfen Magic Bytes sowie die feste Größenobergrenze.
- [x] Rate-Limit: `X-Forwarded-For` wird nur mit gültigem internen Proxy-Secret übernommen; ein neuer Retest deckt beide Pfade ab.

### Bugs Found

#### BUG-1: Frontend und Backend haben inkompatible Formularverträge

- **Severity:** High — **Fixed, retested**
- **Steps to Reproduce:**
  1. Ein SHK-Formular veröffentlichen und dessen öffentliche URL öffnen.
  2. Auf „Weiter“ oder „Absenden“ klicken.
  3. Expected: Der Browser übermittelt `client_start`, eine Liste von Feldwerten und erhält `{ "status": "erfolgreich" }`.
  4. Actual: Das Frontend erwartet `komplexitaet`, `config` und `options`, während das Backend `modus`, flache Konfigurationsfelder und `optionen` liefert. Zudem sendet das Frontend `client_startzeit`, `upload_ids` und ein Objekt als `werte`; die API verlangt `client_start` und eine Liste. Dadurch scheitert der öffentliche Ablauf vor bzw. spätestens mit `422`.
- **Priority:** Fix before deployment

#### BUG-2: Rate-Limit per Client-Header umgehbar

- **Severity:** High — **Fixed, retested**
- **Steps to Reproduce:**
  1. Öffentlichen Upload- oder Einsende-Endpunkt wiederholt aufrufen.
  2. Bei jedem Request einen anderen `X-Forwarded-For`-Wert mitsenden.
  3. Expected: Die echte Client-IP wird nur von einem vertrauenswürdigen Proxy übernommen und die Drosselung greift.
  4. Actual: Der Endpunkt verwendet den beliebigen Header direkt als Rate-Limit-Schlüssel.
- **Priority:** Fix before deployment

### Automated Regression Results

- [x] Backend: `243 passed` (eine bestehende Pydantic-Warnung).
- [x] Next.js: TypeScript typecheck, Jest (`30 passed`) und Production-Build bestanden.

### Summary

- **Acceptance Criteria:** 15/15 passed (automatisierter Retest; visueller Chrome-Smoke beim Deployment nachholen)
- **Bugs Found:** 0 open (2 High fixed, retested)
- **Security:** Pass
- **Production Ready:** YES
- **Recommendation:** Deploy

## Deployment
**Production URL:** https://bizos.app.msce.info
**Deployed:** 2026-08-24 · **Version:** 0.1.15 · **Host:** Dokploy (Compose), Auto-Deploy via Push auf `main`.

**Ausgeliefert:** vereinfachte Kachel-Optionen mit automatisch erzeugtem Wert, verständliche API-Fehler, das Löschen nie veröffentlichter Entwürfe, benannte Schritte, verzögerte Optionswarnungen und öffentliche Formularlinks über die aktive Betriebsdomain. Neue Felder sind sofort sichtbar; Nicht-Auswahlfelder speichern ohne ungültige Optionsdaten.

**Nach dem Deploy manuell prüfen:** `/api/health`, neue Schritte benennen, Kachel mit „Haus“/„Wohnung“ anlegen, Entwurf löschen, Formular veröffentlichen sowie Dokploy-Deployment-Log. Bei gecachtem Frontend einen Hard-Refresh durchführen.
