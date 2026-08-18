"use client";

import * as React from "react";
import { Plus, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/label";
import { TerminDialog } from "@/components/termine/termin-dialog";
import { ApiError } from "@/lib/api/client";
import {
  listVorgangTermine,
  type TerminListItem,
} from "@/lib/api/termine";
import { formatBerlinDateTime, formatBerlinDatum } from "@/lib/zeit";

/** Termine-Abschnitt im Vorgang (PROJ-6, Nested-Route wie PROJ-5 Angebote). */
export function VorgangTermine({
  vorgangId,
  darfSchreiben,
}: {
  vorgangId: string;
  darfSchreiben: boolean;
}) {
  const [liste, setListe] = React.useState<TerminListItem[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOffen, setDialogOffen] = React.useState(false);
  const [bearbeiten, setBearbeiten] = React.useState<TerminListItem | null>(null);

  const laden = React.useCallback(async () => {
    setError(null);
    try {
      const items = await listVorgangTermine(vorgangId);
      setListe(items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Termine konnten nicht geladen werden.");
    }
  }, [vorgangId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  return (
    <div className="space-y-3">
      {error && <Alert variant="danger">{error}</Alert>}

      {liste === null ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : liste.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Termine geplant.</p>
      ) : (
        <ul className="space-y-2">
          {liste.map((t) => {
            const abgesagt = Boolean(t.abgesagt_at);
            return (
              <li
                key={t.id}
                className={`rounded-[var(--radius-md)] border p-3 ${
                  abgesagt ? "border-[var(--color-border)] bg-[var(--color-surface-muted)] opacity-60" : "border-[var(--color-border)] bg-[var(--color-surface)]"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium">{formatBerlinDatum(t.beginn)}</p>
                    <p className="text-sm text-[var(--color-muted-foreground)]">
                      {formatBerlinDateTime(t.beginn)} – {formatBerlinDateTime(t.ende)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {t.konflikt && !abgesagt && (
                      <Badge variant="danger" className="flex items-center gap-1">
                        <AlertTriangle size={12} /> Konflikt
                      </Badge>
                    )}
                    {abgesagt && <Badge variant="neutral">Abgesagt</Badge>}
                  </div>
                </div>
                {t.adresse && (
                  <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">{t.adresse}</p>
                )}
                {t.monteure.length > 0 && (
                  <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
                    {t.monteure.map((m) => m.name).join(", ")}
                  </p>
                )}
                {darfSchreiben && (
                  <div className="mt-2">
                    <Button size="sm" variant="ghost" onClick={() => { setBearbeiten(t); setDialogOffen(true); }}>
                      Bearbeiten
                    </Button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {darfSchreiben && (
        <Button
          size="sm"
          disabled={liste === null}
          onClick={() => { setBearbeiten(null); setDialogOffen(true); }}
        >
          <Plus size={16} /> Termin planen
        </Button>
      )}

      <TerminDialog
        open={dialogOffen}
        onOpenChange={setDialogOffen}
        onSaved={() => {
          setDialogOffen(false);
          void laden();
        }}
        termin={bearbeiten}
        vorgangId={vorgangId}
      />
    </div>
  );
}
