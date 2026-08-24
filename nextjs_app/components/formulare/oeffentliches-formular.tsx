"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { X, ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  getOeffentlichesFormular,
  istUploadErlaubt,
  OeffentlichesFormularError,
  sichtbareFelder,
  submitEinsendung,
  uploadFormularDatei,
  type FeldWert,
} from "@/lib/api/oeffentliche-formulare";
import {
  MAX_UPLOAD_BYTES,
  UPLOAD_MIME,
  type PublicFeld,
  type PublicFormular,
  type PublicSchritt,
} from "@/lib/schemas/formular";
import { useSiteBase } from "@/app/site/site-context";

type WerteMap = Record<string, FeldWert>;

const LEER_WERT = (feldId: string): FeldWert => ({ feld_id: feldId });

function wertFuer(werte: WerteMap, feld: PublicFeld): FeldWert {
  return werte[feld.id] ?? LEER_WERT(feld.id);
}

export function OeffentlichesFormular({ publicId }: { publicId: string }) {
  const router = useRouter();
  const base = useSiteBase();
  const uebermittlungskennung = React.useRef(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`,
  ).current;
  const clientStart = React.useRef(new Date().toISOString()).current;

  const [formular, setFormular] = React.useState<PublicFormular | null>(null);
  const [laden, setLaden] = React.useState(true);
  const [ladefehler, setLadefehler] = React.useState<string | null>(null);
  const [nichtGefunden, setNichtGefunden] = React.useState(false);

  const [schrittIndex, setSchrittIndex] = React.useState(0);
  const [werte, setWerte] = React.useState<WerteMap>({});
  const [honeypot, setHoneypot] = React.useState("");
  const [fehler, setFehler] = React.useState<Record<string, string>>({});
  const [sendet, setSendet] = React.useState(false);
  const [sendefehler, setSendefehler] = React.useState<string | null>(null);
  const [erfolg, setErfolg] = React.useState(false);

  const uploadsLaufend = React.useRef(new Map<string, string>()).current;
  const [uploadFehler, setUploadFehler] = React.useState<Record<string, string>>({});

  React.useEffect(() => {
    let aktiv = true;
    setLaden(true);
    getOeffentlichesFormular(publicId)
      .then((f) => aktiv && setFormular(f))
      .catch((err) => {
        if (!aktiv) return;
        if (err instanceof OeffentlichesFormularError && err.status === 404) {
          setNichtGefunden(true);
        } else {
          setLadefehler(
            "Das Formular konnte nicht geladen werden. Bitte versuchen Sie es später erneut.",
          );
        }
      })
      .finally(() => aktiv && setLaden(false));
    return () => {
      aktiv = false;
    };
  }, [publicId]);

  function setWert(feld: PublicFeld, teil: Partial<FeldWert>) {
    setWerte((prev) => ({
      ...prev,
      [feld.id]: { ...LEER_WERT(feld.id), ...prev[feld.id], ...teil },
    }));
  }

  function schrittGueltig(schritt: PublicSchritt): Record<string, string> {
    const fehlerProFeld: Record<string, string> = {};
    const sichtbar = sichtbareFelder(schritt, formular?.modus ?? "einfach");
    for (const f of sichtbar.felder) {
      const w = wertFuer(werte, f);
      const pflicht = f.pflichtfeld || f.typ === "consent";
      if (f.typ === "consent") {
        if (!w.wert) fehlerProFeld[f.id] = "Bitte stimmen Sie der Datenschutzerklärung zu.";
        continue;
      }
      if (f.typ === "adresse") {
        if (pflicht && !w.wert) fehlerProFeld[f.id] = "Bitte geben Sie Ihre Adresse an.";
        continue;
      }
      if (f.typ === "upload") {
        const ids = w.upload_ids ?? [];
        if (pflicht && ids.length === 0) {
          fehlerProFeld[f.id] = "Bitte laden Sie mindestens eine Datei hoch.";
        }
        continue;
      }
      if (f.typ === "zahl") {
        if (pflicht && w.zahl == null) {
          fehlerProFeld[f.id] = "Bitte geben Sie eine Zahl an.";
        } else if (w.zahl != null) {
          if (f.min != null && w.zahl < f.min) fehlerProFeld[f.id] = `Mindestens ${f.min}.`;
          if (f.max != null && w.zahl > f.max) fehlerProFeld[f.id] = `Höchstens ${f.max}.`;
        }
        continue;
      }
      if (f.typ === "datum") {
        if (pflicht && !w.datum) fehlerProFeld[f.id] = "Bitte wählen Sie ein Datum.";
        continue;
      }
      if (f.typ === "dropdown" || f.typ === "kachel" || f.typ === "radio") {
        const gewaehlt = w.werte && w.werte.length > 0;
        if (pflicht && !gewaehlt) fehlerProFeld[f.id] = "Bitte treffen Sie eine Auswahl.";
        continue;
      }
      // text / mehrzeilig
      const text = w.wert ?? "";
      if (pflicht && !text.trim()) {
        fehlerProFeld[f.id] = "Bitte füllen Sie dieses Feld aus.";
      } else if (f.maxlaenge && text.length > f.maxlaenge) {
        fehlerProFeld[f.id] = `Höchstens ${f.maxlaenge} Zeichen.`;
      } else if (f.reg_exp && text && !new RegExp(f.reg_exp).test(text)) {
        fehlerProFeld[f.id] = "Die Eingabe hat ein ungültiges Format.";
      }
    }
    return fehlerProFeld;
  }

  function aktuellerSchritt(): PublicSchritt | null {
    if (!formular) return null;
    return formular.schritte[schrittIndex] ?? null;
  }

  function weiter() {
    const s = aktuellerSchritt();
    if (!s) return;
    const f = schrittGueltig(s);
    setFehler(f);
    if (Object.keys(f).length === 0) {
      setSchrittIndex((i) => Math.min(i + 1, (formular?.schritte.length ?? 1) - 1));
      if (typeof window !== "undefined") window.scrollTo({ top: 0 });
    }
  }

  function zurueck() {
    setFehler({});
    setSchrittIndex((i) => Math.max(i - 1, 0));
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
  }

  async function onUpload(feld: PublicFeld, dateien: FileList | null) {
    if (!dateien || dateien.length === 0) return;
    setUploadFehler((prev) => ({ ...prev, [feld.id]: "" }));
    const max = feld.max_anzahl ?? 1;
    const aktuelle = wertFuer(werte, feld).upload_ids ?? [];
    const verbleibend = max - aktuelle.length;
    const auswahl = Array.from(dateien).slice(0, Math.max(verbleibend, 0));

    for (const datei of auswahl) {
      const pruef = istUploadErlaubt(datei, MAX_UPLOAD_BYTES, UPLOAD_MIME);
      if (pruef) {
        setUploadFehler((prev) => ({ ...prev, [feld.id]: pruef }));
        return;
      }
    }

    try {
      const neueIds: string[] = [...aktuelle];
      for (const datei of auswahl) {
        const res = await uploadFormularDatei(publicId, datei, feld.id, uebermittlungskennung);
        neueIds.push(res.upload_id);
        uploadsLaufend.set(res.upload_id, datei.name);
      }
      setWert(feld, { upload_ids: neueIds });
    } catch {
      setUploadFehler((prev) => ({
        ...prev,
        [feld.id]: "Ein Datei-Upload ist fehlgeschlagen. Bitte versuchen Sie es erneut.",
      }));
    }
  }

  function uploadEntfernen(feld: PublicFeld, id: string) {
    const aktuelle = wertFuer(werte, feld).upload_ids ?? [];
    setWert(feld, { upload_ids: aktuelle.filter((x) => x !== id) });
  }

  async function absenden() {
    if (!formular) return;
    // Gesamte Formularvalidierung über alle Schritte.
    const alleFehler: Record<string, string> = {};
    for (const s of formular.schritte) {
      Object.assign(alleFehler, schrittGueltig(s));
    }
    setFehler(alleFehler);
    if (Object.keys(alleFehler).length > 0) {
      // Zum ersten fehlerhaften Schritt springen.
      const idx = formular.schritte.findIndex((s) => {
        const f = sichtbareFelder(s, formular.modus);
        return f.felder.some((ff) => alleFehler[ff.id]);
      });
      if (idx >= 0) setSchrittIndex(idx);
      if (typeof window !== "undefined") window.scrollTo({ top: 0 });
      return;
    }

    const feldwerte: FeldWert[] = Object.values(werte);
    setSendet(true);
    setSendefehler(null);
    try {
      const res = await submitEinsendung(publicId, {
        uebermittlungskennung,
        client_start: clientStart,
        honeypot,
        werte: feldwerte,
      });
      if (res.status === "spam") {
        // Spam wird serverseitig nachvollziehbar markiert, kein regulärer Vorgang.
        // Für den Absender wirkt es wie ein erfolgreicher Versand.
        setErfolg(true);
      } else {
        setErfolg(true);
      }
    } catch (err) {
      setSendefehler(
        err instanceof OeffentlichesFormularError
          ? err.message
          : "Die Einsendung konnte nicht gesendet werden. Bitte versuchen Sie es erneut.",
      );
      setSendet(false);
    }
  }

  if (laden) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center text-sm text-[var(--color-muted-foreground)]">
        Wird geladen …
      </div>
    );
  }

  if (nichtGefunden) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <Alert variant="warning">
          Dieses Formular ist derzeit nicht verfügbar. Es wurde möglicherweise noch
          nicht veröffentlicht.
        </Alert>
      </div>
    );
  }

  if (ladefehler) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12 text-center">
        <Alert variant="danger">{ladefehler}</Alert>
        <Button
          className="mt-4"
          variant="outline"
          onClick={() => window.location.reload()}
        >
          Erneut versuchen
        </Button>
      </div>
    );
  }

  if (erfolg) {
    return (
      <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-20 text-center">
        <CheckCircle2 size={48} className="text-[var(--color-success)]" />
        <h1 className="mt-4 text-2xl font-semibold text-[var(--color-foreground)]">
          Vielen Dank. Ihre Angaben sind eingegangen.
        </h1>
        <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
          Wir melden uns zeitnah bei Ihnen.
        </p>
        <a href={base || "/"} className="mt-6">
          <Button variant="outline">Zur Startseite</Button>
        </a>
      </div>
    );
  }

  const s = aktuellerSchritt();
  if (!s || !formular) return null;
  const sichtbar = sichtbareFelder(s, formular.modus);
  const istLetzter = schrittIndex === formular.schritte.length - 1;
  const gesamt = formular.schritte.length;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>{formular.name}</CardTitle>
          <CardDescription>
            Schritt {schrittIndex + 1} von {gesamt}
            {formular.modus === "erweitert" && " · Erweiterte Angaben"}
          </CardDescription>
          {/* Fortschrittsanzeige */}
          <div className="mt-3 flex gap-1.5" aria-hidden>
            {formular.schritte.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 flex-1 rounded-full ${
                  i <= schrittIndex ? "bg-[var(--color-brand)]" : "bg-[var(--color-border)]"
                }`}
              />
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <h2 className="mb-4 text-lg font-semibold">{s.titel || `Schritt ${schrittIndex + 1}`}</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (istLetzter) void absenden();
              else weiter();
            }}
            noValidate
            className="space-y-4"
          >
            {sichtbar.felder.map((f) => (
              <FeldRenderer
                key={f.id}
                feld={f}
                wert={wertFuer(werte, f)}
                fehler={fehler[f.id]}
                onChange={(teil) => setWert(f, teil)}
                onUpload={(files) => void onUpload(f, files)}
                onUploadRemove={(id) => uploadEntfernen(f, id)}
                uploadFehler={uploadFehler[f.id]}
              />
            ))}

            {/* Honeypot: unsichtbar für Menschen, von Bots gefüllt. */}
            <div aria-hidden className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
              <label>
                Bitte hier nicht ausfüllen
                <input
                  tabIndex={-1}
                  autoComplete="off"
                  value={honeypot}
                  onChange={(e) => setHoneypot(e.target.value)}
                />
              </label>
            </div>

            {sendefehler && <Alert variant="danger">{sendefehler}</Alert>}

            <div className="flex items-center justify-between pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={zurueck}
                disabled={schrittIndex === 0 || sendet}
                className={schrittIndex === 0 ? "invisible" : ""}
              >
                <ArrowLeft size={16} /> Zurück
              </Button>
              <Button type="submit" size="lg" disabled={sendet}>
                {sendet ? (
                  "Wird gesendet …"
                ) : istLetzter ? (
                  "Absenden"
                ) : (
                  <>
                    Weiter <ArrowRight size={16} />
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function FeldRenderer({
  feld,
  wert,
  fehler,
  onChange,
  onUpload,
  onUploadRemove,
  uploadFehler,
}: {
  feld: PublicFeld;
  wert: FeldWert;
  fehler?: string;
  onChange: (teil: Partial<FeldWert>) => void;
  onUpload: (dateien: FileList | null) => void;
  onUploadRemove: (id: string) => void;
  uploadFehler?: string;
}) {
  const id = `f-${feld.id}`;
  const labelNode = (
    <Label htmlFor={id}>
      {feld.label}
      {(feld.pflichtfeld || feld.typ === "consent") && (
        <span className="text-[var(--color-danger)]"> *</span>
      )}
    </Label>
  );
  const fehlerNode = fehler ? (
    <Alert variant="danger" className="mt-1">
      {fehler}
    </Alert>
  ) : null;

  switch (feld.typ) {
    case "text":
    case "mehrzeilig":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          {feld.typ === "mehrzeilig" ? (
            <Textarea
              id={id}
              value={wert.wert ?? ""}
              maxLength={feld.maxlaenge ?? undefined}
              onChange={(e) => onChange({ wert: e.target.value })}
            />
          ) : (
            <Input
              id={id}
              type={feld.reg_exp ? "text" : "text"}
              value={wert.wert ?? ""}
              maxLength={feld.maxlaenge ?? undefined}
              onChange={(e) => onChange({ wert: e.target.value })}
            />
          )}
          {fehlerNode}
        </div>
      );

    case "zahl":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <Input
            id={id}
            type="number"
            inputMode="decimal"
            min={feld.min ?? undefined}
            max={feld.max ?? undefined}
            step={feld.ganzzahl ? 1 : "any"}
            value={wert.zahl ?? ""}
            onChange={(e) =>
              onChange({ zahl: e.target.value === "" ? null : Number(e.target.value) })
            }
          />
          {fehlerNode}
        </div>
      );

    case "datum":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <Input
            id={id}
            type="date"
            min={feld.datum_min ?? undefined}
            max={feld.datum_max ?? undefined}
            value={wert.datum ?? ""}
            onChange={(e) => onChange({ datum: e.target.value || null })}
          />
          {fehlerNode}
        </div>
      );

    case "adresse":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <Input
            id={id}
            value={wert.wert ?? ""}
            placeholder="Straße, Hausnummer, PLZ, Ort"
            onChange={(e) => onChange({ wert: e.target.value })}
          />
          {fehlerNode}
        </div>
      );

    case "dropdown":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <select
            id={id}
            value={wert.werte?.[0] ?? ""}
            onChange={(e) => onChange({ werte: e.target.value ? [e.target.value] : [] })}
            className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
          >
            <option value="">Bitte wählen …</option>
            {feld.optionen.map((o) => (
              <option key={o.wert} value={o.wert}>
                {o.label}
              </option>
            ))}
          </select>
          {fehlerNode}
        </div>
      );

    case "radio":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <div className="space-y-1.5">
            {feld.optionen.map((o) => (
              <label key={o.wert} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name={id}
                  value={o.wert}
                  checked={wert.werte?.[0] === o.wert}
                  onChange={() => onChange({ werte: [o.wert] })}
                />
                {o.label}
              </label>
            ))}
          </div>
          {fehlerNode}
        </div>
      );

    case "kachel":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {feld.optionen.map((o) => {
              const aktiv = wert.werte?.[0] === o.wert;
              return (
                <button
                  type="button"
                  key={o.wert}
                  onClick={() => onChange({ werte: aktiv ? [] : [o.wert] })}
                  aria-pressed={aktiv}
                  className={`rounded-[var(--radius-md)] border p-3 text-sm font-medium ${
                    aktiv
                      ? "border-[var(--color-brand)] bg-[var(--color-surface-muted)]"
                      : "border-[var(--color-border)]"
                  }`}
                >
                  {o.label}
                </button>
              );
            })}
          </div>
          {fehlerNode}
        </div>
      );

    case "upload":
      return (
        <div>
          {labelNode}
          {feld.hilfetext && (
            <p className="mb-1 text-xs text-[var(--color-muted-foreground)]">{feld.hilfetext}</p>
          )}
          <input
            id={id}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            multiple
            onChange={(e) => onUpload(e.target.files)}
            className="block w-full text-sm text-[var(--color-muted-foreground)] file:mr-3 file:rounded-[var(--radius-md)] file:border-0 file:bg-[var(--color-surface-muted)] file:px-3 file:py-2 file:text-sm file:font-medium"
          />
          {uploadFehler && <Alert variant="danger" className="mt-1">{uploadFehler}</Alert>}
          {(wert.upload_ids ?? []).length > 0 && (
            <ul className="mt-2 space-y-1">
              {(wert.upload_ids ?? []).map((uid) => (
                <li
                  key={uid}
                  className="flex items-center justify-between rounded-[var(--radius-md)] bg-[var(--color-surface-muted)] px-3 py-1.5 text-sm"
                >
                  <span className="truncate">{uploadsNameFallback(uid)}</span>
                  <button
                    type="button"
                    onClick={() => onUploadRemove(uid)}
                    aria-label="Datei entfernen"
                    className="text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
                  >
                    <X size={16} />
                  </button>
                </li>
              ))}
            </ul>
          )}
          {fehlerNode}
        </div>
      );

    case "consent":
      return (
        <div>
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={!!wert.wert}
              onChange={(e) => onChange({ wert: e.target.checked ? "ja" : "" })}
              className="mt-0.5"
            />
            <span>
              {feld.label}
              <span className="text-[var(--color-danger)]"> *</span>
              {feld.hilfetext && (
                <span className="block text-xs text-[var(--color-muted-foreground)]">
                  {feld.hilfetext}
                </span>
              )}
            </span>
          </label>
          {fehlerNode}
        </div>
      );

    default:
      return null;
  }
}

/** Dateinamen sind nach Upload nicht mehr im Browser bekannt — nur die ID anzeigen. */
function uploadsNameFallback(id: string): string {
  return `Datei (${id.slice(0, 8)}…)`;
}
