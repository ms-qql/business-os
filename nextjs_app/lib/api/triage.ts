import { apiFetch } from "@/lib/api/client";

export type TriageStatus = "gruen" | "gelb" | "rot" | "nicht_bewertet";

/** Berechnetes Triage-Ergebnis aus GET /vorgaenge bzw. GET /vorgaenge/{id}. Nicht persistiert. */
export interface TriageErgebnis {
  status: TriageStatus;
  /** Deutschsprachige, nachvollziehbare Gründe, z. B. „Leistung nicht passend". */
  gruende: string[];
  /** ISO-Kalendertag des gepflegten „Nächster freier Termin", sofern vorhanden. */
  naechster_freier_termin?: string | null;
}

export type LeistungswertKlassifikation = "passend" | "unpassend";

export interface TriageLeistungswert {
  /** Stabiler Optionswert des konfigurierten Leistungsfeldes (nicht das sichtbare Label). */
  wert: string;
  klassifikation: LeistungswertKlassifikation;
}

/** Aktuelle Triage-Konfiguration eines Mandanten (genau eine Zeile). Bei fehlender Zeile leer. */
export interface TriageEinstellung {
  leistungs_formular_id: string | null;
  leistungs_feld_id: string | null;
  wunschtermin_feld_id: string | null;
  /** ISO-Kalendertag (YYYY-MM-DD) oder null, wenn kein Termin gepflegt ist. */
  naechster_freier_termin: string | null;
  leistungswerte: TriageLeistungswert[];
}

/** Vollständige Konfiguration für den atomaren PUT (Inhaber). */
export interface TriageEinstellungInput {
  leistungs_formular_id: string;
  leistungs_feld_id: string;
  wunschtermin_feld_id?: string | null;
  leistungswerte: TriageLeistungswert[];
}

/** Inhaber und Büro lesen; bei fehlender Zeile leere Konfiguration (kein Fehler). */
export function getTriageEinstellung(): Promise<TriageEinstellung> {
  return apiFetch<TriageEinstellung>("/triage/einstellung");
}

/** Inhaber: atomar Formular, Leistungsfeld, optionales Wunschdatumfeld und Werteliste speichern. */
export function putTriageEinstellung(input: TriageEinstellungInput): Promise<TriageEinstellung> {
  return apiFetch<TriageEinstellung>("/triage/einstellung", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/** Inhaber: „Nächster freier Termin" setzen (ISO-Kalendertag) oder mit null entfernen. */
export function patchTriageKapazitaet(naechsterFreierTermin: string | null): Promise<TriageEinstellung> {
  return apiFetch<TriageEinstellung>("/triage/einstellung/kapazitaet", {
    method: "PATCH",
    body: JSON.stringify({ naechster_freier_termin: naechsterFreierTermin }),
  });
}
