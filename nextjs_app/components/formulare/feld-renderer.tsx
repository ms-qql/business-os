import * as React from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Alert } from "@/components/ui/label";
import type { OeffentlichesFeld, FormularFeldDraft } from "@/lib/schemas/formular";

export type FeldWert = string | boolean | AdresseWert | string[] | null;

export interface AdresseWert {
  strasse: string;
  hausnummer: string;
  plz: string;
  ort: string;
}

export function feldSichtbar(
  feld: { pflichtfeld: boolean; optional_in_einfach: boolean },
  modus: "einfach" | "erweitert",
): boolean {
  if (modus === "erweitert") return feld.pflichtfeld || feld.optional_in_einfach;
  return feld.pflichtfeld;
}

interface FeldRendererProps {
  feld: OeffentlichesFeld | FormularFeldDraft;
  value: FeldWert;
  onChange: (wert: FeldWert) => void;
  error?: string;
  disabled?: boolean;
  /** Adress- und Uploadfelder brauchen Sonderbehandlung in der öffentlichen Ansicht. */
  renderUpload?: (feld: OeffentlichesFeld) => React.ReactNode;
}

export function FeldRenderer({
  feld,
  value,
  onChange,
  error,
  disabled,
  renderUpload,
}: FeldRendererProps) {
  if (feld.typ === "upload") {
    return (
      <div>
        <LabelText feld={feld} />
        {renderUpload ? (
          renderUpload(feld)
        ) : (
          <input
            type="file"
            disabled
            className="block w-full text-sm text-[var(--color-muted-foreground)]"
          />
        )}
        {error && <Alert variant="danger" className="mt-1">{error}</Alert>}
      </div>
    );
  }

  if (feld.typ === "consent") {
    const checked = value === true;
    return (
      <div>
        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={checked}
            disabled={disabled}
            onChange={(e) => onChange(e.target.checked)}
            className="mt-1 h-4 w-4"
            aria-invalid={error ? true : undefined}
          />
          <span>{feld.label}</span>
        </label>
        {feld.hilfetext && (
          <p className="mt-1 pl-6 text-xs text-[var(--color-muted-foreground)]">
            {feld.hilfetext}
          </p>
        )}
        {error && (
          <Alert variant="danger" className="mt-1">
            {error}
          </Alert>
        )}
      </div>
    );
  }

  return (
    <div>
      <LabelText feld={feld} />
      {feld.hilfetext && (
        <p className="mb-1.5 text-xs text-[var(--color-muted-foreground)]">
          {feld.hilfetext}
        </p>
      )}
      <FeldControl feld={feld} value={value} onChange={onChange} disabled={disabled} />
      {error && (
        <Alert variant="danger" className="mt-1">
          {error}
        </Alert>
      )}
    </div>
  );
}

function LabelText({ feld }: { feld: OeffentlichesFeld | FormularFeldDraft }) {
  return (
    <label className="mb-1.5 block text-sm font-medium text-[var(--color-foreground)]">
      {feld.label}
      {feld.pflichtfeld && <span className="text-[var(--color-danger)]"> *</span>}
    </label>
  );
}

const inputClass =
  "h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm";

function FeldControl({
  feld,
  value,
  onChange,
  disabled,
}: {
  feld: OeffentlichesFeld | FormularFeldDraft;
  value: FeldWert;
  onChange: (wert: FeldWert) => void;
  disabled?: boolean;
}) {
  const str = typeof value === "string" ? value : "";

  switch (feld.typ) {
    case "text":
      return (
        <Input
          value={str}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          aria-describedby={feld.id}
        />
      );
    case "mehrzeilig":
      return (
        <Textarea
          value={str}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "zahl":
      return (
        <Input
          type="number"
          value={str}
          disabled={disabled}
          min={feld.config.min}
          max={feld.config.max}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "datum":
      return (
        <Input
          type="date"
          value={str}
          disabled={disabled}
          min={feld.config.minDatum}
          max={feld.config.maxDatum}
          onChange={(e) => onChange(e.target.value)}
        />
      );
    case "dropdown":
      return (
        <select
          value={str}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className={inputClass}
        >
          <option value="">Bitte wählen …</option>
          {feld.options.map((o) => (
            <option key={o.wert} value={o.wert}>
              {o.label}
            </option>
          ))}
        </select>
      );
    case "radio":
      return (
        <div className="space-y-1.5">
          {feld.options.map((o) => (
            <label key={o.wert} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name={feld.id}
                value={o.wert}
                checked={str === o.wert}
                disabled={disabled}
                onChange={() => onChange(o.wert)}
              />
              {o.label}
            </label>
          ))}
        </div>
      );
    case "kachel":
      return (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {feld.options.map((o) => {
            const aktiv = str === o.wert;
            return (
              <button
                key={o.wert}
                type="button"
                disabled={disabled}
                onClick={() => onChange(o.wert)}
                className={`rounded-[var(--radius-md)] border p-3 text-left text-sm font-medium ${
                  aktiv
                    ? "border-[var(--color-brand)] bg-[var(--color-surface-muted)]"
                    : "border-[var(--color-border)]"
                }`}
                aria-pressed={aktiv}
              >
                {o.label}
              </button>
            );
          })}
        </div>
      );
    case "adresse": {
      const adr = (value as AdresseWert) ?? {
        strasse: "",
        hausnummer: "",
        plz: "",
        ort: "",
      };
      const set = (teil: keyof AdresseWert, v: string) =>
        onChange({ ...adr, [teil]: v });
      return (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Input
            placeholder="Straße"
            value={adr.strasse}
            disabled={disabled}
            onChange={(e) => set("strasse", e.target.value)}
          />
          <Input
            placeholder="Hausnummer"
            value={adr.hausnummer}
            disabled={disabled}
            onChange={(e) => set("hausnummer", e.target.value)}
          />
          <Input
            placeholder="PLZ"
            value={adr.plz}
            disabled={disabled}
            onChange={(e) => set("plz", e.target.value)}
          />
          <Input
            placeholder="Ort"
            value={adr.ort}
            disabled={disabled}
            onChange={(e) => set("ort", e.target.value)}
          />
        </div>
      );
    }
    default:
      return null;
  }
}
