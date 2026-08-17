"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import {
  getEmailKonto,
  updateEmailKonto,
  testEmailKonto,
  type EmailKontoInput,
} from "@/lib/api/email";

type FormState = {
  imap_host: string;
  imap_port: string;
  imap_user: string;
  imap_passwort: string;
  smtp_host: string;
  smtp_port: string;
  smtp_user: string;
  smtp_passwort: string;
  imap_tls: boolean;
  smtp_tls: boolean;
};

const LEER: FormState = {
  imap_host: "",
  imap_port: "993",
  imap_user: "",
  imap_passwort: "",
  smtp_host: "",
  smtp_port: "465",
  smtp_user: "",
  smtp_passwort: "",
  imap_tls: true,
  smtp_tls: true,
};

export default function PostfachEinstellungenPage() {
  const [form, setForm] = React.useState<FormState>(LEER);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [testing, setTesting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [testResult, setTestResult] = React.useState<{ imap_ok: boolean; smtp_ok: boolean; detail: string } | null>(null);

  React.useEffect(() => {
    getEmailKonto()
      .then((konto) => {
        if (konto) {
          // Passwörter werden nicht im Klartext übertragen — Felder bleiben leer.
          setForm({
            imap_host: konto.imap_host,
            imap_port: String(konto.imap_port),
            imap_user: konto.imap_user,
            imap_passwort: "",
            smtp_host: konto.smtp_host,
            smtp_port: String(konto.smtp_port),
            smtp_user: konto.smtp_user,
            smtp_passwort: "",
            imap_tls: konto.imap_tls,
            smtp_tls: konto.smtp_tls,
          });
        }
      })
      .catch(() => setError("Postfach-Konfiguration konnte nicht geladen werden."))
      .finally(() => setLoading(false));
  }, []);

  function set<K extends keyof FormState>(name: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function buildPayload(): EmailKontoInput {
    const base = {
      imap_host: form.imap_host,
      imap_port: Number(form.imap_port),
      imap_user: form.imap_user,
      smtp_host: form.smtp_host,
      smtp_port: Number(form.smtp_port),
      smtp_user: form.smtp_user,
      imap_tls: form.imap_tls,
      smtp_tls: form.smtp_tls,
    };
    // Leere Passwortfelder nicht mitsenden (Backend behält bestehende bei).
    const payload: Record<string, unknown> = { ...base };
    if (form.imap_passwort) payload.imap_passwort = form.imap_passwort;
    if (form.smtp_passwort) payload.smtp_passwort = form.smtp_passwort;
    return payload as unknown as EmailKontoInput;
  }

  async function onTest() {
    setTesting(true);
    setError(null);
    setInfo(null);
    setTestResult(null);
    try {
      const res = await testEmailKonto(buildPayload());
      setTestResult(res);
      if (res.imap_ok && res.smtp_ok) setInfo("Verbindungstest erfolgreich (Empfang + Versand).");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Test fehlgeschlagen.");
    } finally {
      setTesting(false);
    }
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setInfo(null);
    try {
      await updateEmailKonto(buildPayload());
      setInfo("Postfach gespeichert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Postfach-Einstellungen</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Betriebs-E-Mail-Konto verbinden. Zugangsdaten werden verschlüsselt gespeichert.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>IMAP / SMTP</CardTitle>
          <CardDescription>
            Nur Inhaber. Passwörter werden verschlüsselt gespeichert; leere Felder behalten das bestehende Passwort.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSave} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <Label htmlFor="imap_host">IMAP-Host</Label>
                <Input id="imap_host" required value={form.imap_host} onChange={(e) => set("imap_host", e.target.value)} />
              </div>
              <div>
                <Label htmlFor="imap_port">IMAP-Port</Label>
                <Input id="imap_port" required type="number" value={form.imap_port} onChange={(e) => set("imap_port", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="imap_user">IMAP-Benutzer</Label>
                <Input id="imap_user" required value={form.imap_user} onChange={(e) => set("imap_user", e.target.value)} />
              </div>
              <div>
                <Label htmlFor="imap_tls">TLS</Label>
                <label className="flex h-10 items-center gap-2 text-sm">
                  <input id="imap_tls" type="checkbox" checked={form.imap_tls} onChange={(e) => set("imap_tls", e.target.checked)} />
                  Verschlüsselt
                </label>
              </div>
              <div className="sm:col-span-3">
                <Label htmlFor="imap_passwort">IMAP-Passwort</Label>
                <Input
                  id="imap_passwort"
                  type="password"
                  value={form.imap_passwort}
                  onChange={(e) => set("imap_passwort", e.target.value)}
                  placeholder="Nur ausfüllen, um es zu ändern"
                />
              </div>
              <div>
                <Label htmlFor="smtp_tls">SMTP-TLS</Label>
                <label className="flex h-10 items-center gap-2 text-sm">
                  <input id="smtp_tls" type="checkbox" checked={form.smtp_tls} onChange={(e) => set("smtp_tls", e.target.checked)} />
                  Verschlüsselt
                </label>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <Label htmlFor="smtp_host">SMTP-Host</Label>
                <Input id="smtp_host" required value={form.smtp_host} onChange={(e) => set("smtp_host", e.target.value)} />
              </div>
              <div>
                <Label htmlFor="smtp_port">SMTP-Port</Label>
                <Input id="smtp_port" required type="number" value={form.smtp_port} onChange={(e) => set("smtp_port", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="smtp_user">SMTP-Benutzer</Label>
                <Input id="smtp_user" required value={form.smtp_user} onChange={(e) => set("smtp_user", e.target.value)} />
              </div>
              <div className="sm:col-span-3">
                <Label htmlFor="smtp_passwort">SMTP-Passwort</Label>
                <Input
                  id="smtp_passwort"
                  type="password"
                  value={form.smtp_passwort}
                  onChange={(e) => set("smtp_passwort", e.target.value)}
                  placeholder="Nur ausfüllen, um es zu ändern"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={saving || testing}>
                {saving ? "Wird gespeichert …" : "Speichern"}
              </Button>
              <Button type="button" variant="outline" disabled={saving || testing} onClick={onTest}>
                {testing ? "Testet …" : "Verbindung testen"}
              </Button>
            </div>

            {testResult && (
              <div className="flex flex-wrap gap-2 text-sm">
                <span className={`rounded-full px-2 py-1 ${testResult.imap_ok ? "bg-green-50 text-[var(--color-success)]" : "bg-red-50 text-[var(--color-danger)]"}`}>
                  Empfang (IMAP): {testResult.imap_ok ? "OK" : "fehlgeschlagen"}
                </span>
                <span className={`rounded-full px-2 py-1 ${testResult.smtp_ok ? "bg-green-50 text-[var(--color-success)]" : "bg-red-50 text-[var(--color-danger)]"}`}>
                  Versand (SMTP): {testResult.smtp_ok ? "OK" : "fehlgeschlagen"}
                </span>
                {testResult.detail && (
                  <span className="text-xs text-[var(--color-muted-foreground)]">{testResult.detail}</span>
                )}
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
