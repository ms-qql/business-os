"use client";

import { useAuth } from "@/app/providers";
import { TriageEinstellungen } from "@/components/triage/triage-einstellungen";
import type { Rolle } from "@/lib/theme/tokens";

export default function TriageEinstellungenPage() {
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Triage-Einstellungen</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          {rolle === "Inhaber"
            ? "Leistungsauswahl, Wertklassifikation und Kapazität für die Auto-Triage festlegen."
            : "Die Triage-Konfiguration wird vom Inhaber verwaltet."}
        </p>
      </div>
      {rolle === "Inhaber" ? (
        <TriageEinstellungen />
      ) : (
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Nur der Inhaber darf die Triage-Einstellungen ändern.
        </p>
      )}
    </div>
  );
}
