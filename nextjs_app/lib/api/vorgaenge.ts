import { apiFetch } from "@/lib/api/client";
import type { VorgangStatus } from "@/lib/theme/tokens";

export interface VorgangListItem {
  id: string;
  status: VorgangStatus;
  quelle: string;
  anliegen: string;
  kunde_id: string;
  kunde_name: string;
  objekt_id: string | null;
  objekt_adresse: string | null;
  zugewiesener_nutzer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface VorgangListResult {
  items: VorgangListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface VorgangHistorieEintrag {
  id: string;
  ereignis: string;
  detail: string | null;
  nutzer_id: string | null;
  created_at: string;
}

export interface VorgangDokument {
  id: string;
  dateiname: string;
  content_type: string;
  groesse_bytes: number;
  hochgeladen_von: string | null;
  created_at: string;
}

/** Backend liefert nur IDs, keine verschachtelten Kunde-/Objekt-Objekte — Seite lädt sie separat nach. */
export interface VorgangDetail {
  id: string;
  status: VorgangStatus;
  quelle: string;
  anliegen: string;
  notizen: string | null;
  kunde_id: string;
  objekt_id: string | null;
  zugewiesener_nutzer_id: string | null;
  created_at: string;
  updated_at: string;
  historie: VorgangHistorieEintrag[];
  dokumente: VorgangDokument[];
}

export interface VorgangInput {
  kunde_id: string;
  objekt_id?: string | null;
  anliegen: string;
  quelle?: string;
  notizen?: string;
  status?: VorgangStatus;
}

export interface VorgangPatch {
  status?: VorgangStatus;
  anliegen?: string;
  notizen?: string;
  objekt_id?: string | null;
}

export function listVorgaenge(params: {
  status?: VorgangStatus | "alle";
  suche?: string;
  kunde_id?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<VorgangListResult> {
  const qs = new URLSearchParams();
  if (params.status && params.status !== "alle") qs.set("status", params.status);
  if (params.suche) qs.set("q", params.suche);
  if (params.kunde_id) qs.set("kunde_id", params.kunde_id);
  qs.set("limit", String(params.limit ?? 20));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<VorgangListResult>(`/vorgaenge?${qs.toString()}`);
}

export function getVorgang(id: string): Promise<VorgangDetail> {
  return apiFetch<VorgangDetail>(`/vorgaenge/${id}`);
}

/** Backend gibt beim Anlegen ein VorgangListItem zurück (kein Detail mit Historie/Dokumenten). */
export function createVorgang(input: VorgangInput): Promise<VorgangListItem> {
  return apiFetch<VorgangListItem>("/vorgaenge", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateVorgang(id: string, patch: VorgangPatch): Promise<VorgangDetail> {
  return apiFetch<VorgangDetail>(`/vorgaenge/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function zuweisen(id: string, nutzerId: string): Promise<VorgangDetail> {
  return apiFetch<VorgangDetail>(`/vorgaenge/${id}/zuweisungen`, {
    method: "POST",
    body: JSON.stringify({ nutzer_id: nutzerId }),
  });
}

export function uploadDokument(vorgangId: string, datei: File): Promise<VorgangDokument> {
  const form = new FormData();
  form.append("datei", datei);
  return apiFetch<VorgangDokument>(`/vorgaenge/${vorgangId}/dokumente`, {
    method: "POST",
    body: form,
  });
}

/** Liefert eine kurzlebige, berechtigte Download-Adresse (presigned URL). */
export function dokumentDownloadUrl(
  vorgangId: string,
  dokumentId: string,
): Promise<{ download_url: string }> {
  return apiFetch<{ download_url: string }>(
    `/vorgaenge/${vorgangId}/dokumente/${dokumentId}/download`,
  );
}

/** 204 ohne Inhalt. */
export function deleteDokument(vorgangId: string, dokumentId: string): Promise<void> {
  return apiFetch(`/vorgaenge/${vorgangId}/dokumente/${dokumentId}`, { method: "DELETE" });
}
