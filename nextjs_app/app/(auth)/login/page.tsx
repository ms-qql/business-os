"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/app/providers";
import { ApiError } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [pending, setPending] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await signIn(email, password);
      router.push("/startseite");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Anmeldung fehlgeschlagen. Bitte erneut versuchen.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Anmelden</CardTitle>
          <CardDescription>
            Melden Sie sich mit Ihrer Betriebs-E-Mail an.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">E-Mail-Adresse</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@betrieb.de"
              />
            </div>
            <div>
              <Label htmlFor="password">Passwort</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="absolute inset-y-0 right-0 px-3 text-[var(--color-muted-foreground)]"
                  aria-label={showPassword ? "Passwort verbergen" : "Passwort anzeigen"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            {error && <Alert variant="danger">{error}</Alert>}
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Wird angemeldet …" : "Anmelden"}
            </Button>
          </form>
          <div className="mt-4 text-right">
            <a
              href="/passwort-vergessen"
              className="text-sm text-[var(--color-brand)] hover:underline"
            >
              Passwort vergessen?
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
