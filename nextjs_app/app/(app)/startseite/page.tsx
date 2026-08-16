"use client";

import { useAuth } from "@/app/providers";

export default function StartseitePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Startseite</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Willkommen, {user?.name ?? user?.username}.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div className="text-sm text-[var(--color-muted-foreground)]">Betrieb</div>
          <div className="mt-1 text-lg font-semibold">{user?.mandant_name}</div>
        </div>
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div className="text-sm text-[var(--color-muted-foreground)]">Ihre Rolle</div>
          <div className="mt-1 text-lg font-semibold">{user?.rolle}</div>
        </div>
        {user?.rolle === "Monteur" && (
          <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-sm text-[var(--color-muted-foreground)]">Sicht</div>
            <div className="mt-1 text-lg font-semibold">Nur eigene Termine</div>
          </div>
        )}
      </div>
    </div>
  );
}
