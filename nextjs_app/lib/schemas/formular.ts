/**
 * Domänen-Typen für den Formular-Baukasten (PROJ-13).
 *
 * Spiegelt den API-Vertrag aus features/PROJ-13-formular-baukasten.md
 * (Tech Design → API-Contracts): angemeldete Entwurfs-Endpunkte unter
 * /formulare/* und öffentliche Einbettungs-/Submit-Endpunkte unter
 * /public/formulare/{public_id}.
 *
 * Achtung: Dieses Frontend ist der einzige Editor. Es sendet ausschließlich
 * die festen Feldtypen und Konfigurationsfelder, die der Server zulässt —
 * kein frei definierbarer Feldtyp, keine freie Logik.
 */

/** Feste Feldtypen aus dem Baukasten-Katalog (nicht erweiterbar). */
export type FeldTyp =
  | "text"
  | "mehrzeilig"
  | "dropdown"
  | "kachel"
  | "radio"
  | "zahl"
  | "datum"
  | "upload"
  | "adresse"
  | "consent";

/** Optional mögliche Übernahme-Zuordnung eines Text-/Adress-/Auswahlfelds. */
export type UebernahmeZuordnung =
  | "kontaktname"
  | "email"
  | "telefon"
  | "adresse"
  | "anliegen";

export type Komplexitaet = "einfach" | "erweitert";

export interface FormularOption {
  id: string;
  label: string;
  wert: string;
}

/** Eine Auswahl-/Kachel-/Radio-Option beim öffentlichen Rendern. */
export interface PublicOption {
  label: string;
  wert: string;
}

/**
 * Feld im Entwurf. Typ-abhängige Konfiguration wird über optionale Felder
 * abgebildet; der Server ignoriert nicht zutreffende Felder bzw. fordert
 * passende Werte beim Publish-Check ein.
 */
export interface Feld {
  id: string;
  typ: FeldTyp;
  label: string;
  hilfetext: string | null;
  pflichtfeld: boolean;
  /** Nur für optionale Felder: in der öffentlichen „Erweitert"-Stufe anzeigen. */
  optional_in_einfach: boolean;
  uebernahme: UebernahmeZuordnung | null;
  // Typkonfiguration
  min?: number | null;
  max?: number | null;
  ganzzahl?: boolean;
  reg_exp?: string | null;
  maxlaenge?: number | null;
  datum_min?: string | null;
  datum_max?: string | null;
  max_anzahl?: number | null;
  optionen?: FormularOption[];
}

export interface Schritt {
  id: string;
  titel: string;
  felder: Feld[];
}

/** Vollständiger eigener Entwurf inkl. Publish-Status (GET /formulare/{id}). */
export interface FormularEntwurf {
  id: string;
  name: string;
  komplexitaet: Komplexitaet;
  draft_revision: number;
  veroeffentlicht: boolean;
  public_id: string | null;
  schritte: Schritt[];
  created_at: string;
  updated_at: string;
}

/** Listeneintrag ohne Schritte (GET /formulare). */
export interface FormularListeItem {
  id: string;
  name: string;
  komplexitaet: Komplexitaet;
  draft_revision: number;
  veroeffentlicht: boolean;
  public_id: string | null;
  updated_at: string;
}

export interface FormularListeResult {
  items: FormularListeItem[];
  total: number;
  limit: number;
  offset: number;
}

/** Öffentlich gerenderte Feldregeln (GET /public/formulare/{public_id}). */
export interface PublicFeld {
  id: string;
  typ: FeldTyp;
  label: string;
  hilfetext: string | null;
  pflichtfeld: boolean;
  optionen: PublicOption[];
  min?: number | null;
  max?: number | null;
  ganzzahl?: boolean;
  maxlaenge?: number | null;
  reg_exp?: string | null;
  datum_min?: string | null;
  datum_max?: string | null;
  max_anzahl?: number | null;
}

export interface PublicSchritt {
  id: string;
  titel: string;
  felder: PublicFeld[];
}

export interface PublicFormular {
  name: string;
  /** Komplexitätsstufe der veröffentlichten Fassung: einfach oder erweitert. */
  modus: Komplexitaet;
  schritte: PublicSchritt[];
}

/** Einbindungs-Codes nach Veröffentlichung (GET /formulare/{id}/einbindung). */
export interface FormularEinbindung {
  direktlink: string;
  iframe: string;
  snippet: string;
}

export interface EinsendungErgebnis {
  status: "erfolgreich" | "spam";
}

/** Fester Feldtypen-Katalog für Auswahl-UI und Renderer. */
export interface FeldTypMeta {
  typ: FeldTyp;
  label: string;
  beschreibung: string;
  /** Felder mit Auswahloptionen. */
  hatOptionen: boolean;
}

export const FELDTYPEN: FeldTypMeta[] = [
  {
    typ: "text",
    label: "Text",
    beschreibung: "Eine Zeile, z. B. Name oder Telefon.",
    hatOptionen: false,
  },
  {
    typ: "mehrzeilig",
    label: "Mehrzeiliger Text",
    beschreibung: "Freitext über mehrere Zeilen, z. B. Anliegen.",
    hatOptionen: false,
  },
  {
    typ: "dropdown",
    label: "Auswahl / Dropdown",
    beschreibung: "Eine Auswahl aus einer Liste.",
    hatOptionen: true,
  },
  {
    typ: "kachel",
    label: "Kachel-Auswahl",
    beschreibung: "Eine Auswahl als anklickbare Kacheln.",
    hatOptionen: true,
  },
  {
    typ: "radio",
    label: "Radio-Buttons",
    beschreibung: "Eine Auswahl als Optionsfelder.",
    hatOptionen: true,
  },
  {
    typ: "zahl",
    label: "Mengenfeld / Zahl",
    beschreibung: "Eine Zahl mit optionalem Bereich.",
    hatOptionen: false,
  },
  {
    typ: "datum",
    label: "Datum",
    beschreibung: "Ein Datum mit optionalem Bereich.",
    hatOptionen: false,
  },
  {
    typ: "upload",
    label: "Datei- / Foto-Upload",
    beschreibung: "JPEG, PNG, WebP oder PDF (max. 15 MB je Datei).",
    hatOptionen: false,
  },
  {
    typ: "adresse",
    label: "Adressfeld",
    beschreibung: "Strukturierte Straße, Hausnummer, PLZ und Ort.",
    hatOptionen: false,
  },
  {
    typ: "consent",
    label: "Consent / Datenschutz",
    beschreibung: "Erforderliche Zustimmung zur Datenschutzerklärung.",
    hatOptionen: false,
  },
];

const FELDTYP_LABELS: Record<FeldTyp, string> = FELDTYPEN.reduce(
  (acc, t) => {
    acc[t.typ] = t.label;
    return acc;
  },
  {} as Record<FeldTyp, string>,
);

export function feldTypLabel(typ: FeldTyp): string {
  return FELDTYP_LABELS[typ] ?? typ;
}

/** Feldtypen, die eine verpflichtende Auswahl erfordern. */
export const AUSWAHL_TYPEN: FeldTyp[] = ["dropdown", "kachel", "radio"];

/** Übernahme-Zuordnungen für die Vorgangsübernahme. */
export const UEBERNAHME_OPTIONEN: { wert: UebernahmeZuordnung; label: string }[] = [
  { wert: "kontaktname", label: "Kontaktname" },
  { wert: "email", label: "E-Mail" },
  { wert: "telefon", label: "Telefon" },
  { wert: "adresse", label: "Adresse" },
  { wert: "anliegen", label: "Anliegen" },
];

/** Maximale Upload-Größe laut Tech Design (15 MB je Datei). */
export const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

/** Erlaubte Upload-MIME-Typen laut Tech Design. */
export const UPLOAD_MIME = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
];
