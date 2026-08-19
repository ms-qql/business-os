"use client";

import * as React from "react";
import Link from "next/link";
import { Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { ApiError } from "@/lib/api/client";
import {
  listRechnungen,
  createRechnung,
  getRechnung,
  updateRechnungKopfdaten,
  addPosition,
  updatePosition,
  deletePosition,
  type Rechnung,
  type RechnungListItem,
  type RechnungStatus,
} from "@/lib/api/rechnungen";
import { kopfdatenSchema, type KopfdatenFormValues } from "@/lib/schemas/rechnung";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { RechnungPositionForm, positionToForm } from "@/components/rechnungen/rechnung-position-form";
import { RechnungFreigabe } from "@/components/rechnungen/rechnung-freigabe";
import { berlinDateInputValue } from "@/lib/zeit";

function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

function statusBadgeVariant(status: RechnungStatus): "success" | "neutral" | "danger" {
  if (status === "versendet") return "success";
  if (status === "storniert") return "danger";
  return "neutral";
}

function statusLabel(status: RechnungStatus): string {
  if (status === "versendet") return "Versendet";
  if (status === "storniert") return "Storniert";
  return "Entwurf";
}

function RechnungKopfdatenForm({
  rechnung,
  onSpeichern,
}: {
  rechnung: Rechnung;
  onSpeichern: (r: Rechnung) => void;
}) {
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { register, handleSubmit } = useForm<KopfdatenFormValues>({
    resolver: zodResolver(kopfdatenSchema),
    defaultValues: {
      rechnungsdatum: rechnung.rechnungsdatum
        ? rechnung.rechnungsdatum.slice(0, 10)
        : berlinDateInputValue(),
      leistungsdatum: rechnung.leistungsdatum
        ? rechnung.leistungsdatum.slice(0, 10)
        : berlinDateInputValue(),
      empfaenger_email: rechnung.empfaenger_email ?? "",
    },
  });

  async function submit(values: KopfdatenFormValues) {
    setSpeichert(true);
    setError(null);
    try {
      onSpeichern(
        await updateRechnungKopfdaten(rechnung.id, {
          rechnungsdatum: values.rechnungsdatum,
          leistungsdatum: values.leistungsdatum,
          empfaenger_email: values.empfaenger_email || null,
        }),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit(submit)}
      className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-start"
    >
      <div>
        <Label htmlFor="r-rechnungsdatum">Rechnungsdatum</Label>
        <Input id="r-rechnungsdatum" type="date" {...register("rechnungsdatum")} />
      </div>
      <div>
        <Label htmlFor="r-leistungsdatum">Leistungsdatum</Label>
        <Input id="r-leistungsdatum" type="date" {...register("leistungsdatum")} />
      </div>
      <div>
        <Label htmlFor="r-empfaenger">Empfänger-E-Mail</Label>
        <Input id="r-empfaenger" type="email" {...register("empfaenger_email")} placeholder="kunde@beispiel.de" />
      </div>
      <div className="sm:self-end">
        <Button type="submit" size="sm" variant="secondary" disabled={speichert}>
          {speichert ? "Speichert …" : "Kopfdaten speichern"}
        </Button>
      </div>
      {error && <Alert variant="danger" className="sm:col-span-4">{error}</Alert>}
    </form>
  );
}

function RechnungSummenBlock({ rechnung }: { rechnung: Rechnung }) {
  return (
    <div className="grid grid-cols-3 gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
      <div>
        <p className="text-[var(--color-muted-foreground)]">Netto</p>
        <p className="font-medium">{formatEuro(rechnung.netto_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Steuer</p>
        <p className="font-medium">{formatEuro(rechnung.steuer_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Brutto</p>
        <p className="font-medium">{formatEuro(rechnung.brutto_summe)}</p>
      </div>
    </div>
  );
}

function RechnungPositionenTabelle({
  rechnung,
  bearbeitetId,
  onBearbeiten,
  onEntfernen,
}: {
  rechnung: Rechnung;
  bearbeitetId: string | null;
  onBearbeiten: (id: string) => void;
  onEntfernen: (id: string) => void;
}) {
  if (rechnung.positionen.length === 0) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Positionen hinzugefügt.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Bezeichnung</TableHead>
          <TableHead>Menge</TableHead>
          <TableHead>Einzelpreis</TableHead>
          <TableHead>Steuersatz</TableHead>
          <TableHead>Summe</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {rechnung.positionen.map((p) => (
          <TableRow
            key={p.id}
            className={bearbeitetId === p.id ? "bg-[var(--color-surface-muted)]" : undefined}
          >
            <TableCell>{p.bezeichnung}</TableCell>
            <TableCell>
              {p.menge} {p.einheit}
            </TableCell>
            <TableCell>{formatEuro(p.netto_einzelpreis)}</TableCell>
            <TableCell>{p.steuersatz} %</TableCell>
            <TableCell>{formatEuro(p.positions_summe)}</TableCell>
            <TableCell>
              <div className="flex gap-1">
                <button
                  type="button"
                  aria-label="Position bearbeiten"
                  onClick={() => onBearbeiten(p.id)}
                  className="rounded p-1 hover:bg-[var(--color-border)]"
                >
                  <Pencil size={14} />
                </button>
                <button
                  type="button"
                  aria-label="Position entfernen"
                  onClick={() => onEntfernen(p.id)}
                  className="rounded p-1 hover:bg-[var(--color-border)]"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function RechnungEditor({
  rechnung,
  onChange,
  onFreigabeOeffnen,
}: {
  rechnung: Rechnung;
  onChange: (r: Rechnung) => void;
  onFreigabeOeffnen: () => void;
}) {
  const [bearbeitetId, setBearbeitetId] = React.useState<string | null>(null);
  const [zeigeNeu, setZeigeNeu] = React.useState(false);
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const bearbeitetePosition = rechnung.positionen.find((p) => p.id === bearbeitetId) ?? null;

  async function onHinzufuegen(values: Parameters<typeof addPosition>[1]) {
    setSpeichert(true);
    setError(null);
    try {
      onChange(await addPosition(rechnung.id, values));
      setZeigeNeu(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Position konnte nicht hinzugefügt werden.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onAendern(values: Parameters<typeof updatePosition>[2]) {
    if (!bearbeitetId) return;
    setSpeichert(true);
    setError(null);
    try {
      onChange(await updatePosition(rechnung.id, bearbeitetId, values));
      setBearbeitetId(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Position konnte nicht geändert werden.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onEntfernen(positionId: string) {
    setError(null);
    try {
      onChange(await deletePosition(rechnung.id, positionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Position konnte nicht entfernt werden.");
    }
  }

  return (
    <div className="space-y-4">
      {error && <Alert variant="danger">{error}</Alert>}

      <RechnungKopfdatenForm rechnung={rechnung} onSpeichern={onChange} />

      <RechnungPositionenTabelle
        rechnung={rechnung}
        bearbeitetId={bearbeitetId}
        onBearbeiten={(id) => {
          setBearbeitetId(id);
          setZeigeNeu(false);
        }}
        onEntfernen={onEntfernen}
      />

      {bearbeitetePosition ? (
        <RechnungPositionForm
          initial={positionToForm(bearbeitetePosition)}
          onSubmit={onAendern}
          onAbbrechen={() => setBearbeitetId(null)}
          speichert={speichert}
        />
      ) : zeigeNeu ? (
        <RechnungPositionForm
          onSubmit={onHinzufuegen}
          onAbbrechen={() => setZeigeNeu(false)}
          speichert={speichert}
        />
      ) : (
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={() => setZeigeNeu(true)}
        >
          <Plus size={16} />
          Position hinzufügen
        </Button>
      )}

      <RechnungSummenBlock rechnung={rechnung} />

      <Button
        type="button"
        size="sm"
        disabled={rechnung.positionen.length === 0}
        onClick={onFreigabeOeffnen}
        title={
          rechnung.positionen.length === 0
            ? "Rechnung ohne Position kann nicht freigegeben werden."
            : undefined
        }
      >
        Zur Freigabe
      </Button>
    </div>
  );
}

/** Rechnungen-Abschnitt eines Vorgangs (PROJ-8) — Entwurf erstellen/bearbeiten, freigeben, senden. */
export function VorgangRechnungen({
  vorgangId,
  darfSchreiben,
  kundeEmail,
}: {
  vorgangId: string;
  darfSchreiben: boolean;
  kundeEmail: string | null;
}) {
  const [liste, setListe] = React.useState<RechnungListItem[] | null>(null);
  const [aktuelles, setAktuelles] = React.useState<Rechnung | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [erstellt, setErstellt] = React.useState(false);
  const [freigabeOffen, setFreigabeOffen] = React.useState(false);

  const laden = React.useCallback(async () => {
    setError(null);
    try {
      const items = await listRechnungen(vorgangId);
      setListe(items);
      const entwurf = items.find((r) => r.status === "entwurf");
      if (entwurf) {
        setAktuelles(await getRechnung(entwurf.id));
      } else {
        setAktuelles(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rechnungen konnten nicht geladen werden.");
    }
  }, [vorgangId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onNeueRechnung() {
    setErstellt(true);
    setError(null);
    try {
      const r = await createRechnung(vorgangId, {
        rechnungsdatum: berlinDateInputValue(),
        leistungsdatum: berlinDateInputValue(),
        empfaenger_email: kundeEmail ?? null,
      });
      setAktuelles(r);
      setListe((prev) => [
        {
          id: r.id,
          rechnungsnummer: r.rechnungsnummer,
          status: r.status,
          zahlungsstatus: r.zahlungsstatus,
          brutto_summe: r.brutto_summe,
          versendet_at: r.versendet_at,
          created_at: r.created_at,
        },
        ...(prev ?? []),
      ]);
    } catch (err) {
      // Backend liefert 409 bei nicht „Erledigt" mit deutscher Meldung (AC1).
      setError(err instanceof ApiError ? err.message : "Rechnung konnte nicht erstellt werden.");
    } finally {
      setErstellt(false);
    }
  }

  const hatEntwurf = liste?.some((r) => r.status === "entwurf") ?? false;

  return (
    <div className="space-y-4">
      {error && <Alert variant="danger">{error}</Alert>}

      {liste === null ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : liste.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Rechnung vorhanden.</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {liste.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center gap-2">
              <Link
                href={`/rechnungen/${r.id}`}
                className="font-medium text-[var(--color-brand)] hover:underline"
              >
                {r.rechnungsnummer}
              </Link>
              <Badge variant={statusBadgeVariant(r.status)}>{statusLabel(r.status)}</Badge>
              {r.status === "versendet" && (
                <Badge
                  variant={
                    r.zahlungsstatus === "Bezahlt"
                      ? "success"
                      : r.zahlungsstatus === "Storniert"
                        ? "danger"
                        : "neutral"
                  }
                >
                  {r.zahlungsstatus}
                </Badge>
              )}
              <span className="text-[var(--color-muted-foreground)]">{formatEuro(r.brutto_summe)}</span>
            </li>
          ))}
        </ul>
      )}

      {darfSchreiben && !hatEntwurf && (
        <Alert variant="info">
          Eine Rechnung kann nur aus einem Vorgang mit Status „Erledigt“ erstellt werden.
        </Alert>
      )}

      {darfSchreiben && !aktuelles && (
        <Button size="sm" disabled={erstellt} onClick={onNeueRechnung}>
          <Plus size={16} />
          {erstellt ? "Wird erstellt …" : "Rechnung erstellen"}
        </Button>
      )}

      {darfSchreiben && aktuelles && (
        <RechnungEditor
          rechnung={aktuelles}
          onChange={setAktuelles}
          onFreigabeOeffnen={() => setFreigabeOffen(true)}
        />
      )}

      {aktuelles && (
        <RechnungFreigabe
          rechnung={aktuelles}
          open={freigabeOffen}
          onOpenChange={setFreigabeOffen}
          onVersendet={laden}
        />
      )}
    </div>
  );
}
