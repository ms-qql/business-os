"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { requestPasswordReset } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

export default function PasswortVergessenPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [info, setInfo] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [pending, setPending] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setPending(true);
    try {
      const res = await requestPasswordReset(email);
      // Antwort ist bewusst identisch — verrät nicht, ob die Adresse existiert.
      setInfo(res.detail);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Anfrage fehlgeschlagen.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Passwort vergessen</CardTitle>
          <CardDescription>
            Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Link zum
            Zurücksetzen.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">E-Mail-Adresse</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {info && <Alert variant="success">{info}</Alert>}
            {error && <Alert variant="danger">{error}</Alert>}
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Wird gesendet …" : "Link anfordern"}
            </Button>
          </form>
          <div className="mt-4">
            <a
              href="/login"
              className="text-sm text-[var(--color-brand)] hover:underline"
            >
              Zurück zur Anmeldung
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
