"use client";

import * as React from "react";
import { AlertTriangle } from "lucide-react";
import { getEmailKonto } from "@/lib/api/email";

/**
 * Banner, das bei gestörtem Postfachabruf sichtbar wird (AC5).
 * Lädt den Verbindungsstatus selbstständig — wiederverwendbar in
 * Vorgangsdetail und Inbox.
 */
export function PostfachWarnung() {
  const [fehler, setFehler] = React.useState<string | null>(null);
  const [offen, setOffen] = React.useState(false);

  React.useEffect(() => {
    let aktiv = true;
    getEmailKonto()
      .then((konto) => {
        if (!aktiv) return;
        if (konto?.letzter_abruf_status === "fehler") {
          setFehler(konto.letzter_abruf_fehler_text ?? null);
          setOffen(true);
        } else {
          setOffen(false);
        }
      })
      .catch(() => {
        if (aktiv) setOffen(false);
      });
    return () => {
      aktiv = false;
    };
  }, []);

  if (!offen) return null;

  return (
    <div
      role="alert"
      className="mb-4 flex items-start gap-2 rounded-[var(--radius-md)] border border-amber-200 bg-amber-50 p-3 text-sm text-[var(--color-warning)]"
    >
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <span>
        <strong>E-Mail-Abruf fehlgeschlagen. Bitte Verbindung prüfen.</strong>
        {fehler && <span className="mt-1 block text-xs opacity-90">{fehler}</span>}
      </span>
    </div>
  );
}
