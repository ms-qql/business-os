import { apiFetch, ApiError } from "@/lib/api/client";
import type {
  LandingpageState,
  SektionTyp,
  SektionInhaltUnion,
  WebsiteSection,
} from "@/lib/website-builder-types";

/**
 * Client für den Inhaber-Baukasten (/website-builder/*). Jede Mutation
 * sendet die erwartete `version` und liefert den vollständigen neuen
 * Builder-Zustand zurück. Bei Version-Spiels (parallele Bearbeitung) wirft
 * der Server 409 — der Editor bietet dann „Neu laden“ an, statt Eingaben
 * still zu verwerfen.
 *
 * Vertrag (siehe builder_routes.py / builder_schemas.py):
 *  - DELETE /sections/{id}?version=…  (version als Query)
 *  - POST/DELETE /sections/{id}/bild?version=…  (version als Query, alt_text im Formular)
 *  - PUT /sections/reihenfolge  Body: { version, ordered_ids: [...] } (nicht "ids")
 */

/** Konflikt beim Speichern (serverseitige 409). */
export class BuilderConflictError extends ApiError {
  constructor(message: string) {
    super(409, message);
    this.name = "BuilderConflictError";
  }
}

export function isConflict(err: unknown): boolean {
  return err instanceof ApiError && err.status === 409;
}

// --- Lesen ----------------------------------------------------------------

export function getLandingpage(): Promise<LandingpageState> {
  return apiFetch<LandingpageState>("/website-builder/startseite");
}

// --- Initialisieren (idempotent, Defaultseite) ----------------------------

export function initialisiereLandingpage(): Promise<LandingpageState> {
  return apiFetch<LandingpageState>("/website-builder/startseite/initialisieren", {
    method: "POST",
  });
}

// --- Sektion hinzufügen ---------------------------------------------------

export function addSection(typ: SektionTyp, version: number): Promise<LandingpageState> {
  return apiFetch<LandingpageState>("/website-builder/sections", {
    method: "POST",
    body: JSON.stringify({ type: typ, version }),
  });
}

// --- Sektion bearbeiten (nur passende Felder + visible) -------------------

export function updateSection(
  sectionId: string,
  payload: { inhalt: SektionInhaltUnion; visible?: boolean; version: number },
): Promise<LandingpageState> {
  return apiFetch<LandingpageState>(`/website-builder/sections/${sectionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

// --- Reihenfolge (vollständige, duplikatfreie ID-Liste) -------------------

export function reorderSections(ids: string[], version: number): Promise<LandingpageState> {
  return apiFetch<LandingpageState>("/website-builder/sections/reihenfolge", {
    method: "PUT",
    body: JSON.stringify({ version, ordered_ids: ids }),
  });
}

// --- Sektion löschen (version als Query) ----------------------------------

export function deleteSection(sectionId: string, version: number): Promise<LandingpageState> {
  return apiFetch<LandingpageState>(
    `/website-builder/sections/${sectionId}?version=${encodeURIComponent(String(version))}`,
    { method: "DELETE" },
  );
}

// --- Bild hochladen / entfernen (version als Query) -----------------------

export function uploadSectionBild(
  sectionId: string,
  datei: File,
  altText: string,
  version: number,
): Promise<LandingpageState> {
  const form = new FormData();
  form.append("datei", datei);
  form.append("alt_text", altText);
  return apiFetch<LandingpageState>(
    `/website-builder/sections/${sectionId}/bild?version=${encodeURIComponent(String(version))}`,
    { method: "POST", body: form },
  );
}

export function deleteSectionBild(sectionId: string, version: number): Promise<LandingpageState> {
  return apiFetch<LandingpageState>(
    `/website-builder/sections/${sectionId}/bild?version=${encodeURIComponent(String(version))}`,
    { method: "DELETE" },
  );
}

/** Findet eine Sektion anhand ihrer ID im Zustand. */
export function findSection(state: LandingpageState, id: string): WebsiteSection | undefined {
  return state.sections.find((s) => s.id === id);
}
