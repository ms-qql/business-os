/**
 * Reine Berechnungslogik für Angebotspositionen (PROJ-5).
 * Keine React-/API-Abhängigkeiten — dadurch ohne Mocking testbar.
 * Rundungsregel laut Tech Design: je Position auf 2 Nachkommastellen runden,
 * dann aufsummieren (nicht erst die Endsumme runden).
 */

export type RabattTyp = "prozent" | "betrag";

export interface Position {
  menge: number;
  einzelpreis: number;
  steuersatz: number;
  rabatt_typ: RabattTyp;
  rabatt_wert: number;
}

function runden2(wert: number): number {
  return Math.round((wert + Number.EPSILON) * 100) / 100;
}

/** Positionssumme (netto) nach Rabatt, auf 2 Nachkommastellen gerundet. */
export function positionsSumme(p: Pick<Position, "menge" | "einzelpreis" | "rabatt_typ" | "rabatt_wert">): number {
  const basis = p.menge * p.einzelpreis;
  const netto = p.rabatt_typ === "prozent" ? basis * (1 - p.rabatt_wert / 100) : basis - p.rabatt_wert;
  return runden2(Math.max(0, netto));
}

export interface Summen {
  netto: number;
  steuer: number;
  brutto: number;
}

/** Summiert Netto/Steuer/Brutto über alle Positionen, je Zeile vorher gerundet. */
export function summenBerechnen(positionen: Position[]): Summen {
  let netto = 0;
  let steuer = 0;
  for (const p of positionen) {
    const zeilenNetto = positionsSumme(p);
    netto += zeilenNetto;
    steuer += runden2(zeilenNetto * (p.steuersatz / 100));
  }
  netto = runden2(netto);
  steuer = runden2(steuer);
  return { netto, steuer, brutto: runden2(netto + steuer) };
}

/** Validiert `rabatt_wert` serverseitig gespiegelt (Tech Design Abschnitt E) — für sofortiges Client-Feedback. */
export function rabattFehler(typ: RabattTyp, wert: number, menge: number, einzelpreis: number): string | null {
  if (typ === "prozent") {
    if (wert < 0 || wert > 100) return "Rabatt in Prozent muss zwischen 0 und 100 liegen.";
    return null;
  }
  if (wert < 0) return "Rabattbetrag darf nicht negativ sein.";
  if (menge * einzelpreis - wert < 0) return "Rabattbetrag darf die Positionssumme nicht unter 0 senken.";
  return null;
}
