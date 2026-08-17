import { z } from "zod";
import { VORGANG_STATUS } from "@/lib/theme/tokens";

export const vorgangSchema = z.object({
  kunde_id: z.string().min(1, "Kunde ist erforderlich."),
  objekt_id: z.string().optional(),
  anliegen: z.string().min(3, "Anliegen ist erforderlich."),
  notizen: z.string().optional(),
});

export type VorgangFormValues = z.infer<typeof vorgangSchema>;

export const vorgangStatusSchema = z.object({
  status: z.enum(VORGANG_STATUS),
});
