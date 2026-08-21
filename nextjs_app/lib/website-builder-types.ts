/**
 * Sektionstypen und Inhaltsformen des freien Website-Baukastens (PROJ-12).
 *
 * Diese Typen spiegeln den Backend-Contract aus
 * features/PROJ-12-freier-website-baukasten-und-landingpage.md (Abschnitt
 * Tech Design) exakt wider. Das Backend validiert `website_section.inhalt`
 * serverseitig je Typ über Pydantic-Varianten; das Frontend hält dieselbe
 * Form, ohne eigenes JSON-Schema zu erfinden.
 *
 * Wichtig: Das Backend nutzt die Feldnamen `cta_typ`/`cta_text` (nicht
 * `cta_ziel`/`cta_titel`) und für Listen `kennzahlen`/`fragen`/`schritte`.
 */

/** Feste, erlaubte Sektionstypen. Kein freier Seitentyp außerhalb dieser Liste. */
export type SektionTyp =
  | "hero"
  | "text_mit_bild"
  | "leistungen"
  | "kennzahlen"
  | "ablauf"
  | "faq"
  | "kontakt"
  | "cta";

/** CTA-Ziele sind auf vorhandene öffentliche Pfade/Anker beschränkt. */
export type CtaZiel = "anfrage" | "leistungen" | "kontakt";

/** Paar aus Wert und Beschriftung (Kennzahlen). */
export interface KennzahlItem {
  wert: string;
  label: string;
}

/** Schritt mit Titel und Beschreibung (Ablauf). */
export interface AblaufSchritt {
  titel: string;
  beschreibung: string;
}

/** Frage-Antwort-Paar (FAQ). */
export interface FaqItem {
  frage: string;
  antwort: string;
}

/** Typisierte Inhaltsform je Sektionstyp (Builder-Editor). */
export interface HeroInhalt {
  typ: "hero";
  titel: string;
  text: string;
  cta_typ?: CtaZiel;
  cta_text?: string;
}
export interface TextMitBildInhalt {
  typ: "text_mit_bild";
  titel: string;
  text: string;
}
export interface LeistungenInhalt {
  typ: "leistungen";
  titel: string;
  einleitung?: string;
  cta_typ?: CtaZiel;
  cta_text?: string;
}
export interface KennzahlenInhalt {
  typ: "kennzahlen";
  titel: string;
  kennzahlen: KennzahlItem[];
}
export interface AblaufInhalt {
  typ: "ablauf";
  titel: string;
  schritte: AblaufSchritt[];
}
export interface FaqInhalt {
  typ: "faq";
  titel: string;
  fragen: FaqItem[];
}
export interface KontaktInhalt {
  typ: "kontakt";
  titel: string;
  einleitung?: string;
  cta_typ?: CtaZiel;
  cta_text?: string;
}
export interface CtaInhalt {
  typ: "cta";
  titel: string;
  text: string;
  cta_typ?: CtaZiel;
  cta_text?: string;
}

/** Eine beliebige typisierte Inhaltsvariante. */
export type SektionInhaltUnion =
  | HeroInhalt
  | TextMitBildInhalt
  | LeistungenInhalt
  | KennzahlenInhalt
  | AblaufInhalt
  | FaqInhalt
  | KontaktInhalt
  | CtaInhalt;

/** Bildreferenz im Builder-/öffentlichen Kontext (nie der rohe Objektpfad). */
export interface BildRef {
  url: string;
  alt_text: string;
}

/** Eine vollständige Sektion für den Inhaber-Editor (GET /website-builder/startseite). */
export interface WebsiteSection {
  id: string;
  typ: SektionTyp;
  visible: boolean;
  position: number;
  /** Vollständiger, typisierter Inhalt (discriminated union über `typ`). */
  inhalt: SektionInhaltUnion;
  bild: BildRef | null;
}

/** Vollständiger Builder-Zustand des Inhabers (GET /website-builder/startseite). */
export interface LandingpageState {
  landingpage_id: string;
  version: number;
  sections: WebsiteSection[];
}

/**
 * Öffentliche, gerenderte Sektion (GET /public/site).
 * Das Backend liefert pro sichtbarer Sektion das `inhalt`-Objekt (mit `typ`)
 * plus optional ein `bild`-Objekt. Felder je Typ siehe SektionInhaltUnion.
 */
export interface PublicSection {
  typ: SektionTyp;
  titel?: string;
  text?: string;
  einleitung?: string;
  cta_typ?: CtaZiel;
  cta_text?: string;
  kennzahlen?: KennzahlItem[];
  schritte?: AblaufSchritt[];
  fragen?: FaqItem[];
  bild?: BildRef | null;
  [feld: string]: unknown;
}

/** Metadaten je Typ für Editor-Beschriftungen und leere Defaultinhalte. */
export interface SektionTypMeta {
  typ: SektionTyp;
  label: string;
  beschreibung: string;
}

export const SEKTION_TYPEN: SektionTypMeta[] = [
  { typ: "hero", label: "Hero", beschreibung: "Einsteig mit Hintergrundbild und Kurzformular." },
  { typ: "text_mit_bild", label: "Text mit Bild", beschreibung: "Abschnitt mit Überschrift, Text und Bild." },
  { typ: "leistungen", label: "Leistungen", beschreibung: "Zeigt Ihre aktiven Leistungen." },
  { typ: "kennzahlen", label: "Kennzahlen", beschreibung: "Vertrauensbildende Zahlenpaare." },
  { typ: "ablauf", label: "Ablauf", beschreibung: "Schritte von der Anfrage bis zur Erledigung." },
  { typ: "faq", label: "FAQ", beschreibung: "Häufig gestellte Fragen mit Antworten." },
  { typ: "kontakt", label: "Kontakt", beschreibung: "Kontaktaufruf mit weiterem CTA." },
  { typ: "cta", label: "Abschluss-CTA", beschreibung: "Abschließender Handlungsaufruf." },
];

export const CTA_ZIELE: { wert: CtaZiel; label: string }[] = [
  { wert: "anfrage", label: "Anfrageformular" },
  { wert: "leistungen", label: "Leistungen" },
  { wert: "kontakt", label: "Kontakt (Seitenanker)" },
];

/** Editor-Beschriftung je Typ. */
export function typLabel(typ: SektionTyp): string {
  return SEKTION_TYPEN.find((t) => t.typ === typ)?.label ?? typ;
}

/** Leere Defaultinhalte je Typ für den Editor (wenn das Backend leer liefert). */
export function emptyInhalt(typ: SektionTyp): SektionInhaltUnion {
  switch (typ) {
    case "hero":
      return { typ: "hero", titel: "", text: "", cta_typ: "anfrage", cta_text: "Jetzt Anfrage senden" };
    case "text_mit_bild":
      return { typ: "text_mit_bild", titel: "", text: "" };
    case "leistungen":
      return { typ: "leistungen", titel: "", einleitung: "", cta_typ: "leistungen", cta_text: "Alle Leistungen ansehen" };
    case "kennzahlen":
      return { typ: "kennzahlen", titel: "", kennzahlen: [] };
    case "ablauf":
      return { typ: "ablauf", titel: "", schritte: [] };
    case "faq":
      return { typ: "faq", titel: "", fragen: [] };
    case "kontakt":
      return { typ: "kontakt", titel: "", einleitung: "", cta_typ: "anfrage", cta_text: "Jetzt Anfrage senden" };
    case "cta":
      return { typ: "cta", titel: "", text: "", cta_typ: "anfrage", cta_text: "Jetzt Anfrage senden" };
  }
}
