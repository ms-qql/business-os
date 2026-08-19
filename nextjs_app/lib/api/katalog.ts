import { apiFetch } from "@/lib/api/client";

/**
 * Preisliste / Leistungskatalog (PROJ-7, Schritt 6).
 *
 * HINWEIS ZUM CONTRACT: Das Datenmodell des Katalogs ist im Tech Design (Abschnitt
 * A, Zeile 84) ausdrücklich als offen markiert ("Offen für /abc-architecture: Tiefe
 * des Leistungskatalogs …"). Dieses Frontend geht von folgendem, mit den
 * Anforderungen (Schritt-6-Acceptance: Bezeichnung, Einheit, Netto-Einzelpreis,
 * Steuersatz) kompatiblen Contract aus:
 *
 *   GET  /katalog                       → KatalogListe { positionen: KatalogPosition[] }
 *   POST /katalog/positionen            → legt eine Position an (KatalogPositionInput)
 *   DELETE /katalog/positionen/{id}     → entfernt eine Position
 *   POST /katalog/import                → CSV-Import; Antwort enthält je Zeile
 *                                         übernommene und fehlerhafte Zeilen.
 *
 * Sobald der Backend-Task (t_e42c41a2) den finalen Contract liefert, sind hier nur
 * Feldnamen/Endpunkte anzupassen — die UI-Komponenten hängen allein an diesen Typen.
 */

export interface KatalogPosition {
  id: string;
  bezeichnung: string;
  einheit: string;
  netto_einzelpreis: number;
  steuersatz: number;
}

export interface KatalogListe {
  positionen: KatalogPosition[];
}

export interface KatalogPositionInput {
  bezeichnung: string;
  einheit: string;
  netto_einzelpreis: number;
  steuersatz: number;
}

export interface KatalogImportFehler {
  zeile: number;
  grund: string;
}

export interface KatalogImportZeile {
  zeile: number;
  uebernommen: boolean;
}

export interface KatalogImportResult {
  uebernommen: KatalogImportZeile[];
  fehler: KatalogImportFehler[];
  /** Anzahl tatsächlich neu angelegter Positionen (Duplikate werden als Fehler gemeldet). */
  anzahl_uebernommen: number;
}

export function getKatalog(): Promise<KatalogListe> {
  return apiFetch<KatalogListe>("/katalog");
}

export function addKatalogPosition(input: KatalogPositionInput): Promise<KatalogPosition> {
  return apiFetch<KatalogPosition>("/katalog/positionen", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deleteKatalogPosition(id: string): Promise<void> {
  return apiFetch<void>(`/katalog/positionen/${id}`, { method: "DELETE" });
}

/**
 * CSV-Import mit Fehlermeldung je Zeile. Erwartetes Format (Header optional):
 *   bezeichnung;einheit;netto_einzelpreis;steuersatz
 * Komma statt Punkt oder Währungszeichen im Preis werden serverseitig normalisiert —
 * der Client sendet den Rohtext und lässt die Normalisierung am Server.
 */
export function importKatalogCsv(datei: File): Promise<KatalogImportResult> {
  const form = new FormData();
  form.append("datei", datei);
  return apiFetch<KatalogImportResult>("/katalog/import", {
    method: "POST",
    body: form,
  });
}
