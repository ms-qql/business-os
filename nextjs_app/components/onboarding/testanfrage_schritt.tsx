import * as React from "react";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  starteTestvorgang,
  loescheTestvorgang,
  type OnboardingTestvorgang,
} from "@/lib/api/onboarding";

/**
 * Schritt 7 (Testanfrage). Erzeugt über das echte öffentliche Anfrageformular einen
 * Vorgang mit Testkennzeichen und löscht ihn anschließend spurlos. Der Vorgang ist in
 * der Vorgangsliste als „Test" markiert und aus Auswertungen/Nummernkreisen ausgeschlossen.
 */
export function TestanfrageSchritt({
  testvorgang,
  onChanged,
}: {
  testvorgang: OnboardingTestvorgang | null | undefined;
  onChanged: () => void;
}) {
  const [pending, setPending] = React.useState(false);
  const [deleting, setDeleting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  async function onStart() {
    setPending(true);
    setError(null);
    setInfo(null);
    try {
      const res = await starteTestvorgang();
      onChanged();
      setInfo(
        `Testanfrage erzeugt (Vorgang ${res.vorgang_id}). Die Bestätigungsmail wurde über das Betriebspostfach versendet.`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Testanfrage fehlgeschlagen.");
    } finally {
      setPending(false);
    }
  }

  async function onDelete() {
    if (!testvorgang) return;
    setDeleting(true);
    setError(null);
    setInfo(null);
    try {
      await loescheTestvorgang(testvorgang.vorgang_id);
      onChanged();
      setInfo("Testvorgang und alle zugehörigen Testdaten wurden vollständig gelöscht.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="mt-2 space-y-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4">
      <p className="text-sm text-[var(--color-muted-foreground)]">
        Eine Testanfrage durchläuft den echten öffentlichen Anfrageprozess und erzeugt einen gekennzeichneten
        Testvorgang. Er ist aus Auswertungen und Nummernkreisen ausgeschlossen und jederzeit spurlos löschbar.
      </p>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      {testvorgang ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--color-success)]/40 bg-green-50/40 p-3">
          <div className="text-sm">
            <span className="font-medium text-[var(--color-foreground)]">Testvorgang aktiv</span>
            <span className="ml-2 rounded-full bg-[var(--color-brand)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-brand-foreground)]">
              TEST
            </span>
            <span className="ml-2 text-[var(--color-muted-foreground)]">
              {new Date(testvorgang.erstellt_am).toLocaleString("de-DE")}
            </span>
          </div>
          <Button type="button" variant="danger" size="sm" disabled={deleting} onClick={onDelete}>
            {deleting ? "Wird gelöscht …" : "Testvorgang löschen"}
          </Button>
        </div>
      ) : (
        <Button type="button" variant="outline" disabled={pending} onClick={onStart}>
          {pending ? "Wird erzeugt …" : "Testanfrage starten"}
        </Button>
      )}
    </div>
  );
}
