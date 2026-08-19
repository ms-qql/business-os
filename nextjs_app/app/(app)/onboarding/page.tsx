"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/providers";
import { getToken } from "@/lib/session";
import { ApiError } from "@/lib/api/client";
import { getOnboarding, type OnboardingStatus } from "@/lib/api/onboarding";
import { OnboardingFortschritt } from "@/components/onboarding/onboarding_fortschritt";
import { Alert } from "@/components/ui/label";
import { Rolle } from "@/lib/theme/tokens";

/**
 * Onboarding-Übersichtsseite. Inhaber-only (Tech Design: Betreiber und Inhaber sehen
 * dieselbe Checkliste; Büro/Monteur erhalten eine Zugriffsverweigerung). Der Server
 * erzwingt das zusätzlich; dieser Guard ist die komfortable Client-seitige Abweisung.
 */
export default function OnboardingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [status, setStatus] = React.useState<OnboardingStatus | null>(null);
  const [loadError, setLoadError] = React.useState<string | null>(null);

  const rolle = (user?.rolle ?? "Büro") as Rolle;
  const darf = rolle === "Inhaber";

  const laden = React.useCallback(async () => {
    setLoadError(null);
    try {
      setStatus(await getOnboarding());
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setLoadError("Zugriff verweigert. Das begleitete Onboarding ist nur für den Inhaber verfügbar.");
      } else {
        setLoadError(err instanceof ApiError ? err.message : "Onboarding-Status konnte nicht geladen werden.");
      }
    }
  }, []);

  React.useEffect(() => {
    if (loading) return;
    if (!getToken() || !user) {
      router.replace("/login");
      return;
    }
    if (!darf) {
      setLoadError("Zugriff verweigert. Das begleitete Onboarding ist nur für den Inhaber verfügbar.");
      return;
    }
    void laden();
  }, [loading, user, darf, router, laden]);

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  if (!darf) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Begleitetes Onboarding</h1>
        <Alert variant="danger">
          Zugriff verweigert. Das begleitete Onboarding und die Postfach-Zugangsdaten sind nur für den
          Inhaber verfügbar. Büro und Monteur haben keinen Zugriff auf diesen Bereich.
        </Alert>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Begleitetes Onboarding</h1>
        <Alert variant="danger">{loadError}</Alert>
      </div>
    );
  }

  if (!status) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Begleitetes Onboarding</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Machen Sie Ihren Betrieb startklar. Der Fortschritt wird aus Ihren gespeicherten Einrichtungsdaten
          berechnet — ein Schritt ist erst erledigt, wenn alle zugehörigen Angaben vorliegen.
        </p>
      </div>

      <OnboardingFortschritt status={status} onChanged={laden} />
    </div>
  );
}
