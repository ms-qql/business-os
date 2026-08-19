"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import {
  getWebsiteSettings,
  updateWebsiteSettings,
  uploadLogo,
  type WebsiteSettings,
} from "@/lib/api/website-settings";

export default function WebsiteEinstellungenPage() {
  const [settings, setSettings] = React.useState<WebsiteSettings | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSettings(await getWebsiteSettings());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  function feld<K extends keyof WebsiteSettings>(name: K, value: WebsiteSettings[K]) {
    setSettings((prev) => (prev ? { ...prev, [name]: value } : prev));
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setError(null);
    setInfo(null);
    setSaving(true);
    try {
      const aktualisiert = await updateWebsiteSettings({
        firmenname: settings.firmenname,
        marken_farbe: settings.marken_farbe,
        telefon: settings.telefon,
        email: settings.email,
        adresse: settings.adresse,
        oeffnungszeiten: settings.oeffnungszeiten,
        ueber_uns: settings.ueber_uns,
      });
      setSettings(aktualisiert);
      setInfo("Einstellungen gespeichert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onLogo(e: React.ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    if (!datei) return;
    setError(null);
    setInfo(null);
    try {
      const { logo_url } = await uploadLogo(datei);
      setSettings((prev) => (prev ? { ...prev, logo_url } : prev));
      setInfo("Logo aktualisiert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Logo-Upload fehlgeschlagen.");
    } finally {
      e.target.value = "";
    }
  }

  async function onLeistungAendern(
    slug: string,
    patch: Partial<{ aktiv: boolean; kurzbeschreibung: string; inhalt: string }>,
  ) {
    if (!settings) return;
    setError(null);
    const leistungen = settings.leistungen.map((l) =>
      l.slug === slug ? { ...l, ...patch } : l,
    );
    setSettings({ ...settings, leistungen });
  }

  async function onLeistungenSpeichern() {
    if (!settings) return;
    setError(null);
    setInfo(null);
    setSaving(true);
    try {
      const aktualisiert = await updateWebsiteSettings({ leistungen: settings.leistungen });
      setSettings(aktualisiert);
      setInfo("Leistungen gespeichert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  if (!settings) {
    return <Alert variant="danger">{error ?? "Einstellungen konnten nicht geladen werden."}</Alert>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Website-Einstellungen</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Branding, Kontaktdaten und Leistungsseiten Ihrer öffentlichen Website.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>Branding und Kontakt</CardTitle>
          {settings.domain && (
            <CardDescription>
              Aktueller Status: {settings.domain_status ?? "unbekannt"}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="mb-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="text-[var(--color-muted-foreground)]">Öffentliche Domain: </span>
                <span className="font-medium text-[var(--color-foreground)]">
                  {settings.domain ?? "noch nicht zugeordnet"}
                </span>
              </div>
              <span className="text-[var(--color-muted-foreground)]">
                Status: {settings.domain_status ?? "inaktiv"}
              </span>
            </div>
            <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
              Die Domain wird ausschließlich im begleiteten Onboarding reserviert und mit dem
              Veröffentlichen-Schritt aktiv geschaltet. Sie ist hier nicht editierbar.
            </p>
          </div>

          <form onSubmit={onSave} className="space-y-4">
            <div className="flex items-center gap-4">
              {settings.logo_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={settings.logo_url} alt="Logo" className="h-14 w-auto rounded-[var(--radius-md)] border border-[var(--color-border)]" />
              )}
              <div>
                <Label htmlFor="logo">Logo</Label>
                <input id="logo" type="file" accept="image/*" onChange={onLogo} className="block text-sm" />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="firmenname">Firmenname</Label>
                <Input
                  id="firmenname"
                  required
                  value={settings.firmenname}
                  onChange={(e) => feld("firmenname", e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="marken_farbe">Markenfarbe</Label>
                <Input
                  id="marken_farbe"
                  type="color"
                  value={settings.marken_farbe ?? "#1d4ed8"}
                  onChange={(e) => feld("marken_farbe", e.target.value)}
                  className="h-10 w-20 p-1"
                />
              </div>
              <div>
                <Label htmlFor="telefon">Telefon</Label>
                <Input
                  id="telefon"
                  value={settings.telefon ?? ""}
                  onChange={(e) => feld("telefon", e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="email">E-Mail</Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.email ?? ""}
                  onChange={(e) => feld("email", e.target.value)}
                />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="adresse">Adresse</Label>
                <Input
                  id="adresse"
                  value={settings.adresse ?? ""}
                  onChange={(e) => feld("adresse", e.target.value)}
                  placeholder="Straße, Hausnummer, PLZ, Ort"
                />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="oeffnungszeiten">Öffnungszeiten</Label>
                <Input
                  id="oeffnungszeiten"
                  value={settings.oeffnungszeiten ?? ""}
                  onChange={(e) => feld("oeffnungszeiten", e.target.value)}
                  placeholder="Mo–Fr 8–17 Uhr"
                />
              </div>
              <div className="sm:col-span-2">
                <Label htmlFor="ueber_uns">Über uns</Label>
                <Textarea
                  id="ueber_uns"
                  value={settings.ueber_uns ?? ""}
                  onChange={(e) => feld("ueber_uns", e.target.value)}
                />
              </div>
            </div>

            <Button type="submit" disabled={saving}>
              {saving ? "Wird gespeichert …" : "Speichern"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Leistungsseiten</CardTitle>
          <CardDescription>
            Nur aktivierte Leistungen erscheinen auf der öffentlichen Website.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {settings.leistungen.map((l) => (
            <div key={l.slug} className="rounded-[var(--radius-md)] border border-[var(--color-border)] p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">{l.titel}</span>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={l.aktiv}
                    onChange={(e) => onLeistungAendern(l.slug, { aktiv: e.target.checked })}
                  />
                  Aktiv
                </label>
              </div>
              <div className="mt-3 space-y-2">
                <div>
                  <Label htmlFor={`kurz-${l.slug}`}>Kurzbeschreibung</Label>
                  <Input
                    id={`kurz-${l.slug}`}
                    value={l.kurzbeschreibung}
                    onChange={(e) => onLeistungAendern(l.slug, { kurzbeschreibung: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor={`inhalt-${l.slug}`}>Inhalt</Label>
                  <Textarea
                    id={`inhalt-${l.slug}`}
                    value={l.inhalt}
                    onChange={(e) => onLeistungAendern(l.slug, { inhalt: e.target.value })}
                  />
                </div>
              </div>
            </div>
          ))}
          <Button onClick={onLeistungenSpeichern} disabled={saving} variant="secondary">
            {saving ? "Wird gespeichert …" : "Leistungen speichern"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
