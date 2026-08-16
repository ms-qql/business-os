"use client";

import * as React from "react";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { confirmPasswordReset } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

export default function PasswortZuruecksetzenPageWrapper() {
  return (
    <Suspense>
      <PasswortZuruecksetzenPage />
    </Suspense>
  );
}

function PasswortZuruecksetzenPage() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = React.useState("");
  const [repeat, setRepeat] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [pending, setPending] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 10) {
      setError("Das Passwort muss mindestens 10 Zeichen lang sein.");
      return;
    }
    if (password !== repeat) {
      setError("Die Passwörter stimmen nicht überein.");
      return;
    }
    setPending(true);
    try {
      const res = await confirmPasswordReset(token, password);
      setInfo(res.detail);
      setTimeout(() => router.push("/login"), 1500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Zurücksetzen fehlgeschlagen.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Passwort zurücksetzen</CardTitle>
          <CardDescription>Legen Sie ein neues Passwort fest.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="password">Neues Passwort</Label>
              <Input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="repeat">Passwort wiederholen</Label>
              <Input
                id="repeat"
                type="password"
                required
                value={repeat}
                onChange={(e) => setRepeat(e.target.value)}
              />
            </div>
            {info && <Alert variant="success">{info}</Alert>}
            {error && <Alert variant="danger">{error}</Alert>}
            <Button type="submit" className="w-full" disabled={pending || !token}>
              {pending ? "Wird gespeichert …" : "Passwort speichern"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
