"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listNutzer, inviteNutzer, updateNutzer, type Nutzer } from "@/lib/api/users";
import { ROLLEN, type Rolle } from "@/lib/theme/tokens";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/app/providers";

export default function NutzerverwaltungPage() {
  const { user } = useAuth();
  const [nutzer, setNutzer] = React.useState<Nutzer[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [rolle, setRolle] = React.useState<Rolle>("Büro");

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setNutzer(await listNutzer());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onInvite(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    try {
      const res = await inviteNutzer({ name, email, rolle });
      setInfo(res.detail);
      setName("");
      setEmail("");
      setRolle("Büro");
      await laden();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Einladung fehlgeschlagen.");
    }
  }

  async function onToggleAktiv(n: Nutzer) {
    // Letzten aktiven Inhaber nicht deaktivieren (Schutz serverseitig + hier).
    if (n.rolle === "Inhaber" && n.aktiv) {
      const aktiveInhaber = nutzer.filter(
        (x) => x.rolle === "Inhaber" && x.aktiv,
      ).length;
      if (aktiveInhaber <= 1) {
        setError("Der letzte aktive Inhaber kann nicht deaktiviert werden.");
        return;
      }
    }
    setError(null);
    try {
      await updateNutzer(n.id, { aktiv: !n.aktiv });
      await laden();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Änderung fehlgeschlagen.");
    }
  }

  async function onRolle(n: Nutzer, neue: Rolle) {
    setError(null);
    try {
      await updateNutzer(n.id, { rolle: neue });
      await laden();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rollenänderung fehlgeschlagen.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Nutzerverwaltung</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Nutzer Ihres Betriebs einladen und verwalten.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Neuen Nutzer einladen</CardTitle>
          <CardDescription>
            Der Nutzer erhält einen einmaligen Link zum Setzen des Passworts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onInvite} className="grid gap-4 sm:grid-cols-4">
            <div>
              <Label htmlFor="nname">Name</Label>
              <Input id="nname" required value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="nemail">E-Mail</Label>
              <Input id="nemail" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="nrolle">Rolle</Label>
              <select
                id="nrolle"
                value={rolle}
                onChange={(e) => setRolle(e.target.value as Rolle)}
                className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              >
                {ROLLEN.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <Button type="submit" className="w-full">
                Einladen
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>Nutzerliste</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-left text-[var(--color-muted-foreground)]">
                  <th className="py-2 pr-2 font-medium">Name</th>
                  <th className="py-2 pr-2 font-medium">E-Mail</th>
                  <th className="py-2 pr-2 font-medium">Rolle</th>
                  <th className="py-2 pr-2 font-medium">Status</th>
                  <th className="py-2 font-medium">Aktion</th>
                </tr>
              </thead>
              <tbody>
                {nutzer.map((n) => {
                  const istSelf = user?.user_id === n.id;
                  return (
                    <tr key={n.id} className="border-b border-[var(--color-border)]">
                      <td className="py-2 pr-2">{n.name}</td>
                      <td className="py-2 pr-2">{n.email}</td>
                      <td className="py-2 pr-2">
                        <select
                          value={n.rolle}
                          disabled={istSelf}
                          onChange={(e) => onRolle(n, e.target.value as Rolle)}
                          className="h-9 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm disabled:opacity-50"
                        >
                          {ROLLEN.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="py-2 pr-2">
                        {n.aktiv ? (
                          <span className="text-[var(--color-success)]">aktiv</span>
                        ) : (
                          <span className="text-[var(--color-muted-foreground)]">inaktiv</span>
                        )}
                      </td>
                      <td className="py-2">
                        <Button
                          variant={n.aktiv ? "outline" : "secondary"}
                          size="sm"
                          disabled={istSelf}
                          onClick={() => onToggleAktiv(n)}
                        >
                          {n.aktiv ? "Deaktivieren" : "Aktivieren"}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
