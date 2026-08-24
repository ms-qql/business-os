"use client";

import * as React from "react";
import { Plus, Trash2, ArrowUp, ArrowDown } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { updateFeld, type FeldUpdate } from "@/lib/api/formulare";
import {
  AUSWAHL_TYPEN,
  feldTypLabel,
  UEBERNAHME_OPTIONEN,
  type Feld,
} from "@/lib/schemas/formular";

const LEERE_OPTION = { label: "", wert: "" };

export function FeldDialog({
  formularId,
  schrittId,
  feld,
  draftRevision,
  onClose,
  onSaved,
}: {
  formularId: string;
  schrittId: string;
  feld: Feld;
  draftRevision: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [label, setLabel] = React.useState(feld.label);
  const [hilfetext, setHilfetext] = React.useState(feld.hilfetext ?? "");
  const [pflichtfeld, setPflichtfeld] = React.useState(feld.pflichtfeld);
  const [optionalInEinfach, setOptionalInEinfach] = React.useState(
    feld.optional_in_einfach,
  );
  const [uebernahme, setUebernahme] = React.useState<string>(
    feld.uebernahme ?? "",
  );
  const [min, setMin] = React.useState<string>(feld.min != null ? String(feld.min) : "");
  const [max, setMax] = React.useState<string>(feld.max != null ? String(feld.max) : "");
  const [ganzzahl, setGanzzahl] = React.useState<boolean>(!!feld.ganzzahl);
  const [maxlaenge, setMaxlaenge] = React.useState<string>(
    feld.maxlaenge != null ? String(feld.maxlaenge) : "",
  );
  const [regExp, setRegExp] = React.useState(feld.reg_exp ?? "");
  const [datumMin, setDatumMin] = React.useState(feld.datum_min ?? "");
  const [datumMax, setDatumMax] = React.useState(feld.datum_max ?? "");
  const [maxAnzahl, setMaxAnzahl] = React.useState<string>(
    feld.max_anzahl != null ? String(feld.max_anzahl) : "1",
  );
  const [optionen, setOptionen] = React.useState<{ label: string; wert: string }[]>(
    (feld.optionen ?? []).map((o) => ({ label: o.label, wert: o.wert })),
  );

  const [fehler, setFehler] = React.useState<string | null>(null);
  const [speichert, setSpeichert] = React.useState(false);

  const istAuswahl = AUSWAHL_TYPEN.includes(feld.typ);
  const istZahl = feld.typ === "zahl";
  const istText = feld.typ === "text";
  const istMehrzeilig = feld.typ === "mehrzeilig";
  const istDatum = feld.typ === "datum";
  const istUpload = feld.typ === "upload";

  function optionFehler(): string | null {
    if (!istAuswahl) return null;
    if (optionen.length === 0) return "Mindestens eine Option ist erforderlich.";
    if (optionen.some((o) => !o.label.trim() || !o.wert.trim())) {
      return "Jede Option benötigt eine sichtbare Bezeichnung und einen gespeicherten Wert.";
    }
    const werte = optionen.map((o) => o.wert.trim());
    if (new Set(werte).size !== werte.length) {
      return "Gespeicherte Werte dürfen nicht doppelt vorkommen.";
    }
    return null;
  }

  async function onSpeichern() {
    setFehler(null);
    const oFehler = optionFehler();
    if (!label.trim()) {
      setFehler("Bitte geben Sie eine Bezeichnung an.");
      return;
    }
    if (oFehler) {
      setFehler(oFehler);
      return;
    }

    const update: FeldUpdate = {
      label: label.trim(),
      hilfetext: hilfetext.trim() || null,
      pflichtfeld,
      optional_in_einfach: optionalInEinfach,
      uebernahme: uebernahme ? (uebernahme as FeldUpdate["uebernahme"]) : null,
    };
    if (istText || istMehrzeilig) {
      update.maxlaenge = maxlaenge ? Number(maxlaenge) : null;
      update.reg_exp = regExp.trim() || null;
    }
    if (istZahl) {
      update.min = min ? Number(min) : null;
      update.max = max ? Number(max) : null;
      update.ganzzahl = ganzzahl;
    }
    if (istDatum) {
      update.datum_min = datumMin || null;
      update.datum_max = datumMax || null;
    }
    if (istUpload) {
      update.max_anzahl = maxAnzahl ? Number(maxAnzahl) : null;
    }
    if (istAuswahl) {
      update.optionen = optionen.map((o) => ({
        label: o.label.trim(),
        wert: o.wert.trim(),
      }));
    }

    setSpeichert(true);
    try {
      await updateFeld(formularId, schrittId, feld.id, update, draftRevision);
      onSaved();
      onClose();
    } catch (err) {
      setFehler(
        err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.",
      );
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <Dialog
      open
      onOpenChange={(o) => !o && onClose()}
      title={`Feld bearbeiten — ${feldTypLabel(feld.typ)}`}
      description="Bezeichnung, Pflichtfeld und Hilfetext sind für alle Felder möglich."
    >
      <div className="space-y-4">
        <div>
          <Label htmlFor="f-label">Bezeichnung *</Label>
          <Input
            id="f-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </div>

        <div>
          <Label htmlFor="f-hilfe">Hilfetext (optional)</Label>
          <Textarea
            id="f-hilfe"
            value={hilfetext}
            onChange={(e) => setHilfetext(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap gap-4">
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
              In „Erweitert"-Stufe anzeigen
            </label>
          )}
        </div>

        {/* Typkonfiguration */}
        {istText || istMehrzeilig ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="f-maxlen">Maximale Länge (optional)</Label>
              <Input
                id="f-maxlen"
                type="number"
                min={1}
                value={maxlaenge}
                onChange={(e) => setMaxlaenge(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="f-regexp">Regulärer Ausdruck (optional)</Label>
              <Input
                id="f-regexp"
                value={regExp}
                placeholder="z. B. ^[0-9+ ]+$"
                onChange={(e) => setRegExp(e.target.value)}
              />
            </div>
          </div>
        ) : null}

        {istZahl ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label htmlFor="f-min">Minimum (optional)</Label>
              <Input id="f-min" type="number" value={min} onChange={(e) => setMin(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="f-max">Maximum (optional)</Label>
              <Input id="f-max" type="number" value={max} onChange={(e) => setMax(e.target.value)} />
            </div>
            <label className="flex items-end gap-2 pb-2 text-sm">
              <input type="checkbox" checked={ganzzahl} onChange={(e) => setGanzzahl(e.target.checked)} />
              Ganzzahl
            </label>
          </div>
        ) : null}

        {istDatum ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="f-dmin">Frühestes Datum (optional)</Label>
              <Input id="f-dmin" type="date" value={datumMin} onChange={(e) => setDatumMin(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="f-dmax">Spätestes Datum (optional)</Label>
              <Input id="f-dmax" type="date" value={datumMax} onChange={(e) => setDatumMax(e.target.value)} />
            </div>
          </div>
        ) : null}

        {istUpload ? (
          <div>
            <Label htmlFor="f-maxanz">Maximale Anzahl Dateien</Label>
            <Input
              id="f-maxanz"
              type="number"
              min={1}
              value={maxAnzahl}
              onChange={(e) => setMaxAnzahl(e.target.value)}
            />
          </div>
        ) : null}

        {/* Auswahloptionen */}
        {istAuswahl ? (
          <div>
            <Label>Optionen (sichtbare Bezeichnung + gespeicherter Wert)</Label>
            <div className="mt-1 space-y-2">
              {optionen.map((o, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Input
                    aria-label="Bezeichnung"
                    placeholder="Bezeichnung"
                    value={o.label}
                    onChange={(e) => {
                      const n = [...optionen];
                      n[i].label = e.target.value;
                      setOptionen(n);
                    }}
                  />
                  <Input
                    aria-label="Wert"
                    placeholder="Wert"
                    value={o.wert}
                    onChange={(e) => {
                      const n = [...optionen];
                      n[i].wert = e.target.value;
                      setOptionen(n);
                    }}
                  />
                  <div className="flex items-center">
                    <button
                      type="button"
                      aria-label="Option nach oben"
                      disabled={i === 0}
                      onClick={() => {
                        const n = [...optionen];
                        [n[i - 1], n[i]] = [n[i], n[i - 1]];
                        setOptionen(n);
                      }}
                      className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                    >
                      <ArrowUp size={14} />
                    </button>
                    <button
                      type="button"
                      aria-label="Option nach unten"
                      disabled={i === optionen.length - 1}
                      onClick={() => {
                        const n = [...optionen];
                        [n[i + 1], n[i]] = [n[i], n[i + 1]];
                        setOptionen(n);
                      }}
                      className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                    >
                      <ArrowDown size={14} />
                    </button>
                    <button
                      type="button"
                      aria-label="Option entfernen"
                      onClick={() => setOptionen(optionen.filter((_, j) => j !== i))}
                      className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setOptionen([...optionen, { ...LEERE_OPTION }])}
              >
                <Plus size={14} /> Option hinzufügen
              </Button>
            </div>
          </div>
        ) : null}

        {/* Übernahme-Zuordnung für Text/Adresse/Auswahl */}
        {feld.typ === "text" || feld.typ === "adresse" || istAuswahl ? (
          <div>
            <Label htmlFor="f-uebernahme">Übernahme in Vorgang (optional)</Label>
            <select
              id="f-uebernahme"
              value={uebernahme}
              onChange={(e) => setUebernahme(e.target.value)}
              className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
            >
              <option value="">Keine Zuordnung</option>
              {UEBERNAHME_OPTIONEN.map((o) => (
                <option key={o.wert} value={o.wert}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {fehler && <Alert variant="danger">{fehler}</Alert>}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Abbrechen
          </Button>
          <Button onClick={onSpeichern} disabled={speichert}>
            {speichert ? "Speichert …" : "Speichern"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
