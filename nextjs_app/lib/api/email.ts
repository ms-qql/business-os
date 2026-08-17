import { apiFetch } from "@/lib/api/client";

/** Verbindungsstatus des Postfachs — treibt die PostfachWarnung. */
export type AbrufStatus = "ok" | "fehler" | null;

export interface EmailKonto {
  id: string;
  imap_host: string;
  imap_port: number;
  imap_user: string;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  imap_tls: boolean;
  smtp_tls: boolean;
  letzter_abruf_status: AbrufStatus;
  letzter_abruf_fehler_text: string | null;
  letzter_abruf_at: string | null;
}

export interface EmailKontoInput {
  imap_host: string;
  imap_port: number;
  imap_user: string;
  imap_passwort?: string;
  imap_tls: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_passwort?: string;
  smtp_tls: boolean;
}

export interface EmailKontoTestResult {
  imap_ok: boolean;
  smtp_ok: boolean;
  detail: string;
}

export interface EmailAnhang {
  id: string;
  dateiname: string;
  content_type: string;
  groesse_bytes: number;
  verarbeitet: boolean;
}

export interface EmailInboxItem {
  thread_id: string;
  absender: string;
  empfaenger: string;
  betreff: string | null;
  vorgang_id: string | null;
  kunde_id: string | null;
  letzte_nachricht_am: string | null;
  letzte_nachricht_id: string;
}

export interface EmailNachrichtDetail {
  id: string;
  thread_id: string;
  richtung: "eingehend" | "ausgehend";
  absender: string;
  empfaenger: string;
  betreff: string | null;
  vorgang_id: string | null;
  kunde_id: string | null;
  created_at: string;
  text_html: string | null;
  text_plain: string | null;
  anhaenge: EmailAnhang[];
}

export interface InboxResult {
  items: EmailInboxItem[];
  konto_status: AbrufStatus;
  konto_fehler_text: string | null;
}

export interface EmailThread {
  id: string;
  vorgang_id: string | null;
  kunde_id: string | null;
  betreff: string | null;
  nachrichten: EmailNachrichtDetail[];
}

/** Aktuelle Postfach-Konfiguration (ohne Passwort im Klartext). */
export function getEmailKonto(): Promise<EmailKonto | null> {
  return apiFetch<EmailKonto | null>("/email-konto");
}

/** Nur Inhaber. */
export function updateEmailKonto(input: EmailKontoInput): Promise<EmailKonto> {
  return apiFetch<EmailKonto>("/email-konto", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/** Empfang + Versand testen, ohne zu speichern. Nur Inhaber. */
export function testEmailKonto(input: EmailKontoInput): Promise<EmailKontoTestResult> {
  return apiFetch<EmailKontoTestResult>("/email-konto/test", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** Paginierte Inbox nicht/zugeordneter Nachrichten inkl. Verbindungsstatus. */
export function getInbox(params: {
  zugeordnet?: boolean;
  limit?: number;
  offset?: number;
} = {}): Promise<InboxResult> {
  const qs = new URLSearchParams();
  if (params.zugeordnet !== undefined) qs.set("zugeordnet", String(params.zugeordnet));
  qs.set("limit", String(params.limit ?? 20));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<InboxResult>(`/email/inbox?${qs.toString()}`);
}

export function getEmailNachricht(id: string): Promise<EmailNachrichtDetail> {
  return apiFetch<EmailNachrichtDetail>(`/email/nachrichten/${id}`);
}

/** Nachricht einem vorhandenen Vorgang zuordnen. Büro/Inhaber. */
export function nachrichtZuordnen(id: string, vorgangId: string): Promise<EmailNachrichtDetail> {
  return apiFetch<EmailNachrichtDetail>(`/email/nachrichten/${id}/zuordnen`, {
    method: "POST",
    body: JSON.stringify({ vorgang_id: vorgangId }),
  });
}

/** Neuen Vorgang aus der Nachricht anlegen. Büro/Inhaber. */
export function nachrichtNeuerVorgang(
  id: string,
  input: { kunde_id?: string; anliegen?: string } = {},
): Promise<EmailNachrichtDetail> {
  return apiFetch<EmailNachrichtDetail>(`/email/nachrichten/${id}/vorgang`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** E-Mail-Verlauf eines Vorgangs. Nur Büro und Inhaber. */
export function getVorgangEmails(vorgangId: string): Promise<EmailThread[]> {
  return apiFetch<EmailThread[]>(`/vorgaenge/${vorgangId}/emails`);
}

/** E-Mail verfassen und senden. Nur Büro und Inhaber. */
export function sendVorgangEmail(
  vorgangId: string,
  input: { betreff: string; text: string },
): Promise<EmailNachrichtDetail> {
  return apiFetch<EmailNachrichtDetail>(`/vorgaenge/${vorgangId}/emails`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** Liefert eine kurzlebige, berechtigte Download-Adresse (presigned URL) für einen Anhang. */
export function emailAnhangDownloadUrl(
  vorgangId: string,
  emailId: string,
  anhangId: string,
): Promise<{ download_url: string }> {
  return apiFetch<{ download_url: string }>(
    `/vorgaenge/${vorgangId}/emails/${emailId}/anhaenge/${anhangId}/download`,
  );
}
