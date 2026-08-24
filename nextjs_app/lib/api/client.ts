import { API_BASE, getOperatorToken, getToken } from "@/lib/session";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit,
  token: string | null,
  onUnauthorized: () => void,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    onUnauthorized();
    throw new ApiError(401, "Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.");
  }

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item?.msg).filter(Boolean).join(" ")
        : `Anfrage fehlgeschlagen (${res.status}).`;
    throw new ApiError(res.status, message);
  }
  return data as T;
}

/** Business-Aufruf — sendet den Mandanten-Token aus der aktiven Nutzersitzung. */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return request<T>(path, options, getToken(), () => {
    if (typeof window !== "undefined") {
      import("@/lib/session").then((m) => m.clearToken());
    }
  });
}

/** Betreiber-Aufruf — sendet den getrennten Betreiber-Token, niemals den Business-Token. */
export async function operatorApiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return request<T>(path, options, getOperatorToken(), () => {
    if (typeof window !== "undefined") {
      import("@/lib/session").then((m) => m.clearOperatorToken());
    }
  });
}

/** Öffentlicher (nicht angemeldeter) Aufruf — ohne Token, wirft ApiError. */
export async function publicApiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return request<T>(path, options, null, () => {});
}
