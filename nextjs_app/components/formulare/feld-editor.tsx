"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  FELDTYP_LABELS,
  UEBERNAHME_FELDER,
  UEBERNAHME_LABELS,
  hatOptionen,
  type FeldKonfiguration,
  type FormularFeldDraft,
  type UebernahmeFeld,
} from "@/lib/schemas/formular";

export interface FeldEditorErgebnis {
  label: string;
  hilfetext: string;
  pflichtfeld: boolean;
  optional_in_einfach: boolean;
  config: FeldKonfiguration;
  uebernahme: UebernahmeFeld | null;
  options: { label: string; wert: string }[];
}

interface FeldEditorProps {
  feld: FormularFeldDraft;
  onChange: (ergebnis: FeldEditorErgebnis) => void;
  onAbbrechen: () => void;
}

export function FeldEditor({ feld, onChange, onAbbrechen }: FeldEditorProps) {
  const [label, setLabel] = React.useState(feld.label);
  const [hilfetext, setHilfetext] = React.useState(feld.hilfetext);
  const [pflichtfeld, setPflichtfeld] = React.useState(feld.pflichtfeld);
  const [optionalInEinfach, setOptionalInEinfach] = React.useState(
    feld.optional_in_einfach,
  );
  const [config, setConfig] = React.useState<FeldKonfiguration>(feld.config ?? {});
  const [uebernahme, setUebernahme] = React.useState<UebernahmeFeld | null>(
    feld.uebernahme,
  );
  const [options, setOptions] = React.useState(
    feld.options.map((o) => ({ label: o.label, wert: o.wert })),
  );
  const [optionenGeprueft, setOptionenGeprueft] = React.useState(false);

  const optionDoppelteWerte = React.useMemo(() => {
    const werte = options.map((o) => optionswert(o.label)).filter(Boolean);
    return new Set(werte).size !== werte.length;
  }, [options]);
  const optionLeer = options.some((option) => optionswert(option.label) === "");

  function emit() {
    if (optionLeer) {
      setOptionenGeprueft(true);
      return;
    }
    onChange({
      label,
      hilfetext,
      pflichtfeld,
      optional_in_einfach: optionalInEinfach,
      config,
      uebernahme,
      options: options.map((option) => ({ ...option, wert: optionswert(option.label) })),
    });
  }

  function setConfigWert(key: keyof FeldKonfiguration, v: unknown) {
    setConfig((c) => {
      const next = { ...c };
      if (v === "" || v === null || v === undefined) delete next[key];
      else (next as Record<string, unknown>)[key] = v;
      return next;
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{FELDTYP_LABELS[feld.typ]}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <Label htmlFor="f-label">Bezeichnung</Label>
          <Input
            id="f-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="f-help">Hilfetext (optional)</Label>
          <Input
            id="f-help"
            value={hilfetext}
            onChange={(e) => setHilfetext(e.target.value)}
          />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={pflichtfeld}
            onChange={(e) => setPflichtfeld(e.target.checked)}
          />
          Pflichtfeld
        </label>

        {!pflichtfeld && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={optionalInEinfach}
              onChange={(e) => setOptionalInEinfach(e.target.checked)}
            />
            In Erweitert-Modus zusätzlich anzeigen
          </label>
        )}

        <div>
          <Label htmlFor="f-uebernahme">Übernahme-Zuordnung (optional)</Label>
          <select
            id="f-uebernahme"
            value={uebernahme ?? ""}
            onChange={(e) =>
              setUebernahme((e.target.value || null) as UebernahmeFeld | null)
            }
            className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
          >
            <option value="">Keine Übernahme</option>
            {UEBERNAHME_FELDER.map((u) => (
              <option key={u} value={u}>
                {UEBERNAHME_LABELS[u]}
              </option>
            ))}
          </select>
        </div>

        <TypKonfiguration
          typ={feld.typ}
          config={config}
          setConfigWert={setConfigWert}
        />

        {hatOptionen(feld.typ) && (
          <div>
            <Label>Optionen</Label>
            <p className="mb-2 text-xs text-[var(--color-muted-foreground)]">
              Jede Zeile ist eine auswählbare Kachel. Geben Sie nur den Text ein, den Kunden sehen sollen.
            </p>
            <div className="space-y-2">
              {options.map((o, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Input
                    placeholder="z. B. Haus"
                    value={o.label}
                    onChange={(e) => {
                      const next = [...options];
                      next[i] = { ...o, label: e.target.value };
                      setOptions(next);
                    }}
                  />
                  <button
                    type="button"
                    aria-label="Option entfernen"
                    onClick={() => setOptions(options.filter((_, j) => j !== i))}
                    className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => {
                setOptionenGeprueft(false);
                setOptions([...options, { label: "", wert: "" }]);
              }}
            >
              <Plus size={14} /> Option
            </Button>
            {(optionDoppelteWerte || (optionLeer && optionenGeprueft)) && (
              <Alert variant="danger" className="mt-2">
                {optionLeer
                  ? "Jede Option braucht eine Bezeichnung."
                  : "Zwei Optionen haben dieselbe Bezeichnung. Jede Bezeichnung muss eindeutig sein."}
              </Alert>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="outline" onClick={onAbbrechen}>
            Abbrechen
          </Button>
          <Button
            onClick={emit}
            disabled={label.trim() === "" || optionDoppelteWerte || optionLeer}
          >
            Übernehmen
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function optionswert(label: string): string {
  return label.trim().toLocaleLowerCase("de-DE")
    .replaceAll("ä", "ae").replaceAll("ö", "oe").replaceAll("ü", "ue").replaceAll("ß", "ss")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function TypKonfiguration({
  typ,
  config,
  setConfigWert,
}: {
  typ: FormularFeldDraft["typ"];
  config: FeldKonfiguration;
  setConfigWert: (key: keyof FeldKonfiguration, v: unknown) => void;
}) {
  if (typ === "text" || typ === "mehrzeilig") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="c-max">Max. Länge (optional)</Label>
          <Input
            id="c-max"
            type="number"
            value={config.maxLaenge ?? ""}
            onChange={(e) =>
              setConfigWert("maxLaenge", e.target.value ? Number(e.target.value) : "")
            }
          />
        </div>
        <div>
          <Label htmlFor="c-regex">RegEx (optional)</Label>
          <Input
            id="c-regex"
            value={config.regex ?? ""}
            onChange={(e) => setConfigWert("regex", e.target.value)}
          />
        </div>
      </div>
    );
  }
  if (typ === "zahl") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="c-min">Minimum</Label>
          <Input
            id="c-min"
            type="number"
            value={config.min ?? ""}
            onChange={(e) =>
              setConfigWert("min", e.target.value ? Number(e.target.value) : "")
            }
          />
        </div>
        <div>
          <Label htmlFor="c-maxn">Maximum</Label>
          <Input
            id="c-maxn"
            type="number"
            value={config.max ?? ""}
            onChange={(e) =>
              setConfigWert("max", e.target.value ? Number(e.target.value) : "")
            }
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={config.ganzzahl ?? false}
            onChange={(e) => setConfigWert("ganzzahl", e.target.checked)}
          />
          Nur ganze Zahlen
        </label>
      </div>
    );
  }
  if (typ === "datum") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label htmlFor="c-dmin">Frühestens</Label>
          <Input
            id="c-dmin"
            type="date"
            value={config.minDatum ?? ""}
            onChange={(e) => setConfigWert("minDatum", e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="c-dmax">Spätestens</Label>
          <Input
            id="c-dmax"
            type="date"
            value={config.maxDatum ?? ""}
            onChange={(e) => setConfigWert("maxDatum", e.target.value)}
          />
        </div>
      </div>
    );
  }
  if (typ === "upload") {
    return (
      <div>
        <Label htmlFor="c-an">Maximale Anzahl Dateien</Label>
        <Input
          id="c-an"
          type="number"
          value={config.maxAnzahl ?? ""}
          onChange={(e) =>
            setConfigWert("maxAnzahl", e.target.value ? Number(e.target.value) : "")
          }
        />
      </div>
    );
  }
  return null;
}
