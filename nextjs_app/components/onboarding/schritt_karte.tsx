import * as React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, CircleDashed, CircleDot } from "lucide-react";
import type { OnboardingSchritt } from "@/lib/api/onboarding";
import {
  STATUS_LABEL,
  STATUS_BADGE_VARIANT,
} from "@/components/onboarding/onboarding_status";

/** Ziel-URL je Bearbeitungsziel (Tech Design Abschnitt B). */
const ZIEL_URL: Record<string, string> = {
  "Website-Einstellungen": "/website-einstellungen",
  "Postfach-Einstellungen": "/einstellungen/postfach",
  Onboarding: "/onboarding",
};

function StatusIcon({ status }: { status: OnboardingSchritt["status"] }) {
  if (status === "erledigt") return <CheckCircle2 size={18} className="text-[var(--color-success)]" />;
  if (status === "in_bearbeitung") return <CircleDot size={18} className="text-[var(--color-warning)]" />;
  return <CircleDashed size={18} className="text-[var(--color-muted-foreground)]" />;
}

export function SchrittKarte({ schritt, index }: { schritt: OnboardingSchritt; index: number }) {
  const zielUrl = ZIEL_URL[schritt.bearbeitungsziel];
  const istErledigt = schritt.status === "erledigt";

  return (
    <div
      className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 sm:flex-row sm:items-center sm:justify-between"
      aria-label={`Schritt ${index + 1}: ${schritt.titel}, Status ${STATUS_LABEL[schritt.status]}`}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 shrink-0">
          <StatusIcon status={schritt.status} />
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-[var(--color-muted-foreground)]">
              Schritt {index + 1}
            </span>
            {schritt.pflicht ? (
              <span className="rounded-full bg-[var(--color-surface-muted)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-muted-foreground)]">
                Pflicht
              </span>
            ) : (
              <span className="rounded-full bg-[var(--color-surface-muted)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-muted-foreground)]">
                Optional
              </span>
            )}
          </div>
          <h3 className="font-medium text-[var(--color-foreground)]">{schritt.titel}</h3>
          {/* Konkrete fehlende Eingabe statt nur "unvollständig" (Acceptance-Kriterium). */}
          {!istErledigt && schritt.fehlende_eingabe && (
            <p className="mt-1 text-sm text-[var(--color-danger)]">{schritt.fehlende_eingabe}</p>
          )}
          {istErledigt && (
            <p className="mt-1 text-sm text-[var(--color-success)]">Erledigt.</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 sm:flex-col sm:items-end">
        <Badge variant={STATUS_BADGE_VARIANT[schritt.status]}>{STATUS_LABEL[schritt.status]}</Badge>
        {!istErledigt && zielUrl && (
          <Link
            href={zielUrl}
            className="rounded-[var(--radius-md)] px-3 py-1.5 text-sm font-medium text-[var(--color-brand)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]"
          >
            Jetzt bearbeiten
          </Link>
        )}
      </div>
    </div>
  );
}
