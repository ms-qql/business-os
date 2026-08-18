"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { positionSchema, type PositionFormValues } from "@/lib/schemas/angebot";
import type { PositionInput } from "@/lib/api/angebote";

const LEER: PositionFormValues = {
  bezeichnung: "",
  menge: 1,
  einheit: "Stück",
  einzelpreis: 0,
  steuersatz: 19,
  rabatt_typ: "prozent",
  rabatt_wert: 0,
};

/** Zeile hinzufügen/bearbeiten — Rabatt-Umschalter %/€ wechselt Suffix + Validierungsgrenze live. */
export function PositionForm({
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
    watch,
    formState: { errors },
  } = useForm<PositionFormValues>({
    resolver: zodResolver(positionSchema),
    defaultValues: initial ?? LEER,
  });
  const rabattTyp = watch("rabatt_typ");

  async function submit(values: PositionFormValues) {
    await onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div className="lg:col-span-2">
        <Label htmlFor="pos-bezeichnung">Bezeichnung</Label>
        <Input id="pos-bezeichnung" {...register("bezeichnung")} placeholder="z. B. Montage Heizkörper" />
        {errors.bezeichnung && <Alert variant="danger" className="mt-1">{errors.bezeichnung.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="pos-menge">Menge</Label>
        <Input id="pos-menge" type="number" step="0.01" {...register("menge")} />
        {errors.menge && <Alert variant="danger" className="mt-1">{errors.menge.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="pos-einheit">Einheit</Label>
        <Input id="pos-einheit" {...register("einheit")} placeholder="Stück, Std., m² …" />
        {errors.einheit && <Alert variant="danger" className="mt-1">{errors.einheit.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="pos-einzelpreis">Einzelpreis (€)</Label>
        <Input id="pos-einzelpreis" type="number" step="0.01" {...register("einzelpreis")} />
        {errors.einzelpreis && <Alert variant="danger" className="mt-1">{errors.einzelpreis.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="pos-steuersatz">Steuersatz (%)</Label>
        <Input id="pos-steuersatz" type="number" step="0.01" {...register("steuersatz")} />
        {errors.steuersatz && <Alert variant="danger" className="mt-1">{errors.steuersatz.message}</Alert>}
      </div>

      <div>
        <Label htmlFor="pos-rabatt-typ">Rabatt-Art</Label>
        <Select id="pos-rabatt-typ" {...register("rabatt_typ")}>
          <option value="prozent">Prozent (%)</option>
          <option value="betrag">Euro-Betrag (€)</option>
        </Select>
      </div>

      <div>
        <Label htmlFor="pos-rabatt-wert">Rabatt ({rabattTyp === "prozent" ? "%" : "€"})</Label>
        <Input
          id="pos-rabatt-wert"
          type="number"
          step="0.01"
          max={rabattTyp === "prozent" ? 100 : undefined}
          {...register("rabatt_wert")}
        />
        {errors.rabatt_wert && <Alert variant="danger" className="mt-1">{errors.rabatt_wert.message}</Alert>}
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
