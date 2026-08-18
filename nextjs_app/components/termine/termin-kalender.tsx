"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import type { TerminListItem, TerminMonteur } from "@/lib/api/termine";
import {
  wochenstart,
  wochenTage,
  formatBerlin,
  formatBerlinZeit,
  formatBerlinDatum,
} from "@/lib/zeit";

const WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
const START_STUNDE = 6;
const END_STUNDE = 20;
const STUNDEN = Array.from({ length: END_STUNDE - START_STUNDE + 1 }, (_, i) => START_STUNDE + i);

export interface TerminKalenderProps {
  termine: TerminListItem[];
  ansicht: "woche" | "tag";
  onAnsichtWechsel: (a: "woche" | "tag") => void;
  aufWoche: Date; // Montag der aktuell angezeigten Woche
  onWocheWechsel: (montag: Date) => void;
  darfSchreiben: boolean;
  onTerminKlick: (t: TerminListItem) => void;
  onTerminNeu: (datum?: Date) => void;
  /** Auswählbare Monteure (bei >3); null = alle anzeigen. */
  monteurFilter: string[];
  onMonteurFilter: (ids: string[]) => void;
  alleMonteure: TerminMonteur[];
  konfliktMonteure: string[];
}

function minuteOf(d: Date): number {
  return d.getHours() * 60 + d.getMinutes();
}

export function TerminKalender({
  termine,
  ansicht,
  onAnsichtWechsel,
  aufWoche,
  onWocheWechsel,
  darfSchreiben,
  onTerminKlick,
  onTerminNeu,
  monteurFilter,
  onMonteurFilter,
  alleMonteure,
  konfliktMonteure,
}: TerminKalenderProps) {
  const tage = wochenTage(aufWoche);

  const zeigeTage =
    ansicht === "tag"
      ? [aufWoche, tage[1 % 7], tage[2 % 7], tage[3 % 7], tage[4 % 7], tage[5 % 7], tage[6 % 7]].slice(0, 1)
      : tage;
  // Tagesansicht: nur der Montag selbst als Referenz, aber wir zeigen den ausgewählten Tag.
  const tagesTag = ansicht === "tag" ? aufWoche : null;

  const termineGefiltert = React.useMemo(() => {
    if (monteurFilter.length === 0) return termine;
    return termine.filter((t) =>
      t.monteure.some((m) => monteurFilter.includes(m.nutzer_id)),
    );
  }, [termine, monteurFilter]);

  function vorigeWoche() {
    const d = new Date(aufWoche);
    d.setDate(d.getDate() - 7);
    onWocheWechsel(d);
  }
  function naechsteWoche() {
    const d = new Date(aufWoche);
    d.setDate(d.getDate() + 7);
    onWocheWechsel(d);
  }
  function heuteWoche() {
    onWocheWechsel(wochenstart(new Date()));
  }

  const konfliktNamen = React.useMemo(() => {
    const map = new Map(alleMonteure.map((m) => [m.nutzer_id, m.name]));
    return konfliktMonteure.map((id) => map.get(id) ?? id);
  }, [alleMonteure, konfliktMonteure]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={vorigeWoche} aria-label="Vorige Woche">
            <ChevronLeft size={16} />
          </Button>
          <Button variant="outline" size="sm" onClick={heuteWoche}>
            Heute
          </Button>
          <Button variant="outline" size="sm" onClick={naechsteWoche} aria-label="Nächste Woche">
            <ChevronRight size={16} />
          </Button>
          <span className="ml-2 text-sm font-medium">
            {formatBerlinDatum(aufWoche.toISOString())} – {formatBerlinDatum(tage[6].toISOString())}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-[var(--radius-md)] border border-[var(--color-border)] p-0.5">
            <button
              type="button"
              onClick={() => onAnsichtWechsel("woche")}
              className={`rounded px-3 py-1 text-sm ${
                ansicht === "woche"
                  ? "bg-[var(--color-brand)] text-[var(--color-brand-foreground)]"
                  : "text-[var(--color-muted-foreground)]"
              }`}
            >
              Woche
            </button>
            <button
              type="button"
              onClick={() => onAnsichtWechsel("tag")}
              className={`rounded px-3 py-1 text-sm ${
                ansicht === "tag"
                  ? "bg-[var(--color-brand)] text-[var(--color-brand-foreground)]"
                  : "text-[var(--color-muted-foreground)]"
              }`}
            >
              Tag
            </button>
          </div>
          {darfSchreiben && (
            <Button size="sm" onClick={() => onTerminNeu(tagesTag ?? undefined)}>
              + Termin
            </Button>
          )}
        </div>
      </div>

      {konfliktNamen.length > 0 && (
        <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-[var(--color-warning)]">
          <AlertTriangle size={16} />
          Überschneidung bei: {konfliktNamen.join(", ")}
        </div>
      )}

      {alleMonteure.length > 3 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-[var(--color-muted-foreground)]">Angezeigte Monteure:</span>
          {alleMonteure.map((m) => {
            const aktiv = monteurFilter.includes(m.nutzer_id);
            return (
              <button
                key={m.nutzer_id}
                type="button"
                onClick={() => {
                  const next = aktiv
                    ? monteurFilter.filter((x) => x !== m.nutzer_id)
                    : [...monteurFilter, m.nutzer_id];
                  onMonteurFilter(next);
                }}
                className={`rounded-full px-3 py-1 text-xs transition-colors ${
                  aktiv || monteurFilter.length === 0
                    ? "bg-[var(--color-brand)] text-[var(--color-brand-foreground)]"
                    : "bg-[var(--color-surface-muted)] text-[var(--color-foreground)]"
                }`}
              >
                {m.name}
              </button>
            );
          })}
        </div>
      )}

      {ansicht === "woche" ? (
        <WochenRaster
          tage={tage}
          termine={termineGefiltert}
          onTerminKlick={onTerminKlick}
          darfSchreiben={darfSchreiben}
        />
      ) : (
        <TagesRaster
          tag={aufWoche}
          termine={termineGefiltert}
          onTerminKlick={onTerminKlick}
          darfSchreiben={darfSchreiben}
          onTerminNeu={onTerminNeu}
        />
      )}
    </div>
  );
}

function WochenRaster({
  tage,
  termine,
  onTerminKlick,
  darfSchreiben,
}: {
  tage: Date[];
  termine: TerminListItem[];
  onTerminKlick: (t: TerminListItem) => void;
  darfSchreiben: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="grid min-w-[760px] grid-cols-7">
        {WOCHENTAGE.map((tag, i) => (
          <div
            key={tag}
            className="border-b border-r border-[var(--color-border)] px-2 py-2 text-center text-sm font-medium last:border-r-0"
          >
            {tag}
            <div className="text-xs text-[var(--color-muted-foreground)]">
              {formatBerlin(tage[i].toISOString(), { day: "2-digit", month: "2-digit" })}
            </div>
          </div>
        ))}
        {tage.map((tag, ti) => {
          const tagStart = new Date(tag);
          tagStart.setHours(0, 0, 0, 0);
          const tagEnde = new Date(tag);
          tagEnde.setHours(23, 59, 59, 999);
          const tagTermine = termine.filter((t) => {
            const b = new Date(t.beginn);
            return b >= tagStart && b <= tagEnde;
          });
          return (
            <div
              key={ti}
              className="min-h-[320px] border-r border-[var(--color-border)] p-1 last:border-r-0"
            >
              {tagTermine.length === 0 ? (
                <p className="px-1 pt-2 text-xs text-[var(--color-muted-foreground)]">—</p>
              ) : (
                tagTermine.map((t) => (
                  <TerminBlock
                    key={t.id}
                    termin={t}
                    onClick={() => onTerminKlick(t)}
                    kompakt
                  />
                ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TagesRaster({
  tag,
  termine,
  onTerminKlick,
  darfSchreiben,
  onTerminNeu,
}: {
  tag: Date;
  termine: TerminListItem[];
  onTerminKlick: (t: TerminListItem) => void;
  darfSchreiben: boolean;
  onTerminNeu: (datum?: Date) => void;
}) {
  const tagStart = new Date(tag);
  tagStart.setHours(0, 0, 0, 0);
  const tagEnde = new Date(tag);
  tagEnde.setHours(23, 59, 59, 999);
  const tagTermine = termine
    .filter((t) => {
      const b = new Date(t.beginn);
      return b >= tagStart && b <= tagEnde;
    })
    .sort((a, b) => new Date(a.beginn).getTime() - new Date(b.beginn).getTime());

  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{formatBerlinDatum(tag.toISOString())}</h3>
        {darfSchreiben && (
          <Button size="sm" onClick={() => onTerminNeu(tag)}>
            + Termin
          </Button>
        )}
      </div>
      {tagTermine.length === 0 ? (
        <p className="py-8 text-center text-sm text-[var(--color-muted-foreground)]">
          Keine Termine an diesem Tag.
        </p>
      ) : (
        <div className="space-y-2">
          {tagTermine.map((t) => (
            <TerminBlock key={t.id} termin={t} onClick={() => onTerminKlick(t)} />
          ))}
        </div>
      )}
    </div>
  );
}

function TerminBlock({
  termin,
  onClick,
  kompakt,
}: {
  termin: TerminListItem;
  onClick: () => void;
  kompakt?: boolean;
}) {
  const abgesagt = Boolean(termin.abgesagt_at);
  const konflikt = termin.konflikt;
  const beginn = new Date(termin.beginn);
  const ende = new Date(termin.ende);

  const basis =
    "mb-1 cursor-pointer rounded-[var(--radius-md)] border p-2 text-left text-sm transition-colors";
  const rahmen = abgesagt
    ? "border-[var(--color-border)] bg-[var(--color-surface-muted)] opacity-60 line-through"
    : konflikt
      ? "border-red-300 bg-red-50 hover:bg-red-100"
      : "border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-muted)]";

  return (
    <button type="button" onClick={onClick} className={`${basis} ${rahmen} w-full`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">
          {formatBerlinZeit(termin.beginn)}–{formatBerlinZeit(termin.ende)}
        </span>
        {konflikt && !abgesagt && (
          <Badge variant="danger" className="shrink-0">
            Konflikt
          </Badge>
        )}
        {abgesagt && (
          <Badge variant="neutral" className="shrink-0">
            Abgesagt
          </Badge>
        )}
      </div>
      {!kompakt && (
        <p className="mt-1 text-[var(--color-foreground)]">{termin.anliegen}</p>
      )}
      {termin.adresse && (
        <p className="truncate text-xs text-[var(--color-muted-foreground)]">{termin.adresse}</p>
      )}
      {!kompakt && termin.monteure.length > 0 && (
        <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
          {termin.monteure.map((m) => m.name).join(", ")}
        </p>
      )}
    </button>
  );
}
