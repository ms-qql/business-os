"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { objektSchema, type ObjektFormValues } from "@/lib/schemas/kunde";
import { createObjekt, type Objekt } from "@/lib/api/kunden";
import { ApiError } from "@/lib/api/client";

export function ObjektFormDialog({
  open,
  onOpenChange,
  kundeId,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  kundeId: string;
  onSaved: (objekt: Objekt) => void;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ObjektFormValues>({ resolver: zodResolver(objektSchema) });

  React.useEffect(() => {
    if (open) {
      reset({ adresse: "" });
      setError(null);
    }
  }, [open, reset]);

  async function onSubmit(values: ObjektFormValues) {
    setError(null);
    try {
      const objekt = await createObjekt(kundeId, values);
      onSaved(objekt);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Neues Objekt">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="o-adresse">Adresse</Label>
          <Input id="o-adresse" {...register("adresse")} />
          {errors.adresse && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.adresse.message}</p>}
        </div>
        {error && <Alert variant="danger">{error}</Alert>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Abbrechen
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Speichert …" : "Speichern"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
