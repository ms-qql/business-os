"use client";

import * as React from "react";
import { Phone, Mail, MapPin, FileText, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ApiError } from "@/lib/api/client";
import {
  listTermine,
  getTermin,
  type TerminListItem,
  type Termin,
} from "@/lib/api/termine";
import { wochenstart, formatBerlinDateTime, formatBerlinDatum } from "@/lib/zeit";

/** Monteuransicht (AC-5): eigene Termine, Adresse/Kontakt/Anliegen/freigegebene Anhänge,
 *  keine Preis-/Rechnungsdaten, rein lesend. */
export function MonteurAnsicht({ nutzerId }: { nutzerId: string }) {
  const [liste, setListe] = React.useState<TerminListItem[]>([]);
  const [detail, setDetail] = React.useState<Termin | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [ladeDetail, setLadeDetail] = React.useState(false);

  React.useEffect(() => {
    const laden = async () => {
      setError(null);
      try {
        const montag = wochenstart(new Date());
        const sonntag = new Date(montag);
        sonntag.setDate(montag.getDate() + 7);
        const res = await listTermine({
          von: montag.toISOString(),
          bis: sonntag.toISOString(),
          nutzer_ids: [nutzerId],
        });
        setListe(res.items);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Termine konnten nicht geladen werden.");
      }
    };
    void laden();
  }, [nutzerId]);

  async function onTerminKlick(t: TerminListItem) {
    setLadeDetail(true);
    setError(null);
    try {
      // GET /termine/{id} liefert eingebetteten Kontakt (AC-5) — kein zweiter Request.
      const d = await getTermin(t.id);
      setDetail(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Detail konnte nicht geladen werden.");
    } finally {
      setLadeDetail(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-[var(--radius-md)] border border-red-200 bg-red-50 p-3 text-sm text-[var(--color-danger)]">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-[var(--color-muted-foreground)]">
        Ihre Termine der kommenden Woche. Adresse, Kontakt und Anliegen sind sichtbar — Preise
        und Rechnungsdaten sind ausgeblendet.
      </p>
      {liste.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Aktuell sind Ihnen keine Termine zugewiesen.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {liste.map((t) => {
            const abgesagt = Boolean(t.abgesagt_at);
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onTerminKlick(t)}
                className={`rounded-[var(--radius-lg)] border p-3 text-left transition-colors ${
                  abgesagt
                    ? "border-[var(--color-border)] bg-[var(--color-surface-muted)] opacity-60"
                    : "border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-muted)]"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{formatBerlinDatum(t.beginn)}</span>
                  {abgesagt && <Badge variant="neutral">Abgesagt</Badge>}
                </div>
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  {formatBerlinDateTime(t.beginn)} – {formatBerlinDateTime(t.ende)}
                </p>
                <p className="mt-1 font-medium">{t.anliegen}</p>
                {t.adresse && (
                  <p className="flex items-center gap-1 text-xs text-[var(--color-muted-foreground)]">
                    <MapPin size={12} /> {t.adresse}
                  </p>
                )}
              </button>
            );
          })}
        </div>
      )}

      {detail && (
        <Card className="mt-2">
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{detail.anliegen}</h3>
              {Boolean(detail.abgesagt_at) && <Badge variant="neutral">Abgesagt</Badge>}
            </div>
            <p className="text-[var(--color-muted-foreground)]">
              {formatBerlinDateTime(detail.beginn)} – {formatBerlinDateTime(detail.ende)}
            </p>
            {detail.adresse && (
              <p className="flex items-center gap-2">
                <MapPin size={14} className="text-[var(--color-muted-foreground)]" /> {detail.adresse}
              </p>
            )}
            {ladeDetail && (
              <p className="text-[var(--color-muted-foreground)]">Kontakt wird geladen …</p>
            )}
            {detail.kontakt && (
              <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3">
                <p className="mb-1 font-medium">{detail.kontakt.name}</p>
                {detail.kontakt.telefon && (
                  <p className="flex items-center gap-2 text-[var(--color-muted-foreground)]">
                    <Phone size={14} /> {detail.kontakt.telefon}
                  </p>
                )}
                {detail.kontakt.email && (
                  <p className="flex items-center gap-2 text-[var(--color-muted-foreground)]">
                    <Mail size={14} /> {detail.kontakt.email}
                  </p>
                )}
              </div>
            )}
            {detail.notiz && (
              <p className="flex items-start gap-2">
                <FileText size={14} className="mt-0.5 text-[var(--color-muted-foreground)]" />
                <span>{detail.notiz}</span>
              </p>
            )}
            {detail.konflikt && (
              <p className="flex items-center gap-2 text-[var(--color-warning)]">
                <AlertTriangle size={14} /> Hinweis: Überschneidung mit einem weiteren Termin.
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
