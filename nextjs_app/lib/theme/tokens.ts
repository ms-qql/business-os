/**
 * Zentrale Theme-Tokens (Entsprechung zu AppColors im Flutter-Design).
 * Farbwerte als CSS-Variablen in globals.css (@theme) gesetzt und hier als
 * semantische Hilfen gebündelt, damit alle Komponenten einheitliche Tokens nutzen.
 */
export const AppColors = {
  // Markenfarbe (SHK-Blau)
  brand: "var(--color-brand)",
  brandForeground: "var(--color-brand-foreground)",
  // Flächen
  background: "var(--color-background)",
  surface: "var(--color-surface)",
  surfaceMuted: "var(--color-surface-muted)",
  border: "var(--color-border)",
  // Text
  foreground: "var(--color-foreground)",
  mutedForeground: "var(--color-muted-foreground)",
  // Status
  success: "var(--color-success)",
  warning: "var(--color-warning)",
  danger: "var(--color-danger)",
} as const;

/** Feste Rollen aus PROJ-1 (nicht frei konfigurierbar). */
export type Rolle = "Inhaber" | "Büro" | "Monteur";

export const ROLLEN: Rolle[] = ["Inhaber", "Büro", "Monteur"];

/** Sichtbarkeit von Navigationsbereichen je Rolle. */
export const NAV_RECHTE: Record<Rolle, string[]> = {
  Inhaber: ["startseite", "nutzerverwaltung"],
  Büro: ["startseite"],
  Monteur: ["startseite"],
};
