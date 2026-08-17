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

type ApiNutzer = {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
};

const apiRolle = (rolle: Rolle) => rolle === "Büro" ? "Buero" : rolle;

function nutzer({ role, status, ...nutzer }: ApiNutzer): Nutzer {
  return {
    ...nutzer,
    rolle: role === "Buero" ? "Büro" : role as Rolle,
    aktiv: status === "active",
  };
}

export async function listNutzer(): Promise<Nutzer[]> {
  return (await apiFetch<ApiNutzer[]>("/users")).map(nutzer);
}

export async function inviteNutzer(
  payload: NutzerEinladung,
): Promise<Nutzer> {
  const { name, email, rolle } = payload;
  return nutzer(await apiFetch<ApiNutzer>("/users", {
    method: "POST",
    body: JSON.stringify({ name, email, role: apiRolle(rolle) }),
  }));
}

export async function updateNutzer(
  id: string,
  patch: { rolle?: Rolle; aktiv?: boolean },
): Promise<Nutzer> {
  const { rolle, aktiv } = patch;
  return nutzer(await apiFetch<ApiNutzer>(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      role: rolle === undefined ? undefined : apiRolle(rolle),
      status: aktiv === undefined ? undefined : aktiv ? "active" : "disabled",
    }),
  }));
}
