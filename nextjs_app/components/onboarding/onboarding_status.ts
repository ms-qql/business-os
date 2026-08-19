import type { OnboardingSchrittStatus } from "@/lib/api/onboarding";

/** Sichtbare Beschriftung je Status (deutsch, wie im Acceptance-Kriterium gefordert). */
export const STATUS_LABEL: Record<OnboardingSchrittStatus, string> = {
  offen: "Offen",
  in_bearbeitung: "In Bearbeitung",
  erledigt: "Erledigt",
};

/** Badge-Variante aus components/ui/badge, passend zum Status. */
export const STATUS_BADGE_VARIANT: Record<
  OnboardingSchrittStatus,
  "neutral" | "warning" | "success"
> = {
  offen: "neutral",
  in_bearbeitung: "warning",
  erledigt: "success",
};

/** Reihenfolge für Sortierung/Fortschritt (offen < in_bearbeitung < erledigt). */
export function statusRang(status: OnboardingSchrittStatus): number {
  return status === "offen" ? 0 : status === "in_bearbeitung" ? 1 : 2;
}
