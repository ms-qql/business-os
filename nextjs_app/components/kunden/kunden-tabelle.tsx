"use client";

import * as React from "react";
import Link from "next/link";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/label";
import { KundeFormDialog } from "@/components/kunden/kunde-form-dialog";
import { listKunden, type Kunde } from "@/lib/api/kunden";
import { ApiError } from "@/lib/api/client";
import { kannSchreiben, type Rolle } from "@/lib/theme/tokens";

const LIMIT = 20;

export function KundenTabelle({ rolle }: { rolle: Rolle }) {
  const [items, setItems] = React.useState<Kunde[]>([]);
  const [total, setTotal] = React.useState(0);
  const [offset, setOffset] = React.useState(0);
  const [suche, setSuche] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const darfSchreiben = kannSchreiben(rolle);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listKunden({ suche: suche || undefined, limit: LIMIT, offset });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [suche, offset]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="Suche nach Name, E-Mail oder Telefon …"
          value={suche}
          onChange={(e) => {
            setOffset(0);
            setSuche(e.target.value);
          }}
          className="max-w-sm"
        />
        {darfSchreiben && <Button onClick={() => setDialogOpen(true)}>Neuer Kunde</Button>}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Kunden angelegt.</p>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>E-Mail</TableHead>
                <TableHead>Telefon</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((k) => (
                <TableRow key={k.id}>
                  <TableCell>
                    <Link href={`/kunden/${k.id}`} className="font-medium text-[var(--color-brand)] hover:underline">
                      {k.name}
                    </Link>
                  </TableCell>
                  <TableCell>{k.email ?? "—"}</TableCell>
                  <TableCell>{k.telefon ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between text-sm text-[var(--color-muted-foreground)]">
            <span>
              {offset + 1}–{Math.min(offset + LIMIT, total)} von {total}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
              >
                Zurück
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + LIMIT >= total}
                onClick={() => setOffset((o) => o + LIMIT)}
              >
                Weiter
              </Button>
            </div>
          </div>
        </>
      )}

      {darfSchreiben && (
        <KundeFormDialog open={dialogOpen} onOpenChange={setDialogOpen} onSaved={() => void laden()} />
      )}
    </div>
  );
}
