# PROJ-2: Geführte SHK-Website, Branding und Anfrageformular

## Status: Planned
**Created:** 2026-08-16

## Dependencies
- Requires: PROJ-1 — Mandant und Inhaberzugriff.

## Reuse aus ImmoCRM
- Logo-Speicher und Betriebs-Settings als Vorlage. Öffentliche Website und Formulare werden neu gebaut.

## User Stories
- Als Inhaber möchte ich Logo, Kontaktdaten und Leistungen hinterlegen, damit meine Website professionell wirkt.
- Als Interessent möchte ich eine Leistung finden und eine Anfrage auch mit Fotos absenden.
- Als Interessent möchte ich eine klare Bestätigung erhalten, damit ich weiß, dass die Anfrage angekommen ist.

## Acceptance Criteria
- [ ] Jeder Betrieb erhält eine geführte SHK-Vorlage mit Startseite, Leistungen, Über-uns-/Kontaktbereich, Impressum und Datenschutzhinweis.
- [ ] Inhaber können Logo, Farben, Firmenname, Adresse, Telefonnummer, E-Mail, Öffnungszeiten und vorgegebene Leistungsseiten ändern.
- [ ] Das Formular erfasst Name, Kontaktweg, Adresse, Anliegen, Dringlichkeit, gewünschtes Zeitfenster und bis zu fünf Bilder.
- [ ] Pflichtfelder werden vor Versand mit deutscher Feldmeldung angezeigt; die Website bleibt ohne Anmeldung nutzbar.
- [ ] Eine erfolgreiche Formularübermittlung erzeugt genau einen Vorgang im richtigen Mandanten und zeigt „Vielen Dank. Wir melden uns zeitnah bei Ihnen.“
- [ ] Öffentliche Seiten sind mobil bedienbar und je Mandant nur über dessen Domain erreichbar.

## Edge Cases
- Ungültige oder zu große Dateien werden abgewiesen, ohne die bereits eingegebenen Formulardaten zu verlieren.
- Ein unbekannter oder inaktiver Domainname zeigt keine Daten eines anderen Betriebs.
- Mehrfaches Absenden derselben Anfrage erzeugt keine doppelten Vorgänge.
- Ein nicht gepflegtes Leistungsangebot blendet die betreffende Leistungsseite aus.

## Technical Requirements
- Security: Rate-Limit und Bot-Schutz am öffentlichen Formular; Uploads serverseitig prüfen.
- Accessibility: Beschriftete Felder, Tastaturbedienung und verständliche Fehlermeldungen.

---
<!-- Sections below are added by subsequent skills -->

## Tech Design (Solution Architect)
_To be added by /architecture_

## QA Test Results
_To be added by /qa_

## Deployment
_To be added by /deploy_
