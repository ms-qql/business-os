import { apiFetch } from "@/lib/api/client";

export interface WebsiteLeistung {
  slug: string;
  titel: string;
  aktiv: boolean;
  kurzbeschreibung: string;
  inhalt: string;
}

export interface WebsiteSettings {
  firmenname: string;
  logo_url: string | null;
  marken_farbe: string | null;
  telefon: string | null;
  email: string | null;
  adresse: string | null;
  oeffnungszeiten: string | null;
  ueber_uns: string | null;
  domain: string | null;
  domain_status: string | null;
  leistungen: WebsiteLeistung[];
}

export type WebsiteSettingsPatch = Partial<
  Omit<WebsiteSettings, "domain" | "domain_status" | "logo_url">
>;

/** Nur für angemeldete Inhaber — Backend erzwingt require_role("Inhaber"). */
export function getWebsiteSettings(): Promise<WebsiteSettings> {
  return apiFetch<WebsiteSettings>("/website-settings");
}

export function updateWebsiteSettings(
  patch: WebsiteSettingsPatch,
): Promise<WebsiteSettings> {
  return apiFetch<WebsiteSettings>("/website-settings", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export interface LogoUploadResult {
  logo_url: string;
}

export function uploadLogo(datei: File): Promise<LogoUploadResult> {
  const form = new FormData();
  form.append("datei", datei);
  return apiFetch<LogoUploadResult>("/website-settings/logo", {
    method: "POST",
    body: form,
  });
}
