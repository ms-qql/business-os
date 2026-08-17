"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { KundeFormDialog } from "@/components/kunden/kunde-form-dialog";
import { ObjektFormDialog } from "@/components/kunden/objekt-form-dialog";
import { VorgangStatusBadge } from "@/components/vorgaenge/vorgang-status-badge";
import { getKunde, listObjekte, deleteKunde, type Kunde, type Objekt } from "@/lib/api/kunden";
import { listVorgaenge, type VorgangListItem } from "@/lib/api/vorgaenge";
import { ApiError } from "@/lib/api/client";
import { kannSchreiben, type Rolle } from "@/lib/theme/tokens";

export function KundeDetail({ kundeId, rolle }: { kundeId: string; rolle: Rolle }) {
  const router = useRouter();
  const [kunde, setKunde] = React.useState<Kunde | null>(null);
  const [objekte, setObjekte] = React.useState<Objekt[]>([]);
  const [vorgaenge, setVorgaenge] = React.useState<VorgangListItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [editOpen, setEditOpen] = React.useState(false);
  const [objektDialogOpen, setObjektDialogOpen] = React.useState(false);
  const darfSchreiben = kannSchreiben(rolle);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [k, o, v] = await Promise.all([
        getKunde(kundeId),
        listObjekte(kundeId),
        listVorgaenge({ kunde_id: kundeId, limit: 50 }),
      ]);
      setKunde(k);
      setObjekte(o);
      setVorgaenge(v.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [kundeId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onDelete() {
    if (!kunde) return;
    if (!window.confirm(`Kunde „${kunde.name}" wirklich löschen?`)) return;
    try {
      await deleteKunde(kunde.id);
      router.push("/kunden");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Löschen fehlgeschlagen.",
      );
    }
  }

  if (loading) return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  if (error && !kunde) return <Alert variant="danger">{error}</Alert>;
  if (!kunde) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{kunde.name}</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            {kunde.email ?? "—"} · {kunde.telefon ?? "—"}
          </p>
        </div>
        {darfSchreiben && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setEditOpen(true)}>
              Bearbeiten
            </Button>
            <Button variant="danger" onClick={onDelete}>
              Löschen
            </Button>
          </div>
        )}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Objekte</CardTitle>
            <CardDescription>Einsatzadressen dieses Kunden.</CardDescription>
          </div>
          {darfSchreiben && (
            <Button size="sm" onClick={() => setObjektDialogOpen(true)}>
              Neues Objekt
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {objekte.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Objekte hinterlegt.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {objekte.map((o) => (
                <li key={o.id}>{o.adresse}</li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Vorgangshistorie</CardTitle>
        </CardHeader>
        <CardContent>
          {vorgaenge.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Vorgänge für diesen Kunden.</p>
          ) : (
            <ul className="divide-y divide-[var(--color-border)]">
              {vorgaenge.map((v) => (
                <li key={v.id} className="flex items-center justify-between py-2">
                  <Link href={`/vorgaenge/${v.id}`} className="text-[var(--color-brand)] hover:underline">
                    {v.anliegen}
                  </Link>
                  <VorgangStatusBadge status={v.status} />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <KundeFormDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        kunde={kunde}
        onSaved={(k) => setKunde(k)}
      />
      <ObjektFormDialog
        open={objektDialogOpen}
        onOpenChange={setObjektDialogOpen}
        kundeId={kunde.id}
        onSaved={(o) => setObjekte((prev) => [...prev, o])}
      />
    </div>
  );
}
