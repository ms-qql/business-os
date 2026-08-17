import { apiFetch } from "@/lib/api/client";

export interface Kunde {
  id: string;
  name: string;
  email: string | null;
  telefon: string | null;
  notiz: string | null;
  created_at: string;
  updated_at: string;
}

export interface KundeListResult {
  items: Kunde[];
  total: number;
  limit: number;
  offset: number;
}

export interface KundeInput {
  name: string;
  email?: string;
  telefon?: string;
  notiz?: string;
}

/** Antwort auf Anlage: der neue Kunde flach + Hinweis auf mögliche Bestandskunden (kein Merge). */
export interface KundeCreateResult extends Kunde {
  moegliche_duplikate: Kunde[];
}

export function listKunden(params: {
  suche?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<KundeListResult> {
  const qs = new URLSearchParams();
  if (params.suche) qs.set("q", params.suche);
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<KundeListResult>(`/kunden?${qs.toString()}`);
}

export function getKunde(id: string): Promise<Kunde> {
  return apiFetch<Kunde>(`/kunden/${id}`);
}

export function createKunde(input: KundeInput): Promise<KundeCreateResult> {
  return apiFetch<KundeCreateResult>("/kunden", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateKunde(id: string, patch: Partial<KundeInput>): Promise<Kunde> {
  return apiFetch<Kunde>(`/kunden/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

/** Backend liefert 409, solange Vorgänge oder Rechnungen bestehen (AC: Löschsperre). 204 ohne Inhalt. */
export function deleteKunde(id: string): Promise<void> {
  return apiFetch(`/kunden/${id}`, { method: "DELETE" });
}

export interface Objekt {
  id: string;
  kunde_id: string;
  adresse: string;
  notiz: string | null;
  created_at: string;
}

export interface ObjektInput {
  adresse: string;
  notiz?: string;
}

export function listObjekte(kundeId: string): Promise<Objekt[]> {
  return apiFetch<Objekt[]>(`/kunden/${kundeId}/objekte`);
}

export function createObjekt(kundeId: string, input: ObjektInput): Promise<Objekt> {
  return apiFetch<Objekt>(`/kunden/${kundeId}/objekte`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
