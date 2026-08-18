"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { terminSchema, type TerminFormValues } from "@/lib/schemas/termin";
import {
  createTermin,
  updateTermin,
  createVorgangTermin,
  listMonteure,
  listVorgangOptionen,
  type TerminListItem,
  type MonteurOption,
  type VorgangOption,
} from "@/lib/api/termine";
import { ApiError } from "@/lib/api/client";
import { berlinZuIso, berlinDateInputValue } from "@/lib/zeit";

export interface TerminDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
  /** Wenn gesetzt, ist der Termin im Bearbeitungsmodus (sonst Anlage). */
  termin?: TerminListItem | null;
  /** Wenn gesetzt, wird der Termin direkt am Vorgang angelegt (Nested-Route). */
  vorgangId?: string | null;
}

function heuteZeit(): string {
  const jetzt = new Date();
  return `${String(jetzt.getHours()).padStart(2, "0")}:${String(jetzt.getMinutes()).padStart(2, "0")}`;
}

export function TerminDialog({
  open,
  onOpenChange,
  onSaved,
  termin,
  vorgangId,
}: TerminDialogProps) {
  const istBearbeiten = Boolean(termin);
  const [error, setError] = React.useState<string | null>(null);
  const [konflikt, setKonflikt] = React.useState<string[]>([]);
  const [monteure, setMonteure] = React.useState<MonteurOption[]>([]);
  const [vorgangOptionen, setVorgangOptionen] = React.useState<VorgangOption[]>([]);
  const [gewaehlteMonteure, setGewaehlteMonteure] = React.useState<string[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<TerminFormValues>({ resolver: zodResolver(terminSchema) });

  const vorgang_id = watch("vorgang_id");
  const datum = watch("datum");

  React.useEffect(() => {
    if (!open) return;
    setError(null);
    setKonflikt([]);
    const ladeOptionen = async () => {
      try {
        const [m, v] = await Promise.all([listMonteure(), listVorgangOptionen()]);
        setMonteure(m.filter((x) => x.aktiv)); // deaktivierte ausgeblendet (Edge Case)
        setVorgangOptionen(v);
      } catch {
        setMonteure([]);
        setVorgangOptionen([]);
      }
    };
    void ladeOptionen();

    if (termin) {
      const beginn = new Date(termin.beginn);
      const ende = new Date(termin.ende);
      const fmt = (d: Date) =>
        `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
      const datumStr = `${beginn.getFullYear()}-${String(beginn.getMonth() + 1).padStart(2, "0")}-${String(beginn.getDate()).padStart(2, "0")}`;
      reset({
        vorgang_id: termin.vorgang_id,
        datum: datumStr,
        beginn: fmt(beginn),
        ende: fmt(ende),
        adresse: termin.adresse ?? "",
        notiz: termin.notiz ?? "",
        monteure: termin.monteure.map((x) => x.nutzer_id),
      });
      setGewaehlteMonteure(termin.monteure.map((x) => x.nutzer_id));
    } else {
      reset({
        vorgang_id: vorgangId ?? "",
        datum: berlinDateInputValue(),
        beginn: "09:00",
        ende: "11:00",
        adresse: "",
        notiz: "",
        monteure: [],
      });
      setGewaehlteMonteure([]);
    }
  }, [open, termin, vorgangId, reset]);

  function toggleMonteur(id: string) {
    setGewaehlteMonteure((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id];
      setValue("monteure", next, { shouldValidate: true });
      return next;
    });
  }

  async function onSubmit(values: TerminFormValues) {
    setError(null);
    setKonflikt([]);
    const beginnIso = berlinZuIso(values.datum, values.beginn);
    const endeIso = berlinZuIso(values.datum, values.ende);
    const payload = {
      vorgang_id: values.vorgang_id,
      beginn: beginnIso,
      ende: endeIso,
      adresse: values.adresse || null,
      notiz: values.notiz || null,
      monteure: gewaehlteMonteure,
    };
    try {
      const res = istBearbeiten && termin
        ? await updateTermin(termin.id, payload)
        : vorgangId
          ? await createVorgangTermin(vorgangId, payload)
          : await createTermin(payload);
      if (res.konflikt) setKonflikt(res.konflikt_monteure);
      onSaved();
      if (!res.konflikt) onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={istBearbeiten ? "Termin bearbeiten" : "Neuer Termin"}
      description="Beginn und Ende sind Pflicht; ein Termin ohne Monteur ist zulässig (Warnung)."
      className="max-w-xl"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="t-vorgang">Vorgang</Label>
          {vorgangId ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Anlage direkt am gewählten Vorgang.
            </p>
          ) : (
            <Select id="t-vorgang" {...register("vorgang_id")} disabled={istBearbeiten}>
              <option value="">— Vorgang wählen —</option>
              {vorgangOptionen.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.anliegen}
                </option>
              ))}
            </Select>
          )}
          {errors.vorgang_id && (
            <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.vorgang_id.message}</p>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div>
            <Label htmlFor="t-datum">Datum</Label>
            <Input id="t-datum" type="date" {...register("datum")} />
            {errors.datum && (
              <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.datum.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="t-beginn">Beginn</Label>
            <Input id="t-beginn" type="time" {...register("beginn")} />
            {errors.beginn && (
              <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.beginn.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="t-ende">Ende</Label>
            <Input id="t-ende" type="time" {...register("ende")} />
            {errors.ende && (
              <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.ende.message}</p>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="t-adresse">Adresse (optional)</Label>
          <Input
            id="t-adresse"
            placeholder="Objektadresse des Kunden oder Freitext"
            {...register("adresse")}
          />
        </div>

        <div>
          <Label>Monteure (Mehrfachauswahl)</Label>
          {monteure.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Keine aktiven Monteure im Mandanten verfügbar.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {monteure.map((m) => {
                const aktiv = gewaehlteMonteure.includes(m.id);
                return (
                  <button
                    type="button"
                    key={m.id}
                    onClick={() => toggleMonteur(m.id)}
                    className={`rounded-full px-3 py-1 text-sm transition-colors ${
                      aktiv
                        ? "bg-[var(--color-brand)] text-[var(--color-brand-foreground)]"
                        : "bg-[var(--color-surface-muted)] text-[var(--color-foreground)] hover:bg-[var(--color-border)]"
                    }`}
                  >
                    {m.name}
                  </button>
                );
              })}
            </div>
          )}
          {gewaehlteMonteure.length === 0 && (
            <p className="mt-1 text-xs text-[var(--color-warning)]">
              Kein Monteur zugewiesen — Termin ist zulässig, aber unbelegt.
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="t-notiz">Notiz (intern)</Label>
          <Textarea id="t-notiz" rows={3} {...register("notiz")} />
        </div>

        {konflikt.length > 0 && (
          <Alert variant="warning">
            <span className="flex items-center gap-2">
              <AlertTriangle size={16} />
              Überschneidung: Dieser Termin überlappt mit einem anderen Termin
              {gewaehlteMonteure.length === 1 ? " des Monteurs" : " mindestens eines Monteurs"}.
              Der Termin wurde trotzdem gespeichert.
            </span>
          </Alert>
        )}
        {error && <Alert variant="danger">{error}</Alert>}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Abbrechen
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Speichert …" : istBearbeiten ? "Speichern" : "Anlegen"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
