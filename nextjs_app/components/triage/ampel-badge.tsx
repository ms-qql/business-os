import * as React from "react";
import { Badge } from "@/components/ui/badge";
import type { TriageStatus } from "@/lib/api/triage";

const META: Record<TriageStatus, { label: string; variant: "success" | "warning" | "danger" | "neutral" }> = {
  gruen: { label: "Grün", variant: "success" },
  gelb: { label: "Gelb", variant: "warning" },
  rot: { label: "Rot", variant: "danger" },
  nicht_bewertet: { label: "Nicht bewertet", variant: "neutral" },
};

/**
 * Kompakte Ampelanzeige für die Vorgangstabelle. Zeigt Farbe plus optionalen Kurzgrund.
 * Für vollständige Begründung siehe TriageCard im Vorgangsdetail.
 */
export function AmpelBadge({ status, kurzgrund }: { status: TriageStatus; kurzgrund?: string | null }) {
  const meta = META[status];
  return (
    <span className="inline-flex items-center gap-2" aria-label={`Ampel: ${meta.label}${kurzgrund ? `, ${kurzgrund}` : ""}`}>
      <Badge variant={meta.variant}>{meta.label}</Badge>
      {kurzgrund ? (
        <span className="text-xs text-[var(--color-muted-foreground)]">{kurzgrund}</span>
      ) : null}
    </span>
  );
}
