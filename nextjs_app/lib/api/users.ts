import { apiFetch } from "@/lib/api/client";
import type { Rolle } from "@/lib/theme/tokens";

export interface Nutzer {
  id: string;
  name: string;
  email: string;
  rolle: Rolle;
  aktiv: boolean;
}

export interface NutzerEinladung {
  name: string;
  email: string;
  rolle: Rolle;
}

export async function listNutzer(): Promise<Nutzer[]> {
  return apiFetch<Nutzer[]>("/users");
}

export async function inviteNutzer(
  payload: NutzerEinladung,
): Promise<{ detail: string }> {
  return apiFetch("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateNutzer(
  id: string,
  patch: { rolle?: Rolle; aktiv?: boolean },
): Promise<{ detail: string }> {
  return apiFetch(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}
