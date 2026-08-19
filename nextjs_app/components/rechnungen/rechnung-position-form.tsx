"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { positionSchema, type PositionFormValues } from "@/lib/schemas/rechnung";
import type { PositionInput, RechnungPosition } from "@/lib/api/rechnungen";

const LEER: PositionFormValues = {
  bezeichnung: "",
  menge: 1,
  einheit: "Stück",
  netto_einzelpreis: 0,
  steuersatz: 19,
};

/** Zeile hinzufügen/bearbeiten — ohne Rabatt (V1, siehe Tech Design ADR-8). */
export function RechnungPositionForm({
  initial,
  onSubmit,
  onAbbrechen,
  speichert,
}: {
  initial?: PositionFormValues;
  onSubmit: (values: PositionInput) => Promise<void>;
  onAbbrechen?: () => void;
  speichert: boolean;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PositionFormValues>({
    resolver: zodResolver(positionSchema),
    defaultValues: initial ?? LEER,
  });

  async function submit(values: PositionFormValues) {
    await onSubmit({
      bezeichnung: values.bezeichnung,
      menge: values.menge,
      einheit: values.einheit,
      netto_einzelpreis: values.netto_einzelpreis,
      steuersatz: values.steuersatz,
    });
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div className="lg:col-span-2">
        <Label htmlFor="rpos-bezeichnung">Bezeichnung</Label>
        <Input id="rpos-bezeichnung" {...register("bezeichnung")} placeholder="z. B. Montage Heizkörper" />
        {errors.bezeichnung && <Alert variant="danger" className="mt-1">{errors.bezeichnung.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="rpos-menge">Menge</Label>
        <Input id="rpos-menge" type="number" step="0.01" {...register("menge")} />
        {errors.menge && <Alert variant="danger" className="mt-1">{errors.menge.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="rpos-einheit">Einheit</Label>
        <Input id="rpos-einheit" {...register("einheit")} placeholder="Stück, Std., m² …" />
        {errors.einheit && <Alert variant="danger" className="mt-1">{errors.einheit.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="rpos-preis">Netto-Einzelpreis (€)</Label>
        <Input id="rpos-preis" type="number" step="0.01" {...register("netto_einzelpreis")} />
        {errors.netto_einzelpreis && (
          <Alert variant="danger" className="mt-1">{errors.netto_einzelpreis.message}</Alert>
        )}
      </div>

      <div>
        <Label htmlFor="rpos-steuersatz">Steuersatz (%)</Label>
        <Input id="rpos-steuersatz" type="number" step="0.01" {...register("steuersatz")} />
        {errors.steuersatz && <Alert variant="danger" className="mt-1">{errors.steuersatz.message}</Alert>}
      </div>

      <div className="flex items-end gap-2 lg:col-span-4">
        <Button type="submit" size="sm" disabled={speichert}>
          {speichert ? "Speichert …" : initial ? "Position speichern" : "Position hinzufügen"}
        </Button>
        {onAbbrechen && (
          <Button type="button" size="sm" variant="secondary" onClick={onAbbrechen} disabled={speichert}>
            Abbrechen
          </Button>
        )}
      </div>
    </form>
  );
}

export function positionToForm(p: RechnungPosition): PositionFormValues {
  return {
    bezeichnung: p.bezeichnung,
    menge: p.menge,
    einheit: p.einheit,
    netto_einzelpreis: p.netto_einzelpreis,
    steuersatz: p.steuersatz,
  };
}
