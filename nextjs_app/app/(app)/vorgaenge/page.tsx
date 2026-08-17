"use client";

import { useAuth } from "@/app/providers";
import { VorgaengeTabelle } from "@/components/vorgaenge/vorgaenge-tabelle";
import type { Rolle } from "@/lib/theme/tokens";

export default function VorgaengePage() {
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Vorgänge</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          {rolle === "Monteur"
            ? "Ihr zugewiesener Vorgang."
            : "Vorgänge suchen, nach Status filtern und bearbeiten."}
        </p>
      </div>
      <VorgaengeTabelle rolle={rolle} />
    </div>
  );
}
