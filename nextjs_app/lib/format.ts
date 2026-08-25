import { cn } from "@/lib/utils";

/** Locale-Formatter für Business-OS (de-DE, EUR). */

export function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", {
    style: "currency",
    currency: "EUR",
  });
}

export function formatProzent(wert: number): string {
  return `${wert.toLocaleString("de-DE", { maximumFractionDigits: 2 })} %`;
}

export function formatZahl(wert: number, nachkomma = 2): string {
  return wert.toLocaleString("de-DE", {
    minimumFractionDigits: nachkomma,
    maximumFractionDigits: nachkomma,
  });
}

/** Markiert negative Beträge rot (für Angebotspositionen mit negativem Preis). */
export function vorzeichenKlasse(wert: number): string {
  return cn(wert < 0 ? "text-[var(--color-danger)]" : "");
}
