"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PublicApiError, submitAnfrage, uploadAnfrageBild } from "@/lib/api/public";
import { useSiteBase } from "@/app/site/site-context";
import { liesKurzformular } from "@/components/website-builder/section-renderer";

const MAX_BILDER = 5;
const MAX_DATEIGROESSE = 8 * 1024 * 1024; // 8 MB

const schema = z
  .object({
    name: z.string().trim().min(1, "Bitte geben Sie Ihren Namen an."),
    kontaktweg: z.enum(["Telefon", "E-Mail"]),
    telefon: z.string().trim().optional(),
    email: z.string().trim().optional(),
    adresse: z.string().trim().min(1, "Bitte geben Sie Ihre Adresse an."),
    anliegen: z.string().trim().min(1, "Bitte beschreiben Sie Ihr Anliegen."),
    dringlichkeit: z.enum(["Normal", "Dringend"]),
    zeitfenster: z.string().trim().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.kontaktweg === "Telefon" && !data.telefon) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["telefon"],
        message: "Bitte geben Sie eine Telefonnummer an.",
      });
    }
    if (data.kontaktweg === "E-Mail") {
      if (!data.email) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["email"],
          message: "Bitte geben Sie eine E-Mail-Adresse an.",
        });
      } else if (!z.string().email().safeParse(data.email).success) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["email"],
          message: "Bitte geben Sie eine gültige E-Mail-Adresse an.",
        });
      }
    }
  });

type FormValues = z.infer<typeof schema>;

export default function AnfragePage() {
  const router = useRouter();
  const base = useSiteBase();
  const uebermittlungskennung = React.useRef(crypto.randomUUID()).current;
  const hochgeladeneBilder = React.useRef(new Map<File, string>()).current;

  const [bilder, setBilder] = React.useState<File[]>([]);
  const [bilderFehler, setBilderFehler] = React.useState<string | null>(null);
  const [sendenFehler, setSendenFehler] = React.useState<string | null>(null);
  const [wirdGesendet, setWirdGesendet] = React.useState(false);

  // Vorgabe aus dem öffentlichen Kurzformular (Hero) einmalig übernehmen —
  // wird nur über sessionStorage und ohne Kontaktdaten in der URL übergeben.
  const vorgabe = React.useRef(liesKurzformular()).current;
  const kontaktwegDefault: "Telefon" | "E-Mail" = vorgabe?.email
    ? "E-Mail"
    : "Telefon";

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: vorgabe?.name ?? "",
      kontaktweg: kontaktwegDefault,
      telefon: vorgabe?.telefon ?? "",
      email: vorgabe?.email ?? "",
      dringlichkeit: "Normal",
    },
  });

  const kontaktweg = watch("kontaktweg");

  function onBilderChange(e: React.ChangeEvent<HTMLInputElement>) {
    const dateien = Array.from(e.target.files ?? []);
    if (dateien.length > MAX_BILDER) {
      setBilderFehler(`Bitte wählen Sie höchstens ${MAX_BILDER} Bilder aus.`);
      e.target.value = "";
      return;
    }
    const zuGross = dateien.find((d) => d.size > MAX_DATEIGROESSE);
    if (zuGross) {
      setBilderFehler(`„${zuGross.name}" ist zu groß (maximal 8 MB je Bild).`);
      e.target.value = "";
      return;
    }
    const keinBild = dateien.find((d) => !d.type.startsWith("image/"));
    if (keinBild) {
      setBilderFehler(`„${keinBild.name}" ist kein Bild.`);
      e.target.value = "";
      return;
    }
    setBilderFehler(null);
    setBilder(dateien);
  }

  function bildEntfernen(index: number) {
    setBilder((prev) => prev.filter((_, i) => i !== index));
  }

  async function onSubmit(data: FormValues) {
    setSendenFehler(null);
    setWirdGesendet(true);
    try {
      // Bei einem Retry nach fehlgeschlagenem Versand nur neue/fehlende Dateien
      // hochladen — bereits erhaltene upload_ids wiederverwenden, sonst würde
      // jeder Retry dieselben Bilder erneut hochladen und das Server-Limit sprengen.
      const upload_ids: string[] = [];
      for (const datei of bilder) {
        let uploadId = hochgeladeneBilder.get(datei);
        if (!uploadId) {
          const res = await uploadAnfrageBild(datei, uebermittlungskennung);
          uploadId = res.upload_id;
          hochgeladeneBilder.set(datei, uploadId);
        }
        upload_ids.push(uploadId);
      }
      await submitAnfrage({
        name: data.name,
        kontaktweg: data.kontaktweg,
        telefon: data.telefon || undefined,
        email: data.email || undefined,
        adresse: data.adresse,
        anliegen: data.anliegen,
        dringlichkeit: data.dringlichkeit,
        zeitfenster: data.zeitfenster || undefined,
        uebermittlungskennung,
        upload_ids,
      });
      router.push(`${base}/anfrage/danke`);
    } catch (err) {
      setSendenFehler(
        err instanceof PublicApiError
          ? err.message
          : "Die Anfrage konnte nicht gesendet werden. Bitte versuchen Sie es erneut.",
      );
      setWirdGesendet(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader>
          <CardTitle>Anfrage senden</CardTitle>
          <CardDescription>
            Beschreiben Sie kurz Ihr Anliegen — wir melden uns zeitnah bei Ihnen.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" {...register("name")} />
              {errors.name && <Alert variant="danger" className="mt-1">{errors.name.message}</Alert>}
            </div>

            <div>
              <Label htmlFor="kontaktweg">Bevorzugter Kontaktweg</Label>
              <select
                id="kontaktweg"
                {...register("kontaktweg")}
                className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              >
                <option value="Telefon">Telefon</option>
                <option value="E-Mail">E-Mail</option>
              </select>
            </div>

            {kontaktweg === "Telefon" ? (
              <div>
                <Label htmlFor="telefon">Telefonnummer</Label>
                <Input id="telefon" type="tel" {...register("telefon")} />
                {errors.telefon && <Alert variant="danger" className="mt-1">{errors.telefon.message}</Alert>}
              </div>
            ) : (
              <div>
                <Label htmlFor="email">E-Mail-Adresse</Label>
                <Input id="email" type="email" {...register("email")} />
                {errors.email && <Alert variant="danger" className="mt-1">{errors.email.message}</Alert>}
              </div>
            )}

            <div>
              <Label htmlFor="adresse">Adresse</Label>
              <Input id="adresse" {...register("adresse")} placeholder="Straße, Hausnummer, PLZ, Ort" />
              {errors.adresse && <Alert variant="danger" className="mt-1">{errors.adresse.message}</Alert>}
            </div>

            <div>
              <Label htmlFor="anliegen">Anliegen</Label>
              <Textarea id="anliegen" {...register("anliegen")} />
              {errors.anliegen && <Alert variant="danger" className="mt-1">{errors.anliegen.message}</Alert>}
            </div>

            <div>
              <Label htmlFor="dringlichkeit">Dringlichkeit</Label>
              <select
                id="dringlichkeit"
                {...register("dringlichkeit")}
                className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              >
                <option value="Normal">Normal</option>
                <option value="Dringend">Dringend</option>
              </select>
            </div>

            <div>
              <Label htmlFor="zeitfenster">Gewünschtes Zeitfenster (optional)</Label>
              <Input id="zeitfenster" {...register("zeitfenster")} placeholder="z. B. werktags vormittags" />
            </div>

            <div>
              <Label htmlFor="bilder">Fotos (optional, maximal {MAX_BILDER})</Label>
              <input
                id="bilder"
                type="file"
                accept="image/*"
                multiple
                onChange={onBilderChange}
                className="block w-full text-sm text-[var(--color-muted-foreground)] file:mr-3 file:rounded-[var(--radius-md)] file:border-0 file:bg-[var(--color-surface-muted)] file:px-3 file:py-2 file:text-sm file:font-medium"
              />
              {bilderFehler && <Alert variant="danger" className="mt-1">{bilderFehler}</Alert>}
              {bilder.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {bilder.map((b, i) => (
                    <li key={`${b.name}-${i}`} className="flex items-center justify-between rounded-[var(--radius-md)] bg-[var(--color-surface-muted)] px-3 py-1.5 text-sm">
                      <span className="truncate">{b.name}</span>
                      <button
                        type="button"
                        onClick={() => bildEntfernen(i)}
                        aria-label={`${b.name} entfernen`}
                        className="text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
                      >
                        <X size={16} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {sendenFehler && <Alert variant="danger">{sendenFehler}</Alert>}

            <Button type="submit" size="lg" className="w-full" disabled={wirdGesendet}>
              {wirdGesendet ? "Wird gesendet …" : "Anfrage absenden"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
