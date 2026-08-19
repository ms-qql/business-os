import { z } from "zod";

/** Rechnungssteller-Profil (Texte, keine Zahlen/Buttons). Spiegelt exakt den Backend-Contract. */
export const rechnungsstellerSchema = z.object({
  firma_name: z.string().min(1, "Firmenname ist erforderlich."),
  strasse: z.string().min(1, "Straße ist erforderlich."),
  hausnummer: z.string().min(1, "Hausnummer ist erforderlich."),
  plz: z.string().min(1, "PLZ ist erforderlich."),
  ort: z.string().min(1, "Ort ist erforderlich."),
  steuernummer: z.string().optional().default(""),
  ust_id: z.string().optional().default(""),
});

export type RechnungsstellerFormValues = z.infer<typeof rechnungsstellerSchema>;

/** Eine Rechnungsposition — kein Rabatt in V1 (laut Tech Design ADR-8). */
export const positionSchema = z.object({
  bezeichnung: z.string().min(1, "Bezeichnung ist erforderlich."),
  menge: z.coerce.number().positive("Menge muss größer als 0 sein."),
  einheit: z.string().min(1, "Einheit ist erforderlich."),
  netto_einzelpreis: z.coerce.number().min(0, "Einzelpreis darf nicht negativ sein."),
  steuersatz: z.coerce
    .number()
    .min(0, "Steuersatz darf nicht negativ sein.")
    .max(100, "Steuersatz darf 100 % nicht überschreiten."),
});

export type PositionFormValues = z.infer<typeof positionSchema>;

/** Kopfdaten des Entwurfs (Datum + Empfänger). */
export const kopfdatenSchema = z.object({
  rechnungsdatum: z.string().min(1, "Rechnungsdatum ist erforderlich."),
  leistungsdatum: z.string().min(1, "Leistungsdatum ist erforderlich."),
  empfaenger_email: z
    .string()
    .email("Ungültige E-Mail-Adresse.")
    .or(z.literal("")),
});

export type KopfdatenFormValues = z.infer<typeof kopfdatenSchema>;

/** Zahlungsstatus-Wechsel (nur Offen/Bezahlt/Storniert). */
export const zahlungsstatusSchema = z.object({
  zahlungsstatus: z.enum(["Offen", "Bezahlt", "Storniert"]),
});

export type ZahlungsstatusFormValues = z.infer<typeof zahlungsstatusSchema>;
