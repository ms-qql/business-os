"use client";

import { useAuth } from "@/app/providers";
import { MonteurAnsicht } from "@/components/termine/monteur-ansicht";
import { TerminUebersicht } from "@/components/termine/termin-uebersicht";
import type { Rolle } from "@/lib/theme/tokens";

export default function TerminePage() {
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  if (rolle === "Monteur") {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Meine Termine</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Ihre Einsätze der kommenden Woche.
          </p>
        </div>
        <MonteurAnsicht nutzerId={user!.user_id} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Termine</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Teamkalender: Termine planen, Monteuren zuweisen und Überschneidungen erkennen.
        </p>
      </div>
      <TerminUebersicht />
    </div>
  );
}
