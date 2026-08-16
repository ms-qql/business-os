"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { createBetrieb, operatorLogout } from "@/lib/api/operator";
import { ApiError } from "@/lib/api/client";

export default function BetriebAnlegenPage() {
  const router = useRouter();
  const [firmenname, setFirmenname] = React.useState("");
  const [inhaberName, setInhaberName] = React.useState("");
  const [inhaberEmail, setInhaberEmail] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [pending, setPending] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setPending(true);
    try {
      const res = await createBetrieb({
        name: firmenname,
        owner_name: inhaberName,
        owner_email: inhaberEmail,
      });
      setInfo(`Betrieb „${res.name}" angelegt. Der Inhaber erhält einen Einladungslink.`);
      setFirmenname("");
      setInhaberName("");
      setInhaberEmail("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Anlage fehlgeschlagen.");
    } finally {
      setPending(false);
    }
  }

  async function onLogout() {
    await operatorLogout();
    router.replace("/operator-login");
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Betrieb anlegen</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Legt einen neuen Betrieb samt erstem Inhaber an (nur Betreiber).
          </p>
        </div>
        <button
          onClick={onLogout}
          className="text-sm text-[var(--color-danger)] hover:underline"
        >
          Abmelden
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Neuer Betrieb</CardTitle>
          <CardDescription>
            Der angegebene Inhaber erhält einen Einladungslink zum Setzen des
            Passworts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="firma">Firmenname</Label>
              <Input id="firma" required value={firmenname} onChange={(e) => setFirmenname(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="iname">Name des Inhabers</Label>
              <Input id="iname" required value={inhaberName} onChange={(e) => setInhaberName(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="iemail">E-Mail des Inhabers</Label>
              <Input id="iemail" type="email" required value={inhaberEmail} onChange={(e) => setInhaberEmail(e.target.value)} />
            </div>
            {error && <Alert variant="danger">{error}</Alert>}
            {info && <Alert variant="success">{info}</Alert>}
            <Button type="submit" disabled={pending}>
              {pending ? "Wird angelegt …" : "Betrieb anlegen"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
