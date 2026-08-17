"use client";

import { useAuth } from "@/app/providers";
import { KundenTabelle } from "@/components/kunden/kunden-tabelle";
import type { Rolle } from "@/lib/theme/tokens";

export default function KundenPage() {
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Kunden</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Kunden suchen, anlegen und bearbeiten.
        </p>
      </div>
      <KundenTabelle rolle={rolle} />
    </div>
  );
}
