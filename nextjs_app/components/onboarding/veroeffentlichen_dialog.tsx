import * as React from "react";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { Dialog } from "@/components/ui/dialog";
import { ApiError } from "@/lib/api/client";
import { veroeffentlichen, type OnboardingSchritt, type OnboardingStatus } from "@/lib/api/onboarding";

/**
 * Veröffentlichen-Knopf + Bestätigungsdialog. Erst aktiv, wenn alle Pflichtschritte
 * (1–5 und 7) erledigt sind. Nennt andernfalls die noch offenen Schritte. Die
 * serverseitige Prüfung in POST /onboarding/veroeffentlichen ist die alleinige
 * Wahrheit (Tech Design ADR-7-2) — der Button-Zustand ist nur komfortable Vorab-Anzeige.
 */
export function VeroeffentlichenDialog({
  status,
  onVeroeffentlicht,
}: {
  status: OnboardingStatus;
  onVeroeffentlicht: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const offenePflicht = status.schritte.filter((s) => s.pflicht && s.status !== "erledigt");
  const darf = offenePflicht.length === 0;

  async function onBestaetigen() {
    setPending(true);
    setError(null);
    try {
      await veroeffentlichen();
      setOpen(false);
      onVeroeffentlicht();
    } catch (err) {
      // 409 mit konkreten Schritten → serverseitig abgelehnt (z. B. SMTP zwischenzeitlich ausgefallen).
      setError(err instanceof ApiError ? err.message : "Veröffentlichung fehlgeschlagen.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button
        type="button"
        disabled={!darf || status.veroeffentlicht}
        onClick={() => setOpen(true)}
      >
        {status.veroeffentlicht ? "Bereits veröffentlicht" : "Website veröffentlichen"}
      </Button>

      {!darf && (
        <p className="text-sm text-[var(--color-warning)]" role="status">
          Noch offen: {offenePflicht.map((s: OnboardingSchritt) => s.titel).join(", ")}
        </p>
      )}

      <Dialog
        open={open}
        onOpenChange={setOpen}
        title="Website veröffentlichen?"
        description="Die reservierte Domain wird aktiv geschaltet und die öffentliche Website damit live geschaltet."
      >
        {error && <Alert variant="danger">{error}</Alert>}
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Alle Pflichtschritte sind erfüllt. Nach der Veröffentlichung bleibt die Website online, auch wenn
          später ein Pflichtschritt nachträglich unvollständig wird — es erscheint dann ein Hinweis im Status.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            Abbrechen
          </Button>
          <Button type="button" disabled={pending} onClick={onBestaetigen}>
            {pending ? "Wird veröffentlicht …" : "Jetzt veröffentlichen"}
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
