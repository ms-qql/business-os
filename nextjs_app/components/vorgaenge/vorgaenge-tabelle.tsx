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
import { AmpelBadge } from "@/components/triage/ampel-badge";
import { listVorgaenge, type VorgangListItem, type TriageFilter } from "@/lib/api/vorgaenge";
import { ApiError } from "@/lib/api/client";
import { VORGANG_STATUS, kannSchreiben, type Rolle, type VorgangStatus } from "@/lib/theme/tokens";
import type { TriageStatus } from "@/lib/api/triage";

const LIMIT = 20;

const TRIAGE_OPTIONEN: { value: TriageStatus | "alle"; label: string }[] = [
  { value: "alle", label: "Alle Ampeln" },
  { value: "gruen", label: "Grün" },
  { value: "gelb", label: "Gelb" },
  { value: "rot", label: "Rot" },
  { value: "nicht_bewertet", label: "Nicht bewertet" },
];

export function VorgaengeTabelle({ rolle }: { rolle: Rolle }) {
  const [items, setItems] = React.useState<VorgangListItem[]>([]);
  const [total, setTotal] = React.useState(0);
  const [offset, setOffset] = React.useState(0);
  const [suche, setSuche] = React.useState("");
  const [status, setStatus] = React.useState<VorgangStatus | "alle">("alle");
  const [triage, setTriage] = React.useState<TriageFilter>("alle");
  const [ampelSort, setAmpelSort] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const darfSchreiben = kannSchreiben(rolle);
  // Monteure sehen keine Triage-UI (serverseitig ohnehin ausgeblendet).
  const zeigeTriage = rolle !== "Monteur";

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listVorgaenge({
        status,
        suche: suche || undefined,
        triage: zeigeTriage ? triage : "alle",
        ampelSort: zeigeTriage && ampelSort,
        limit: LIMIT,
        offset,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [status, suche, triage, ampelSort, offset, zeigeTriage]);

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
        {zeigeTriage && (
          <>
            <Select
              value={triage}
              onChange={(e) => {
                setOffset(0);
                setTriage(e.target.value as TriageFilter);
              }}
              className="w-auto"
              aria-label="Nach Ampelfarbe filtern"
            >
              {TRIAGE_OPTIONEN.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
            <label className="flex items-center gap-2 text-sm text-[var(--color-muted-foreground)]">
              <input
                type="checkbox"
                checked={ampelSort}
                onChange={(e) => {
                  setOffset(0);
                  setAmpelSort(e.target.checked);
                }}
                className="h-4 w-4 rounded border-[var(--color-border)]"
              />
              Nach Ampel sortieren
            </label>
          </>
        )}
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
                {zeigeTriage && <TableHead>Ampel</TableHead>}
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
                  {zeigeTriage && (
                    <TableCell>
                      {v.triage ? (
                        <AmpelBadge status={v.triage.status} kurzgrund={v.triage.gruende[0] ?? null} />
                      ) : (
                        <span className="text-xs text-[var(--color-muted-foreground)]">—</span>
                      )}
                    </TableCell>
                  )}
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
