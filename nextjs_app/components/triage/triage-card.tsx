import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert } from "@/components/ui/label";
import { AmpelBadge } from "@/components/triage/ampel-badge";
import type { TriageErgebnis } from "@/lib/api/triage";

/**
 * Vollständige, nachvollziehbare Ampelbewertung im Vorgangsdetail.
 * Zeigt Farbe und alle deutschsprachigen Gründe; „Nicht bewertet" erklärt die fehlende Grundlage.
 */
export function TriageCard({ triage }: { triage: TriageErgebnis | null | undefined }) {
  if (!triage) return null;

  const kurzgrund = triage.gruende.length > 0 ? triage.gruende[0] : null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Triage-Ampel</CardTitle>
          <AmpelBadge status={triage.status} kurzgrund={kurzgrund} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {triage.gruende.length === 0 ? (
          <p className="text-[var(--color-muted-foreground)]">Keine Begründung verfügbar.</p>
        ) : (
          <ul className="space-y-1.5">
            {triage.gruende.map((g, i) => (
              <li key={i} className="flex items-start gap-2">
                <span aria-hidden className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-muted-foreground)]" />
                <span>{g}</span>
              </li>
            ))}
          </ul>
        )}

        {triage.naechster_freier_termin ? (
          <Alert variant="info">
            Nächster freier Termin: {new Date(triage.naechster_freier_termin).toLocaleDateString("de-DE")}
          </Alert>
        ) : null}
      </CardContent>
    </Card>
  );
}
