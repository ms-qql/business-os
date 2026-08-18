"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Send } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { angebotFreigeben, angebotSenden, type Angebot, type FreigabeResult } from "@/lib/api/angebote";
import { freigabeSchema, type FreigabeFormValues } from "@/lib/schemas/angebot";

function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

/**
 * Freigabeansicht vor Versand (AC „erst der ausdrückliche Klick sendet").
 * Zweistufig wie im Tech Design: erst POST .../freigabe (prüft + erzeugt PDF-Vorschau,
 * versendet nichts), dann erst der explizite „Angebot senden"-Klick löst POST .../senden aus.
 */
export function AngebotFreigabe({
  angebot,
  vorschlagEmpfaenger,
  open,
  onOpenChange,
  onVersendet,
}: {
  angebot: Angebot;
  vorschlagEmpfaenger: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onVersendet: () => void;
}) {
  const [freigabe, setFreigabe] = React.useState<FreigabeResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [bereitet, setBereitet] = React.useState(false);
  const [sendet, setSendet] = React.useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FreigabeFormValues>({
    resolver: zodResolver(freigabeSchema),
    defaultValues: { empfaenger: vorschlagEmpfaenger, betreff: `Ihr Angebot ${angebot.nummer}` },
  });

  React.useEffect(() => {
    if (!open) {
      setFreigabe(null);
      setError(null);
    }
  }, [open]);

  async function onVorbereiten(values: FreigabeFormValues) {
    setBereitet(true);
    setError(null);
    try {
      setFreigabe(await angebotFreigeben(angebot.id, values));
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
      await angebotSenden(angebot.id);
      onOpenChange(false);
      onVersendet();
    } catch (err) {
      // Edge Case: Versand fehlgeschlagen → Angebot bleibt Entwurf.
      setError(err instanceof ApiError ? err.message : "Angebot wurde nicht versendet.");
    } finally {
      setSendet(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Angebot freigeben und senden" className="max-w-2xl" description={`Angebot ${angebot.nummer} · Version ${angebot.version}`}>
      <div className="space-y-4">
        {!freigabe ? (
          <form onSubmit={handleSubmit(onVorbereiten)} className="space-y-3">
            <div>
              <Label htmlFor="freigabe-empfaenger">Empfänger</Label>
              <Input id="freigabe-empfaenger" {...register("empfaenger")} placeholder="kunde@beispiel.de" />
              {errors.empfaenger && <Alert variant="danger" className="mt-1">{errors.empfaenger.message}</Alert>}
            </div>
            <div>
              <Label htmlFor="freigabe-betreff">Betreff</Label>
              <Input id="freigabe-betreff" {...register("betreff")} />
              {errors.betreff && <Alert variant="danger" className="mt-1">{errors.betreff.message}</Alert>}
            </div>
            {error && <Alert variant="danger">{error}</Alert>}
            <Button type="submit" size="sm" disabled={bereitet}>
              {bereitet ? "Bereitet vor …" : "Vorschau erzeugen"}
            </Button>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="text-sm">
              <p><span className="text-[var(--color-muted-foreground)]">Empfänger:</span> {freigabe.empfaenger}</p>
              <p><span className="text-[var(--color-muted-foreground)]">Betreff:</span> {freigabe.betreff}</p>
              <p className="mt-1 font-medium">Gesamtsumme (brutto): {formatEuro(freigabe.brutto_summe)}</p>
            </div>

            <iframe
              src={freigabe.pdf_url}
              title="PDF-Vorschau des Angebots"
              className="h-96 w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
            />

            {error && <Alert variant="danger">{error}</Alert>}

            <div className="flex gap-2">
              <Button size="sm" onClick={onSenden} disabled={sendet}>
                <Send size={16} />
                {sendet ? "Wird gesendet …" : "Angebot senden"}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setFreigabe(null)} disabled={sendet}>
                Zurück
              </Button>
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}
