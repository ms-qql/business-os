import { API_BASE } from "@/lib/session";
import type {
  EinsendungErgebnis,
  FeldTyp,
  PublicFormular,
  PublicSchritt,
} from "@/lib/schemas/formular";

/** Fehler eines öffentlichen (nicht angemeldeten) Formular-Aufrufs. */
export class OeffentlichesFormularError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "OeffentlichesFormularError";
  }
}

async function publicRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const message =
      (data && (data.detail as string)) ||
      `Anfrage fehlgeschlagen (${res.status}).`;
    throw new OeffentlichesFormularError(res.status, message);
  }
  return data as T;
}

/** Veröffentlichten Snapshot für die Einbettung laden (404 = nicht verfügbar). */
export function getOeffentlichesFormular(publicId: string): Promise<PublicFormular> {
  return publicRequest<PublicFormular>(`/public/formulare/${publicId}`);
}

export interface UploadAntwort {
  upload_id: string;
}

/** Datei für ein Uploadfeld des laufenden Versuchs hochladen. */
export function uploadFormularDatei(
  publicId: string,
  datei: File,
  feldId: string,
  uebermittlungskennung: string,
): Promise<UploadAntwort> {
  const form = new FormData();
  form.append("uebermittlungskennung", uebermittlungskennung);
  form.append("feld_id", feldId);
  form.append("datei", datei);
  return publicRequest<UploadAntwort>(
    `/public/formulare/${publicId}/uploads`,
    { method: "POST", body: form },
  );
}

/** Antwortwert eines Feldes in der Einsendung (laut Snapshot-Typ). */
export interface FeldWert {
  feld_id: string;
  /** Text/Mehrzeilig/Zahl(einfach)/Datum(einfach)/Adresse(JSON)/Consent(bool). */
  wert?: string;
  /** Zahl als Number, Datum als ISO, falls als solche übertragen. */
  zahl?: number | null;
  datum?: string | null;
  /** Mehrfach-Auswahl (Kachel/Radio/Dropdown mit mehreren). */
  werte?: string[];
  /** Upload-IDs eines Uploadfelds. */
  upload_ids?: string[];
}

export interface EinsendungInput {
  uebermittlungskennung: string;
  client_start: string;
  honeypot: string;
  werte: FeldWert[];
}

/** Einsendung absenden. Server entscheidet Spam/normal, bleibt atomar. */
export function submitEinsendung(
  publicId: string,
  input: EinsendungInput,
): Promise<EinsendungErgebnis> {
  return publicRequest<EinsendungErgebnis>(`/public/formulare/${publicId}/einsendungen`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** Öffentliche Upload-Prüfung: Datei vorselektieren (Größe/Typ), bevor hochgeladen wird. */
export function istUploadErlaubt(datei: File, maxBytes: number, erlaubteMime: string[]): string | null {
  if (datei.size > maxBytes) {
    return `„${datei.name}" ist zu groß (maximal ${Math.round(maxBytes / (1024 * 1024))} MB je Datei).`;
  }
  if (!erlaubteMime.includes(datei.type)) {
    return `„${datei.name}" ist kein erlaubter Dateityp (JPEG, PNG, WebP oder PDF).`;
  }
  return null;
}

/** Hilfsfunktion: berechnet, welche Felder in der aktuellen (Einfach/Erweitert)-Stufe sichtbar sind. */
export function sichtbareFelder(schritt: PublicSchritt, modus: "einfach" | "erweitert"): PublicSchritt {
  if (modus === "erweitert") return schritt;
  return {
    ...schritt,
    felder: schritt.felder.filter(
      (f) => f.pflichtfeld || f.typ === "consent",
    ),
  };
}

export type { FeldTyp };
