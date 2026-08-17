"use client";

import * as React from "react";
import Link from "next/link";
import { Paperclip, AlertTriangle, Link2, FilePlus2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  getInbox,
  getEmailNachricht,
  nachrichtZuordnen,
  nachrichtNeuerVorgang,
  emailAnhangDownloadUrl,
  type EmailNachrichtDetail,
  type EmailInboxItem,
} from "@/lib/api/email";
import { listVorgaenge, type VorgangListItem } from "@/lib/api/vorgaenge";
import { PostfachWarnung } from "@/components/email/postfach-warnung";

function formatDatum(iso: string): string {
  return new Date(iso).toLocaleString("de-DE");
}

function NachrichtDetail({
  nachricht,
  onVerarbeitet,
}: {
  nachricht: EmailNachrichtDetail;
  onVerarbeitet: () => void;
}) {
  const [vorgaenge, setVorgaenge] = React.useState<VorgangListItem[]>([]);
  const [vorgangId, setVorgangId] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    listVorgaenge({ limit: 200 })
      .then((r) => setVorgaenge(r.items))
      .catch(() => setVorgaenge([]));
  }, []);

  async function onDownload(anhangId: string) {
    try {
      if (!nachricht.vorgang_id) return;
      const { download_url } = await emailAnhangDownloadUrl(nachricht.vorgang_id, nachricht.id, anhangId);
      window.open(download_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Download fehlgeschlagen.");
    }
  }

  async function onZuordnen() {
    if (!vorgangId) return;
    setBusy(true);
    setError(null);
    try {
      await nachrichtZuordnen(nachricht.id, vorgangId);
      onVerarbeitet();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Zuordnung fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  async function onNeuerVorgang() {
    setBusy(true);
    setError(null);
    try {
      await nachrichtNeuerVorgang(nachricht.id, { anliegen: nachricht.betreff || "(ohne Betreff)" });
      onVerarbeitet();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Anlegen fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  const zugeordnet = Boolean(nachricht.vorgang_id);

  return (
    <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <h3 className="font-semibold">{nachricht.betreff || "(ohne Betreff)"}</h3>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
        Von: {nachricht.absender} · An: {nachricht.empfaenger} · {formatDatum(nachricht.created_at)}
      </p>

      <div className="mt-3 text-sm">
        {nachricht.text_html ? (
          <div dangerouslySetInnerHTML={{ __html: nachricht.text_html }} />
        ) : (
          <p className="whitespace-pre-wrap">{nachricht.text_plain ?? ""}</p>
        )}
      </div>

      {nachricht.anhaenge.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {nachricht.anhaenge.map((a) =>
            a.verarbeitet && nachricht.vorgang_id ? (
              <button
                key={a.id}
                type="button"
                onClick={() => onDownload(a.id)}
                className="inline-flex items-center gap-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-xs hover:bg-[var(--color-surface-muted)]"
              >
                <Paperclip size={12} />
                {a.dateiname} ({(a.groesse_bytes / 1024).toFixed(0)} KB)
              </button>
            ) : (
              <span
                key={a.id}
                className="inline-flex items-center gap-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-muted)] px-2 py-1 text-xs text-[var(--color-muted-foreground)]"
              >
                <AlertTriangle size={12} />
                {a.dateiname} — Anhang konnte nicht verarbeitet werden.
              </span>
            ),
          )}
        </div>
      )}

      {error && <Alert variant="danger" className="mt-3">{error}</Alert>}

      {zugeordnet ? (
        <p className="mt-3 text-sm">
          Zugeordnet zu Vorgang{" "}
          <Link href={`/vorgaenge/${nachricht.vorgang_id}`} className="text-[var(--color-brand)] hover:underline">
            {nachricht.vorgang_id}
          </Link>
        </p>
      ) : (
        <div className="mt-4 space-y-3 border-t border-[var(--color-border)] pt-3">
          <p className="text-sm font-medium">Noch keinem Vorgang zugeordnet</p>
          <div className="flex flex-wrap items-end gap-2">
            <div className="flex-1">
              <Label htmlFor="vorgang-wahl">Vorhandenem Vorgang zuordnen</Label>
              <Select id="vorgang-wahl" value={vorgangId} onChange={(e) => setVorgangId(e.target.value)} className="w-full">
                <option value="">— Vorgang wählen —</option>
                {vorgaenge.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.anliegen} ({v.kunde_name})
                  </option>
                ))}
              </Select>
            </div>
            <Button size="sm" disabled={busy || !vorgangId} onClick={onZuordnen}>
              <Link2 size={16} />
              Zuordnen
            </Button>
          </div>
          <Button size="sm" variant="outline" disabled={busy} onClick={onNeuerVorgang}>
            <FilePlus2 size={16} />
            Neuen Vorgang aus Nachricht anlegen
          </Button>
        </div>
      )}
    </div>
  );
}

export function EmailInbox() {
  const [filter, setFilter] = React.useState<"offen" | "zugeordnet">("offen");
  const [items, setItems] = React.useState<EmailInboxItem[]>([]);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [detail, setDetail] = React.useState<EmailNachrichtDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getInbox({ zugeordnet: filter === "zugeordnet" });
      setItems(res.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Inbox konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onSelect(id: string) {
    setSelectedId(id);
    setDetail(null);
    try {
      setDetail(await getEmailNachricht(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Nachricht konnte nicht geladen werden.");
    }
  }

  async function onVerarbeitet() {
    setSelectedId(null);
    setDetail(null);
    await laden();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">E-Mail-Postfach</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Eingehende E-Mails, die noch keinem Vorgang zugeordnet sind.
        </p>
      </div>

      <PostfachWarnung />

      {error && <Alert variant="danger">{error}</Alert>}

      <div className="flex gap-2">
        <Button
          size="sm"
          variant={filter === "offen" ? "primary" : "outline"}
          onClick={() => setFilter("offen")}
        >
          Nicht zugeordnet
        </Button>
        <Button
          size="sm"
          variant={filter === "zugeordnet" ? "primary" : "outline"}
          onClick={() => setFilter("zugeordnet")}
        >
          Zugeordnet
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Keine Nachrichten in dieser Ansicht.</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <ul className="divide-y divide-[var(--color-border)] rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)]">
            {items.map((n) => (
              <li key={n.thread_id}>
                <button
                  type="button"
                  onClick={() => onSelect(n.letzte_nachricht_id)}
                  className={`w-full px-4 py-3 text-left hover:bg-[var(--color-surface-muted)] ${
                    selectedId === n.letzte_nachricht_id ? "bg-[var(--color-surface-muted)]" : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium">{n.betreff || "(ohne Betreff)"}</span>
                    <span className="shrink-0 text-xs text-[var(--color-muted-foreground)]">
                      {n.letzte_nachricht_am ? formatDatum(n.letzte_nachricht_am) : ""}
                    </span>
                  </div>
                  <p className="truncate text-xs text-[var(--color-muted-foreground)]">{n.absender}</p>
                </button>
              </li>
            ))}
          </ul>

          <div>
            {detail ? (
              <NachrichtDetail nachricht={detail} onVerarbeitet={onVerarbeitet} />
            ) : (
              <p className="text-sm text-[var(--color-muted-foreground)]">Nachricht auswählen, um Details zu sehen.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
