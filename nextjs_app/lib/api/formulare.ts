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
  return apiFetch<{ items: RawFormularListeItem[]; total: number; limit: number; offset: number }>(
    `/formulare?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`,
  ).then(({ items, ...page }) => ({ ...page, items: items.map(mapListItem) }));
}

// --- Anlegen (Leerform oder Vorlage) --------------------------------------

export function createFormular(
  vorlage?: "shk" | "entruempelung",
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>("/formulare", {
    method: "POST",
    body: JSON.stringify(vorlage ? { vorlage } : {}),
  }).then(mapDraft);
}

// --- Draft lesen ----------------------------------------------------------

export function getFormular(id: string): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(`/formulare/${encodeURIComponent(id)}`).then(mapDraft);
}

// --- Name ändern ----------------------------------------------------------

export function renameFormular(
  id: string,
  name: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(`/formulare/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ name, draft_revision: draftRevision }),
  }).then(mapDraft);
}

export function setKomplexitaet(
  id: string,
  komplexitaet: Komplexitaet,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(`/formulare/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ komplexitaet, draft_revision: draftRevision }),
  }).then(mapDraft);
}

export function deleteFormular(id: string): Promise<void> {
  return apiFetch<void>(`/formulare/${encodeURIComponent(id)}`, { method: "DELETE" });
}

// --- Schritte -------------------------------------------------------------

export function addSchritt(
  id: string,
  titel: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte`,
    { method: "POST", body: JSON.stringify({ draft_revision: draftRevision }) },
  ).then(mapDraft);
}

export function renameSchritt(
  id: string,
  stepId: string,
  titel: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ titel, draft_revision: draftRevision }),
    },
  ).then(mapDraft);
}

export function deleteSchritt(
  id: string,
  stepId: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}?draft_revision=${encodeURIComponent(String(draftRevision))}`,
    { method: "DELETE" },
  ).then(mapDraft);
}

export function reorderSchritte(
  id: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/reihenfolge`,
    {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
    },
  ).then(mapDraft);
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
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder`,
    {
      method: "POST",
      body: JSON.stringify({ typ: payload.typ, draft_revision: draftRevision }),
    },
  ).then(mapDraft);
}

export function updateFeld(
  id: string,
  stepId: string,
  fieldId: string,
  payload: Partial<FeldPayload>,
  draftRevision: number,
): Promise<FormularDraft> {
  const { config, options, ...field } = payload;
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/${encodeURIComponent(fieldId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        ...field,
        ...configToApi(config),
        optionen: options,
        draft_revision: draftRevision,
      }),
    },
  ).then(mapDraft);
}

export function deleteFeld(
  id: string,
  stepId: string,
  fieldId: string,
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/${encodeURIComponent(fieldId)}?draft_revision=${encodeURIComponent(String(draftRevision))}`,
    { method: "DELETE" },
  ).then(mapDraft);
}

export function reorderFelder(
  id: string,
  stepId: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/schritte/${encodeURIComponent(stepId)}/felder/reihenfolge`,
    {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
    },
  ).then(mapDraft);
}

// --- Veröffentlichung -----------------------------------------------------

export interface Veroeffentlicht {
  version: { id: string; nummer: number; public_id: string; veroeffentlicht_am: string };
}

export function veroeffentlichen(id: string, draftRevision: number): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/veroeffentlichen`,
    { method: "POST", body: JSON.stringify({ draft_revision: draftRevision }) },
  ).then(mapDraft);
}

export function veroeffentlichungZuruecknehmen(id: string, draftRevision: number): Promise<FormularDraft> {
  return apiFetch<RawFormularDraft>(
    `/formulare/${encodeURIComponent(id)}/veroeffentlichung-zuruecknehmen`,
    { method: "POST", body: JSON.stringify({ draft_revision: draftRevision }) },
  ).then(mapDraft);
}

export function getEinbindung(id: string): Promise<Einbindung> {
  return apiFetch<{ direktlink: string; iframe: string; snippet: string }>(
    `/formulare/${encodeURIComponent(id)}/einbindung`,
  ).then(({ direktlink, iframe, snippet }) => ({ url: direktlink, iframe, javascript: snippet }));
}

// --- Öffentlich -----------------------------------------------------------

export function getPublicFormular(publicId: string): Promise<FormularSnapshot> {
  return publicApiFetch<RawPublicFormular>(
    `/public/formulare/${encodeURIComponent(publicId)}`,
  ).then(mapPublicFormular);
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
  uploads: Record<string, string[]>;
  honeypot: string;
  client_startzeit: string;
}

export function submitEinsendung(
  publicId: string,
  payload: EinsendungPayload,
): Promise<{ status: "erfolgreich" | "spam" }> {
  return publicApiFetch<{ status: "erfolgreich" | "spam" }>(
    `/public/formulare/${encodeURIComponent(publicId)}/einsendungen`,
    {
      method: "POST",
      body: JSON.stringify({
        uebermittlungskennung: payload.uebermittlungskennung,
        client_start: payload.client_startzeit,
        honeypot: payload.honeypot,
        werte: [
          ...Object.entries(payload.werte).map(([feld_id, wert]) => feldWertToApi(feld_id, wert)),
          ...Object.entries(payload.uploads).map(([feld_id, upload_ids]) => ({ feld_id, upload_ids })),
        ],
      }),
    },
  );
}

type RawFeld = Record<string, unknown> & { id: string; typ: Feldtyp; label: string; pflichtfeld: boolean };
type RawFormularDraft = Record<string, unknown> & { id: string; name: string; komplexitaet: Komplexitaet; draft_revision: number; veroeffentlicht: boolean; schritte: Array<Record<string, unknown> & { id: string; titel: string; felder: RawFeld[] }> };
type RawFormularListeItem = Record<string, unknown> & { id: string; name: string; draft_revision: number; veroeffentlicht: boolean; updated_at: string };
type RawPublicFormular = { name: string; modus: Komplexitaet; schritte: Array<{ titel: string; felder: RawFeld[] }> };

function configToApi(config?: FeldKonfiguration) {
  if (!config) return {};
  return { min: config.min, max: config.max, ganzzahl: config.ganzzahl, maxlaenge: config.maxLaenge, reg_exp: config.regex, datum_min: config.minDatum, datum_max: config.maxDatum, max_anzahl: config.maxAnzahl };
}

function mapFeld(feld: RawFeld) {
  return {
    id: feld.id,
    position: Number(feld.position ?? 0),
    typ: feld.typ,
    label: feld.label,
    hilfetext: String(feld.hilfetext ?? ""),
    pflichtfeld: feld.pflichtfeld,
    optional_in_einfach: Boolean(feld.optional_in_einfach),
    config: { min: feld.min as number | undefined, max: feld.max as number | undefined, ganzzahl: feld.ganzzahl as boolean | undefined, maxLaenge: feld.maxlaenge as number | undefined, regex: feld.reg_exp as string | undefined, minDatum: feld.datum_min as string | undefined, maxDatum: feld.datum_max as string | undefined, maxAnzahl: feld.max_anzahl as number | undefined },
    options: ((feld.optionen ?? []) as Array<Record<string, unknown>>).map((option, index) => ({ id: String(option.id ?? index), position: Number(option.position ?? index + 1), label: String(option.label), wert: String(option.wert) })),
    uebernahme: (feld.uebernahme ?? null) as UebernahmeFeld | null,
  };
}

function mapDraft(draft: RawFormularDraft): FormularDraft {
  return { id: draft.id, mandant_id: String(draft.mandant_id ?? ""), name: draft.name, komplexitaet: draft.komplexitaet, draft_revision: draft.draft_revision, veroeffentlicht: draft.veroeffentlicht, public_id: (draft.public_id ?? null) as string | null, version_nummer: null, schritte: draft.schritte.map((schritt, index) => ({ id: schritt.id, position: Number(schritt.position ?? index + 1), titel: schritt.titel, felder: schritt.felder.map(mapFeld) })) };
}

function mapListItem(item: RawFormularListeItem) {
  return { id: item.id, name: item.name, draft_revision: item.draft_revision, veroeffentlicht: item.veroeffentlicht, version_nummer: null, aktualisiert_am: item.updated_at };
}

function mapPublicFormular(formular: RawPublicFormular): FormularSnapshot {
  return { name: formular.name, komplexitaet: formular.modus, schritte: formular.schritte.map((schritt) => ({ titel: schritt.titel, felder: schritt.felder.map(mapFeld) })) };
}

function feldWertToApi(feld_id: string, wert: unknown) {
  if (Array.isArray(wert)) return { feld_id, werte: wert };
  if (typeof wert === "number") return { feld_id, zahl: wert };
  if (typeof wert === "boolean") return { feld_id, wert: String(wert) };
  if (wert && typeof wert === "object") return { feld_id, wert: Object.values(wert as Record<string, unknown>).filter(Boolean).join(" ") };
  return { feld_id, wert: wert == null ? "" : String(wert) };
}
