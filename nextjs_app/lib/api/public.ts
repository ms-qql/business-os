import { API_BASE } from "@/lib/session";

/** Fehler eines öffentlichen (nicht angemeldeten) API-Aufrufs. */
export class PublicApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "PublicApiError";
  }
}

async function publicRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const message =
      (data && (data.detail as string)) ||
      `Anfrage fehlgeschlagen (${res.status}).`;
    throw new PublicApiError(res.status, message);
  }
  return data as T;
}

export interface PublicLeistung {
  slug: string;
  titel: string;
  kurzbeschreibung: string;
}

export interface PublicLeistungDetail extends PublicLeistung {
  inhalt: string;
}

export interface PublicSite {
  firmenname: string;
  logo_url: string | null;
  marken_farbe: string | null;
  telefon: string | null;
  email: string | null;
  adresse: string | null;
  oeffnungszeiten: string | null;
  ueber_uns: string | null;
  leistungen: PublicLeistung[];
}

/** Website-Einstellungen + aktive Leistungen für die aufgelöste Betriebsdomain. */
export function getPublicSite(): Promise<PublicSite> {
  return publicRequest<PublicSite>("/public/site");
}

/** Eine aktive Leistungsseite; 404, wenn inaktiv/unbekannt (wie „nicht vorhanden“ behandelt). */
export function getPublicLeistung(slug: string): Promise<PublicLeistungDetail> {
  return publicRequest<PublicLeistungDetail>(
    `/public/leistungen/${encodeURIComponent(slug)}`,
  );
}

export interface AnfrageUpload {
  upload_id: string;
}

/** Ein Bild für den laufenden Formularversuch hochladen (serverseitig geprüft). */
export function uploadAnfrageBild(
  datei: File,
  uebermittlungskennung: string,
): Promise<AnfrageUpload> {
  const form = new FormData();
  form.append("uebermittlungskennung", uebermittlungskennung);
  form.append("datei", datei);
  return publicRequest<AnfrageUpload>("/public/anfragen/uploads", {
    method: "POST",
    body: form,
  });
}

export type Kontaktweg = "Telefon" | "E-Mail";
export type Dringlichkeit = "Normal" | "Dringend";

export interface AnfrageInput {
  name: string;
  kontaktweg: Kontaktweg;
  telefon?: string;
  email?: string;
  adresse: string;
  anliegen: string;
  dringlichkeit: Dringlichkeit;
  zeitfenster?: string;
  uebermittlungskennung: string;
  upload_ids: string[];
}

/**
 * Anfrage einmalig einreichen. `uebermittlungskennung` macht Wiederholungen
 * (z. B. nach Netzabbruch) idempotent — der Server erzeugt pro Kennung
 * höchstens einen Vorgang.
 */
export function submitAnfrage(input: AnfrageInput): Promise<{ ok: boolean }> {
  return publicRequest("/public/anfragen", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
