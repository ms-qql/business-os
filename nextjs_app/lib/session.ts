/** Same-origin: der Browser ruft immer /api/*, next.config.mjs proxied zum Backend. */
export const API_BASE = "/api";

const TOKEN_KEY = "bo_access_token";
const OPERATOR_TOKEN_KEY = "bo_operator_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

/** Betreiber-Sitzung — getrennt vom Business-Token, nur für /operator und /admin gültig. */
export function getOperatorToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(OPERATOR_TOKEN_KEY);
}

export function setOperatorToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(OPERATOR_TOKEN_KEY, token);
}

export function clearOperatorToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(OPERATOR_TOKEN_KEY);
}
