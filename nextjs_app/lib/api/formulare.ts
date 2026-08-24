import { apiFetch, ApiError } from "@/lib/api/client";
import type {
  Feld,
  FeldTyp,
  FormularEinbindung,
  FormularEntwurf,
  FormularListeResult,
  Komplexitaet,
  Schritt,
  UebernahmeZuordnung,
} from "@/lib/schemas/formular";

/** Konflikt beim Speichern (serverseitige 409 wegen veralteter draft_revision). */
export class FormularConflictError extends ApiError {
  constructor(message: string) {
    super(409, message);
    this.name = "FormularConflictError";
  }
}

export function isFormularConflict(err: unknown): boolean {
  return err instanceof ApiError && err.status === 409;
}

// --- Liste / Anlage -------------------------------------------------------

export function listFormulare(params: {
  limit?: number;
  offset?: number;
} = {}): Promise<FormularListeResult> {
  const qs = new URLSearchParams();
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<FormularListeResult>(`/formulare?${qs.toString()}`);
}

/** Leerformular oder Branchenvorlage (shk/entruempelung). */
export function createFormular(vorlage?: "shk" | "entruempelung"): Promise<FormularEntwurf> {
  const body = vorlage ? { vorlage } : {};
  return apiFetch<FormularEntwurf>("/formulare", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// --- Entwurf lesen / benennen --------------------------------------------

export function getFormular(id: string): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}`);
}

export function renameFormular(
  id: string,
  name: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name, draft_revision: draftRevision }),
  });
}

export function setKomplexitaet(
  id: string,
  komplexitaet: Komplexitaet,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ komplexitaet, draft_revision: draftRevision }),
  });
}

// --- Schritte -------------------------------------------------------------

export function addSchritt(
  id: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}/schritte`, {
    method: "POST",
    body: JSON.stringify({ draft_revision: draftRevision }),
  });
}

export function updateSchritt(
  id: string,
  schrittId: string,
  titel: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}/schritte/${schrittId}`, {
    method: "PATCH",
    body: JSON.stringify({ titel, draft_revision: draftRevision }),
  });
}

export function deleteSchritt(
  id: string,
  schrittId: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(
    `/formulare/${id}/schritte/${schrittId}?draft_revision=${encodeURIComponent(
      String(draftRevision),
    )}`,
    { method: "DELETE" },
  );
}

export function reorderSchritte(
  id: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}/schritte/reihenfolge`, {
    method: "PUT",
    body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
  });
}

// --- Felder ---------------------------------------------------------------

export function addFeld(
  id: string,
  schrittId: string,
  typ: FeldTyp,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(
    `/formulare/${id}/schritte/${schrittId}/felder`,
    {
      method: "POST",
      body: JSON.stringify({ typ, draft_revision: draftRevision }),
    },
  );
}

/** Vollständig validierter Editorzustand eines Felds. */
export interface FeldUpdate {
  label: string;
  hilfetext?: string | null;
  pflichtfeld: boolean;
  optional_in_einfach: boolean;
  uebernahme?: UebernahmeZuordnung | null;
  min?: number | null;
  max?: number | null;
  ganzzahl?: boolean;
  reg_exp?: string | null;
  maxlaenge?: number | null;
  datum_min?: string | null;
  datum_max?: string | null;
  max_anzahl?: number | null;
  optionen?: { label: string; wert: string }[];
}

export function updateFeld(
  id: string,
  schrittId: string,
  feldId: string,
  update: FeldUpdate,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(
    `/formulare/${id}/schritte/${schrittId}/felder/${feldId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ ...update, draft_revision: draftRevision }),
    },
  );
}

export function deleteFeld(
  id: string,
  schrittId: string,
  feldId: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(
    `/formulare/${id}/schritte/${schrittId}/felder/${feldId}?draft_revision=${encodeURIComponent(
      String(draftRevision),
    )}`,
    { method: "DELETE" },
  );
}

export function reorderFelder(
  id: string,
  schrittId: string,
  orderedIds: string[],
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(
    `/formulare/${id}/schritte/${schrittId}/felder/reihenfolge`,
    {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds, draft_revision: draftRevision }),
    },
  );
}

// --- Publish / Einbindung -------------------------------------------------

export function publishFormular(
  id: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}/veroeffentlichen`, {
    method: "POST",
    body: JSON.stringify({ draft_revision: draftRevision }),
  });
}

export function unpublishFormular(
  id: string,
  draftRevision: number,
): Promise<FormularEntwurf> {
  return apiFetch<FormularEntwurf>(`/formulare/${id}/veroeffentlichung-zuruecknehmen`, {
    method: "POST",
    body: JSON.stringify({ draft_revision: draftRevision }),
  });
}

export function getEinbindung(id: string): Promise<FormularEinbindung> {
  return apiFetch<FormularEinbindung>(`/formulare/${id}/einbindung`);
}

/** Findet ein Feld anhand der ID im Entwurf. */
export function findFeld(entwurf: FormularEntwurf, feldId: string): Feld | undefined {
  for (const s of entwurf.schritte) {
    const f = s.felder.find((x) => x.id === feldId);
    if (f) return f;
  }
  return undefined;
}

/** Findet einen Schritt anhand der ID im Entwurf. */
export function findSchritt(
  entwurf: FormularEntwurf,
  schrittId: string,
): Schritt | undefined {
  return entwurf.schritte.find((s) => s.id === schrittId);
}
