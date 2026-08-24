"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { ChevronUp, ChevronDown, Plus, Trash2, Eye, Pencil, Send, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import {
  addFeld,
  addSchritt,
  deleteFeld,
  deleteSchritt,
  getFormular,
  isFormularConflict,
  renameFormular,
  renameSchritt,
  reorderFelder,
  reorderSchritte,
  setKomplexitaet,
  updateFeld,
  veroeffentlichen,
  veroeffentlichungZuruecknehmen,
  getEinbindung,
  type Veroeffentlicht,
} from "@/lib/api/formulare";
import {
  FELDTYPEN,
  FELDTYP_LABELS,
  KOMPLEXITAET,
  KOMPLEXITAET_LABELS,
  type Einbindung,
  type FormularDraft,
  type FormularFeldDraft,
  type Feldtyp,
} from "@/lib/schemas/formular";
import { FeldRenderer, feldSichtbar, type FeldWert } from "@/components/formulare/feld-renderer";
import { FeldEditor, type FeldEditorErgebnis } from "@/components/formulare/feld-editor";

export default function FormularEditorPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [draft, setDraft] = React.useState<FormularDraft | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [conflict, setConflict] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  const [activeStepId, setActiveStepId] = React.useState<string | null>(null);
  const [bearbeiteFeld, setBearbeiteFeld] = React.useState<FormularFeldDraft | null>(null);
  const [neuerTyp, setNeuerTyp] = React.useState<Feldtyp | "">("");
  const [vorschauModus, setVorschauModus] = React.useState<"einfach" | "erweitert" | null>(null);
  const [publishError, setPublishError] = React.useState<string | null>(null);
  const [publishing, setPublishing] = React.useState(false);
  const [einbindung, setEinbindung] = React.useState<Einbindung | null>(null);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    setConflict(false);
    try {
      const d = await getFormular(id);
      setDraft(d);
      if (activeStepId === null && d.schritte.length > 0) {
        setActiveStepId(d.schritte[0].id);
      }
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [id, activeStepId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  function reloadAfter(d: FormularDraft) {
    setDraft(d);
    setConflict(false);
    setError(null);
    setBearbeiteFeld(null);
  }

  async function guard<T>(fn: () => Promise<T>): Promise<T | null> {
    setSaving(true);
    setError(null);
    setPublishError(null);
    try {
      return await fn();
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
      return null;
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }
  if (conflict) {
    return (
      <div className="space-y-4">
        <Alert variant="warning">
          Ihr Formular-Entwurf war veraltet. Bitte laden Sie die Seite neu, bevor Sie
          die Änderung erneut speichern.
        </Alert>
        <Button onClick={() => void laden()}>Neu laden</Button>
      </div>
    );
  }
  if (!draft) {
    return <Alert variant="danger">{error ?? "Formular konnte nicht geladen werden."}</Alert>;
  }

  const activeStep = draft.schritte.find((s) => s.id === activeStepId) ?? null;
  const [publishHinweis, darf] = publishVoraussetzungen(draft);

  async function onRename(name: string) {
    if (!draft || name.trim() === "") return;
    const res = await guard(() => renameFormular(draft!.id, name, draft!.draft_revision));
    if (res) reloadAfter(res);
  }

  async function onKomplexitaet(k: FormularDraft["komplexitaet"]) {
    if (!draft) return;
    const res = await guard(() => setKomplexitaet(draft!.id, k, draft!.draft_revision));
    if (res) reloadAfter(res);
  }

  async function onAddStep() {
    if (!draft) return;
    const res = await guard(() =>
      addSchritt(draft!.id, `Schritt ${draft!.schritte.length + 1}`, draft!.draft_revision),
    );
    if (res) {
      reloadAfter(res);
      setActiveStepId(res.schritte[res.schritte.length - 1].id);
    }
  }

  async function onRenameStep(stepId: string, titel: string) {
    if (!draft || titel.trim() === "") return;
    const res = await guard(() =>
      renameSchritt(draft!.id, stepId, titel, draft!.draft_revision),
    );
    if (res) reloadAfter(res);
  }

  async function onDeleteStep(stepId: string) {
    if (!draft) return;
    if (!window.confirm("Diesen Schritt wirklich löschen?")) return;
    const res = await guard(() => deleteSchritt(draft!.id, stepId, draft!.draft_revision));
    if (res) {
      reloadAfter(res);
      setActiveStepId(res.schritte[0]?.id ?? null);
    }
  }

  async function onMoveStep(stepId: string, richtung: -1 | 1) {
    if (!draft) return;
    const ids = draft.schritte.map((s) => s.id);
    const idx = ids.indexOf(stepId);
    const neu = idx + richtung;
    if (neu < 0 || neu >= ids.length) return;
    [ids[idx], ids[neu]] = [ids[neu], ids[idx]];
    const res = await guard(() => reorderSchritte(draft!.id, ids, draft!.draft_revision));
    if (res) reloadAfter(res);
  }

  async function onAddFeld(typ: Feldtyp) {
    if (!draft || !activeStep) return;
    const res = await guard(() =>
      addFeld(
        draft!.id,
        activeStep!.id,
        { typ, label: FELDTYP_LABELS[typ], hilfetext: "", pflichtfeld: false, optional_in_einfach: false },
        draft!.draft_revision,
      ),
    );
    if (res) {
      reloadAfter(res);
      const step = res.schritte.find((s) => s.id === activeStep!.id)!;
      setBearbeiteFeld(step.felder[step.felder.length - 1]);
      setNeuerTyp("");
    }
  }

  async function onSaveFeld(feld: FormularFeldDraft, erg: FeldEditorErgebnis) {
    if (!draft || !activeStep) return;
    const res = await guard(() =>
      updateFeld(
        draft!.id,
        activeStep!.id,
        feld.id,
        {
          label: erg.label,
          hilfetext: erg.hilfetext,
          pflichtfeld: erg.pflichtfeld,
          optional_in_einfach: erg.optional_in_einfach,
          config: erg.config,
          uebernahme: erg.uebernahme,
          options: erg.options,
        },
        draft!.draft_revision,
      ),
    );
    if (res) reloadAfter(res);
  }

  async function onDeleteFeld(feldId: string) {
    if (!draft || !activeStep) return;
    if (!window.confirm("Dieses Feld wirklich löschen?")) return;
    const res = await guard(() =>
      deleteFeld(draft!.id, activeStep!.id, feldId, draft!.draft_revision),
    );
    if (res) reloadAfter(res);
  }

  async function onMoveFeld(feldId: string, richtung: -1 | 1) {
    if (!draft || !activeStep) return;
    const ids = activeStep.felder.map((f) => f.id);
    const idx = ids.indexOf(feldId);
    const neu = idx + richtung;
    if (neu < 0 || neu >= ids.length) return;
    [ids[idx], ids[neu]] = [ids[neu], ids[idx]];
    const res = await guard(() =>
      reorderFelder(draft!.id, activeStep!.id, ids, draft!.draft_revision),
    );
    if (res) reloadAfter(res);
  }

  async function onPublish() {
    if (!draft) return;
    setPublishing(true);
    setPublishError(null);
    try {
      const res: Veroeffentlicht = await veroeffentlichen(draft.id);
      const d = await getFormular(draft.id);
      reloadAfter(d);
      setEinbindung(null);
      setPublishError(null);
      void res;
    } catch (err) {
      setPublishError(
        err instanceof ApiError ? err.message : "Veröffentlichung fehlgeschlagen.",
      );
    } finally {
      setPublishing(false);
    }
  }

  async function onZuruecknehmen() {
    if (!draft) return;
    const res = await guard(() => veroeffentlichungZuruecknehmen(draft!.id));
    if (res) {
      reloadAfter(res);
      setEinbindung(null);
    }
  }

  async function onEinbindung() {
    if (!draft) return;
    try {
      setEinbindung(await getEinbindung(draft.id));
    } catch (err) {
      setPublishError(err instanceof ApiError ? err.message : "Einbindung nicht verfügbar.");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1">
          <Input
            defaultValue={draft.name}
            onBlur={(e) => onRename(e.target.value)}
            className="max-w-sm text-xl font-semibold"
            aria-label="Formularname"
          />
          <div className="mt-2 flex items-center gap-3">
            <Select
              value={draft.komplexitaet}
              onChange={(e) => void onKomplexitaet(e.target.value as FormularDraft["komplexitaet"])}
              className="max-w-xs"
            >
              {KOMPLEXITAET.map((k) => (
                <option key={k} value={k}>
                  {KOMPLEXITAET_LABELS[k]}
                </option>
              ))}
            </Select>
            <span
              className={`text-xs font-medium ${
                draft.veroeffentlicht ? "text-[var(--color-success)]" : "text-[var(--color-muted-foreground)]"
              }`}
            >
              {draft.veroeffentlicht
                ? `Veröffentlicht (Version ${draft.version_nummer})`
                : "Entwurf"}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {draft.veroeffentlicht && (
            <Button variant="outline" onClick={() => void onZuruecknehmen()} disabled={saving}>
              Veröffentlichung zurücknehmen
            </Button>
          )}
          <Button onClick={() => void onPublish()} disabled={!darf || publishing}>
            <Send size={16} /> Veröffentlichen
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {publishError && <Alert variant="danger">{publishError}</Alert>}
      {!darf && publishHinweis && (
        <Alert variant="warning">{publishHinweis}</Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.5fr]">
        {/* Schritte */}
        <Card>
          <CardHeader>
            <CardTitle>Schritte</CardTitle>
            <CardDescription>Mehrstufige Gliederung des Formulars.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {draft.schritte.length === 0 && (
              <p className="text-sm text-[var(--color-muted-foreground)]">
                Noch keine Schritte vorhanden.
              </p>
            )}
            <ul className="space-y-2">
              {draft.schritte.map((s, i) => (
                <li
                  key={s.id}
                  className={`flex items-center gap-2 rounded-[var(--radius-md)] border p-2 ${
                    s.id === activeStepId
                      ? "border-[var(--color-brand)] bg-[var(--color-surface-muted)]"
                      : "border-[var(--color-border)]"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setActiveStepId(s.id)}
                    className="flex-1 text-left text-sm font-medium"
                    aria-pressed={s.id === activeStepId}
                  >
                    {s.titel}
                  </button>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => void onMoveStep(s.id, -1)}
                      disabled={i === 0 || saving}
                      aria-label="Schritt nach oben"
                      className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                    >
                      <ChevronUp size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={() => void onMoveStep(s.id, 1)}
                      disabled={i === draft.schritte.length - 1 || saving}
                      aria-label="Schritt nach unten"
                      className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                    >
                      <ChevronDown size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteStep(s.id)}
                      disabled={saving}
                      aria-label="Schritt löschen"
                      className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)] disabled:opacity-40"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <Button variant="outline" onClick={() => void onAddStep()} disabled={saving}>
              <Plus size={16} /> Schritt hinzufügen
            </Button>
          </CardContent>
        </Card>

        {/* Felder des aktiven Schritts */}
        <Card>
          <CardHeader className="flex-row items-center justify-between gap-2 space-y-0">
            <div>
              <CardTitle>Felder</CardTitle>
              <CardDescription>
                {activeStep ? activeStep.titel : "Wählen Sie links einen Schritt aus."}
              </CardDescription>
            </div>
            {activeStep && (
              <Button variant="outline" size="sm" onClick={() => setVorschauModus(vorschauModus ? null : "einfach")}>
                {vorschauModus ? <Pencil size={16} /> : <Eye size={16} />}
                {vorschauModus ? "Editor" : "Vorschau"}
              </Button>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {!activeStep ? (
              <p className="text-sm text-[var(--color-muted-foreground)]">Kein Schritt ausgewählt.</p>
            ) : vorschauModus ? (
              <Vorschau schritt={activeStep} modus={vorschauModus} />
            ) : (
              <>
                {activeStep.felder.map((f, i) =>
                  bearbeiteFeld?.id === f.id ? (
                    <FeldEditor
                      key={f.id}
                      feld={f}
                      onChange={(erg) => void onSaveFeld(f, erg)}
                      onAbbrechen={() => setBearbeiteFeld(null)}
                    />
                  ) : (
                    <div
                      key={f.id}
                      className="rounded-[var(--radius-md)] border border-[var(--color-border)] p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-sm">
                          <span className="font-medium">{f.label || "(ohne Bezeichnung)"}</span>
                          <span className="ml-2 text-xs text-[var(--color-muted-foreground)]">
                            {FELDTYP_LABELS[f.typ]}
                            {f.pflichtfeld ? " · Pflicht" : ""}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => void onMoveFeld(f.id, -1)}
                            disabled={i === 0 || saving}
                            aria-label="Feld nach oben"
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                          >
                            <ChevronUp size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => void onMoveFeld(f.id, 1)}
                            disabled={i === activeStep.felder.length - 1 || saving}
                            aria-label="Feld nach unten"
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                          >
                            <ChevronDown size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => setBearbeiteFeld(f)}
                            aria-label="Feld bearbeiten"
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)]"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => void onDeleteFeld(f.id)}
                            disabled={saving}
                            aria-label="Feld löschen"
                            className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)] disabled:opacity-40"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ),
                )}

                {bearbeiteFeld === null && (
                  <div className="flex items-end gap-2 border-t border-[var(--color-border)] pt-3">
                    <div className="flex-1">
                      <Label htmlFor="neu-feld" className="text-xs">
                        Feld hinzufügen
                      </Label>
                      <Select
                        id="neu-feld"
                        value={neuerTyp}
                        onChange={(e) => setNeuerTyp(e.target.value as Feldtyp)}
                      >
                        <option value="">Feldtyp wählen …</option>
                        {FELDTYPEN.map((t) => (
                          <option key={t} value={t}>
                            {FELDTYP_LABELS[t]}
                          </option>
                        ))}
                      </Select>
                    </div>
                    <Button
                      onClick={() => neuerTyp && void onAddFeld(neuerTyp)}
                      disabled={!neuerTyp || saving}
                    >
                      <Plus size={16} /> Hinzufügen
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Einbindung */}
      {draft.veroeffentlicht && (
        <Card>
          <CardHeader>
            <CardTitle>Einbindung</CardTitle>
            <CardDescription>
              Alle Varianten zeigen ausschließlich die veröffentlichte Fassung.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" onClick={() => void onEinbindung()}>
              <Link2 size={16} /> Einbindungscode laden
            </Button>
            {einbindung && (
              <div className="space-y-3">
                <div>
                  <Label>Direktlink</Label>
                  <code className="block break-all rounded bg-[var(--color-surface-muted)] p-2 text-xs">
                    {einbindung.url}
                  </code>
                </div>
                <div>
                  <Label>iframe-Einbettung</Label>
                  <textarea
                    readOnly
                    value={einbindung.iframe}
                    rows={3}
                    className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-xs"
                  />
                </div>
                <div>
                  <Label>JavaScript-Snippet</Label>
                  <textarea
                    readOnly
                    value={einbindung.javascript}
                    rows={3}
                    className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-xs"
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Vorschau({
  schritt,
  modus,
}: {
  schritt: FormularDraft["schritte"][number];
  modus: "einfach" | "erweitert";
}) {
  const [werte, setWerte] = React.useState<Record<string, FeldWert>>({});
  const sichtbare = schritt.felder.filter((f) => feldSichtbar(f, modus));
  if (sichtbare.length === 0) {
    return (
      <p className="text-sm text-[var(--color-muted-foreground)]">
        In diesem Modus werden keine Felder angezeigt.
      </p>
    );
  }
  return (
    <div className="space-y-4">
      <p className="text-xs font-medium text-[var(--color-muted-foreground)]">
        Vorschau ({modus === "einfach" ? "Einfach" : "Erweitert"})
      </p>
      {sichtbare.map((f) => (
        <FeldRenderer
          key={f.id}
          feld={f}
          value={werte[f.id] ?? null}
          onChange={(w) => setWerte((prev) => ({ ...prev, [f.id]: w }))}
        />
      ))}
    </div>
  );
}

/** Clientseitige Hinweis-Logik; die verbindliche Prüfung erfolgt serverseitig. */
function publishVoraussetzungen(draft: FormularDraft): [string | null, boolean] {
  if (draft.schritte.length === 0) {
    return ["Ein Formular braucht mindestens einen Schritt.", false];
  }
  const alleFelder = draft.schritte.flatMap((s) => s.felder);
  if (alleFelder.length === 0) {
    return ["Ein Formular braucht mindestens ein Feld.", false];
  }
  const consents = alleFelder.filter((f) => f.typ === "consent" && f.pflichtfeld);
  if (consents.length !== 1) {
    return [
      "Genau ein Pflicht-Einwilligungsfeld (Datenschutz) ist für die Veröffentlichung nötig.",
      false,
    ];
  }
  const optionFelderUngueltig = alleFelder.some((f) => {
    if (!["dropdown", "kachel", "radio"].includes(f.typ)) return false;
    const werte = f.options.map((o) => o.wert.trim()).filter(Boolean);
    return werte.length === 0 || new Set(werte).size !== werte.length;
  });
  if (optionFelderUngueltig) {
    return ["Eine Auswahl enthält leere oder doppelte Werte.", false];
  }
  return [null, true];
}
