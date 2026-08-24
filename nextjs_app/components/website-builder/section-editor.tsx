"use client";

import * as React from "react";
import { Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";
import { deleteSectionBild, isConflict, uploadSectionBild } from "@/lib/api/website-builder";
import {
  CTA_ZIELE,
  typLabel,
  type CtaZiel,
  type LandingpageState,
  type SektionInhaltUnion,
  type SektionTyp,
  type WebsiteSection,
} from "@/lib/website-builder-types";

interface Props {
  section: WebsiteSection;
  version: number;
  onSaveInhalt: (inhalt: SektionInhaltUnion, visible: boolean) => Promise<LandingpageState>;
  /** Wird nach einem erfolgreichen Bild-Upload/-Löschen mit dem neuen Zustand aufgerufen. */
  onStateUpdate: (state: LandingpageState) => void;
}

/** Editor für die typenbezogenen Felder einer einzelnen Sektion. */
export function SectionEditor({ section, version, onSaveInhalt, onStateUpdate }: Props) {
  const [inhalt, setInhalt] = React.useState<SektionInhaltUnion>(section.inhalt);
  const [visible, setVisible] = React.useState(section.visible);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Bild-Upload-State
  const [alt, setAlt] = React.useState(section.bild?.alt_text ?? "");
  const [bildFehler, setBildFehler] = React.useState<string | null>(null);
  const [bildSpeichern, setBildSpeichern] = React.useState(false);
  const bildUrl = section.bild?.url ?? null;

  // Beim Wechsel in der Sektionsliste darf kein Inhalt des zuvor gewählten
  // Typs im Editor bleiben (z. B. Hero statt Kennzahlen).
  React.useEffect(() => {
    setInhalt(section.inhalt);
    setVisible(section.visible);
    setError(null);
  }, [section.id, section.inhalt, section.visible]);

  // Alt-Text aus dem Serverzustand übernehmen, sobald sich das Bild ändert.
  React.useEffect(() => {
    setAlt(section.bild?.alt_text ?? "");
  }, [section.bild?.alt_text]);

  const erlaubtBild = section.typ === "hero" || section.typ === "text_mit_bild";
  const inhaltDirty =
    JSON.stringify(inhalt) !== JSON.stringify(section.inhalt) || visible !== section.visible;

  function patch(teil: Partial<SektionInhaltUnion>) {
    setInhalt((prev) => ({ ...prev, ...teil }) as SektionInhaltUnion);
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSaveInhalt(inhalt, visible);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onBild(e: React.ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    if (datei) await ladeBildHoch(datei, e);
  }

  async function ladeBildHoch(datei: File, e?: React.ChangeEvent<HTMLInputElement>) {
    const res = await handleBild(async () => {
      const gespeicherterInhalt = inhaltDirty ? await onSaveInhalt(inhalt, visible) : null;
      return uploadSectionBild(section.id, datei, alt, gespeicherterInhalt?.version ?? version);
    }, e);
    if (res) {
      const aktualisiert = res.sections.find((s) => s.id === section.id);
      setAlt(aktualisiert?.bild?.alt_text ?? alt);
    }
  }

  async function onBildEntfernen() {
    await handleBild(() => deleteSectionBild(section.id, version));
  }

  async function handleBild(
    fn: () => Promise<LandingpageState>,
    e?: React.ChangeEvent<HTMLInputElement>,
  ): Promise<LandingpageState | null> {
    setBildFehler(null);
    setBildSpeichern(true);
    try {
      const res = await fn();
      onStateUpdate(res);
      return res;
    } catch (err) {
      setBildFehler(err instanceof ApiError ? err.message : "Bildvorgang fehlgeschlagen.");
      if (e) e.target.value = "";
      return null;
    } finally {
      setBildSpeichern(false);
    }
  }

  return (
    <form onSubmit={onSave} className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[var(--color-muted-foreground)]">
          {typLabel(section.typ)}
        </span>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={visible}
            onChange={(e) => setVisible(e.target.checked)}
            aria-label={`${typLabel(section.typ)} sichtbar`}
          />
          Sichtbar
        </label>
      </div>

      <InhaltFelder typ={section.typ} inhalt={inhalt} onChange={(teil) => patch(teil)} />

      {erlaubtBild && (
        <div className="rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-3">
          <Label>Bild</Label>
          {bildUrl ? (
            <div className="mt-2 flex items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={bildUrl}
                alt={alt ?? ""}
                className="h-16 w-auto rounded-[var(--radius-md)] border border-[var(--color-border)]"
              />
              {section.bild?.anzeigename && (
                <span className="text-xs text-[var(--color-muted-foreground)]">
                  {section.bild.anzeigename}
                </span>
              )}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onBildEntfernen}
                disabled={bildSpeichern}
              >
                <X size={16} /> Entfernen
              </Button>
            </div>
          ) : (
            <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
              Ohne Bild bleibt die Sektion als Textvariante nutzbar.
            </p>
          )}
          <div className="mt-2 space-y-2">
            <div>
              <Label htmlFor={`alt-${section.id}`} className="text-xs">
                Alternativtext (Barrierefreiheit)
              </Label>
              <Input
                id={`alt-${section.id}`}
                value={alt}
                onChange={(e) => setAlt(e.target.value)}
                placeholder="Beschreibung des Bildinhalts"
                className="h-9"
              />
            </div>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const datei = e.dataTransfer.files[0];
                if (datei) void ladeBildHoch(datei);
              }}
              className="rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] p-2"
            >
              <input
                id={`bild-${section.id}`}
                type="file"
                accept="image/*"
                onChange={onBild}
                disabled={bildSpeichern}
                className="block w-full text-sm text-[var(--color-muted-foreground)] file:mr-3 file:rounded-[var(--radius-md)] file:border-0 file:bg-[var(--color-surface)] file:px-3 file:py-2 file:text-sm file:font-medium"
              />
              <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">Oder Bild hierher ziehen.</p>
            </div>
          </div>
          {bildFehler && <Alert variant="danger" className="mt-2">{bildFehler}</Alert>}
        </div>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={saving || !inhaltDirty}>
          {saving ? "Wird gespeichert …" : "Inhalt speichern"}
        </Button>
        {!inhaltDirty && (
          <span className="text-xs text-[var(--color-muted-foreground)]">Keine Änderungen.</span>
        )}
      </div>
    </form>
  );
}

/** Typenbezogene Felder je Sektionstyp. */
function InhaltFelder({
  typ,
  inhalt,
  onChange,
}: {
  typ: SektionTyp;
  inhalt: SektionInhaltUnion;
  onChange: (teil: Partial<SektionInhaltUnion>) => void;
}) {
  switch (typ) {
    case "hero": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "hero" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <Feld label="Text">
            <Textarea value={c.text} onChange={(e) => onChange({ text: e.target.value })} />
          </Feld>
          <CtaFelder
            titel={c.cta_text ?? ""}
            ziel={c.cta_typ}
            onTitel={(v) => onChange({ cta_text: v })}
            onZiel={(v) => onChange({ cta_typ: v })}
          />
        </>
      );
    }
    case "text_mit_bild": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "text_mit_bild" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <Feld label="Text">
            <Textarea value={c.text} onChange={(e) => onChange({ text: e.target.value })} />
          </Feld>
        </>
      );
    }
    case "leistungen": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "leistungen" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <Feld label="Einleitung">
            <Textarea
              value={c.einleitung ?? ""}
              onChange={(e) => onChange({ einleitung: e.target.value })}
            />
          </Feld>
          <CtaFelder
            titel={c.cta_text ?? ""}
            ziel={c.cta_typ}
            onTitel={(v) => onChange({ cta_text: v })}
            onZiel={(v) => onChange({ cta_typ: v })}
          />
          <p className="text-xs text-[var(--color-muted-foreground)]">
            Es werden automatisch Ihre aktiven Leistungen aus den Website-Einstellungen angezeigt.
          </p>
        </>
      );
    }
    case "kennzahlen": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "kennzahlen" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <PaarListe
            titel="Kennzahl"
            paare={c.kennzahlen.map((k) => ({ a: k.wert, b: k.label }))}
            aufLabel="Wert"
            abLabel="Beschriftung"
            onChange={(paare) => onChange({ kennzahlen: paare.map((p) => ({ wert: p.a, label: p.b })) })}
          />
        </>
      );
    }
    case "ablauf": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "ablauf" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <PaarListe
            titel="Schritt"
            paare={c.schritte.map((s) => ({ a: s.titel, b: s.beschreibung }))}
            aufLabel="Schritttitel"
            abLabel="Beschreibung"
            mehrzeilig
            onChange={(paare) =>
              onChange({ schritte: paare.map((p) => ({ titel: p.a, beschreibung: p.b })) })
            }
          />
        </>
      );
    }
    case "faq": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "faq" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <PaarListe
            titel="Frage"
            paare={c.fragen.map((f) => ({ a: f.frage, b: f.antwort }))}
            aufLabel="Frage"
            abLabel="Antwort"
            mehrzeilig
            onChange={(paare) =>
              onChange({ fragen: paare.map((p) => ({ frage: p.a, antwort: p.b })) })
            }
          />
        </>
      );
    }
    case "kontakt": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "kontakt" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <Feld label="Einleitung">
            <Textarea
              value={c.einleitung ?? ""}
              onChange={(e) => onChange({ einleitung: e.target.value })}
            />
          </Feld>
          <CtaFelder
            titel={c.cta_text ?? ""}
            ziel={c.cta_typ}
            onTitel={(v) => onChange({ cta_text: v })}
            onZiel={(v) => onChange({ cta_typ: v })}
          />
        </>
      );
    }
    case "cta": {
      const c = inhalt as Extract<SektionInhaltUnion, { typ: "cta" }>;
      return (
        <>
          <Feld label="Titel">
            <Input value={c.titel} onChange={(e) => onChange({ titel: e.target.value })} />
          </Feld>
          <Feld label="Text">
            <Textarea value={c.text} onChange={(e) => onChange({ text: e.target.value })} />
          </Feld>
          <CtaFelder
            titel={c.cta_text ?? ""}
            ziel={c.cta_typ}
            onTitel={(v) => onChange({ cta_text: v })}
            onZiel={(v) => onChange({ cta_typ: v })}
          />
        </>
      );
    }
  }
}

function Feld({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function CtaFelder({
  titel,
  ziel,
  onTitel,
  onZiel,
}: {
  titel: string;
  ziel: CtaZiel | undefined;
  onTitel: (v: string) => void;
  onZiel: (v: CtaZiel | undefined) => void;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <Label>CTA-Text</Label>
        <Input
          value={titel}
          onChange={(e) => onTitel(e.target.value)}
          placeholder="z. B. Jetzt Anfrage senden"
        />
      </div>
      <div>
        <Label>CTA-Ziel</Label>
        <Select
          value={ziel ?? ""}
          onChange={(e) => onZiel((e.target.value || undefined) as CtaZiel | undefined)}
        >
          <option value="">Kein CTA</option>
          {CTA_ZIELE.map((z) => (
            <option key={z.wert} value={z.wert}>
              {z.label}
            </option>
          ))}
        </Select>
      </div>
    </div>
  );
}

/** Generische Liste eines Werte-Paars (Kennzahlen, Ablauf, FAQ).
 * Arbeitet auf einer neutralen Form { a, b } und wird je Sektionstyp über
 * eine Adapter-Mapping angeschlossen. */
function PaarListe({
  titel,
  paare,
  aufLabel,
  abLabel,
  mehrzeilig,
  onChange,
}: {
  titel: string;
  paare: { a: string; b: string }[];
  aufLabel: string;
  abLabel: string;
  mehrzeilig?: boolean;
  onChange: (paare: { a: string; b: string }[]) => void;
}) {
  function setZeile(i: number, feld: "a" | "b", wert: string) {
    onChange(paare.map((p, idx) => (idx === i ? { ...p, [feld]: wert } : p)));
  }
  function hinzufuegen() {
    onChange([...paare, { a: "", b: "" }]);
  }
  function entfernen(i: number) {
    onChange(paare.filter((_, idx) => idx !== i));
  }

  return (
    <div className="space-y-2">
      <Label>
        {titel} ({paare.length})
      </Label>
      {paare.map((p, i) => (
        <div
          key={i}
          className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] p-2"
        >
          <div className="flex-1 space-y-2">
            <Input
              aria-label={`${aufLabel} ${i + 1}`}
              value={p.a}
              onChange={(e) => setZeile(i, "a", e.target.value)}
              placeholder={aufLabel}
            />
            {mehrzeilig ? (
              <Textarea
                aria-label={`${abLabel} ${i + 1}`}
                value={p.b}
                onChange={(e) => setZeile(i, "b", e.target.value)}
                placeholder={abLabel}
              />
            ) : (
              <Input
                aria-label={`${abLabel} ${i + 1}`}
                value={p.b}
                onChange={(e) => setZeile(i, "b", e.target.value)}
                placeholder={abLabel}
              />
            )}
          </div>
          <button
            type="button"
            onClick={() => entfernen(i)}
            aria-label={`${titel} ${i + 1} entfernen`}
            className="mt-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      <Button type="button" variant="secondary" size="sm" onClick={hinzufuegen}>
        {titel} hinzufügen
      </Button>
    </div>
  );
}
