import { apiFetch } from "@/lib/api/client";

/**
 * Onboarding-Endpunkte (PROJ-7). Verträge exakt nach Tech Design, Abschnitt E.
 * Alle Endpunkte sind Inhaber-only; der Server leitet mandant_id aus dem JWT ab.
 */

export type OnboardingSchrittStatus = "offen" | "in_bearbeitung" | "erledigt";

export type OnboardingSchrittId =
  | "betriebsdaten"
  | "branding"
  | "leistungsseiten"
  | "domain"
  | "postfach"
  | "preisliste"
  | "testanfrage";

export interface OnboardingPostfachTest {
  imap_ok: boolean;
  smtp_ok: boolean;
  tested_at: string | null;
}

export interface OnboardingTestvorgang {
  vorgang_id: string;
  erstellt_am: string;
  anfrage_id?: string;
}

export interface OnboardingSchritt {
  id: OnboardingSchrittId;
  titel: string;
  status: OnboardingSchrittStatus;
  /** Konkrete, fehlende Eingabe auf Deutsch (z. B. "Markenfarbe fehlt"). Leer, wenn erledigt. */
  fehlende_eingabe: string | null;
  /** Ziel der betroffenen Einstellungsfläche, z. B. "Website-Einstellungen". */
  bearbeitungsziel: string;
  pflicht: boolean;
  domain_status?: string | null;
  postfach_test?: OnboardingPostfachTest | null;
  testvorgang?: OnboardingTestvorgang | null;
}

export interface OnboardingStatus {
  schritte: OnboardingSchritt[];
  /** True, wenn bereits veröffentlicht (Domain aktiv) — Website bleibt dann online trotz offener Schritte. */
  veroeffentlicht: boolean;
  veroeffentlicht_am: string | null;
  /** Warnung, wenn eine bereits live Website einen Pflichtschritt verliert (nachträglich unvollständig). */
  warnung?: string | null;
}

/** GET /onboarding — berechneter Fortschritt aller sieben Schritte. Inhaber-only. */
export function getOnboarding(): Promise<OnboardingStatus> {
  return apiFetch<OnboardingStatus>("/onboarding");
}

/** PUT /onboarding/domain — reserviert hostname mit Status inaktiv. Inhaber-only. */
export function setOnboardingDomain(hostname: string): Promise<{ hostname: string; status: string }> {
  return apiFetch<{ hostname: string; status: string }>("/onboarding/domain", {
    method: "PUT",
    body: JSON.stringify({ hostname }),
  });
}

export interface PostfachTestResult {
  imap_ok: boolean;
  smtp_ok: boolean;
  ok: boolean;
  detail: string;
}

/**
 * POST /onboarding/postfach-test — testet Empfang und Versand der gespeicherten,
 * verschlüsselten Konfiguration. Kein Passwort im Request/Response. Inhaber-only.
 */
export function startPostfachTest(): Promise<PostfachTestResult> {
  return apiFetch<PostfachTestResult>("/onboarding/postfach-test", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export interface TestvorgangResult {
  vorgang_id: string;
  anfrage_id: string;
  ist_test: boolean;
  erstellt_am: string;
}

/** POST /onboarding/testvorgang — erzeugt einen gekennzeichneten Testvorgang samt Test-Stammdaten. Inhaber-only. */
export function starteTestvorgang(): Promise<TestvorgangResult> {
  return apiFetch<TestvorgangResult>("/onboarding/testvorgang", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

/** DELETE /onboarding/testvorgang/{vorgang_id} — löscht ausschließlich den eigenen Testvorgang inkl. Test-Stammdaten. Inhaber-only. */
export function loescheTestvorgang(vorgangId: string): Promise<void> {
  return apiFetch<void>(`/onboarding/testvorgang/${vorgangId}`, {
    method: "DELETE",
  });
}

export interface VeroeffentlichenResult {
  domain_status: string;
  veroeffentlicht_am: string;
}

/**
 * POST /onboarding/veroeffentlichen — prüft serverseitig alle Pflichtregeln erneut
 * und setzt nur dann die reservierte Domain auf aktiv. Bei fehlenden Regeln 409
 * mit `fehlende_schritte`. Inhaber-only.
 */
export function veroeffentlichen(): Promise<VeroeffentlichenResult> {
  return apiFetch<VeroeffentlichenResult>("/onboarding/veroeffentlichen", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
