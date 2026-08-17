"use client";

import * as React from "react";
import { Send, Paperclip, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  getVorgangEmails,
  sendVorgangEmail,
  emailAnhangDownloadUrl,
  type EmailNachrichtDetail,
  type EmailThread,
  type EmailAnhang,
} from "@/lib/api/email";

function formatDatum(iso: string): string {
  return new Date(iso).toLocaleString("de-DE");
}

function AnhangChip({
  vorgangId,
  email,
  anhang,
}: {
  vorgangId: string;
  email: EmailNachrichtDetail;
  anhang: EmailAnhang;
}) {
  async function onDownload() {
    if (!anhang.verarbeitet) return;
    try {
      const { download_url } = await emailAnhangDownloadUrl(vorgangId, email.id, anhang.id);
      window.open(download_url, "_blank", "noopener,noreferrer");
    } catch {
      /* still download attempt below */
    }
  }

  if (!anhang.verarbeitet) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-muted)] px-2 py-1 text-xs text-[var(--color-muted-foreground)]">
        <AlertTriangle size={12} />
        {anhang.dateiname} — Anhang konnte nicht verarbeitet werden.
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onDownload}
      className="inline-flex items-center gap-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-xs hover:bg-[var(--color-surface-muted)]"
    >
      <Paperclip size={12} />
      {anhang.dateiname}
      <span className="text-[var(--color-muted-foreground)]">
        ({(anhang.groesse_bytes / 1024).toFixed(0)} KB)
      </span>
    </button>
  );
}

function EmailComposer({ vorgangId, onGesendet }: { vorgangId: string; onGesendet: () => void }) {
  const [betreff, setBetreff] = React.useState("");
  const [text, setText] = React.useState("");
  const [sende, setSende] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function onSend(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError("Bitte einen Text eingeben.");
      return;
    }
    setSende(true);
    setError(null);
    try {
      await sendVorgangEmail(vorgangId, { betreff, text });
      setBetreff("");
      setText("");
      onGesendet();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Senden fehlgeschlagen.");
    } finally {
      setSende(false);
    }
  }

  return (
    <form onSubmit={onSend} className="space-y-3">
      <div>
        <Label htmlFor="email-betreff">Betreff</Label>
        <Input
          id="email-betreff"
          value={betreff}
          onChange={(e) => setBetreff(e.target.value)}
          placeholder="Betreff (optional)"
        />
      </div>
      <div>
        <Label htmlFor="email-text">Nachricht</Label>
        <Textarea
          id="email-text"
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="E-Mail an Kunde schreiben …"
        />
      </div>
      {error && <Alert variant="danger">{error}</Alert>}
      <Button type="submit" disabled={sende} size="sm">
        <Send size={16} />
        {sende ? "Wird gesendet …" : "E-Mail senden"}
      </Button>
    </form>
  );
}

/** E-Mail-Verlauf eines Vorgangs inkl. Verfassen/Senden (AC3, nur Büro/Inhaber). */
export function VorgangEmail({ vorgangId, darfSchreiben }: { vorgangId: string; darfSchreiben: boolean }) {
  const [threads, setThreads] = React.useState<EmailThread[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const laden = React.useCallback(async () => {
    setError(null);
    try {
      setThreads(await getVorgangEmails(vorgangId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "E-Mails konnten nicht geladen werden.");
    }
  }, [vorgangId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  return (
    <div className="space-y-4">
      {error && <Alert variant="danger">{error}</Alert>}

      {threads === null ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : threads.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine E-Mail-Kommunikation.</p>
      ) : (
        <ul className="space-y-3">
          {threads.flatMap((thread) => thread.nachrichten).map((mail) => (
            <li
              key={mail.id}
              className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
            >
              <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      mail.richtung === "ausgehend"
                        ? "bg-blue-50 text-[var(--color-brand)]"
                        : "bg-[var(--color-surface-muted)] text-[var(--color-foreground)]"
                    }`}
                  >
                    {mail.richtung === "ausgehend" ? "Gesendet" : "Empfangen"}
                  </span>
                  <span>{mail.betreff || "(ohne Betreff)"}</span>
                </div>
                <span className="text-xs text-[var(--color-muted-foreground)]">{formatDatum(mail.created_at)}</span>
              </div>
              <p className="text-xs text-[var(--color-muted-foreground)]">
                {mail.richtung === "ausgehend" ? `An: ${mail.empfaenger}` : `Von: ${mail.absender}`}
              </p>
              <div className="mt-2 text-sm">
                {mail.text_html ? (
                  // Inhalt serverseitig bereinigt (bleach) — siehe Tech Design.
                  <div dangerouslySetInnerHTML={{ __html: mail.text_html }} />
                ) : (
                  <p className="whitespace-pre-wrap">{mail.text_plain ?? ""}</p>
                )}
              </div>
              {mail.anhaenge.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {mail.anhaenge.map((a) => (
                    <AnhangChip key={a.id} vorgangId={vorgangId} email={mail} anhang={a} />
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {darfSchreiben && (
        <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-4">
          <h4 className="mb-3 text-sm font-semibold">E-Mail schreiben</h4>
          <EmailComposer vorgangId={vorgangId} onGesendet={laden} />
        </div>
      )}
    </div>
  );
}
