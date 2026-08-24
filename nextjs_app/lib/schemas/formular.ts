import { z } from "zod";

/** Fester Feldtypen-Katalog aus PROJ-13 (nicht frei erweiterbar). */
export const FELDTYPEN = [
  "text",
  "mehrzeilig",
  "dropdown",
  "kachel",
  "radio",
  "zahl",
  "datum",
  "upload",
  "adresse",
  "consent",
] as const;
export type Feldtyp = (typeof FELDTYPEN)[number];

export const FELDTYP_LABELS: Record<Feldtyp, string> = {
  text: "Textfeld",
  mehrzeilig: "Mehrzeiliger Text",
  dropdown: "Auswahl (Dropdown)",
  kachel: "Kachel-Auswahl",
  radio: "Radio-Buttons",
  zahl: "Mengenfeld (Zahl)",
  datum: "Datum",
  upload: "Datei-/Foto-Upload",
  adresse: "Adressfeld",
  consent: "Einwilligung (Datenschutz)",
};

/** Felder mit einer geordneten Optionsliste. */
export const OPTION_FELDTYPEN: Feldtyp[] = ["dropdown", "kachel", "radio"];

export function hatOptionen(typ: Feldtyp): boolean {
  return OPTION_FELDTYPEN.includes(typ);
}

/** Übernahme-Zuordnung (nur Text-, Adress- oder Auswahlfelder). */
export const UEBERNAHME_FELDER = [
  "kontaktname",
  "email",
  "telefon",
  "adresse",
  "anliegen",
] as const;
export type UebernahmeFeld = (typeof UEBERNAHME_FELDER)[number];

export const UEBERNAHME_LABELS: Record<UebernahmeFeld, string> = {
  kontaktname: "Kontaktname",
  email: "E-Mail",
  telefon: "Telefon",
  adresse: "Adresse",
  anliegen: "Anliegen",
};

export const KOMPLEXITAET = ["einfach", "erweitert"] as const;
export type Komplexitaet = (typeof KOMPLEXITAET)[number];

export const KOMPLEXITAET_LABELS: Record<Komplexitaet, string> = {
  einfach: "Einfach (nur Pflichtfelder)",
  erweitert: "Erweitert (zusätzlich optionale Felder)",
};

/** Pro Typ erlaubte Konfiguration (Teilmenge wird serverseitig geprüft). */
export interface FeldKonfiguration {
  // text / mehrzeilig
  maxLaenge?: number;
  regex?: string;
  // zahl
  min?: number;
  max?: number;
  ganzzahl?: boolean;
  // datum
  minDatum?: string;
  maxDatum?: string;
  // upload
  maxAnzahl?: number;
}

export const feldKonfigurationSchema = z
  .object({
    maxLaenge: z.number().int().positive().optional(),
    regex: z.string().optional(),
    min: z.number().optional(),
    max: z.number().optional(),
    ganzzahl: z.boolean().optional(),
    minDatum: z.string().optional(),
    maxDatum: z.string().optional(),
    maxAnzahl: z.number().int().positive().optional(),
  })
  .partial();

export const optionSchema = z.object({
  id: z.string(),
  position: z.number(),
  label: z.string(),
  wert: z.string(),
});
export type FormularOption = z.infer<typeof optionSchema>;

export const feldDraftSchema = z.object({
  id: z.string(),
  position: z.number(),
  typ: z.enum(FELDTYPEN),
  label: z.string(),
  hilfetext: z.string(),
  pflichtfeld: z.boolean(),
  optional_in_einfach: z.boolean(),
  config: feldKonfigurationSchema,
  options: z.array(optionSchema),
  uebernahme: z.enum(UEBERNAHME_FELDER).nullable(),
});
export type FormularFeldDraft = z.infer<typeof feldDraftSchema>;

export const schrittDraftSchema = z.object({
  id: z.string(),
  position: z.number(),
  titel: z.string(),
  felder: z.array(feldDraftSchema),
});
export type FormularSchrittDraft = z.infer<typeof schrittDraftSchema>;

export const formularDraftSchema = z.object({
  id: z.string(),
  mandant_id: z.string(),
  name: z.string(),
  komplexitaet: z.enum(KOMPLEXITAET),
  draft_revision: z.number(),
  veroeffentlicht: z.boolean(),
  public_id: z.string().nullable(),
  version_nummer: z.number().nullable(),
  schritte: z.array(schrittDraftSchema),
});
export type FormularDraft = z.infer<typeof formularDraftSchema>;

export const formularListeItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  draft_revision: z.number(),
  veroeffentlicht: z.boolean(),
  version_nummer: z.number().nullable(),
  aktualisiert_am: z.string(),
});
export type FormularListeItem = z.infer<typeof formularListeItemSchema>;

export const formularListeSchema = z.object({
  items: z.array(formularListeItemSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export type FormularListe = z.infer<typeof formularListeSchema>;

export const einbindungSchema = z.object({
  url: z.string(),
  iframe: z.string(),
  javascript: z.string(),
});
export type Einbindung = z.infer<typeof einbindungSchema>;

// --- Öffentlicher Snapshot -------------------------------------------------

export const oeffentlicheOptionSchema = z.object({
  label: z.string(),
  wert: z.string(),
});
export const oeffentlichesFeldSchema = z.object({
  id: z.string(),
  typ: z.enum(FELDTYPEN),
  label: z.string(),
  hilfetext: z.string(),
  pflichtfeld: z.boolean(),
  optional_in_einfach: z.boolean(),
  config: feldKonfigurationSchema,
  options: z.array(oeffentlicheOptionSchema),
  uebernahme: z.enum(UEBERNAHME_FELDER).nullable(),
});
export const oeffentlicherSchrittSchema = z.object({
  titel: z.string(),
  felder: z.array(oeffentlichesFeldSchema),
});
export const formularSnapshotSchema = z.object({
  name: z.string(),
  komplexitaet: z.enum(KOMPLEXITAET),
  schritte: z.array(oeffentlicherSchrittSchema),
});
export type OeffentlicherSchritt = z.infer<typeof oeffentlicherSchrittSchema>;
export type OeffentlichesFeld = z.infer<typeof oeffentlichesFeldSchema>;
export type FormularSnapshot = z.infer<typeof formularSnapshotSchema>;
