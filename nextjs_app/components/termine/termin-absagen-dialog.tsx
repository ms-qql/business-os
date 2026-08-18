"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { terminAbsagen, type TerminListItem } from "@/lib/api/termine";
import { ApiError } from "@/lib/api/client";
import { formatBerlinDateTime } from "@/lib/zeit";

export function TerminAbsagenDialog({
  termin,
  open,
  onOpenChange,
  onAbsagt,
}: {
  termin: TerminListItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAbsagt: () => void;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const [speichert, setSpeichert] = React.useState(false);

  React.useEffect(() => {
    if (open) {
      setError(null);
      setSpeichert(false);
    }
  }, [open]);

  async function onBestaetigen() {
    if (!termin) return;
    setSpeichert(true);
    setError(null);
    try {
      await terminAbsagen(termin.id);
      onAbsagt();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Absagen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Termin absagen" className="max-w-md">
      {termin && (
        <div className="space-y-4">
          <p className="text-sm text-[var(--color-foreground)]">
            Möchten Sie den folgenden Termin absagen? Er bleibt zur Nachvollziehbarkeit
            in der Historie erhalten und wird in der Kalenderansicht ausgegraut dargestellt.
          </p>
          <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
            <p className="font-medium">{termin.anliegen}</p>
            <p className="text-[var(--color-muted-foreground)]">
              {formatBerlinDateTime(termin.beginn)} – {formatBerlinDateTime(termin.ende)}
            </p>
            {termin.adresse && (
              <p className="text-[var(--color-muted-foreground)]">{termin.adresse}</p>
            )}
          </div>
          {error && <Alert variant="danger">{error}</Alert>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Behalten
            </Button>
            <Button type="button" variant="danger" disabled={speichert} onClick={onBestaetigen}>
              {speichert ? "Wird abgesagt …" : "Termin absagen"}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
