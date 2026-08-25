import * as React from "react";
import Link from "next/link";
import { Boxes, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { getKategorien, getGewerke } from "@/lib/api/gewerke";

/**
 * Schritt 6 (Preisliste/Leistungskatalog) — Ablösung der bisherigen /katalog-UI
 * durch den Gewerke-Katalog (PROJ-22). Der Schritt gilt als erledigt, sobald
 * mindestens ein Gewerk im Katalog angelegt ist (serverseitig via count_gewerke
 * berechnet). Hier zeigen wir den Status und verlinken in den Katalog.
 */
export function PreislisteSchritt({ onChanged }: { onChanged: () => void }) {
  const [anzahl, setAnzahl] = React.useState<number | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    (async () => {
      try {
        const kategorien = await getKategorien();
        const gewerke = await getGewerke();
        if (active) setAnzahl(gewerke.items.length + kategorien.length);
      } catch (err) {
        if (active)
          setError(
            err instanceof ApiError
              ? "Katalog konnte nicht geladen werden."
              : "Katalog konnte nicht geladen werden.",
          );
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="mt-2 space-y-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4">
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}

      <p className="text-sm text-[var(--color-muted-foreground)]">
        Legen Sie im Gewerke-Katalog wiederverwendbare Kalkulationseinheiten an (Lohn, Material,
        Fremdleistung). Diese ersetzen die bisherige Preisliste und werden beim Schreiben von
        Angeboten als Vorlage genutzt.
      </p>

      {anzahl !== null && (
        <p className="text-sm">
          <span className="font-medium">{anzahl}</span>{" "}
          {anzahl === 1 ? "Eintrag" : "Einträge"} im Gewerke-Katalog.
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Link href="/gewerke">
          <Button>
            <Boxes size={16} /> Zum Gewerke-Katalog
            <ArrowRight size={16} />
          </Button>
        </Link>
        <Button variant="secondary" onClick={onChanged}>
          Status aktualisieren
        </Button>
      </div>
    </div>
  );
}
