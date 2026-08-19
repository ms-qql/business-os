import { apiFetch } from "@/lib/api/client";

/**
 * API-Client für PROJ-8 (PDF-Rechnungen). Spiegelt exakt den Vertrag aus
 * features/PROJ-8-...md, Abschnitt C — alle Endpunkte sind Büro/Inhaber,
 * mandant_id kommt niemals aus Pfad/Body (serverseitig aus JWT).
 */

export type RechnungStatus = "entwurf" | "versendet" | "storniert";
export type Zahlungsstatus = "Offen" | "Bezahlt" | "Storniert";

export interface RechnungPosition {
  id: string;
  bezeichnung: string;
  menge: number;
  einheit: string;
  netto_einzelpreis: number;
  steuersatz: number;
  sortierung: number;
  /** Serverberechnete Netto-Positionssumme (2 NK), inkl. Mehrfachheit. */
  positions_summe: number;
}

export interface Rechnung {
  id: string;
  vorgang_id: string;
  rechnungsnummer: string;
  rechnungsdatum: string | null;
  leistungsdatum: string | null;
  status: RechnungStatus;
  zahlungsstatus: Zahlungsstatus;
  netto_summe: number;
  steuer_summe: number;
  brutto_summe: number;
  empfaenger_email: string | null;
  freigabe_at: string | null;
  versendet_at: string | null;
  versendet_von: string | null;
  storniert_at: string | null;
  storniert_von: string | null;
  fassung_id: string | null;
  positionen: RechnungPosition[];
  created_at: string;
  updated_at: string;
}

export interface RechnungListItem {
  id: string;
  rechnungsnummer: string;
  status: RechnungStatus;
  zahlungsstatus: Zahlungsstatus;
  brutto_summe: number;
  versendet_at: string | null;
  created_at: string;
}

export interface PositionInput {
  bezeichnung: string;
  menge: number;
  einheit: string;
  netto_einzelpreis: number;
  steuersatz: number;
}

export interface EntwurfInput {
  rechnungsdatum: string;
  leistungsdatum: string;
  angebot_id?: string | null;
  empfaenger_email?: string | null;
}

export interface FreigabeResult {
  empfaenger: string | null;
  betreff: string;
  rechnungsnummer: string;
  netto_summe: number;
  steuer_summe: number;
  brutto_summe: number;
  pdf_download_url: string;
}

export interface SendenResult {
  rechnung: Rechnung;
  versendet: boolean;
  fehler_text: string | null;
}

/** Rechnungsstellerprofil (ein Profil je Mandant, Quelle für neue Entwürfe). */
export interface RechnungsstellerProfil {
  firma_name: string;
  strasse: string;
  hausnummer: string;
  plz: string;
  ort: string;
  steuernummer?: string | null;
  ust_id?: string | null;
}

/* --- Rechnungssteller-Einstellungen (nur Inhaber) --- */

/** GET /einstellungen/rechnungssteller — null, solange noch nicht gepflegt. */
export function getRechnungssteller(): Promise<RechnungsstellerProfil | null> {
  return apiFetch<RechnungsstellerProfil | null>("/einstellungen/rechnungssteller");
}

/** PUT /einstellungen/rechnungssteller — Profil vollständig speichern. */
export function updateRechnungssteller(
  input: RechnungsstellerProfil,
): Promise<RechnungsstellerProfil> {
  return apiFetch<RechnungsstellerProfil>("/einstellungen/rechnungssteller", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/* --- Rechnungen am Vorgang --- */

/** GET /vorgaenge/{id}/rechnungen — neueste zuerst. */
export function listRechnungen(vorgangId: string): Promise<RechnungListItem[]> {
  return apiFetch<RechnungListItem[]>(`/vorgaenge/${vorgangId}/rechnungen`);
}

/** POST /vorgaenge/{id}/rechnungen — Entwurf samt reservierter Nummer anlegen. */
export function createRechnung(vorgangId: string, input: EntwurfInput): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/vorgaenge/${vorgangId}/rechnungen`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** GET /rechnungen/{id} — Entwurf bzw. Beleg inkl. Positionen und Summen. */
export function getRechnung(id: string): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${id}`);
}

/** PATCH /rechnungen/{id} — nur Entwurf: Datum und Empfänger-E-Mail. */
export function updateRechnungKopfdaten(
  id: string,
  input: { rechnungsdatum?: string | null; leistungsdatum?: string | null; empfaenger_email?: string | null },
): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

/** POST /rechnungen/{id}/positionen — Position hinzufügen, nur solange Entwurf. */
export function addPosition(rechnungId: string, input: PositionInput): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${rechnungId}/positionen`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** PATCH /rechnungen/{id}/positionen/{position_id} — Position ändern, nur solange Entwurf. */
export function updatePosition(
  rechnungId: string,
  positionId: string,
  input: PositionInput,
): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${rechnungId}/positionen/${positionId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

/** DELETE /rechnungen/{id}/positionen/{position_id} — Position entfernen, nur solange Entwurf. */
export function deletePosition(rechnungId: string, positionId: string): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${rechnungId}/positionen/${positionId}`, {
    method: "DELETE",
  });
}

/**
 * POST /rechnungen/{id}/freigabe — prüft Snapshot, erzeugt PDF-Vorschau,
 * versendet nichts. Empfänger/Betreff/Summen stammen aus gespeicherten Daten.
 */
export function rechnungFreigeben(id: string): Promise<FreigabeResult> {
  return apiFetch<FreigabeResult>(`/rechnungen/${id}/freigabe`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/** POST /rechnungen/{id}/senden — einziger Endpunkt, der tatsächlich versendet. */
export function rechnungSenden(id: string): Promise<SendenResult> {
  return apiFetch<SendenResult>(`/rechnungen/${id}/senden`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/** GET /rechnungen/{id}/pdf — kurzlebige, berechtigte Download-URL. */
export function getRechnungPdfUrl(id: string): Promise<{ download_url: string }> {
  return apiFetch<{ download_url: string }>(`/rechnungen/${id}/pdf`);
}

/** PATCH /rechnungen/{id}/zahlungsstatus — nur versendet: Offen/Bezahlt/Storniert. */
export function setzeZahlungsstatus(
  id: string,
  zahlungsstatus: Zahlungsstatus,
): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${id}/zahlungsstatus`, {
    method: "PATCH",
    body: JSON.stringify({ zahlungsstatus }),
  });
}

/** POST /rechnungen/{id}/storno — nur versendet: Original stornieren, Beleg bleibt lesbar. */
export function rechnungStornieren(id: string): Promise<Rechnung> {
  return apiFetch<Rechnung>(`/rechnungen/${id}/storno`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}
