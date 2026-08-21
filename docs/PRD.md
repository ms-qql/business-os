# PRD — Business OS für kleine SHK-Betriebe

**Status:** Freigegeben  
**Stand:** 2026-08-16

## Vision

Business OS ist eine geführte Website plus einfache Betriebszentrale für SHK-Servicebetriebe mit ein bis drei Mitarbeitern. Eine Web- oder E-Mail-Anfrage wird ohne Medienbruch zu Kunde, Vorgang, Angebot oder Termin und schließlich zu einer PDF-Rechnung.

Das Produkt gewinnt nicht über ERP-Breite, sondern über einen verständlichen Ablauf: weniger verlorene Anfragen, weniger Büro nach Feierabend und ein professioneller Auftritt, der in wenigen Tagen eingerichtet ist.

## Zielgruppe

Primär: Inhaber-geführte SHK-Servicebetriebe mit 1–3 Mitarbeitern, wenig bestehender Branchensoftware und einer veralteten oder fehlenden Website. Sie arbeiten tagsüber beim Kunden, bearbeiten Anfragen abends und nutzen häufig Telefon, E-Mail, WhatsApp, Papier oder Excel parallel.

Sekundär: Bürokräfte und Monteure derselben Betriebe. Bürokräfte pflegen Vorgänge und Dokumente; Monteure sehen nur ihre eigenen Termine und Auftragsinformationen auf dem Mobilgerät.

## Produktversprechen

> Website, Anfragen und Büroarbeit in einem einfachen Ablauf — für SHK-Betriebe, die keine weitere komplizierte Handwerkersoftware wollen.

## Entscheidungen

| Bereich | Festlegung |
|---|---|
| Startsegment | SHK-Service |
| Auslieferung der Website | Je Mandant konfigurierbare Landingpage aus freigegebenen Sektionen |
| Eingangskanäle V1 | Website-Formular und E-Mail |
| Rollen | Inhaber, Büro, Monteur |
| Mandantenmodell | Multi-Tenant mit strikt getrennten Betriebsdaten |
| Rechnungen | PDF-Rechnung; keine Buchhaltung und keine E-Rechnung in V1 |
| Kommunikation | Entwürfe werden stets durch Menschen freigegeben |
| Produktfokus | Website-first: Anfrage zum Auftrag, nicht vollständiges ERP |

## Roadmap

| Priorität | Feature | Ziel |
|---|---|---|
| P0 | Mandanten, Anmeldung und Rollen | Betriebsdaten und Ansichten sicher trennen |
| P0 | Geführte SHK-Website und Anfrageformular | Betrieb veröffentlichen und vollständige Anfragen mit Fotos erzeugen |
| P0 | Kunden, Vorgänge und Dokumente | Anfrage, Kunde, Objekt, Status, Historie und Anhänge zentral führen |
| P0 | E-Mail-Inbox und Antwort | E-Mail-Anfragen und freigegebene Antworten im selben Vorgang führen |
| P0 | Angebote und PDF-Versand | Einfache Positionen in ein prüfbares Angebot überführen |
| P0 | Einfache Terminplanung | Termin einem von maximal drei Teammitgliedern zuordnen |
| P0 | PDF-Rechnungen | Rechnung aus erledigtem Vorgang erstellen und ablegen |
| P0 | Begleitetes Onboarding | Betrieb, Branding, Postfach und Preisliste startklar einrichten, inkl. Testdurchstich vor Livegang |
| P1 | Mobile Monteuransicht und Automationen | Aufträge mobil abschließen sowie Erinnerungen auslösen |
| P1 | Datenschutz, Datenexport und Aufbewahrung | Mandantenexport und automatisierte Löschregeln ergänzen |
| P1 | KI-Assistenz | Zusammenfassungen, Klassifizierung und Textentwürfe mit Freigabe |
| P1 | Branchenpakete | Weitere Gewerke als konfigurierte Vorlage statt eigener Anwendung |
| P1 | Freier Website-Baukasten und Landingpage | Hochwertige, modular konfigurierbare Startseite mit Bildern und Kurzformular |
| P2 | E-Rechnungen | Strukturierte Rechnungsformate ergänzen |
| P2 | Telefonie, Routen, Kundenportal | Nur bei belegtem Kundenbedarf |

## Erfolgsmessung

- Mindestens 80 % der Webanfragen werden vollständig als Vorgang angelegt.
- Ein Betrieb kann seine Website und den ersten Anfragefluss in einem begleiteten Termin produktiv nutzen.
- Der Inhaber kann aus einer vollständigen Anfrage in höchstens fünf Minuten ein Angebot oder einen Termin vorbereiten.
- Jede E-Mail-Antwort, jedes Angebot und jeder Termin bleibt am zugehörigen Vorgang sichtbar.

## Rahmenbedingungen

- Deutschsprachiges, mobiles Webprodukt; öffentliche Seiten müssen suchmaschinenfreundlich sein.
- Datenschutz nach DSGVO: Mandantentrennung, Zugriff nach Rolle, transparente Verarbeitung, Lösch- und Exportmöglichkeit.
- Persönliches Onboarding ist Teil des Angebots; Selbstkonfiguration ist kein V1-Erfolgsmaßstab.
- Der Baukasten bleibt auf freigegebene, responsive Sektionstypen begrenzt; kein freies HTML oder individuelles Seitenlayout.

## Nicht-Ziele

- Lager, Materialwirtschaft, Lohn, Finanzbuchhaltung, DATEV-Integration und komplexe Nachkalkulation.
- GAEB, Großhändler-Integration, Routenoptimierung und Offline-Synchronisierung.
- Freie Rollen- und Rechteverwaltung, mehrstufige Unternehmenshierarchien oder Agentur-/Reseller-Modell.
- Autonom versendete Angebote, Rechnungen oder Kundenantworten.
- WhatsApp, Sprachagent, Recruiting und weitere Gewerke vor bestätigtem Bedarf.

## Aus vorigem Brainstorm bewusst vertagt

Die bereits beschriebene Auto-Triage nach Kapazität und Deckungsbeitrag, Angebots-KI, Warteliste, Telefon-Transkription und Recruiting bleiben wertvolle spätere Optionen. Sie sind nicht V1, weil Website-first V1 zuerst den durchgehenden Grundfluss und die Nutzung durch einen Referenzbetrieb beweisen muss.

## Wiederverwendungsentscheidung

ImmoCRM liefert technische Vorlagen für E-Mail, Dateien, Zugangsdaten, Erinnerungen und Termine. Das neue Produkt übernimmt keine Immobilienlogik, Flutter-Oberflächen oder das separate Datenbank-Mandantenmodell. Details: [Reuse-Audit](reuse-audit-immocrm.md).

Die Übernahme verändert vor allem die Umsetzung, nicht den Kundenfluss: PROJ-4, PROJ-6, PROJ-7 und spätere Erinnerungen starten mit bewährten technischen Bausteinen. Die fachlich differenzierenden Teile — SHK-Website, Anfrage-/Vorgangsmodell, Angebote und Rechnungen — werden bewusst neu spezifiziert.
