import { apiFetch, publicApiFetch, ApiError } from "@/lib/api/client";
import type {
  Einbindung,
  FeldKonfiguration,
  FormularDraft,
  FormularListe,
  FormularSnapshot,
  Feldtyp,
  Komplexitaet,
  UebernahmeFeld,
} from "@/lib/schemas/formular";

/** Serverseitiger Versionskonflikt (parallele Bearbeitung) → 409. */
export class FormularConflictError extends ApiError {
  constructor(message: string) {
    super(409, message);
    this.name = "FormularConflictError";
  }
}

export function isFormularConflict(err: unknown): boolean {
  return err instanceof ApiError && err.status === 409;
}

// --- Liste ----------------------------------------------------------------

export function getFormulare(limit = 50, offset = 0): Promise<FormularListe> {
  return apiFetch<FormularListe>(
    `/formulare?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`,
  );
}

// --- Anlegen (Leerform oder Vorlage) --------------------------------------

export function createFormular(
  vorlage?: "shk" | "entruempelung",
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>("/formulare", {
    method: "POST",
    body: JSON.stringify(vorlage ? { vorlage } : {}),
  });
}

// --- Draft lesen ----------------------------------------------------------

export function getFormular(id: string): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(`/formulare/${encodeURIComponent(id)}`);
}

// --- Name ändern ----------------------------------------------------------

export function renameFormular(
  id: string,
  name: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(`/formulare/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ name, draft_revision: draftRevision }),
  });
}

export function setKomplexitaet(
  id: string,
  komplexitaet: Komplexitaet,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(`/formulare/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ komplexitaet, draft_revision: draftRevision }),
  });
}

// --- Schritte -------------------------------------------------------------

export function addSchritt(
  id: string,
  titel: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte`,
    { method: "POST", body: JSON.stringify({ titel, draft_revision: draftRevision }) },
  );
}

export function renameSchritt(
  id: string,
  stepId: string,
  titel: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ titel, draft_revision: draftRevision }),
    },
  );
}

export function deleteSchritt(
  id: string,
  stepId: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}?draft_revision=${encodeURIComponent(String(draftRevision))}`,
    { method: "DELETE" },
  );
}

export function reorderSchritte(
  id: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/reihenfolge`,
    {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
    },
  );
}

// --- Felder ---------------------------------------------------------------

interface OptionPayload {
  label: string;
  wert: string;
}

interface FeldPayload {
  typ?: Feldtyp;
  label?: string;
  hilfetext?: string;
  pflichtfeld?: boolean;
  optional_in_einfach?: boolean;
  config?: FeldKonfiguration;
  uebernahme?: UebernahmeFeld | null;
  options?: OptionPayload[];
}

export function addFeld(
  id: string,
  stepId: string,
  payload: FeldPayload,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder`,
    {
      method: "POST",
      body: JSON.stringify({ ...payload, draft_revision: draftRevision }),
    },
  );
}

export function updateFeld(
  id: string,
  stepId: string,
  fieldId: string,
  payload: Partial<FeldPayload>,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/${encodeURIComponent(fieldId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ ...payload, draft_revision: draftRevision }),
    },
  );
}

export function deleteFeld(
  id: string,
  stepId: string,
  fieldId: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/${encodeURIComponent(fieldId)}?draft_revision=${encodeURIComponent(String(draftRevision))}`,
    { method: "DELETE" },
  );
}

export function reorderFelder(
  id: string,
  stepId: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/reihenfolge`,
    {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
    },
  );
}

// --- Veröffentlichung -----------------------------------------------------

export interface Veroeffentlicht {
  version: { id: string; nummer: number; public_id: string; veroeffentlicht_am: string };
}

export function veroeffentlichen(id: string): Promise<Veroeffentlicht> {
  return apiFetch<Veroeffentlicht>(
    `/formulare/${encodeURIComponent(id)}/veroeffentlichen`,
    { method: "POST" },
  );
}

export function veroeffentlichungZuruecknehmen(id: string): Promise<FormularDraft> {
  return apiFetch<FormularDraft>(
    `/formulare/${encodeURIComponent(id)}/veroeffentlichung-zuruecknehmen`,
    { method: "POST" },
  );
}

export function getEinbindung(id: string): Promise<Einbindung> {
  return apiFetch<Einbindung>(`/formulare/${encodeURIComponent(id)}/einbindung`);
}

// --- Öffentlich -----------------------------------------------------------

export function getPublicFormular(publicId: string): Promise<FormularSnapshot> {
  return publicApiFetch<FormularSnapshot>(
    `/public/formulare/${encodeURIComponent(publicId)}`,
  );
}

export interface PublicUpload {
  upload_id: string;
}

export function uploadFormularDatei(
  publicId: string,
  datei: File,
  feldId: string,
  uebermittlungskennung: string,
): Promise<PublicUpload> {
  const form = new FormData();
  form.append("datei", datei);
  form.append("feld_id", feldId);
  form.append("uebermittlungskennung", uebermittlungskennung);
  return publicApiFetch<PublicUpload>(
    `/public/formulare/${encodeURIComponent(publicId)}/uploads`,
    { method: "POST", body: form },
  );
}

export interface EinsendungPayload {
  uebermittlungskennung: string;
  werte: Record<string, unknown>;
  upload_ids: string[];
  honeypot: string;
  client_startzeit: string;
}

export function submitEinsendung(
  publicId: string,
  payload: EinsendungPayload,
): Promise<{ ok: boolean }> {
  return publicApiFetch<{ ok: boolean }>(
    `/public/formulare/${encodeURIComponent(publicId)}/einsendungen`,
    { method: "POST", body: JSON.stringify(payload) },
  );
}
