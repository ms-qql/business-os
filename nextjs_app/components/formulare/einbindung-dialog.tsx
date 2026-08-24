"use client";

import * as React from "react";
import { Copy, Check } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { getEinbindung } from "@/lib/api/formulare";
import type { FormularEinbindung } from "@/lib/schemas/formular";

export function EinbindungDialog({
  formularId,
  onClose,
}: {
  formularId: string;
  onClose: () => void;
}) {
  const [daten, setDaten] = React.useState<FormularEinbindung | null>(null);
  const [fehler, setFehler] = React.useState<string | null>(null);
  const [kopiert, setKopiert] = React.useState<string | null>(null);

  React.useEffect(() => {
    let aktiv = true;
    setFehler(null);
    getEinbindung(formularId)
      .then((d) => aktiv && setDaten(d))
      .catch((err) => {
        if (!aktiv) return;
        setFehler(
          err instanceof ApiError
            ? err.message
            : "Einbindungscodes konnten nicht geladen werden.",
        );
      });
    return () => {
      aktiv = false;
    };
  }, [formularId]);

  async function kopieren(text: string,feld: string) {
    try {
      await navigator.clipboard.writeText(text);
      setKopiert(feld);
      window.setTimeout(() => setKopiert((k) => (k === feld ? null : k)), 1500);
    } catch {
      /* Clipboard nicht verfügbar — Nutzer kann manuell kopieren. */
    }
  }

  return (
    <Dialog
      open
      onOpenChange={(o) => !o && onClose()}
      title="Formular einbinden"
      description="Alle Varianten zeigen ausschließlich die veröffentlichte Fassung."
    >
      {fehler && <Alert variant="danger">{fehler}</Alert>}
      {!daten && !fehler && (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      )}
      {daten && (
        <div className="space-y-4">
          <div>
            <Label>Direktlink</Label>
            <CodeBlock code={daten.direktlink} kopiert={kopiert === "direktlink"} onKopieren={() => kopieren(daten.direktlink, "direktlink")} />
          </div>
          <div>
            <Label>iframe-Einbettung</Label>
            <CodeBlock code={daten.iframe} kopiert={kopiert === "iframe"} onKopieren={() => kopieren(daten.iframe, "iframe")} />
          </div>
          <div>
            <Label>JavaScript-Snippet</Label>
            <CodeBlock code={daten.snippet} kopiert={kopiert === "snippet"} onKopieren={() => kopieren(daten.snippet, "snippet")} />
          </div>
          <div className="flex justify-end">
            <Button variant="outline" onClick={onClose}>
              Schließen
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}

function CodeBlock({
  code,
  kopiert,
  onKopieren,
}: {
  code: string;
  kopiert: boolean;
  onKopieren: () => void;
}) {
  return (
    <div className="mt-1 flex items-stretch gap-2">
      <pre className="flex-1 overflow-x-auto rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-2 text-xs">
        <code>{code}</code>
      </pre>
      <button
        type="button"
        onClick={onKopieren}
        aria-label="Code kopieren"
        className="flex w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted-foreground)] hover:text-[var(--color-brand)]"
      >
        {kopiert ? <Check size={16} /> : <Copy size={16} />}
      </button>
    </div>
  );
}
