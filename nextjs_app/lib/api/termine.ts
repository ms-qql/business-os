import { apiFetch } from "@/lib/api/client";

/** Spiegelt den API-Vertrag aus features/PROJ-6-...md (Tech Design, Abschnitt API-Form). */

export interface TerminMonteur {
  nutzer_id: string;
  name: string;
  aktiv: boolean;
}

/** Eingebetteter Kundenkontakt — nur in GET /termine/{id}, niemals Preis-/Rechnungsfelder (AC-5). */
export interface TerminKontakt {
  name: string;
  telefon: string | null;
  email: string | null;
}

export interface Termin {
  id: string;
  mandant_id: string;
  vorgang_id: string;
  beginn: string; // ISO (UTC), serverseitig Europa/Berlin
  ende: string; // ISO (UTC)
  adresse: string | null;
  notiz: string | null;
  abgesagt_at: string | null;
  anliegen: string;
  monteure: TerminMonteur[];
  konflikt: boolean;
  konflikt_monteure: string[]; // IDs betroffener Monteure (AC-4)
  /** Nur in Detail (GET /termine/{id}): eingebetteter Kontakt, für Monteuransicht ohne Preise. */
  kontakt?: TerminKontakt | null;
    /** True, wenn dieser Termin dem aktuellen Betrachter gehört (Monteuransicht). */
  ist_eigen?: boolean;
}

export interface TerminListItem {
  id: string;
  vorgang_id: string;
  beginn: string;
  ende: string;
  adresse: string | null;
  notiz: string | null;
  abgesagt_at: string | null;
  anliegen: string;
  monteure: TerminMonteur[];
  konflikt: boolean;
  konflikt_monteure: string[];
}

export interface TerminListResult {
  items: TerminListItem[];
  konflikt_monteure: string[]; // IDs aller Monteure mit Überschneidung im Fenster
  total: number;
}

export interface TerminErgebnis {
  termin: Termin;
  konflikt: boolean;
  konflikt_monteure: string[];
}

export interface KonfliktHinweis {
  konflikt: boolean;
  konflikt_monteure: string[];
}

export interface TerminInput {
  vorgang_id: string;
  beginn: string; // ISO
  ende: string; // ISO
  adresse?: string | null;
  notiz?: string | null;
  monteure: string[]; // Nutzer-IDs (Rolle Monteur)
}

export interface VorgangOption {
  id: string;
  anliegen: string;
}

export interface MonteurOption {
  id: string;
  name: string;
  aktiv: boolean;
}

/** GET /termine?von=&bis=&nutzer_ids= — Kalenderfenster (Wochenansicht lädt nur sichtbaren Zeitraum). */
export function listTermine(params: {
  von: string;
  bis: string;
  nutzer_ids?: string[];
}): Promise<TerminListResult> {
  const qs = new URLSearchParams();
  qs.set("von", params.von);
  qs.set("bis", params.bis);
  if (params.nutzer_ids && params.nutzer_ids.length > 0) {
    qs.set("nutzer_ids", params.nutzer_ids.join(","));
  }
  return apiFetch<TerminListResult>(`/termine?${qs.toString()}`);
}

/** GET /termine/{id} — inkl. eingebettetem Kundenkontakt (AC-5), kein zweiter Request nötig. */
export function getTermin(id: string): Promise<Termin> {
  return apiFetch<Termin>(`/termine/${id}`);
}

/** POST /termine — anlegen; validiert ende > beginn (422) und vorgang im Mandanten (422). */
export function createTermin(input: TerminInput): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>("/termine", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** PATCH /termine/{id} — ändern/verschieben; Antwort enthält konflikt-Flag (AC-4). */
export function updateTermin(id: string, input: TerminInput): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>(`/termine/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

/** POST /termine/{id}/absagen — Termin absagen (kein hartes Löschen, bleibt in Historie). */
export function terminAbsagen(id: string): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>(`/termine/${id}/absagen`, { method: "POST" });
}

/** POST /termine/{id}/zuweisungen — Monteur zuweisen. */
export function terminZuweisen(id: string, nutzerId: string): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>(`/termine/${id}/zuweisungen`, {
    method: "POST",
    body: JSON.stringify({ nutzer_id: nutzerId }),
  });
}

/** DELETE /termine/{id}/zuweisungen/{nutzer_id} — Monteur entziehen. */
export function terminEntziehen(id: string, nutzerId: string): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>(`/termine/${id}/zuweisungen/${nutzerId}`, {
    method: "DELETE",
  });
}

/** GET /nutzer/monteure — aktive Monteure des Mandanten für die Auswahl im Termin-Dialog. */
export function listMonteure(): Promise<MonteurOption[]> {
  return apiFetch<MonteurOption[]>("/nutzer/monteure");
}

/** GET /vorgaenge?status=alle — Vorgänge zur Auswahl im Termin-Dialog (nur eigener Mandant). */
export function listVorgangOptionen(): Promise<VorgangOption[]> {
  const qs = new URLSearchParams();
  qs.set("limit", "100");
  qs.set("status", "alle");
  return apiFetch<{ items: VorgangOption[] }>(`/vorgaenge?${qs.toString()}`).then(
    (r) => r.items,
  );
}

/** Vorgangs-verknüpfte Liste (Nested-Route, wie PROJ-5 Angebote). */
export function listVorgangTermine(vorgangId: string): Promise<TerminListItem[]> {
  return apiFetch<TerminListItem[]>(`/vorgaenge/${vorgangId}/termine`);
}

/** Vorgangs-verknüpftes Anlegen (Nested-Route). */
export function createVorgangTermin(
  vorgangId: string,
  input: Omit<TerminInput, "vorgang_id">,
): Promise<TerminErgebnis> {
  return apiFetch<TerminErgebnis>(`/vorgaenge/${vorgangId}/termine`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
