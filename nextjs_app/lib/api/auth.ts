import { apiFetch } from "@/lib/api/client";
import { setToken, clearToken } from "@/lib/session";
import type { Rolle } from "@/lib/theme/tokens";

export interface AuthUser {
  user_id: string;
  username: string;
  name?: string;
  rolle: Rolle;
  mandant_id: string;
  mandant_name: string;
  paket_kennung?: string | null;
  paket_name?: string | null;
}

interface LoginResponse {
  access_token: string;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return fetchMe();
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    clearToken();
  }
}

/** Passwort-Reset anfordern — Antwort ist bewusst identisch für bekannt/unbekannt. */
export async function requestPasswordReset(email: string): Promise<{ detail: string }> {
  return apiFetch("/auth/password-reset", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function confirmPasswordReset(
  token: string,
  password: string,
): Promise<{ detail: string }> {
  return apiFetch("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export async function fetchMe(): Promise<AuthUser> {
  const me = await apiFetch<{
    id: string; mandant_id: string; name: string; email: string; role: string;
    paket_kennung?: string | null; paket_name?: string | null;
  }>("/auth/me");
  return {
    user_id: me.id,
    username: me.email,
    name: me.name,
    rolle: me.role === "Buero" ? "Büro" : me.role as Rolle,
    mandant_id: me.mandant_id,
    mandant_name: "Mein Betrieb",
    paket_kennung: me.paket_kennung ?? null,
    paket_name: me.paket_name ?? null,
  };
}

/** Einladung einlösen — neuer Betriebsnutzer setzt sein Passwort selbst. */
export async function acceptInvitation(
  token: string,
  password: string,
): Promise<{ ok: boolean }> {
  return apiFetch("/auth/invitations/accept", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}
