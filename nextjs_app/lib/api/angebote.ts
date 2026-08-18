import { apiFetch } from "@/lib/api/client";
import type { RabattTyp } from "@/lib/angebot-berechnung";

/** Spiegelt den API-Vertrag aus dem Tech Design (features/PROJ-5-...md, Abschnitt C). */

export type AngebotStatus = "entwurf" | "versendet";

export interface AngebotPosition {
  id: string;
  bezeichnung: string;
  menge: number;
  einheit: string;
  einzelpreis: number;
  steuersatz: number;
  rabatt_typ: RabattTyp;
  rabatt_wert: number;
  positions_summe: number;
  reihenfolge: number;
}

export interface Angebot {
  id: string;
  vorgang_id: string;
  nummer: string;
  version: number;
  status: AngebotStatus;
  gueltig_bis: string | null;
  freitext: string | null;
  netto_summe: number;
  steuer_summe: number;
  brutto_summe: number;
  empfaenger: string | null;
  versendet_am: string | null;
  versendet_von: string | null;
  positionen: AngebotPosition[];
  created_at: string;
  updated_at: string;
}

export interface AngebotListItem {
  id: string;
  nummer: string;
  version: number;
  status: AngebotStatus;
  brutto_summe: number;
  versendet_am: string | null;
  created_at: string;
}

export interface PositionInput {
  bezeichnung: string;
  menge: number;
  einheit: string;
  einzelpreis: number;
  steuersatz: number;
  rabatt_typ: RabattTyp;
  rabatt_wert: number;
}

export interface KopfdatenInput {
  gueltig_bis?: string | null;
  freitext?: string | null;
}

export interface FreigabeResult {
  empfaenger: string;
  betreff: string;
  netto_summe: number;
  steuer_summe: number;
  brutto_summe: number;
  pdf_url: string;
}

/** GET /vorgaenge/{id}/angebote — alle Versionen, neueste zuerst. */
export function listAngebote(vorgangId: string): Promise<AngebotListItem[]> {
  return apiFetch<AngebotListItem[]>(`/vorgaenge/${vorgangId}/angebote`);
}

/** POST /vorgaenge/{id}/angebote — neuen Entwurf anlegen (Version 1). */
export function createAngebot(vorgangId: string): Promise<Angebot> {
  return apiFetch<Angebot>(`/vorgaenge/${vorgangId}/angebote`, { method: "POST", body: JSON.stringify({}) });
}

/** GET /angebote/{id} — inkl. Positionen und berechneter Summen. */
export function getAngebot(id: string): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${id}`);
}

/** PATCH /angebote/{id} — Kopfdaten, nur solange Entwurf. */
export function updateAngebotKopfdaten(id: string, input: KopfdatenInput): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${id}`, { method: "PATCH", body: JSON.stringify(input) });
}

/** POST /angebote/{id}/positionen — Position hinzufügen, nur solange Entwurf. */
export function addPosition(angebotId: string, input: PositionInput): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${angebotId}/positionen`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** PATCH /angebote/{id}/positionen/{position_id} — Position ändern, nur solange Entwurf. */
export function updatePosition(angebotId: string, positionId: string, input: PositionInput): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${angebotId}/positionen/${positionId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

/** DELETE /angebote/{id}/positionen/{position_id} — Position entfernen, nur solange Entwurf. */
export function deletePosition(angebotId: string, positionId: string): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${angebotId}/positionen/${positionId}`, { method: "DELETE" });
}

/** GET /angebote/{id}/pdf — kurzlebige, berechtigte Download-URL. */
export function getAngebotPdfUrl(id: string): Promise<{ download_url: string }> {
  return apiFetch<{ download_url: string }>(`/angebote/${id}/pdf`);
}

/** POST /angebote/{id}/freigabe — prüft Positionen+Empfänger, erzeugt PDF-Vorschau, versendet nichts. */
export function angebotFreigeben(
  id: string,
  input: { empfaenger: string; betreff: string },
): Promise<FreigabeResult> {
  return apiFetch<FreigabeResult>(`/angebote/${id}/freigabe`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** POST /angebote/{id}/senden — einziger Endpunkt, der tatsächlich versendet. */
export function angebotSenden(id: string): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${id}/senden`, { method: "POST" });
}

/** POST /angebote/{id}/neue-version — nur auf versendetem Angebot, kopiert Positionen in neuen Entwurf. */
export function angebotNeueVersion(id: string): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${id}/neue-version`, { method: "POST" });
}
