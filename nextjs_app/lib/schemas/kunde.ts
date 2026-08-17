import { z } from "zod";

export const kundeSchema = z
  .object({
    name: z.string().min(2, "Name ist erforderlich."),
    email: z.string().email("Ungültige E-Mail-Adresse.").optional().or(z.literal("")),
    telefon: z.string().optional().or(z.literal("")),
  })
  .refine((v) => v.email || v.telefon, {
    message: "E-Mail oder Telefonnummer ist erforderlich.",
    path: ["telefon"],
  });

export type KundeFormValues = z.infer<typeof kundeSchema>;

export const objektSchema = z.object({
  adresse: z.string().min(3, "Adresse ist erforderlich."),
});

export type ObjektFormValues = z.infer<typeof objektSchema>;
