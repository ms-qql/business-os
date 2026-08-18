"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { PositionForm } from "@/components/angebote/position-form";
import { AngebotFreigabe } from "@/components/angebote/angebot-freigabe";
import { ApiError } from "@/lib/api/client";
import {
  listAngebote,
  createAngebot,
  getAngebot,
  updateAngebotKopfdaten,
  addPosition,
  updatePosition,
  deletePosition,
  angebotNeueVersion,
  type Angebot,
  type AngebotListItem,
  type AngebotPosition,
} from "@/lib/api/angebote";
import { kopfdatenSchema, type KopfdatenFormValues } from "@/lib/schemas/angebot";
import type { PositionFormValues } from "@/lib/schemas/angebot";

function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

function KopfdatenForm({ angebot, onSpeichern }: { angebot: Angebot; onSpeichern: (a: Angebot) => void }) {
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { register, handleSubmit } = useForm<KopfdatenFormValues>({
    resolver: zodResolver(kopfdatenSchema),
    defaultValues: { gueltig_bis: angebot.gueltig_bis ?? "", freitext: angebot.freitext ?? "" },
  });

  async function submit(values: KopfdatenFormValues) {
    setSpeichert(true);
    setError(null);
    try {
      onSpeichern(
        await updateAngebotKopfdaten(angebot.id, {
          gueltig_bis: values.gueltig_bis || null,
          freitext: values.freitext || null,
        }),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="grid gap-3 sm:grid-cols-[auto_1fr] sm:items-start">
      <div>
        <Label htmlFor="gueltig-bis">Gültig bis</Label>
        <Input id="gueltig-bis" type="date" {...register("gueltig_bis")} />
      </div>
      <div>
        <Label htmlFor="freitext">Freitext</Label>
        <Textarea id="freitext" rows={3} {...register("freitext")} placeholder="Zusätzlicher Text im Angebot …" />
      </div>
      {error && <Alert variant="danger" className="sm:col-span-2">{error}</Alert>}
      <div className="sm:col-span-2">
        <Button type="submit" size="sm" variant="secondary" disabled={speichert}>
          {speichert ? "Speichert …" : "Kopfdaten speichern"}
        </Button>
      </div>
    </form>
  );
}

function SummenBlock({ angebot }: { angebot: Angebot }) {
  return (
    <div className="grid grid-cols-3 gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
      <div>
        <p className="text-[var(--color-muted-foreground)]">Netto</p>
        <p className="font-medium">{formatEuro(angebot.netto_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Steuer</p>
        <p className="font-medium">{formatEuro(angebot.steuer_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Brutto</p>
        <p className="font-medium">{formatEuro(angebot.brutto_summe)}</p>
      </div>
    </div>
  );
}

function PositionenTabelle({
  angebot,
  bearbeitetId,
  onBearbeiten,
  onEntfernen,
}: {
  angebot: Angebot;
  bearbeitetId: string | null;
  onBearbeiten: (id: string) => void;
  onEntfernen: (id: string) => void;
}) {
  if (angebot.positionen.length === 0) {
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
          <TableHead>Rabatt</TableHead>
          <TableHead>Summe</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {angebot.positionen.map((p) => (
          <TableRow key={p.id} className={bearbeitetId === p.id ? "bg-[var(--color-surface-muted)]" : undefined}>
            <TableCell>{p.bezeichnung}</TableCell>
            <TableCell>{p.menge} {p.einheit}</TableCell>
            <TableCell>{formatEuro(p.einzelpreis)}</TableCell>
            <TableCell>{p.steuersatz} %</TableCell>
            <TableCell>{p.rabatt_typ === "prozent" ? `${p.rabatt_wert} %` : formatEuro(p.rabatt_wert)}</TableCell>
            <TableCell>{formatEuro(p.positions_summe)}</TableCell>
            <TableCell>
              <div className="flex gap-1">
                <button type="button" aria-label="Position bearbeiten" onClick={() => onBearbeiten(p.id)} className="rounded p-1 hover:bg-[var(--color-border)]">
                  <Pencil size={14} />
                </button>
                <button type="button" aria-label="Position entfernen" onClick={() => onEntfernen(p.id)} className="rounded p-1 hover:bg-[var(--color-border)]">
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

function toFormValues(p: AngebotPosition): PositionFormValues {
  return {
    bezeichnung: p.bezeichnung,
    menge: p.menge,
    einheit: p.einheit,
    einzelpreis: p.einzelpreis,
    steuersatz: p.steuersatz,
    rabatt_typ: p.rabatt_typ,
    rabatt_wert: p.rabatt_wert,
  };
}

function AngebotEditor({
  angebot,
  onChange,
  onFreigabeOeffnen,
}: {
  angebot: Angebot;
  onChange: (a: Angebot) => void;
  onFreigabeOeffnen: () => void;
}) {
  const [bearbeitetId, setBearbeitetId] = React.useState<string | null>(null);
  const [zeigeNeu, setZeigeNeu] = React.useState(false);
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const bearbeitetePosition = angebot.positionen.find((p) => p.id === bearbeitetId) ?? null;

  async function onHinzufuegen(values: PositionFormValues) {
    setSpeichert(true);
    setError(null);
    try {
      onChange(await addPosition(angebot.id, values));
      setZeigeNeu(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Position konnte nicht hinzugefügt werden.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onAendern(values: PositionFormValues) {
    if (!bearbeitetId) return;
    setSpeichert(true);
    setError(null);
    try {
      onChange(await updatePosition(angebot.id, bearbeitetId, values));
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
      onChange(await deletePosition(angebot.id, positionId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Position konnte nicht entfernt werden.");
    }
  }

  return (
    <div className="space-y-4">
      {error && <Alert variant="danger">{error}</Alert>}

      <KopfdatenForm angebot={angebot} onSpeichern={onChange} />

      <PositionenTabelle
        angebot={angebot}
        bearbeitetId={bearbeitetId}
        onBearbeiten={(id) => {
          setBearbeitetId(id);
          setZeigeNeu(false);
        }}
        onEntfernen={onEntfernen}
      />

      {bearbeitetePosition ? (
        <PositionForm
          initial={toFormValues(bearbeitetePosition)}
          onSubmit={onAendern}
          onAbbrechen={() => setBearbeitetId(null)}
          speichert={speichert}
        />
      ) : zeigeNeu ? (
        <PositionForm onSubmit={onHinzufuegen} onAbbrechen={() => setZeigeNeu(false)} speichert={speichert} />
      ) : (
        <Button type="button" size="sm" variant="secondary" onClick={() => setZeigeNeu(true)}>
          <Plus size={16} />
          Position hinzufügen
        </Button>
      )}

      <SummenBlock angebot={angebot} />

      <Button
        type="button"
        size="sm"
        disabled={angebot.positionen.length === 0}
        onClick={onFreigabeOeffnen}
        title={angebot.positionen.length === 0 ? "Angebot ohne Position kann nicht freigegeben werden." : undefined}
      >
        Zur Freigabe
      </Button>
    </div>
  );
}

/** Angebote-Abschnitt eines Vorgangs (PROJ-5) — Entwurf erstellen/bearbeiten, freigeben, senden. */
export function VorgangAngebote({
  vorgangId,
  darfSchreiben,
  kundeEmail,
}: {
  vorgangId: string;
  darfSchreiben: boolean;
  kundeEmail: string | null;
}) {
  const [liste, setListe] = React.useState<AngebotListItem[] | null>(null);
  const [aktuelles, setAktuelles] = React.useState<Angebot | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [erstellt, setErstellt] = React.useState(false);
  const [freigabeOffen, setFreigabeOffen] = React.useState(false);

  const laden = React.useCallback(async () => {
    setError(null);
    try {
      const items = await listAngebote(vorgangId);
      setListe(items);
      const entwurf = items.find((a) => a.status === "entwurf");
      if (entwurf) {
        setAktuelles(await getAngebot(entwurf.id));
      } else {
        setAktuelles(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Angebote konnten nicht geladen werden.");
    }
  }, [vorgangId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onNeuesAngebot() {
    setErstellt(true);
    setError(null);
    try {
      const a = await createAngebot(vorgangId);
      setAktuelles(a);
      setListe((prev) => [{ id: a.id, nummer: a.nummer, version: a.version, status: a.status, brutto_summe: a.brutto_summe, versendet_am: a.versendet_am, created_at: a.created_at }, ...(prev ?? [])]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Angebot konnte nicht erstellt werden.");
    } finally {
      setErstellt(false);
    }
  }

  async function onNeueVersion(vorgaengerId: string) {
    setErstellt(true);
    setError(null);
    try {
      const a = await angebotNeueVersion(vorgaengerId);
      setAktuelles(a);
      await laden();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Neue Version konnte nicht erstellt werden.");
    } finally {
      setErstellt(false);
    }
  }

  const letztes = liste?.[0] ?? null;

  return (
    <div className="space-y-4">
      {error && <Alert variant="danger">{error}</Alert>}

      {liste === null ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : liste.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch kein Angebot vorhanden.</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {liste.map((a) => (
            <li key={a.id} className="flex items-center gap-2">
              <span className="font-medium">{a.nummer}</span>
              <span className="text-[var(--color-muted-foreground)]">Version {a.version}</span>
              <Badge variant={a.status === "versendet" ? "success" : "neutral"}>
                {a.status === "versendet" ? "Versendet" : "Entwurf"}
              </Badge>
              <span className="text-[var(--color-muted-foreground)]">{formatEuro(a.brutto_summe)}</span>
            </li>
          ))}
        </ul>
      )}

      {darfSchreiben && !aktuelles && (!letztes || letztes.status === "versendet") && (
        <Button size="sm" disabled={erstellt} onClick={() => (letztes ? onNeueVersion(letztes.id) : onNeuesAngebot())}>
          <Plus size={16} />
          {erstellt ? "Wird erstellt …" : letztes ? "Neue Version erstellen" : "Angebot erstellen"}
        </Button>
      )}

      {darfSchreiben && aktuelles && (
        <AngebotEditor angebot={aktuelles} onChange={setAktuelles} onFreigabeOeffnen={() => setFreigabeOffen(true)} />
      )}

      {aktuelles && (
        <AngebotFreigabe
          angebot={aktuelles}
          vorschlagEmpfaenger={kundeEmail ?? ""}
          open={freigabeOffen}
          onOpenChange={setFreigabeOffen}
          onVersendet={laden}
        />
      )}
    </div>
  );
}
