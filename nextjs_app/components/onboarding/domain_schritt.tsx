import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { setOnboardingDomain } from "@/lib/api/onboarding";
import { getWebsiteSettings } from "@/lib/api/website-settings";

/**
 * Schritt 4 (Domain). Reservieren der Domain mit Status inaktiv — ausschließlich
 * über PUT /onboarding/domain. Das Feld `domain` wurde aus PATCH /website-settings
 * entfernt (Tech Design ADR-7-2); die bisherige Website-Einstellungen-Seite zeigt
 * die zugeordnete Domain nur noch lesend. Der Hostname selbst wird hier aus
 * GET /website-settings gelesen (der Onboarding-Vertrag liefert nur domain_status).
 */
export function DomainSchritt({
  domainStatus,
  onReserviert,
}: {
  domainStatus: string | null | undefined;
  onReserviert: () => void;
}) {
  const [hostname, setHostname] = React.useState<string | null>(null);
  const [wert, setWert] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getWebsiteSettings()
      .then((s) => setHostname(s.domain))
      .catch(() => setHostname(null));
  }, []);

  const bereitsReserviert = !!hostname;
  const istAktiv = domainStatus === "aktiv" || hostname !== null;

  async function onReservieren(e: React.FormEvent) {
    e.preventDefault();
    const host = wert.trim().toLowerCase();
    if (!host) {
      setError("Bitte geben Sie eine Domain ein.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await setOnboardingDomain(host);
      setWert("");
      setHostname(host);
      onReserviert();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Domain konnte nicht reserviert werden.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4">
      {bereitsReserviert ? (
        <div className="space-y-2 text-sm">
          <p>
            Reservierte Domain:{" "}
            <span className="font-medium text-[var(--color-foreground)]">{hostname}</span>
          </p>
          <p className="text-[var(--color-muted-foreground)]">
            Status: {istAktiv ? "veröffentlicht (live)" : "reserviert, noch nicht veröffentlicht"}.
            Die Zuordnung wird erst mit dem Veröffentlichen-Schritt aktiv.
          </p>
        </div>
      ) : (
        <form onSubmit={onReservieren} className="space-y-3">
          <div>
            <Label htmlFor="onb-domain">Domain reservieren</Label>
            <Input
              id="onb-domain"
              value={wert}
              onChange={(e) => setWert(e.target.value)}
              placeholder="beispiel.de"
              aria-describedby="onb-domain-hint"
            />
            <p id="onb-domain-hint" className="mt-1 text-xs text-[var(--color-muted-foreground)]">
              DNS muss extern auf diesen Server zeigen. Die Domain ist nach der Reservierung noch
              nicht live — die Veröffentlichung erfolgt erst über den abschließenden Knopf.
            </p>
          </div>
          {error && <Alert variant="danger">{error}</Alert>}
          <Button type="submit" disabled={saving}>
            {saving ? "Wird reserviert …" : "Domain reservieren"}
          </Button>
        </form>
      )}
    </div>
  );
}
