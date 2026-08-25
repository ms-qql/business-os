import { apiFetch } from "@/lib/api/client";
import type { Angebot } from "@/lib/api/angebote";

/**
 * Gewerke-Kalkulationseinheiten (PROJ-22).
 *
 * Vertrag exakt nach Backend (app/features/gewerke/schemas.py + angebote/routes.py).
 * Alle Schreibpfade sind Inhaber/Büro; Monteur erhält keinen Zugriff. Mandantenzugehörigkeit
 * wird serverseitig aus dem JWT abgeleitet — kein mandant_id im Request.
 */

export type Kostenart = "lohn" | "material" | "fremdleistung" | "sonstiges_geraete";

export const KOSTENART_LABELS: Record<Kostenart, string> = {
  lohn: "Lohn",
  material: "Material",
  fremdleistung: "Fremdleistung",
  sonstiges_geraete: "Sonstiges/Geräte",
};

export type GewerkKalkulationsart = "je_einheit" | "gesamtpreis";

export const KALKULATIONSART_LABELS: Record<GewerkKalkulationsart, string> = {
  je_einheit: "je Einheit",
  gesamtpreis: "Gesamtpreis",
};

/** Kostenzeile eines Gewerks (Eingabe + Antwort). */
export interface Kostenzeile {
  id: string;
  kostenart: Kostenart;
  beschreibung: string | null;
  menge: number;
  einheit: string;
  ek_einzelpreis: number;
  zuschlag_prozent: number;
  /** Serverseitig berechneter Verkaufspreis der Zeile (2 Dezimalstellen). */
  vk_preis: number;
}

/** Listen-Eintrag (GewerkListe.items). */
export interface GewerkKurz {
  id: string;
  bezeichnung: string;
  einheit: string;
  kalkulationsart: GewerkKalkulationsart;
  kategorie_id: string | null;
  /** Berechneter Verkaufspreis (VK-Summe der Zeilen). */
  vk_preis: number;
}

export interface GewerkDetail {
  id: string;
  bezeichnung: string;
  einheit: string;
  kalkulationsart: GewerkKalkulationsart;
  kategorie_id: string | null;
  langbeschreibung: string | null;
  steuersatz: number;
  kostenzeilen: Kostenzeile[];
  /** Berechneter Verkaufspreis (VK-Summe der Zeilen). */
  vk_preis: number;
}

export interface GewerkKategorie {
  id: string;
  name: string;
  anzahl_gewerke: number;
}

export interface GewerkListe {
  items: GewerkKurz[];
}

// --- Eingabe-Payloads ---

export interface KostenzeileInput {
  kostenart: Kostenart;
  beschreibung?: string | null;
  menge: number;
  einheit: string;
  ek_einzelpreis: number;
  zuschlag_prozent: number;
}

export interface GewerkInput {
  bezeichnung: string;
  einheit: string;
  kalkulationsart: GewerkKalkulationsart;
  kategorie_id?: string | null;
  langbeschreibung?: string | null;
  steuersatz?: number;
  kostenzeilen: KostenzeileInput[];
  /** Bestätigt eine Warnung bei gleicher Bezeichnung + Einheit im Mandanten. */
  duplikat_bestaetigt?: boolean;
}

export interface KategorieInput {
  name: string;
}

// --- Endpunkte: Kategorien ---

export function getKategorien(): Promise<GewerkKategorie[]> {
  return apiFetch<GewerkKategorie[]>("/gewerke/kategorien");
}

export function addKategorie(input: KategorieInput): Promise<GewerkKategorie> {
  return apiFetch<GewerkKategorie>("/gewerke/kategorien", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateKategorie(id: string, input: KategorieInput): Promise<GewerkKategorie> {
  return apiFetch<GewerkKategorie>(`/gewerke/kategorien/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteKategorie(id: string): Promise<void> {
  return apiFetch<void>(`/gewerke/kategorien/${id}`, { method: "DELETE" });
}

// --- Endpunkte: Gewerke ---

export function getGewerke(params?: {
  suchbegriff?: string;
  kategorie_id?: string;
}): Promise<GewerkListe> {
  const qs = new URLSearchParams();
  if (params?.suchbegriff) qs.set("suchbegriff", params.suchbegriff);
  if (params?.kategorie_id) qs.set("kategorie_id", params.kategorie_id);
  const q = qs.toString();
  return apiFetch<GewerkListe>(`/gewerke${q ? `?${q}` : ""}`);
}

export function getGewerk(id: string): Promise<GewerkDetail> {
  return apiFetch<GewerkDetail>(`/gewerke/${id}`);
}

export function addGewerk(input: GewerkInput): Promise<GewerkDetail> {
  return apiFetch<GewerkDetail>("/gewerke", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateGewerk(id: string, input: GewerkInput): Promise<GewerkDetail> {
  return apiFetch<GewerkDetail>(`/gewerke/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteGewerk(id: string): Promise<void> {
  return apiFetch<void>(`/gewerke/${id}`, { method: "DELETE" });
}

// --- Endpunkt: Übernahme in ein Angebot (Snapshot, keine Live-Referenz) ---

export interface GewerkUebernahmeInput {
  gewerk_id: string;
  menge: number;
  sortierung?: number;
}

export function gewerkInAngebotUebernehmen(
  angebotId: string,
  input: GewerkUebernahmeInput,
): Promise<Angebot> {
  return apiFetch<Angebot>(`/angebote/${angebotId}/positionen/aus-gewerk`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

// --- Endpunkt: Interner Preis-Override einer kalkulierten Position ---

export interface PreisOverrideInput {
  einzelpreis: number;
  begruendung?: string | null;
}

export function positionPreisOverride(
  angebotId: string,
  positionId: string,
  input: PreisOverrideInput,
): Promise<Angebot> {
  return apiFetch<Angebot>(
    `/angebote/${angebotId}/positionen/${positionId}/preis-override`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
}
