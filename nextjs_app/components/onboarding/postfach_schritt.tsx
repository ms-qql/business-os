import * as React from "react";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  startPostfachTest,
  type OnboardingPostfachTest,
} from "@/lib/api/onboarding";
import { getEmailKonto, type EmailKonto } from "@/lib/api/email";

/**
 * Schritt 5 (Betriebspostfach). Startet den gespeicherten Empfangs- und Versandtest
 * ohne Zugangsdaten erneut anzuzeigen (Tech Design Abschnitt B/D). Erfolg gilt nur,
 * wenn IMAP UND SMTP im selben Lauf erfolgreich waren; ein Teilerfolg bleibt
 * "In Bearbeitung" mit Nennung des fehlgeschlagenen Teils (Acceptance-Kriterium).
 */
export function PostfachSchritt({
  postfachTest,
  onGetestet,
}: {
  postfachTest: OnboardingPostfachTest | null | undefined;
  onGetestet: () => void;
}) {
  const [konto, setKonto] = React.useState<EmailKonto | null>(null);
  const [testing, setTesting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<{ imap_ok: boolean; smtp_ok: boolean; detail: string } | null>(null);

  React.useEffect(() => {
    getEmailKonto()
      .then(setKonto)
      .catch(() => setKonto(null));
  }, []);

  async function onTest() {
    setTesting(true);
    setError(null);
    setResult(null);
    try {
      const res = await startPostfachTest();
      setResult(res);
      if (res.imap_ok && res.smtp_ok) onGetestet();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Verbindungstest fehlgeschlagen.");
    } finally {
      setTesting(false);
    }
  }

  // Anzeige: Serveradresse, Port, Benutzername und Zeitpunkt/Ergebnis des letzten Tests.
  // Niemals Passwörter im Klartext (Tech Design Security-Anforderung).
  return (
    <div className="mt-2 space-y-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4">
      {konto ? (
        <dl className="grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
          <div className="flex justify-between gap-2">
            <dt className="text-[var(--color-muted-foreground)]">IMAP</dt>
            <dd className="font-medium">
              {konto.imap_host}:{konto.imap_port} · {konto.imap_user}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-[var(--color-muted-foreground)]">SMTP</dt>
            <dd className="font-medium">
              {konto.smtp_host}:{konto.smtp_port} · {konto.smtp_user}
            </dd>
          </div>
          <div className="flex justify-between gap-2 sm:col-span-2">
            <dt className="text-[var(--color-muted-foreground)]">Letzter Test</dt>
            <dd className="font-medium">
              {postfachTest?.tested_at
                ? new Date(postfachTest.tested_at).toLocaleString("de-DE")
                : "kein Test"}
              {postfachTest && (
                <span
                  className={
                    postfachTest.imap_ok && postfachTest.smtp_ok
                      ? " ml-2 text-[var(--color-success)]"
                      : " ml-2 text-[var(--color-warning)]"
                  }
                >
                  ({postfachTest.imap_ok ? "IMAP OK" : "IMAP offen"},{" "}
                  {postfachTest.smtp_ok ? "SMTP OK" : "SMTP offen"})
                </span>
              )}
            </dd>
          </div>
        </dl>
      ) : (
        <Alert variant="warning">
          Es ist noch kein Betriebspostfach gespeichert. Richten Sie es unter „Postfach-Einstellungen“
          ein, bevor Sie den Verbindungstest starten können.
        </Alert>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

      {result && !result.imap_ok && (
        <Alert variant="warning">IMAP-Empfangstest fehlgeschlagen: {result.detail}</Alert>
      )}
      {result && result.imap_ok && !result.smtp_ok && (
        <Alert variant="warning">SMTP-Versandtest fehlgeschlagen: {result.detail}</Alert>
      )}
      {result && result.imap_ok && result.smtp_ok && (
        <Alert variant="success">Verbindungstest erfolgreich (Empfang und Versand).</Alert>
      )}

      <Button type="button" variant="outline" disabled={testing || !konto} onClick={onTest}>
        {testing ? "Testet …" : "Verbindung testen"}
      </Button>
    </div>
  );
}
