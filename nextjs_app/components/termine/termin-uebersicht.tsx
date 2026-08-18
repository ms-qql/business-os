"use client";

import * as React from "react";
import { CalendarDays } from "lucide-react";
import { TerminKalender } from "@/components/termine/termin-kalender";
import { TerminDialog } from "@/components/termine/termin-dialog";
import { TerminAbsagenDialog } from "@/components/termine/termin-absagen-dialog";
import { Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { listTermine, getTermin, type TerminListItem, type TerminMonteur } from "@/lib/api/termine";
import { wochenstart } from "@/lib/zeit";

/** Büro/Inhaber-Kalenderansicht: Woche/Tag, max. 3 Monteure, Konfliktwarnung rot. */
export function TerminUebersicht() {
  const [termine, setTermine] = React.useState<TerminListItem[]>([]);
  const [konfliktMonteure, setKonfliktMonteure] = React.useState<string[]>([]);
  const [alleMonteure, setAlleMonteure] = React.useState<TerminMonteur[]>([]);
  const [aufWoche, setAufWoche] = React.useState<Date>(wochenstart(new Date()));
  const [ansicht, setAnsicht] = React.useState<"woche" | "tag">("woche");
  const [monteurFilter, setMonteurFilter] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [laden, setLaden] = React.useState(true);

  const [dialogOffen, setDialogOffen] = React.useState(false);
  const [bearbeitenTermin, setBearbeitenTermin] = React.useState<TerminListItem | null>(null);
  const [neuDatum, setNeuDatum] = React.useState<Date | undefined>(undefined);
  const [absagenTermin, setAbsagenTermin] = React.useState<TerminListItem | null>(null);

  const ladenTermine = React.useCallback(async (montag: Date) => {
    setLaden(true);
    setError(null);
    try {
      const sonntag = new Date(montag);
      sonntag.setDate(montag.getDate() + 7);
      const res = await listTermine({
        von: montag.toISOString(),
        bis: sonntag.toISOString(),
        nutzer_ids: monteurFilter.length > 0 ? monteurFilter : undefined,
      });
      setTermine(res.items);
      setKonfliktMonteure(res.konflikt_monteure ?? []);
      // Monteure aus den geladenen Terminen aggregieren (für Auswahl bei >3).
      const map = new Map<string, TerminMonteur>();
      for (const t of res.items) {
        for (const m of t.monteure) {
          map.set(m.nutzer_id, m);
        }
      }
      setAlleMonteure(Array.from(map.values()));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Termine konnten nicht geladen werden.");
    } finally {
      setLaden(false);
    }
  }, [monteurFilter]);

  React.useEffect(() => {
    void ladenTermine(aufWoche);
  }, [ladenTermine, aufWoche]);

  function onTerminKlick(t: TerminListItem) {
    setBearbeitenTermin(t);
    setNeuDatum(undefined);
    setDialogOffen(true);
  }

  function onTerminNeu(datum?: Date) {
    setBearbeitenTermin(null);
    setNeuDatum(datum);
    setDialogOffen(true);
  }

  function onTerminAbsagenKlick(t: TerminListItem) {
    setAbsagenTermin(t);
  }

  return (
    <div className="space-y-3">
      {error && <Alert variant="danger">{error}</Alert>}

      {laden && termine.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : (
        <TerminKalender
          termine={termine}
          ansicht={ansicht}
          onAnsichtWechsel={setAnsicht}
          aufWoche={aufWoche}
          onWocheWechsel={setAufWoche}
          darfSchreiben
          onTerminKlick={onTerminKlick}
          onTerminNeu={onTerminNeu}
          monteurFilter={monteurFilter}
          onMonteurFilter={setMonteurFilter}
          alleMonteure={alleMonteure}
          konfliktMonteure={konfliktMonteure}
        />
      )}

      <TerminDialog
        open={dialogOffen}
        onOpenChange={setDialogOffen}
        onSaved={() => {
          setDialogOffen(false);
          void ladenTermine(aufWoche);
        }}
        termin={bearbeitenTermin}
      />

      <TerminAbsagenDialog
        termin={absagenTermin}
        open={Boolean(absagenTermin)}
        onOpenChange={(o) => !o && setAbsagenTermin(null)}
        onAbsagt={() => void ladenTermine(aufWoche)}
      />
    </div>
  );
}
