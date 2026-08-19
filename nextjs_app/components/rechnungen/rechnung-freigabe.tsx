"use client";

import * as React from "react";
import { Send } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  rechnungFreigeben,
  rechnungSenden,
  type Rechnung,
  type FreigabeResult,
} from "@/lib/api/rechnungen";

function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

/**
 * Freigabeansicht vor Versand (AC: erst der ausdrückliche Klick sendet).
 * Zweistufig wie im Tech Design: erst POST .../freigabe (prüft Snapshot + erzeugt
 * PDF-Vorschau, versendet nichts), dann erst „Rechnung senden" löst POST .../senden aus.
 */
export function RechnungFreigabe({
  rechnung,
  open,
  onOpenChange,
  onVersendet,
}: {
  rechnung: Rechnung;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVersendet: () => void;
}) {
  const [freigabe, setFreigabe] = React.useState<FreigabeResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [bereitet, setBereitet] = React.useState(false);
  const [sendet, setSendet] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setFreigabe(null);
      setError(null);
    }
  }, [open]);

  async function onVorbereiten() {
    setBereitet(true);
    setError(null);
    try {
      // Kein Body — Empfänger/Betreff/Summen kommen aus gespeicherten Daten.
      setFreigabe(await rechnungFreigeben(rechnung.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Freigabe konnte nicht vorbereitet werden.");
    } finally {
      setBereitet(false);
    }
  }

  async function onSenden() {
    setSendet(true);
    setError(null);
    try {
      const result = await rechnungSenden(rechnung.id);
      if (!result.versendet) {
        // Versandfehler verändert Entwurf/Zahlungsstatus nicht (Edge Case).
        setError(result.fehler_text ?? "Rechnung wurde nicht versendet.");
        return;
      }
      onOpenChange(false);
      onVersendet();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rechnung wurde nicht versendet.");
    } finally {
      setSendet(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title="Rechnung freigeben und senden"
      className="max-w-2xl"
      description={`Rechnung ${rechnung.rechnungsnummer}`}
    >
      <div className="space-y-4">
        {!freigabe ? (
          <div className="space-y-3">
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Mit „Vorschau erzeugen“ werden Empfänger, Betreff, Rechnungsnummer und die
              PDF-Vorschau aus den gespeicherten Daten geprüft. Es wird noch nichts versendet.
            </p>
            {error && <Alert variant="danger">{error}</Alert>}
            <Button type="button" size="sm" disabled={bereitet} onClick={onVorbereiten}>
              {bereitet ? "Bereitet vor …" : "Vorschau erzeugen"}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-sm">
              <p>
                <span className="text-[var(--color-muted-foreground)]">Empfänger:</span>{" "}
                {freigabe.empfaenger ?? "—"}
              </p>
              <p>
                <span className="text-[var(--color-muted-foreground)]">Betreff:</span>{" "}
                {freigabe.betreff}
              </p>
              <p>
                <span className="text-[var(--color-muted-foreground)]">Rechnungsnummer:</span>{" "}
                {freigabe.rechnungsnummer}
              </p>
              <p className="mt-1 font-medium">
                Gesamtsumme (brutto): {formatEuro(freigabe.brutto_summe)}
              </p>
            </div>

            <iframe
              src={freigabe.pdf_download_url}
              title="PDF-Vorschau der Rechnung"
              className="h-96 w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
            />

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="flex gap-2">
              <Button size="sm" onClick={onSenden} disabled={sendet}>
                <Send size={16} />
                {sendet ? "Wird gesendet …" : "Rechnung senden"}
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setFreigabe(null)}
                disabled={sendet}
              >
                Zurück
              </Button>
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}
