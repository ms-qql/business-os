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
}

export interface LoginResponse {
  access_token: string;
  user: AuthUser;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data.user;
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
  return apiFetch<AuthUser>("/auth/me");
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
