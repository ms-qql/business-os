import { z } from "zod";
import { rabattFehler } from "@/lib/angebot-berechnung";

export const positionSchema = z
  .object({
    bezeichnung: z.string().min(1, "Bezeichnung ist erforderlich."),
    menge: z.coerce.number().positive("Menge muss größer als 0 sein."),
    einheit: z.string().min(1, "Einheit ist erforderlich."),
    einzelpreis: z.coerce.number().min(0, "Einzelpreis darf nicht negativ sein."),
    steuersatz: z.coerce.number().min(0, "Steuersatz darf nicht negativ sein.").max(100, "Steuersatz darf 100 % nicht überschreiten."),
    rabatt_typ: z.enum(["prozent", "betrag"]),
    rabatt_wert: z.coerce.number().min(0, "Rabatt darf nicht negativ sein."),
  })
  .refine((v) => rabattFehler(v.rabatt_typ, v.rabatt_wert, v.menge, v.einzelpreis) === null, (v) => ({
    message: rabattFehler(v.rabatt_typ, v.rabatt_wert, v.menge, v.einzelpreis) ?? "Ungültiger Rabatt.",
    path: ["rabatt_wert"],
  }));

export type PositionFormValues = z.infer<typeof positionSchema>;

export const kopfdatenSchema = z.object({
  gueltig_bis: z.string().optional().or(z.literal("")),
  freitext: z.string().optional().or(z.literal("")),
});

export type KopfdatenFormValues = z.infer<typeof kopfdatenSchema>;

export const freigabeSchema = z.object({
  empfaenger: z.string().email("Ungültige E-Mail-Adresse."),
  betreff: z.string().min(1, "Betreff ist erforderlich."),
});

export type FreigabeFormValues = z.infer<typeof freigabeSchema>;
