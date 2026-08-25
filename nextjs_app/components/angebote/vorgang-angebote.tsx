"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2, Pencil, Boxes, Calculator } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Dialog } from "@/components/ui/dialog";
import { PositionForm } from "@/components/angebote/position-form";
import { AngebotFreigabe } from "@/components/angebote/angebot-freigabe";
import { GewerkUebernahme } from "@/components/gewerke/gewerk_uebernahme";
import { PositionOverride } from "@/components/gewerke/position_override";
import { ApiError } from "@/lib/api/client";
import { formatEuro } from "@/lib/format";
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

function formatEuroLocal(wert: number): string {
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
        <p className="font-medium">{formatEuroLocal(angebot.netto_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Steuer</p>
        <p className="font-medium">{formatEuroLocal(angebot.steuer_summe)}</p>
      </div>
      <div>
        <p className="text-[var(--color-muted-foreground)]">Brutto</p>
        <p className="font-medium">{formatEuroLocal(angebot.brutto_summe)}</p>
      </div>
    </div>
  );
}

function PositionenTabelle({
  angebot,
  bearbeitetId,
  overrideId,
  onBearbeiten,
  onEntfernen,
  onOverrideStarten,
}: {
  angebot: Angebot;
  bearbeitetId: string | null;
  overrideId: string | null;
  onBearbeiten: (id: string) => void;
  onEntfernen: (id: string) => void;
  onOverrideStarten: (id: string) => void;
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
          <TableRow key={p.id} className={bearbeitetId === p.id || overrideId === p.id ? "bg-[var(--color-surface-muted)]" : undefined}>
            <TableCell>
              <div className="flex items-center gap-2">
                {p.bezeichnung}
                {p.aus_gewerk && (
                  <Badge variant="brand" title="Aus einem Gewerk übernommen (Kalkulations-Snapshot)">
                    Gewerk
                  </Badge>
                )}
              </div>
              {p.aus_gewerk && p.kalkulierter_einzelpreis !== null && p.kalkulierter_einzelpreis !== p.einzelpreis && (
                <div className="mt-0.5 text-xs text-[var(--color-muted-foreground)]">
                  kalkuliert: {formatEuroLocal(p.kalkulierter_einzelpreis)}
                  {p.preis_override_begruendung ? ` · ${p.preis_override_begruendung}` : ""}
                </div>
              )}
            </TableCell>
            <TableCell>{p.menge} {p.einheit}</TableCell>
            <TableCell>{formatEuroLocal(p.einzelpreis)}</TableCell>
            <TableCell>{p.steuersatz} %</TableCell>
            <TableCell>{p.rabatt_typ === "prozent" ? `${p.rabatt_wert} %` : formatEuroLocal(p.rabatt_wert)}</TableCell>
            <TableCell>{formatEuroLocal(p.positions_summe)}</TableCell>
            <TableCell>
              <div className="flex gap-1">
                <button type="button" aria-label="Position bearbeiten" onClick={() => onBearbeiten(p.id)} className="rounded p-1 hover:bg-[var(--color-border)]">
                  <Pencil size={14} />
                </button>
                {p.aus_gewerk && (
                  <button
                    type="button"
                    aria-label="Preis anpassen (interne Begründung)"
                    onClick={() => onOverrideStarten(p.id)}
                    className="rounded p-1 hover:bg-[var(--color-border)]"
                    title="Preis anpassen (interne Begründung)"
                  >
                    <Calculator size={14} />
                  </button>
                )}
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
  const [uebernahmeOffen, setUebernahmeOffen] = React.useState(false);
  const [overrideId, setOverrideId] = React.useState<string | null>(null);
  const [speichert, setSpeichert] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const bearbeitetePosition = angebot.positionen.find((p) => p.id === bearbeitetId) ?? null;
  const overridePosition = angebot.positionen.find((p) => p.id === overrideId) ?? null;

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
        overrideId={overrideId}
        onBearbeiten={(id) => {
          setBearbeitetId(id);
          setOverrideId(null);
          setZeigeNeu(false);
        }}
        onEntfernen={onEntfernen}
        onOverrideStarten={(id) => {
          setOverrideId(id);
          setBearbeitetId(null);
          setZeigeNeu(false);
        }}
      />

      {overridePosition && (
        <PositionOverride
          angebot={angebot}
          position={overridePosition}
          onAngepasst={(a) => {
            onChange(a);
            setOverrideId(null);
          }}
          onAbbrechen={() => setOverrideId(null)}
        />
      )}

      {bearbeitetePosition ? (
        <PositionForm
          initial={toFormValues(bearbeitetePosition)}
          onSubmit={onAendern}
          onAbbrechen={() => setBearbeitetId(null)}
          speichert={speichert}
        />
      ) : zeigeNeu ? (
        <PositionForm onSubmit={onHinzufuegen} onAbbrechen={() => setZeigeNeu(false)} speichert={speichert} />
      ) : overridePosition ? null : (
        <div className="flex flex-wrap gap-2">
          <Button type="button" size="sm" variant="secondary" onClick={() => setZeigeNeu(true)}>
            <Plus size={16} />
            Position hinzufügen
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={() => setUebernahmeOffen(true)}>
            <Boxes size={16} />
            Aus Gewerk übernehmen
          </Button>
        </div>
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

      <Dialog
        open={uebernahmeOffen}
        onOpenChange={setUebernahmeOffen}
        title="Gewerk übernehmen"
        description="Das Gewerk wird als Kalkulations-Snapshot in das Angebot übernommen."
        className="max-w-2xl"
      >
        <GewerkUebernahme
          angebotId={angebot.id}
          onUebernommen={(a) => {
            onChange(a);
            setUebernahmeOffen(false);
          }}
        />
      </Dialog>
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
      setListe((prev) => [{ id: a.id, angebot_nummer: a.angebot_nummer, version: a.version, status: a.status, brutto_summe: a.brutto_summe, versendet_at: a.versendet_at, created_at: a.created_at }, ...(prev ?? [])]);
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
              <span className="font-medium">{a.angebot_nummer}</span>
              <span className="text-[var(--color-muted-foreground)]">Version {a.version}</span>
              <Badge variant={a.status === "versendet" ? "success" : "neutral"}>
                {a.status === "versendet" ? "Versendet" : "Entwurf"}
              </Badge>
              <span className="text-[var(--color-muted-foreground)]">{formatEuroLocal(a.brutto_summe)}</span>
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
