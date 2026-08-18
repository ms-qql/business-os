/**
 * Zeit-Helfer für PROJ-6 (Terminplanung).
 * Alle Termine werden einheitlich in der Zeitzone Europa/Berlin interpretiert
 * und gespeichert (siehe Tech Design, AC-7). Vergleiche für Konflikte laufen
 * stets in derselben Zeitzone.
 */

const TZ = "Europe/Berlin";

/** Formatiert einen ISO-Zeitstempel (UTC oder mit Offset) als Europa/Berlin-String. */
export function formatBerlin(zeit: string, options: Intl.DateTimeFormatOptions = {}): string {
  const d = new Date(zeit);
  return new Intl.DateTimeFormat("de-DE", {
    timeZone: TZ,
    ...options,
  }).format(d);
}

/** Datum + Uhrzeit, z. B. "Mo, 18.08. 14:30". */
export function formatBerlinDateTime(zeit: string): string {
  return formatBerlin(zeit, {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Nur Uhrzeit, z. B. "14:30". */
export function formatBerlinZeit(zeit: string): string {
  return formatBerlin(zeit, { hour: "2-digit", minute: "2-digit" });
}

/** Nur Datum, z. B. "Mo, 18.08.2026". */
export function formatBerlinDatum(zeit: string): string {
  return formatBerlin(zeit, {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Montag (00:00 Europa/Berlin) der Woche, die das gegebene Datum enthält. */
export function wochenstart(bezug: Date = new Date()): Date {
  // lokal in Berlin rechnen, damit Wochenstart konsistent zur Anzeige ist
  const berlin = new Date(bezug.toLocaleString("en-US", { timeZone: TZ }));
  const tag = berlin.getDay(); // 0=So … 6=Sa
  const diff = (tag + 6) % 7; // Tage seit Montag
  berlin.setDate(berlin.getDate() - diff);
  berlin.setHours(0, 0, 0, 0);
  return berlin;
}

/** Liefert die nächsten 7 Tage (Mo–So) ab einem Montag als Date-Array. */
export function wochenTage(montag: Date): Date[] {
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(montag);
    d.setDate(montag.getDate() + i);
    return d;
  });
}

/** YYYY-MM-DD im Berliner Kalender für ein <input type="date">-Default. */
export function berlinDateInputValue(d: Date = new Date()): string {
  const berlin = new Date(d.toLocaleString("en-US", { timeZone: TZ }));
  const y = berlin.getFullYear();
  const m = String(berlin.getMonth() + 1).padStart(2, "0");
  const t = String(berlin.getDate()).padStart(2, "0");
  return `${y}-${m}-${t}`;
}

/** Montiert aus einem HTML-date/time-Wert (als Europa/Berlin interpretiert) einen ISO-String. */
export function berlinZuIso(dateValue: string, timeValue: string): string {
  // Der Browser liefert lokale Eingabewerte; wir interpretieren sie als Europa/Berlin.
  // Durch das Anhängen von "T" + Zeit + und einem Berliner-Offset-Rückgriff erzeugen wir
  // einen korrekten UTC-ISO-Wert. Wir nutzen dazu einen Date-Parse mit expliziter Zone.
  const ohneZone = `${dateValue}T${timeValue}:00`;
  // JS parst "2026-08-18T14:30:00" als lokal; wir verschieben in Berlin-Zeit.
  const lokal = new Date(ohneZone);
  // Umrechnung: annehmen, die Eingabe sei Berliner Zeit → UTC = lokal - offset
  const alsBerlin = new Date(lokal.getTime() - berlinOffsetMs(lokal));
  return alsBerlin.toISOString();
}

/** Aktueller Berliner Offset (ms) zu einem gegebenen Zeitpunkt. */
function berlinOffsetMs(zeitpunkt: Date): number {
  // Erzeuge einen Zeitstempel, der so aussieht, als sei er in Berlin, und messe den Unterschied.
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = fmt.formatToParts(zeitpunkt);
  const map: Record<string, number> = {};
  for (const p of parts) {
    if (p.type !== "literal") map[p.type] = parseInt(p.value, 10);
  }
  const berlin = Date.UTC(map.year, map.month - 1, map.day, map.hour, map.minute, map.second);
  return berlin - zeitpunkt.getTime();
}

/** Aktueller Zeitpunkt als ISO (UTC), interpretiert aus Berliner "now". */
export function jetztIso(): string {
  return new Date().toISOString();
}
