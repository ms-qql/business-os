import { operatorApiFetch } from "@/lib/api/client";
import { setOperatorToken, clearOperatorToken } from "@/lib/session";

export interface BetriebAnlage {
  name: string;
  owner_name: string;
  owner_email: string;
}

export interface OperatorLoginResponse {
  access_token: string;
  token_type: string;
}

export async function operatorLogin(
  email: string,
  password: string,
): Promise<void> {
  const data = await operatorApiFetch<OperatorLoginResponse>(
    "/operator/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
  );
  setOperatorToken(data.access_token);
}

export async function operatorLogout(): Promise<void> {
  try {
    await operatorApiFetch("/operator/auth/logout", { method: "POST" });
  } finally {
    clearOperatorToken();
  }
}

export async function createBetrieb(
  payload: BetriebAnlage,
): Promise<{ id: string; name: string; status: string }> {
  return operatorApiFetch("/admin/mandanten", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
