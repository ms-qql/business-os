"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ChevronLeft, ChevronRight, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import { getPublicFormular, uploadFormularDatei, submitEinsendung } from "@/lib/api/formulare";
import { FeldRenderer, feldSichtbar, type AdresseWert, type FeldWert } from "@/components/formulare/feld-renderer";
import type { OeffentlichesFeld, FormularSnapshot } from "@/lib/schemas/formular";

const MAX_DATEIGROESSE = 15 * 1024 * 1024; // 15 MB
const ERLAUBTE_TYPEN = ["image/jpeg", "image/png", "image/webp", "application/pdf"];

export default function PublicFormularPage() {
  const params = useParams<{ public_id: string }>();
  const publicId = params.public_id;
  const uebermittlungskennung = React.useRef(crypto.randomUUID()).current;
  const clientStartzeit = React.useRef(new Date().toISOString()).current;

  const [snapshot, setSnapshot] = React.useState<FormularSnapshot | null>(null);
  const [nichtVerfuegbar, setNichtVerfuegbar] = React.useState(false);
  const [ladeFehler, setLadeFehler] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const [schrittIndex, setSchrittIndex] = React.useState(0);
  const [werte, setWerte] = React.useState<Record<string, FeldWert>>({});
  const [dateien, setDateien] = React.useState<Record<string, File[]>>({});
  const [honeypot, setHoneypot] = React.useState("");
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [sendeFehler, setSendeFehler] = React.useState<string | null>(null);
  const [wirdGesendet, setWirdGesendet] = React.useState(false);
  const [gesendet, setGesendet] = React.useState(false);

  React.useEffect(() => {
    getPublicFormular(publicId)
      .then(setSnapshot)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNichtVerfuegbar(true);
        else setLadeFehler("Das Formular ist derzeit nicht erreichbar.");
      })
      .finally(() => setLoading(false));
  }, [publicId]);

  if (loading) {
    return <p className="mx-auto max-w-2xl px-4 py-12 text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }
  if (nichtVerfuegbar || !snapshot) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <Alert variant="danger">
          Dieses Formular ist nicht verfügbar. Es wurde möglicherweise zurückgenommen oder
          existiert nicht.
        </Alert>
      </div>
    );
  }
  if (ladeFehler) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <Alert variant="danger">{ladeFehler}</Alert>
        <Button className="mt-4" onClick={() => window.location.reload()}>
          Erneut versuchen
        </Button>
      </div>
    );
  }

  if (gesendet) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <Card>
          <CardContent className="py-10 text-center">
            <h1 className="text-xl font-semibold">Vielen Dank!</h1>
            <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
              Ihre Angaben wurden übermittelt. Der Betrieb meldet sich zeitnah bei Ihnen.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const modus = snapshot.komplexitaet;
  const schritte = snapshot.schritte;
  const aktiverSchritt = schritte[schrittIndex];
  const sichtbareFelder = aktiverSchritt.felder.filter((f) => feldSichtbar(f, modus));
  const istLetzter = schrittIndex === schritte.length - 1;

  function setValue(feldId: string, w: FeldWert) {
    setWerte((prev) => ({ ...prev, [feldId]: w }));
  }

  function validiere(felder: OeffentlichesFeld[]): Record<string, string> {
    const fehler: Record<string, string> = {};
    for (const f of felder) {
      const w = werte[f.id];
      if (f.typ === "consent") {
        if (w !== true) fehler[f.id] = "Bitte stimmen Sie der Datenschutzerklärung zu.";
        continue;
      }
      const required = f.pflichtfeld;
      if (f.typ === "upload") {
        const anz = (dateien[f.id] ?? []).length;
        if (required && anz === 0) fehler[f.id] = "Bitte laden Sie mindestens eine Datei hoch.";
        continue;
      }
      const leer =
        w === null ||
        w === undefined ||
        (typeof w === "string" && w.trim() === "") ||
        (f.typ === "adresse" &&
          (!w || !(w as AdresseWert).strasse || !(w as AdresseWert).ort));
      if (required && leer) {
        fehler[f.id] = "Dieses Feld ist erforderlich.";
        continue;
      }
      if (leer) continue;
      if (f.typ === "text" || f.typ === "mehrzeilig") {
        const s = String(w);
        if (f.config.maxLaenge && s.length > f.config.maxLaenge) {
          fehler[f.id] = `Maximal ${f.config.maxLaenge} Zeichen erlaubt.`;
        } else if (f.config.regex && !new RegExp(f.config.regex).test(s)) {
          fehler[f.id] = "Die Eingabe hat kein gültiges Format.";
        }
      }
      if (f.typ === "zahl") {
        const n = Number(w);
        if (Number.isNaN(n)) fehler[f.id] = "Bitte eine Zahl eingeben.";
        else if (f.config.ganzzahl && !Number.isInteger(n))
          fehler[f.id] = "Bitte eine ganze Zahl eingeben.";
        else if (f.config.min !== undefined && n < f.config.min)
          fehler[f.id] = `Mindestens ${f.config.min}.`;
        else if (f.config.max !== undefined && n > f.config.max)
          fehler[f.id] = `Höchstens ${f.config.max}.`;
      }
      if (f.typ === "datum") {
        const d = String(w);
        if (f.config.minDatum && d < f.config.minDatum)
          fehler[f.id] = "Datum liegt vor dem erlaubten Bereich.";
        else if (f.config.maxDatum && d > f.config.maxDatum)
          fehler[f.id] = "Datum liegt nach dem erlaubten Bereich.";
      }
    }
    return fehler;
  }

  function onWeiter() {
    const fehler = validiere(sichtbareFelder);
    setErrors(fehler);
    if (Object.keys(fehler).length === 0) {
      setSchrittIndex((i) => Math.min(i + 1, schritte.length - 1));
    }
  }

  function onZurueck() {
    setErrors({});
    setSchrittIndex((i) => Math.max(i - 1, 0));
  }

  async function onSubmit() {
    const alleSichtbaren = schritte.flatMap((s) => s.felder).filter((f) => feldSichtbar(f, modus));
    const fehler = validiere(alleSichtbaren);
    setErrors(fehler);
    if (Object.keys(fehler).length > 0) {
      const idx = schritte.findIndex((s) =>
        s.felder.some((f) => feldSichtbar(f, modus) && fehler[f.id]),
      );
      if (idx >= 0) setSchrittIndex(idx);
      return;
    }

    setWirdGesendet(true);
    setSendeFehler(null);
    try {
      // Dateien zuerst hochladen (Server prüft Typ/Größe/Menge); danach Einsendung.
      const uploads: Record<string, string[]> = {};
      for (const f of alleSichtbaren) {
        if (f.typ !== "upload") continue;
        for (const datei of dateien[f.id] ?? []) {
          const res = await uploadFormularDatei(publicId, datei, f.id, uebermittlungskennung);
          (uploads[f.id] ??= []).push(res.upload_id);
        }
      }
      const payloadWerte: Record<string, unknown> = {};
      for (const f of alleSichtbaren) {
        if (f.typ === "upload") continue;
        const w = werte[f.id];
        payloadWerte[f.id] =
          f.typ === "adresse" ? w ?? null : w === undefined ? null : w;
      }
      await submitEinsendung(publicId, {
        uebermittlungskennung,
        werte: payloadWerte,
        uploads,
        honeypot,
        client_startzeit: clientStartzeit,
      });
      setGesendet(true);
    } catch (err) {
      setSendeFehler(
        err instanceof ApiError
          ? err.message
          : "Die Übermittlung ist fehlgeschlagen. Bitte versuchen Sie es erneut.",
      );
      setWirdGesendet(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader>
          <CardTitle>{snapshot.name}</CardTitle>
          <CardDescription>
            Schritt {schrittIndex + 1} von {schritte.length}: {aktiverSchritt.titel}
          </CardDescription>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[var(--color-surface-muted)]">
            <div
              className="h-full bg-[var(--color-brand)] transition-all"
              style={{ width: `${((schrittIndex + 1) / schritte.length) * 100}%` }}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Honeypot — für Menschen unsichtbar */}
          <div aria-hidden className="absolute -left-[9999px]" style={{ position: "absolute", left: "-9999px" }}>
            <label>
              Firma
              <input
                tabIndex={-1}
                autoComplete="off"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
              />
            </label>
          </div>

          {sichtbareFelder.map((f) => (
            <FeldRenderer
              key={f.id}
              feld={f}
              value={werte[f.id] ?? null}
              onChange={(w) => setValue(f.id, w)}
              error={errors[f.id]}
              renderUpload={(uf) => (
                <UploadFeld
                  feld={uf}
                  dateien={dateien[uf.id] ?? []}
                  onChange={(files) => setDateien((prev) => ({ ...prev, [uf.id]: files }))}
                />
              )}
            />
          ))}

          {sendeFehler && <Alert variant="danger">{sendeFehler}</Alert>}

          <div className="flex items-center justify-between pt-2">
            <Button
              variant="outline"
              onClick={onZurueck}
              disabled={schrittIndex === 0 || wirdGesendet}
            >
              <ChevronLeft size={16} /> Zurück
            </Button>
            {istLetzter ? (
              <Button onClick={() => void onSubmit()} disabled={wirdGesendet}>
                <Send size={16} /> {wirdGesendet ? "Wird gesendet …" : "Absenden"}
              </Button>
            ) : (
              <Button onClick={onWeiter} disabled={wirdGesendet}>
                Weiter <ChevronRight size={16} />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function UploadFeld({
  feld,
  dateien,
  onChange,
}: {
  feld: OeffentlichesFeld;
  dateien: File[];
  onChange: (files: File[]) => void;
}) {
  const [fehler, setFehler] = React.useState<string | null>(null);
  const maxAnzahl = feld.config.maxAnzahl ?? 5;

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    setFehler(null);
    const neu = Array.from(e.target.files ?? []);
    for (const d of neu) {
      if (!ERLAUBTE_TYPEN.includes(d.type)) {
        setFehler(`„${d.name}" ist kein erlaubter Dateityp (JPEG, PNG, WebP, PDF).`);
        e.target.value = "";
        return;
      }
      if (d.size > MAX_DATEIGROESSE) {
        setFehler(`„${d.name}" ist zu groß (maximal 15 MB).`);
        e.target.value = "";
        return;
      }
    }
    const kombiniert = [...dateien, ...neu];
    if (kombiniert.length > maxAnzahl) {
      setFehler(`Höchstens ${maxAnzahl} Dateien erlaubt.`);
      e.target.value = "";
      return;
    }
    onChange(kombiniert);
  }

  return (
    <div>
      <input
        type="file"
        accept=".jpg,.jpeg,.png,.webp,.pdf,image/jpeg,image/png,image/webp,application/pdf"
        multiple
        onChange={onPick}
        className="block w-full text-sm text-[var(--color-muted-foreground)] file:mr-3 file:rounded-[var(--radius-md)] file:border-0 file:bg-[var(--color-surface-muted)] file:px-3 file:py-2 file:text-sm file:font-medium"
      />
      {fehler && <Alert variant="danger" className="mt-1">{fehler}</Alert>}
      {dateien.length > 0 && (
        <ul className="mt-2 space-y-1">
          {dateien.map((d, i) => (
            <li
              key={`${d.name}-${i}`}
              className="flex items-center justify-between rounded-[var(--radius-md)] bg-[var(--color-surface-muted)] px-3 py-1.5 text-sm"
            >
              <span className="truncate">{d.name}</span>
              <button
                type="button"
                onClick={() => onChange(dateien.filter((_, j) => j !== i))}
                aria-label={`${d.name} entfernen`}
                className="text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)]"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
