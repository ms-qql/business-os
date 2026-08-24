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
  | "testanfrage"
  | "branchenpaket";

/** Feste Branchenpaket-Kennungen (PROJ-14, Tech Design Abschnitt API-Contracts). */
export type BranchenpaketKennung = "shk" | "entruempelung";

/** Nicht veränderbare Wahloption aus GET /onboarding/branchenpakete. */
export interface BranchenpaketOption {
  kennung: BranchenpaketKennung;
  name: string;
  beschreibung: string;
}

/** Schreibgeschützte Paketinfo nach erfolgreicher Übernahme (in GET /onboarding + GET /auth/me). */
export interface BranchenpaketInfo {
  kennung: BranchenpaketKennung;
  name: string;
  version: string;
  uebernommen_am: string;
}

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
  /** Schreibgeschützte Paketkennzeichnung des Mandanten (PROJ-14). Nur nach Übernahme gesetzt. */
  paket_info?: BranchenpaketInfo | null;
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

/**
 * GET /onboarding/branchenpakete — liefert genau zwei nicht veränderbare
 * Wahloptionen (shk, entruempelung). Inhaber-Wahlkarte ruft ihn vor der Auswahl.
 * Keine Versions- oder Seed-Details im Browser.
 */
export function getBranchenpakete(): Promise<{ pakete: BranchenpaketOption[] }> {
  return apiFetch<{ pakete: BranchenpaketOption[] }>("/onboarding/branchenpakete");
}

export interface BranchenpaketUebernahmeResult {
  kennung: BranchenpaketKennung;
  name: string;
  version: string;
  uebernommen_am: string;
  onboarding_status: OnboardingStatus;
}

/**
 * POST /onboarding/branchenpaket-uebernehmen — nimmt nur `kennung` an und kopiert
 * atomar alle Zielinhalte in genau einen Mandanten. Liefert die Paketinfo plus den
 * aktualisierten Onboarding-Status. Ungültiger/defekter Katalog: 422; bereits
 * übernommenes/nicht leeres Ziel: 409. Inhaber-only, einmalig.
 */
export function uebernehmeBranchenpaket(
  kennung: BranchenpaketKennung,
): Promise<BranchenpaketUebernahmeResult> {
  return apiFetch<BranchenpaketUebernahmeResult>("/onboarding/branchenpaket-uebernehmen", {
    method: "POST",
    body: JSON.stringify({ kennung }),
  });
}
