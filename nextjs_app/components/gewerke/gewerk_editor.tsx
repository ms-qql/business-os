"use client";

import * as React from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { formatEuro, formatProzent } from "@/lib/format";
import {
  addGewerk,
  updateGewerk,
  type GewerkDetail,
  type GewerkKategorie,
  type KostenzeileInput,
  type Kostenart,
  type GewerkKalkulationsart,
  KOSTENART_LABELS,
  KALKULATIONSART_LABELS,
} from "@/lib/api/gewerke";

const SERVER_FEHLER = "Keine Verbindung zum Server. Änderungen wurden nicht gespeichert.";

/** Spiegelt die serverseitige Regel VK = EK + (EK × Zuschlag/100) auf 2 Nachkommastellen. */
function zeilenVk(ek: number, menge: number, zuschlag: number): number {
  const vk = ek * (1 + zuschlag / 100);
  const gesamt = vk * menge;
  return Math.round(gesamt * 100) / 100;
}

function gewerkPreis(zeilen: KostenzeileInput[]): number {
  return Math.round(
    zeilen.reduce((s, z) => s + zeilenVk(z.ek_einzelpreis, z.menge, z.zuschlag_prozent), 0) *
      100,
  ) / 100;
}

function neueZeile(): KostenzeileInput {
  return {
    kostenart: "lohn",
    menge: 1,
    einheit: "Std.",
    ek_einzelpreis: 0,
    zuschlag_prozent: 0,
  };
}

function zeileAusDetail(z: GewerkDetail["kostenzeilen"][number]): KostenzeileInput {
  return {
    kostenart: z.kostenart,
    menge: z.menge,
    einheit: z.einheit,
    ek_einzelpreis: z.ek_einzelpreis,
    zuschlag_prozent: z.zuschlag_prozent,
  };
}

const KOSTENARTEN: Kostenart[] = ["lohn", "material", "fremdleistung", "sonstiges_geraete"];

/** Editor für ein Gewerk (neu oder bestehend). Schreibt über /gewerke. */
export function GewerkEditor({
  gewerk,
  kategorien,
  onGespeichert,
  onAbbrechen,
}: {
  gewerk: GewerkDetail | null;
  kategorien: GewerkKategorie[];
  onGespeichert: (id: string) => void;
  onAbbrechen: () => void;
}) {
  const [bezeichnung, setBezeichnung] = React.useState(gewerk?.bezeichnung ?? "");
  const [lang, setLang] = React.useState(gewerk?.langbeschreibung ?? "");
  const [einheit, setEinheit] = React.useState(gewerk?.einheit ?? "Stück");
  const [kalkulationsart, setKalkulationsart] = React.useState<GewerkKalkulationsart>(
    gewerk?.kalkulationsart ?? "je_einheit",
  );
  const [steuersatz, setSteuersatz] = React.useState<number>(gewerk?.steuersatz ?? 19);
  const [kategorieId, setKategorieId] = React.useState<string | null>(gewerk?.kategorie_id ?? null);
  const [zeilen, setZeilen] = React.useState<KostenzeileInput[]>(
    gewerk ? gewerk.kostenzeilen.map(zeileAusDetail) : [neueZeile()],
  );

  const [fehler, setFehler] = React.useState<string | null>(null);
  const [warnung, setWarnung] = React.useState<string | null>(null);
  const [speichert, setSpeichert] = React.useState(false);

  const preis = gewerkPreis(zeilen);

  function zeileAendern(index: number, patch: Partial<KostenzeileInput>) {
    setZeilen((prev) => prev.map((z, i) => (i === index ? { ...z, ...patch } : z)));
  }

  function zeileHinzufuegen() {
    setZeilen((prev) => [...prev, neueZeile()]);
  }

  function zeileEntfernen(index: number) {
    setZeilen((prev) => prev.filter((_, i) => i !== index));
  }

  async function speichern(duplikatBestaetigt: boolean) {
    setFehler(null);
    setWarnung(null);

    if (!bezeichnung.trim()) {
      setFehler("Bezeichnung ist erforderlich.");
      return;
    }
    if (!einheit.trim()) {
      setFehler("Einheit ist erforderlich.");
      return;
    }
    if (!(steuersatz >= 0 && steuersatz <= 100)) {
      setFehler("Steuersatz muss zwischen 0 und 100 % liegen.");
      return;
    }
    if (zeilen.length === 0) {
      setFehler("Mindestens eine Kostenzeile ist erforderlich.");
      return;
    }
    for (const z of zeilen) {
      if (!(z.menge > 0)) {
        setFehler("Menge einer Kostenzeile muss größer als 0 sein.");
        return;
      }
      if (!(z.ek_einzelpreis > 0)) {
        setFehler("Einkaufspreis einer Kostenzeile muss größer als 0 sein.");
        return;
      }
      if (z.zuschlag_prozent < 0) {
        setFehler("Zuschlag darf nicht negativ sein.");
        return;
      }
    }
    // Duplikatprüfung: gleiche (Bezeichnung, Einheit) darf nicht zweimal vorkommen.
    const sig = (z: KostenzeileInput) =>
      `${z.kostenart}|${z.einheit}|${Math.round(z.ek_einzelpreis * 100)}|${Math.round(
        z.zuschlag_prozent * 100,
      )}`;
    const seen = new Set<string>();
    for (const z of zeilen) {
      const s = sig(z);
      if (seen.has(s)) {
        setFehler("Doppelte Kostenzeilen sind nicht erlaubt.");
        return;
      }
      seen.add(s);
    }

    const payload = {
      bezeichnung: bezeichnung.trim(),
      langbeschreibung: lang.trim() || null,
      einheit: einheit.trim(),
      kalkulationsart,
      steuersatz,
      kategorie_id: kategorieId,
      kostenzeilen: zeilen,
      duplikat_bestaetigt: duplikatBestaetigt || undefined,
    };

    setSpeichert(true);
    try {
      const ergebnis = gewerk
        ? await updateGewerk(gewerk.id, payload)
        : await addGewerk(payload);
      onGespeichert(ergebnis.id);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setWarnung(
          "Es existiert bereits ein Gewerk mit derselben Bezeichnung und Einheit. Trotzdem speichern?",
        );
      } else {
        setFehler(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
      }
    } finally {
      setSpeichert(false);
    }
  }

  return (
    <div className="space-y-5">
      {fehler && <Alert variant="danger">{fehler}</Alert>}
      {warnung && (
        <Alert variant="warning">
          <p>{warnung}</p>
          <div className="mt-2 flex gap-2">
            <Button size="sm" variant="danger" disabled={speichert} onClick={() => speichern(true)}>
              Trotzdem speichern
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setWarnung(null)}>
              Abbrechen
            </Button>
          </div>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label htmlFor="gw-bez">Bezeichnung</Label>
          <Input
            id="gw-bez"
            value={bezeichnung}
            onChange={(e) => setBezeichnung(e.target.value)}
            placeholder="z. B. Bad-Komplettsanierung"
          />
        </div>

        <div>
          <Label htmlFor="gw-kat">Kategorie</Label>
          <Select
            id="gw-kat"
            value={kategorieId ?? ""}
            onChange={(e) => setKategorieId(e.target.value || null)}
          >
            <option value="">— keine —</option>
            {kategorien.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="gw-einheit">Einheit</Label>
          <Input
            id="gw-einheit"
            value={einheit}
            onChange={(e) => setEinheit(e.target.value)}
            placeholder="Stück, Std., m² …"
          />
        </div>

        <div>
          <Label htmlFor="gw-art">Kalkulationsart</Label>
          <Select
            id="gw-art"
            value={kalkulationsart}
            onChange={(e) => setKalkulationsart(e.target.value as GewerkKalkulationsart)}
          >
            {(Object.keys(KALKULATIONSART_LABELS) as GewerkKalkulationsart[]).map((a) => (
              <option key={a} value={a}>
                {KALKULATIONSART_LABELS[a]}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="gw-steuersatz">Steuersatz (%)</Label>
          <Input
            id="gw-steuersatz"
            type="number"
            step="0.01"
            min="0"
            max="100"
            value={steuersatz}
            onChange={(e) => setSteuersatz(Number(e.target.value))}
          />
        </div>

        <div className="sm:col-span-2">
          <Label htmlFor="gw-lang">Langbeschreibung (optional)</Label>
          <Textarea
            id="gw-lang"
            rows={3}
            value={lang}
            onChange={(e) => setLang(e.target.value)}
          />
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[var(--color-foreground)]">Kostenzeilen</h3>
          <Button type="button" size="sm" variant="secondary" onClick={zeileHinzufuegen}>
            <Plus size={14} /> Zeile
          </Button>
        </div>

        <div className="space-y-2">
          <div className="hidden grid-cols-[1.1fr_0.7fr_0.7fr_1fr_0.7fr_0.8fr_auto] gap-2 px-1 text-xs font-medium text-[var(--color-muted-foreground)] sm:grid">
            <span>Kostenart</span>
            <span>Menge</span>
            <span>Einheit</span>
            <span>EK €</span>
            <span>Zuschlag %</span>
            <span>VK</span>
            <span />
          </div>
          {zeilen.map((z, i) => (
            <div
              key={i}
              className="grid grid-cols-2 gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/30 p-2 sm:grid-cols-[1.1fr_0.7fr_0.7fr_1fr_0.7fr_0.8fr_auto] sm:items-center"
            >
              <Select
                aria-label="Kostenart"
                value={z.kostenart}
                onChange={(e) => zeileAendern(i, { kostenart: e.target.value as Kostenart })}
              >
                {KOSTENARTEN.map((k) => (
                  <option key={k} value={k}>
                    {KOSTENART_LABELS[k]}
                  </option>
                ))}
              </Select>
              <Input
                aria-label="Menge"
                type="number"
                step="0.01"
                min="0"
                value={z.menge}
                onChange={(e) => zeileAendern(i, { menge: Number(e.target.value) })}
              />
              <Input
                aria-label="Einheit"
                value={z.einheit}
                onChange={(e) => zeileAendern(i, { einheit: e.target.value })}
              />
              <Input
                aria-label="Einkaufspreis"
                type="number"
                step="0.01"
                min="0"
                value={z.ek_einzelpreis}
                onChange={(e) => zeileAendern(i, { ek_einzelpreis: Number(e.target.value) })}
              />
              <Input
                aria-label="Zuschlag"
                type="number"
                step="0.01"
                min="0"
                value={z.zuschlag_prozent}
                onChange={(e) => zeileAendern(i, { zuschlag_prozent: Number(e.target.value) })}
              />
              <span className="px-1 text-right text-sm font-medium">
                {formatEuro(zeilenVk(z.ek_einzelpreis, z.menge, z.zuschlag_prozent))}
              </span>
              <button
                type="button"
                aria-label="Kostenzeile entfernen"
                onClick={() => zeileEntfernen(i)}
                className="rounded p-1 text-[var(--color-danger)] hover:bg-[var(--color-border)]"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {zeilen.length === 0 && (
            <p className="text-sm text-[var(--color-muted-foreground)]">
              Mindestens eine Kostenzeile ist erforderlich.
            </p>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3">
        <div className="text-sm">
          <span className="text-[var(--color-muted-foreground)]">
            Verkaufspreis ({KALKULATIONSART_LABELS[kalkulationsart]}):{" "}
          </span>
          <span className="font-semibold">{formatEuro(preis)}</span>
          <span className="ml-2 text-[var(--color-muted-foreground)]">
            zzgl. {formatProzent(steuersatz)} MwSt
          </span>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="secondary" onClick={onAbbrechen} disabled={speichert}>
            Abbrechen
          </Button>
          <Button type="button" onClick={() => speichern(false)} disabled={speichert}>
            {speichert ? "Speichert …" : gewerk ? "Speichern" : "Gewerk anlegen"}
          </Button>
        </div>
      </div>
    </div>
  );
}
