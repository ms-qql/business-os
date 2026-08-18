import { z } from "zod";

/** Formular-Schema für Termin-Anlage/Bearbeitung (PROJ-6 AC-1, AC-7).
 *  Beginn und Ende sind Pflicht; es gilt ende > beginn (serverseitig 422, hier vorab geprüft). */
export const terminSchema = z
  .object({
    vorgang_id: z.string().min(1, "Bitte einen Vorgang wählen."),
    datum: z.string().min(1, "Bitte ein Datum wählen."),
    beginn: z.string().min(1, "Beginn ist erforderlich."),
    ende: z.string().min(1, "Ende ist erforderlich."),
    adresse: z.string().optional().default(""),
    notiz: z.string().optional().default(""),
    monteure: z.array(z.string()).default([]),
  })
  .refine((v) => v.ende > v.beginn, {
    message: "Das Ende muss nach dem Beginn liegen.",
    path: ["ende"],
  });

export type TerminFormValues = z.infer<typeof terminSchema>;
