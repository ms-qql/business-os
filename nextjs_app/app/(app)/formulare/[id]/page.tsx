"use client";

import * as React from "react";
import {
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Pencil,
  Eye,
  Rocket,
  Undo2,
  Share2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useParams } from "next/navigation";
import { ApiError } from "@/lib/api/client";
import {
  addFeld,
  addSchritt,
  deleteFeld,
  deleteSchritt,
  getFormular,
  isFormularConflict,
  publishFormular,
  renameFormular,
  reorderFelder,
  reorderSchritte,
  setKomplexitaet,
  unpublishFormular,
  updateSchritt,
} from "@/lib/api/formulare";
import {
  FELDTYPEN,
  type FeldTyp,
  type FormularEntwurf,
} from "@/lib/schemas/formular";
import { FeldDialog } from "@/components/formulare/feld-dialog";
import { FormularVorschau, FeldKurz } from "@/components/formulare/formular-vorschau";
import { EinbindungDialog } from "@/components/formulare/einbindung-dialog";

type Tab = "bearbeiten" | "vorschau";

export default function FormularEditorPage() {
  const { id: formularId } = useParams<{ id: string }>();
  const [entwurf, setEntwurf] = React.useState<FormularEntwurf | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [conflict, setConflict] = React.useState(false);

  const [name, setName] = React.useState("");
  const [tab, setTab] = React.useState<Tab>("bearbeiten");
  const [vorschauModus, setVorschauModus] = React.useState<"einfach" | "erweitert">(
    "einfach",
  );

  const [aktiverSchritt, setAktiverSchritt] = React.useState<string | null>(null);
  const [neuerTyp, setNeuerTyp] = React.useState<FeldTyp | "">("");
  const [speichert, setSpeichert] = React.useState(false);

  const [feldDialogSchritt, setFeldDialogSchritt] = React.useState<string | null>(null);
  const [feldDialogId, setFeldDialogId] = React.useState<string | null>(null);

  const [publishInfo, setPublishInfo] = React.useState<string | null>(null);
  const [einbindungOffen, setEinbindungOffen] = React.useState(false);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    setConflict(false);
    try {
      const e = await getFormular(formularId);
      setEntwurf(e);
      setName(e.name);
      setVorschauModus(e.komplexitaet);
      if (aktiverSchritt === null && e.schritte.length > 0) {
        setAktiverSchritt(e.schritte[0].id);
      }
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, [formularId, aktiverSchritt]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function nachMutation(res: FormularEntwurf) {
    setEntwurf(res);
    setConflict(false);
    setError(null);
  }

  async function onRename() {
    if (!entwurf || !name.trim()) return;
    setSpeichert(true);
    try {
      const res = await renameFormular(entwurf.id, name.trim(), entwurf.draft_revision);
      await nachMutation(res);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Umbenennen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onKomplexitaet(m: "einfach" | "erweitert") {
    if (!entwurf) return;
    setSpeichert(true);
    try {
      const res = await setKomplexitaet(entwurf.id, m, entwurf.draft_revision);
      await nachMutation(res);
      setVorschauModus(m);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onAddSchritt() {
    if (!entwurf) return;
    setSpeichert(true);
    try {
      const res = await addSchritt(entwurf.id, entwurf.draft_revision);
      await nachMutation(res);
      setAktiverSchritt(res.schritte[res.schritte.length - 1].id);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Hinzufügen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onRenameSchritt(schrittId: string, titel: string) {
    if (!entwurf) return;
    try {
      const res = await updateSchritt(entwurf.id, schrittId, titel, entwurf.draft_revision);
      await nachMutation(res);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    }
  }

  async function onDeleteSchritt(schrittId: string) {
    if (!entwurf) return;
    if (!window.confirm("Diesen Schritt und alle seine Felder entfernen?")) return;
    setSpeichert(true);
    try {
      const res = await deleteSchritt(entwurf.id, schrittId, entwurf.draft_revision);
      await nachMutation(res);
      if (aktiverSchritt === schrittId) setAktiverSchritt(res.schritte[0]?.id ?? null);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onMoveSchritt(schrittId: string, richtung: -1 | 1) {
    if (!entwurf) return;
    const ids = entwurf.schritte.map((s) => s.id);
    const idx = ids.indexOf(schrittId);
    const neu = idx + richtung;
    if (neu < 0 || neu >= ids.length) return;
    [ids[idx], ids[neu]] = [ids[neu], ids[idx]];
    setSpeichert(true);
    try {
      const res = await reorderSchritte(entwurf.id, ids, entwurf.draft_revision);
      await nachMutation(res);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Sortieren fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onAddFeld(schrittId: string) {
    if (!entwurf || !neuerTyp) return;
    setSpeichert(true);
    try {
      const res = await addFeld(entwurf.id, schrittId, neuerTyp, entwurf.draft_revision);
      await nachMutation(res);
      setNeuerTyp("");
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Hinzufügen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onDeleteFeld(schrittId: string, feldId: string) {
    if (!entwurf) return;
    setSpeichert(true);
    try {
      const res = await deleteFeld(entwurf.id, schrittId, feldId, entwurf.draft_revision);
      await nachMutation(res);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onMoveFeld(schrittId: string, feldId: string, richtung: -1 | 1) {
    if (!entwurf) return;
    const schritt = entwurf.schritte.find((s) => s.id === schrittId);
    if (!schritt) return;
    const ids = schritt.felder.map((f) => f.id);
    const idx = ids.indexOf(feldId);
    const neu = idx + richtung;
    if (neu < 0 || neu >= ids.length) return;
    [ids[idx], ids[neu]] = [ids[neu], ids[idx]];
    setSpeichert(true);
    try {
      const res = await reorderFelder(entwurf.id, schrittId, ids, entwurf.draft_revision);
      await nachMutation(res);
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Sortieren fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onPublish() {
    if (!entwurf) return;
    setSpeichert(true);
    setPublishInfo(null);
    setError(null);
    try {
      const res = await publishFormular(entwurf.id, entwurf.draft_revision);
      await nachMutation(res);
      setPublishInfo("Formular veröffentlicht. Alle Einbettungen zeigen nun diese Fassung.");
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Veröffentlichen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onUnpublish() {
    if (!entwurf) return;
    if (!window.confirm("Veröffentlichung zurücknehmen? Einbettungen zeigen dann keine Formularstruktur mehr.")) return;
    setSpeichert(true);
    setPublishInfo(null);
    try {
      const res = await unpublishFormular(entwurf.id, entwurf.draft_revision);
      await nachMutation(res);
      setPublishInfo("Veröffentlichung zurückgenommen.");
    } catch (err) {
      if (isFormularConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Zurücknehmen fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }
  if (conflict) {
    return (
      <div className="space-y-4">
        <Alert variant="warning">
          Ihr Editor-Stand war veraltet. Bitte laden Sie die Seite neu, bevor Sie
          die Änderung erneut speichern.
        </Alert>
        <Button onClick={() => void laden()}>Neu laden</Button>
      </div>
    );
  }
  if (!entwurf) {
    return <Alert variant="danger">{error ?? "Formular konnte nicht geladen werden."}</Alert>;
  }

  const aktiver = entwurf.schritte.find((s) => s.id === aktiverSchritt) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Input
              aria-label="Formularname"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={onRename}
              className="max-w-sm text-xl font-semibold"
            />
            {entwurf.veroeffentlicht ? (
              <Badge variant="success">Veröffentlicht</Badge>
            ) : (
              <Badge variant="warning">Entwurf</Badge>
            )}
          </div>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Komplexitätsstufe: {entwurf.komplexitaet === "einfach" ? "Einfach" : "Erweitert"} ·
            Entwurfsrevision {entwurf.draft_revision}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => setTab("bearbeiten")}>
            <Pencil size={14} /> Bearbeiten
          </Button>
          <Button variant="outline" size="sm" onClick={() => setTab("vorschau")}>
            <Eye size={14} /> Vorschau
          </Button>
          {entwurf.veroeffentlicht ? (
            <>
              <Button variant="outline" size="sm" onClick={() => setEinbindungOffen(true)}>
                <Share2 size={14} /> Einbinden
              </Button>
              <Button variant="outline" size="sm" onClick={() => void onUnpublish()} disabled={speichert}>
                <Undo2 size={14} /> Zurücknehmen
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={() => void onPublish()} disabled={speichert}>
              <Rocket size={14} /> Veröffentlichen
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {publishInfo && <Alert variant="success">{publishInfo}</Alert>}

      {/* Komplexitätsstufe */}
      <Card>
        <CardHeader>
          <CardTitle>Komplexitätsstufe</CardTitle>
          <CardDescription>
            „Einfach" zeigt nur Pflichtfelder. „Erweitert" blendet zusätzlich die als
            optional markierten Zusatzfelder ein.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button
              variant={entwurf.komplexitaet === "einfach" ? "primary" : "outline"}
              size="sm"
              onClick={() => void onKomplexitaet("einfach")}
              disabled={speichert}
            >
              Einfach
            </Button>
            <Button
              variant={entwurf.komplexitaet === "erweitert" ? "primary" : "outline"}
              size="sm"
              onClick={() => void onKomplexitaet("erweitert")}
              disabled={speichert}
            >
              Erweitert
            </Button>
          </div>
        </CardContent>
      </Card>

      {tab === "bearbeiten" ? (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
          {/* Schritte */}
          <Card>
            <CardHeader>
              <CardTitle>Schritte</CardTitle>
              <CardDescription>
                Ein Formular kann beliebig viele Schritte enthalten.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {entwurf.schritte.length === 0 && (
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  Noch keine Schritte vorhanden.
                </p>
              )}
              <ul className="space-y-2">
                {entwurf.schritte.map((s, i) => (
                  <li
                    key={s.id}
                    className={`rounded-[var(--radius-md)] border p-2 ${
                      s.id === aktiverSchritt
                        ? "border-[var(--color-brand)] bg-[var(--color-surface-muted)]"
                        : "border-[var(--color-border)]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setAktiverSchritt(s.id)}
                        className="flex-1 text-left"
                        aria-pressed={s.id === aktiverSchritt}
                      >
                        <span className="text-sm font-medium">
                          {i + 1}. {s.titel || "Ohne Titel"}
                        </span>
                        <span className="ml-2 text-xs text-[var(--color-muted-foreground)]">
                          {s.felder.length} Felder
                        </span>
                      </button>
                      <div className="flex items-center">
                        <button
                          type="button"
                          aria-label={`Schritt ${i + 1} nach oben`}
                          disabled={i === 0 || speichert}
                          onClick={() => void onMoveSchritt(s.id, -1)}
                          className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                        >
                          <ChevronUp size={16} />
                        </button>
                        <button
                          type="button"
                          aria-label={`Schritt ${i + 1} nach unten`}
                          disabled={i === entwurf.schritte.length - 1 || speichert}
                          onClick={() => void onMoveSchritt(s.id, 1)}
                          className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                        >
                          <ChevronDown size={16} />
                        </button>
                        <button
                          type="button"
                          aria-label={`Schritt ${i + 1} löschen`}
                          onClick={() => void onDeleteSchritt(s.id)}
                          disabled={speichert}
                          className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)] disabled:opacity-40"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                    <Input
                      aria-label="Schritttitel"
                      defaultValue={s.titel}
                      onBlur={(e) => void onRenameSchritt(s.id, e.target.value)}
                      placeholder="Schritttitel"
                      className="mt-2 h-8 text-sm"
                    />
                  </li>
                ))}
              </ul>
              <Button variant="outline" size="sm" onClick={() => void onAddSchritt()} disabled={speichert}>
                <Plus size={14} /> Schritt hinzufügen
              </Button>
            </CardContent>
          </Card>

          {/* Felder des aktiven Schritts */}
          <Card>
            <CardHeader>
              <CardTitle>Felder</CardTitle>
              <CardDescription>
                Fester Katalog: Text, mehrzeilig, Auswahl, Kachel, Radio, Zahl, Datum,
                Upload, Adresse, Consent.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!aktiver ? (
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  Wählen Sie links einen Schritt aus.
                </p>
              ) : (
                <div className="space-y-3">
                  {aktiver.felder.length === 0 && (
                    <p className="text-sm text-[var(--color-muted-foreground)]">
                      Noch keine Felder in diesem Schritt.
                    </p>
                  )}
                  <ul className="space-y-2">
                    {aktiver.felder.map((f, fi) => (
                      <li
                        key={f.id}
                        className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--color-border)] p-2"
                      >
                        <div className="flex-1">
                          <FeldKurz feld={f} />
                        </div>
                        <div className="flex items-center">
                          <button
                            type="button"
                            aria-label={`Feld ${fi + 1} nach oben`}
                            disabled={fi === 0 || speichert}
                            onClick={() => void onMoveFeld(aktiver.id, f.id, -1)}
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                          >
                            <ChevronUp size={14} />
                          </button>
                          <button
                            type="button"
                            aria-label={`Feld ${fi + 1} nach unten`}
                            disabled={fi === aktiver.felder.length - 1 || speichert}
                            onClick={() => void onMoveFeld(aktiver.id, f.id, 1)}
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                          >
                            <ChevronDown size={14} />
                          </button>
                          <button
                            type="button"
                            aria-label={`Feld ${fi + 1} bearbeiten`}
                            onClick={() => {
                              setFeldDialogSchritt(aktiver.id);
                              setFeldDialogId(f.id);
                            }}
                            className="rounded p-1 hover:bg-[var(--color-surface-muted)]"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            type="button"
                            aria-label={`Feld ${fi + 1} löschen`}
                            onClick={() => void onDeleteFeld(aktiver.id, f.id)}
                            disabled={speichert}
                            className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)] disabled:opacity-40"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>

                  <div className="flex items-end gap-2 border-t border-[var(--color-border)] pt-3">
                    <div className="flex-1">
                      <Label htmlFor="neu-typ" className="text-xs">
                        Feldtyp hinzufügen
                      </Label>
                      <select
                        id="neu-typ"
                        value={neuerTyp}
                        onChange={(e) => setNeuerTyp(e.target.value as FeldTyp)}
                        className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
                      >
                        <option value="">Typ wählen …</option>
                        {FELDTYPEN.map((t) => (
                          <option key={t.typ} value={t.typ}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <Button
                      onClick={() => void onAddFeld(aktiver.id)}
                      disabled={!neuerTyp || speichert}
                    >
                      <Plus size={14} /> Hinzufügen
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <CardTitle>Vorschau</CardTitle>
              <div className="flex gap-2">
                <Button
                  variant={vorschauModus === "einfach" ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setVorschauModus("einfach")}
                >
                  Einfach
                </Button>
                <Button
                  variant={vorschauModus === "erweitert" ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setVorschauModus("erweitert")}
                >
                  Erweitert
                </Button>
              </div>
            </div>
            <CardDescription>
              So sieht die öffentliche Eingabe in der gewählten Stufe aus (ohne
              Absenden).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FormularVorschau schritte={entwurf.schritte} modus={vorschauModus} />
          </CardContent>
        </Card>
      )}

      {feldDialogSchritt && feldDialogId && (
        (() => {
          const schritt = entwurf.schritte.find((s) => s.id === feldDialogSchritt);
          const feld = schritt?.felder.find((f) => f.id === feldDialogId);
          if (!schritt || !feld) return null;
          return (
            <FeldDialog
              formularId={entwurf.id}
              schrittId={schritt.id}
              feld={feld}
              draftRevision={entwurf.draft_revision}
              onClose={() => {
                setFeldDialogSchritt(null);
                setFeldDialogId(null);
              }}
              onSaved={() => void laden()}
            />
          );
        })()
      )}

      {einbindungOffen && (
        <EinbindungDialog formularId={entwurf.id} onClose={() => setEinbindungOffen(false)} />
      )}
    </div>
  );
}
