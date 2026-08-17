"use client";

import * as React from "react";
import Link from "next/link";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Alert } from "@/components/ui/label";
import { VorgangStatusBadge } from "@/components/vorgaenge/vorgang-status-badge";
import { VorgangFormDialog } from "@/components/vorgaenge/vorgang-form-dialog";
import { listVorgaenge, type VorgangListItem } from "@/lib/api/vorgaenge";
import { ApiError } from "@/lib/api/client";
import { VORGANG_STATUS, kannSchreiben, type Rolle, type VorgangStatus } from "@/lib/theme/tokens";

const LIMIT = 20;

export function VorgaengeTabelle({ rolle }: { rolle: Rolle }) {
  const [items, setItems] = React.useState<VorgangListItem[]>([]);
  const [total, setTotal] = React.useState(0);
  const [offset, setOffset] = React.useState(0);
  const [suche, setSuche] = React.useState("");
  const [status, setStatus] = React.useState<VorgangStatus | "alle">("alle");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const darfSchreiben = kannSchreiben(rolle);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listVorgaenge({ status, suche: suche || undefined, limit: LIMIT, offset });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [status, suche, offset]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder="Suche nach Kunde oder Anliegen …"
          value={suche}
          onChange={(e) => {
            setOffset(0);
            setSuche(e.target.value);
          }}
          className="max-w-sm"
        />
        <Select
          value={status}
          onChange={(e) => {
            setOffset(0);
            setStatus(e.target.value as VorgangStatus | "alle");
          }}
          className="w-auto"
        >
          <option value="alle">Alle Status</option>
          {VORGANG_STATUS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
        {darfSchreiben && <Button onClick={() => setDialogOpen(true)}>Neuer Vorgang</Button>}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Keine Vorgänge gefunden.</p>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kunde</TableHead>
                <TableHead>Anliegen</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Zugewiesen</TableHead>
                <TableHead>Erstellt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((v) => (
                <TableRow key={v.id}>
                  <TableCell>
                    <Link href={`/vorgaenge/${v.id}`} className="font-medium text-[var(--color-brand)] hover:underline">
                      {v.kunde_name}
                    </Link>
                  </TableCell>
                  <TableCell>{v.anliegen}</TableCell>
                  <TableCell>
                    <VorgangStatusBadge status={v.status} />
                  </TableCell>
                  <TableCell>{v.zugewiesener_nutzer_id ? "Ja" : "—"}</TableCell>
                  <TableCell>{new Date(v.created_at).toLocaleDateString("de-DE")}</TableCell>
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
        <VorgangFormDialog open={dialogOpen} onOpenChange={setDialogOpen} onSaved={() => void laden()} />
      )}
    </div>
  );
}
