"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { kundeSchema, type KundeFormValues } from "@/lib/schemas/kunde";
import { createKunde, updateKunde, type Kunde } from "@/lib/api/kunden";
import { ApiError } from "@/lib/api/client";

export function KundeFormDialog({
  open,
  onOpenChange,
  kunde,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Vorhanden = Bearbeiten, sonst Neuanlage. */
  kunde?: Kunde | null;
  onSaved: (kunde: Kunde) => void;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const [duplikate, setDuplikate] = React.useState<Kunde[]>([]);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<KundeFormValues>({ resolver: zodResolver(kundeSchema) });

  React.useEffect(() => {
    if (open) {
      reset({
        name: kunde?.name ?? "",
        email: kunde?.email ?? "",
        telefon: kunde?.telefon ?? "",
      });
      setError(null);
      setDuplikate([]);
    }
  }, [open, kunde, reset]);

  async function onSubmit(values: KundeFormValues) {
    setError(null);
    setDuplikate([]);
    const input = {
      name: values.name,
      email: values.email || undefined,
      telefon: values.telefon || undefined,
    };
    try {
      if (kunde) {
        const updated = await updateKunde(kunde.id, input);
        onSaved(updated);
        onOpenChange(false);
      } else {
        const res = await createKunde(input);
        onSaved(res);
        if (res.moegliche_duplikate.length > 0) {
          // Dialog bleibt offen, damit der Hinweis auf mögliche Bestandskunden sichtbar ist.
          setDuplikate(res.moegliche_duplikate);
        } else {
          onOpenChange(false);
        }
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={kunde ? "Kunde bearbeiten" : "Neuer Kunde"}
      description="Name sowie E-Mail-Adresse oder Telefonnummer angeben."
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="k-name">Name</Label>
          <Input id="k-name" {...register("name")} />
          {errors.name && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.name.message}</p>}
        </div>
        <div>
          <Label htmlFor="k-email">E-Mail</Label>
          <Input id="k-email" type="email" {...register("email")} />
          {errors.email && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.email.message}</p>}
        </div>
        <div>
          <Label htmlFor="k-telefon">Telefon</Label>
          <Input id="k-telefon" {...register("telefon")} />
          {errors.telefon && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.telefon.message}</p>}
        </div>
        {error && <Alert variant="danger">{error}</Alert>}
        {duplikate.length > 0 && (
          <Alert variant="warning">
            Möglicher Bestandskunde mit gleicher E-Mail-Adresse oder Telefonnummer:{" "}
            {duplikate.map((d) => d.name).join(", ")}. Der Kunde wurde trotzdem neu angelegt.
          </Alert>
        )}
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
