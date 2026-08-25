"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { formatEuro } from "@/lib/format";
import { positionPreisOverride } from "@/lib/api/gewerke";
import type { Angebot, AngebotPosition } from "@/lib/api/angebote";

const SERVER_FEHLER = "Keine Verbindung zum Server. Die Preisanpassung wurde nicht gespeichert.";

/**
 * Interner Preis-Override einer aus einem Gewerk übernommenen Position.
 * Bei Abweichung vom kalkulierten Wert ist eine interne Begründung Pflicht
 * (erscheint NICHT im Kunden-PDF). Wird exakt auf den kalkulierten Wert
 * zurückgestellt, werden beide Felder geleert.
 */
export function PositionOverride({
  angebot,
  position,
  onAngepasst,
  onAbbrechen,
}: {
  angebot: Angebot;
  position: AngebotPosition;
  onAngepasst: (angebot: Angebot) => void;
  onAbbrechen: () => void;
}) {
  const kalkuliert = position.kalkulierter_einzelpreis ?? position.einzelpreis;
  const [preis, setPreis] = React.useState(position.einzelpreis);
  const [begruendung, setBegruendung] = React.useState(position.preis_override_begruendung ?? "");
  const [error, setError] = React.useState<string | null>(null);
  const [speichert, setSpeichert] = React.useState(false);

  async function onSpeichern() {
    if (!(preis >= 0)) {
      setError("Der Preis darf nicht negativ sein.");
      return;
    }
    if (Math.abs(preis - kalkuliert) >= 0.005 && !begruendung.trim()) {
      setError("Bei einer Abweichung vom kalkulierten Preis ist eine interne Begründung erforderlich.");
      return;
    }
    setError(null);
    setSpeichert(true);
    try {
      const a = await positionPreisOverride(angebot.id, position.id, {
        einzelpreis: preis,
        begruendung: begruendung.trim() || null,
      });
      onAngepasst(a);
    } catch (err) {
      setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <div className="space-y-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="ov-preis">Neuer Einzelpreis (€)</Label>
          <Input
            id="ov-preis"
            type="number"
            step="0.01"
            min="0"
            value={preis}
            onChange={(e) => setPreis(Number(e.target.value))}
          />
          <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
            Kalkuliert: {formatEuro(kalkuliert)}
          </p>
        </div>
        <div>
          <Label htmlFor="ov-begr">Interne Begründung</Label>
          <Input
            id="ov-begr"
            value={begruendung}
            onChange={(e) => setBegruendung(e.target.value)}
            placeholder="Nur intern, nicht im Angebot sichtbar"
          />
        </div>
      </div>
      {error && <Alert variant="danger">{error}</Alert>}
      <div className="flex gap-2">
        <Button size="sm" onClick={() => void onSpeichern()} disabled={speichert}>
          {speichert ? "Speichert …" : "Preis anpassen"}
        </Button>
        <Button size="sm" variant="secondary" onClick={onAbbrechen} disabled={speichert}>
          Abbrechen
        </Button>
      </div>
    </div>
  );
}
