"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { vorgangSchema, type VorgangFormValues } from "@/lib/schemas/vorgang";
import { createVorgang, type VorgangListItem } from "@/lib/api/vorgaenge";
import { listKunden, listObjekte, type Kunde, type Objekt } from "@/lib/api/kunden";
import { ApiError } from "@/lib/api/client";

export function VorgangFormDialog({
  open,
  onOpenChange,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (vorgang: VorgangListItem) => void;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const [kundenSuche, setKundenSuche] = React.useState("");
  const [kunden, setKunden] = React.useState<Kunde[]>([]);
  const [objekte, setObjekte] = React.useState<Objekt[]>([]);
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<VorgangFormValues>({ resolver: zodResolver(vorgangSchema) });
  const kundeId = watch("kunde_id");

  React.useEffect(() => {
    if (open) {
      reset({ kunde_id: "", objekt_id: "", anliegen: "", notizen: "" });
      setError(null);
      setKundenSuche("");
      setKunden([]);
      setObjekte([]);
    }
  }, [open, reset]);

  React.useEffect(() => {
    if (!open || kundenSuche.trim().length < 2) return;
    const t = setTimeout(() => {
      listKunden({ suche: kundenSuche, limit: 10 })
        .then((res) => setKunden(res.items))
        .catch(() => setKunden([]));
    }, 250);
    return () => clearTimeout(t);
  }, [kundenSuche, open]);

  React.useEffect(() => {
    if (!kundeId) {
      setObjekte([]);
      return;
    }
    listObjekte(kundeId)
      .then(setObjekte)
      .catch(() => setObjekte([]));
  }, [kundeId]);

  async function onSubmit(values: VorgangFormValues) {
    setError(null);
    try {
      const vorgang = await createVorgang({
        kunde_id: values.kunde_id,
        objekt_id: values.objekt_id || null,
        anliegen: values.anliegen,
        notizen: values.notizen || undefined,
        quelle: "Büro",
      });
      onSaved(vorgang);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} title="Neuer Vorgang" className="max-w-xl">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="v-kunde-suche">Kunde suchen</Label>
          <Input
            id="v-kunde-suche"
            placeholder="Name, E-Mail oder Telefon …"
            value={kundenSuche}
            onChange={(e) => setKundenSuche(e.target.value)}
          />
          <Select className="mt-2" {...register("kunde_id")}>
            <option value="">— Kunde wählen —</option>
            {kunden.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </Select>
          {errors.kunde_id && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.kunde_id.message}</p>}
        </div>
        <div>
          <Label htmlFor="v-objekt">Objekt (optional)</Label>
          <Select id="v-objekt" disabled={!kundeId} {...register("objekt_id")}>
            <option value="">— kein Objekt —</option>
            {objekte.map((o) => (
              <option key={o.id} value={o.id}>
                {o.adresse}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="v-anliegen">Anliegen</Label>
          <Textarea id="v-anliegen" {...register("anliegen")} />
          {errors.anliegen && <p className="mt-1 text-xs text-[var(--color-danger)]">{errors.anliegen.message}</p>}
        </div>
        <div>
          <Label htmlFor="v-notizen">Interne Notizen</Label>
          <Textarea id="v-notizen" {...register("notizen")} />
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
