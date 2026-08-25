"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { formatEuro } from "@/lib/format";
import {
  getGewerke,
  gewerkInAngebotUebernehmen,
  type GewerkKurz,
} from "@/lib/api/gewerke";

const SERVER_FEHLER = "Keine Verbindung zum Server. Das Gewerk konnte nicht übernommen werden.";

/** Nimmt ein Gewerk als Angebotsposition auf (Snapshot, keine Live-Referenz). */
export function GewerkUebernahme({
  angebotId,
  onUebernommen,
}: {
  angebotId: string;
  onUebernommen: (angebot: import("@/lib/api/angebote").Angebot) => void;
}) {
  const [gewerke, setGewerke] = React.useState<GewerkKurz[]>([]);
  const [suchbegriff, setSuchbegriff] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [auswahl, setAuswahl] = React.useState<string | null>(null);
  const [menge, setMenge] = React.useState(1);
  const [uebernimmt, setUebernimmt] = React.useState(false);

  React.useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getGewerke();
        if (active) setGewerke(res.items);
      } catch (err) {
        if (active)
          setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const gefiltert = gewerke.filter((g) =>
    g.bezeichnung.toLowerCase().includes(suchbegriff.trim().toLowerCase()),
  );

  async function onUebernehmen() {
    if (!auswahl) {
      setError("Bitte ein Gewerk auswählen.");
      return;
    }
    if (!(menge > 0)) {
      setError("Die Menge muss größer als 0 sein.");
      return;
    }
    setError(null);
    setUebernimmt(true);
    try {
      const angebot = await gewerkInAngebotUebernehmen(angebotId, {
        gewerk_id: auswahl,
        menge,
      });
      onUebernommen(angebot);
    } catch (err) {
      setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
    } finally {
      setUebernimmt(false);
    }
  }

  return (
    <div className="space-y-3">
      {error && <Alert variant="danger">{error}</Alert>}

      <div className="relative">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted-foreground)]"
        />
        <Input
          value={suchbegriff}
          onChange={(e) => setSuchbegriff(e.target.value)}
          placeholder="Gewerk suchen …"
          className="pl-9"
          aria-label="Gewerk suchen"
        />
      </div>

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : gefiltert.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Keine Gewerke gefunden. Legen Sie zuerst Gewerke im Gewerke-Katalog an.
        </p>
      ) : (
        <ul className="max-h-64 space-y-1 overflow-auto rounded-[var(--radius-md)] border border-[var(--color-border)] p-1">
          {gefiltert.map((g) => (
            <li key={g.id}>
              <button
                type="button"
                onClick={() => setAuswahl(g.id)}
                className={`flex w-full items-center justify-between rounded-[var(--radius-sm)] px-2.5 py-2 text-left text-sm ${
                  auswahl === g.id
                    ? "bg-[var(--color-surface-muted)] font-medium"
                    : "hover:bg-[var(--color-surface-muted)]/60"
                }`}
              >
                <span>
                  {g.bezeichnung}
                  <span className="ml-1 text-xs text-[var(--color-muted-foreground)]">
                    ({g.einheit})
                  </span>
                </span>
                <span className="text-[var(--color-muted-foreground)]">{formatEuro(g.vk_preis)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-32">
          <Label htmlFor="gw-ueb-menge">Menge</Label>
          <Input
            id="gw-ueb-menge"
            type="number"
            step="0.01"
            min="0"
            value={menge}
            onChange={(e) => setMenge(Number(e.target.value))}
          />
        </div>
        <Button onClick={() => void onUebernehmen()} disabled={uebernimmt || !auswahl}>
          {uebernimmt ? "Übernimmt …" : "Übernehmen"}
        </Button>
      </div>
    </div>
  );
}
