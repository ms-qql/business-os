"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  updateRechnungssteller,
  type RechnungsstellerProfil,
} from "@/lib/api/rechnungen";
import { rechnungsstellerSchema, type RechnungsstellerFormValues } from "@/lib/schemas/rechnung";

const LEER: RechnungsstellerFormValues = {
  firma_name: "",
  strasse: "",
  hausnummer: "",
  plz: "",
  ort: "",
  steuernummer: "",
  ust_id: "",
};

/**
 * Profil-Formular für den Rechnungssteller (PROJ-8). Quelle für neue Entwürfe;
 * eine vollständige Pflege ist Voraussetzung für die Freigabe. Nur Inhaber.
 */
export function RechnungsstellerProfilForm({
  initial,
}: {
  initial: RechnungsstellerProfil | null;
}) {
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RechnungsstellerFormValues>({
    resolver: zodResolver(rechnungsstellerSchema),
    defaultValues: {
      firma_name: initial?.firma_name ?? "",
      strasse: initial?.strasse ?? "",
      hausnummer: initial?.hausnummer ?? "",
      plz: initial?.plz ?? "",
      ort: initial?.ort ?? "",
      steuernummer: initial?.steuernummer ?? "",
      ust_id: initial?.ust_id ?? "",
    },
  });

  async function submit(values: RechnungsstellerFormValues) {
    setSpeichert(true);
    setError(null);
    setInfo(null);
    try {
      await updateRechnungssteller(values);
      setInfo("Rechnungssteller-Profil gespeichert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-4">
      <div>
        <Label htmlFor="rs-firma_name">Firmenname</Label>
        <Input id="rs-firma_name" {...register("firma_name")} placeholder="z. B. Muster Sanitär GmbH" />
        {errors.firma_name && <Alert variant="danger" className="mt-1">{errors.firma_name.message}</Alert>}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="rs-strasse">Straße</Label>
          <Input id="rs-strasse" {...register("strasse")} placeholder="z. B. Hauptstraße" />
          {errors.strasse && <Alert variant="danger" className="mt-1">{errors.strasse.message}</Alert>}
        </div>

        <div>
          <Label htmlFor="rs-hausnummer">Hausnummer</Label>
          <Input id="rs-hausnummer" {...register("hausnummer")} placeholder="z. B. 12" />
          {errors.hausnummer && <Alert variant="danger" className="mt-1">{errors.hausnummer.message}</Alert>}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <Label htmlFor="rs-plz">PLZ</Label>
          <Input id="rs-plz" {...register("plz")} placeholder="z. B. 12345" />
          {errors.plz && <Alert variant="danger" className="mt-1">{errors.plz.message}</Alert>}
        </div>

        <div className="sm:col-span-2">
          <Label htmlFor="rs-ort">Ort</Label>
          <Input id="rs-ort" {...register("ort")} placeholder="z. B. Musterstadt" />
          {errors.ort && <Alert variant="danger" className="mt-1">{errors.ort.message}</Alert>}
        </div>
      </div>

      <div>
        <Label htmlFor="rs-steuernummer">Steuernummer (optional)</Label>
        <Input
          id="rs-steuernummer"
          {...register("steuernummer")}
          placeholder="z. B. 12/345/67890"
        />
        {errors.steuernummer && (
          <Alert variant="danger" className="mt-1">{errors.steuernummer.message}</Alert>
        )}
      </div>

      <div>
        <Label htmlFor="rs-ust_id">USt-IdNr. (optional)</Label>
        <Input
          id="rs-ust_id"
          {...register("ust_id")}
          placeholder="z. B. DE123456789"
        />
        {errors.ust_id && (
          <Alert variant="danger" className="mt-1">{errors.ust_id.message}</Alert>
        )}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <div>
        <Button type="submit" disabled={speichert}>
          {speichert ? "Wird gespeichert …" : "Profil speichern"}
        </Button>
      </div>
    </form>
  );
}
