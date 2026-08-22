"use client";

import * as React from "react";
import { ChevronUp, ChevronDown, Plus, Trash2, Eye, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import {
  addSection,
  deleteSection,
  getLandingpage,
  initialisiereLandingpage,
  isConflict,
  reorderSections,
  updateSection,
} from "@/lib/api/website-builder";
import { getWebsiteSettings, type WebsiteSettings } from "@/lib/api/website-settings";
import type { PublicSite } from "@/lib/api/public";
import { SectionEditor } from "@/components/website-builder/section-editor";
import { SectionRenderer } from "@/components/website-builder/section-renderer";
import {
  SEKTION_TYPEN,
  typLabel,
  type LandingpageState,
  type PublicSection,
  type SektionInhaltUnion,
  type SektionTyp,
  type WebsiteSection,
} from "@/lib/website-builder-types";

export default function WebsiteBuilderPage() {
  const [state, setState] = React.useState<LandingpageState | null>(null);
  const [settings, setSettings] = React.useState<WebsiteSettings | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [conflict, setConflict] = React.useState(false);
  const [aktiveId, setAktiveId] = React.useState<string | null>(null);
  const [neuerTyp, setNeuerTyp] = React.useState<SektionTyp | "">("");
  const [zeigeVorschau, setZeigeVorschau] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    setConflict(false);
    try {
      let st: LandingpageState;
      try {
        st = await getLandingpage();
      } catch (err) {
        // Leere Landingpage (noch nicht initialisiert) -> Defaultseite anlegen.
        if (err instanceof ApiError && err.status === 409) throw err;
        st = await initialisiereLandingpage();
      }
      if (st.sections.length === 0) {
        st = await initialisiereLandingpage();
      }
      setState(st);
      if (st.sections.length > 0 && aktiveId === null) {
        setAktiveId(st.sections[0].id);
      }
      try {
        setSettings(await getWebsiteSettings());
      } catch {
        setSettings(null);
      }
    } catch (err) {
      if (isConflict(err)) {
        setConflict(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
      }
    } finally {
      setLoading(false);
    }
  }, [aktiveId]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function reloadAfter(res: LandingpageState) {
    setState(res);
    setConflict(false);
    setError(null);
  }

  async function onAdd() {
    if (!neuerTyp || !state) return;
    setSaving(true);
    setError(null);
    try {
      const res = await addSection(neuerTyp, state.version);
      await reloadAfter(res);
      setNeuerTyp("");
      setAktiveId(res.sections[res.sections.length - 1].id);
    } catch (err) {
      if (isConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Hinzufügen fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    if (!state) return;
    if (!window.confirm("Diese Sektion wirklich entfernen?")) return;
    setSaving(true);
    setError(null);
    try {
      const res = await deleteSection(id, state.version);
      await reloadAfter(res);
      if (aktiveId === id) setAktiveId(res.sections[0]?.id ?? null);
    } catch (err) {
      if (isConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onMove(id: string, richtung: -1 | 1) {
    if (!state) return;
    const ids = state.sections.map((s) => s.id);
    const idx = ids.indexOf(id);
    const neu = idx + richtung;
    if (neu < 0 || neu >= ids.length) return;
    [ids[idx], ids[neu]] = [ids[neu], ids[idx]];
    setSaving(true);
    setError(null);
    try {
      const res = await reorderSections(ids, state.version);
      await reloadAfter(res);
    } catch (err) {
      if (isConflict(err)) setConflict(true);
      else setError(err instanceof ApiError ? err.message : "Sortieren fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onSaveInhalt(section: WebsiteSection, inhalt: SektionInhaltUnion, visible: boolean) {
    if (!state) return;
    const res = await updateSection(section.id, { inhalt, visible, version: state.version });
    await reloadAfter(res);
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  if (conflict) {
    return (
      <div className="space-y-4">
        <Alert variant="warning">
          Ihr Builder-Stand war veraltet. Bitte laden Sie die Seite neu, bevor Sie die Änderung
          erneut speichern.
        </Alert>
        <Button onClick={() => void laden()}>Neu laden</Button>
      </div>
    );
  }

  if (!state) {
    return <Alert variant="danger">{error ?? "Landingpage konnte nicht geladen werden."}</Alert>;
  }

  const aktive = state.sections.find((s) => s.id === aktiveId) ?? null;
  const previewSite = settings ? toPreviewSite(settings) : null;
  const previewSections: PublicSection[] = state.sections
    .filter((s) => s.visible)
    .map((s) => ({ ...s.inhalt, bild: s.bild } as PublicSection));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Landingpage gestalten</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Halten Sie Ihre öffentliche Startseite aktuell — ohne Layout oder HTML.
          </p>
        </div>
        <Button variant="outline" onClick={() => setZeigeVorschau((v) => !v)}>
          {zeigeVorschau ? <Pencil size={16} /> : <Eye size={16} />}
          {zeigeVorschau ? "Editor" : "Vorschau"}
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {zeigeVorschau ? (
        <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)]">
          {previewSite ? (
            <SectionRenderer sections={previewSections} site={previewSite} />
          ) : (
            <p className="p-4 text-sm text-[var(--color-muted-foreground)]">
              Vorschau der öffentlichen Website (Einstellungen werden geladen …).
            </p>
          )}
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
          {/* Sektionsliste */}
          <Card>
            <CardHeader>
              <CardTitle>Sektionen</CardTitle>
              <CardDescription>
                Reihenfolge, Sichtbarkeit und Inhalt Ihrer Startseite.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {state.sections.length === 0 && (
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  Noch keine Sektionen vorhanden.
                </p>
              )}
              <ul className="space-y-2">
                {state.sections.map((s, i) => (
                  <li
                    key={s.id}
                    className={`flex items-center gap-2 rounded-[var(--radius-md)] border p-2 ${
                      s.id === aktiveId
                        ? "border-[var(--color-brand)] bg-[var(--color-surface-muted)]"
                        : "border-[var(--color-border)]"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => setAktiveId(s.id)}
                      className="flex-1 text-left text-sm font-medium"
                      aria-pressed={s.id === aktiveId}
                    >
                      <span className={s.visible ? "" : "text-[var(--color-muted-foreground)] line-through"}>
                        {typLabel(s.typ)}
                      </span>
                    </button>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => onMove(s.id, -1)}
                        disabled={i === 0 || saving}
                        aria-label={`${typLabel(s.typ)} nach oben`}
                        className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                      >
                        <ChevronUp size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onMove(s.id, 1)}
                        disabled={i === state.sections.length - 1 || saving}
                        aria-label={`${typLabel(s.typ)} nach unten`}
                        className="rounded p-1 hover:bg-[var(--color-surface-muted)] disabled:opacity-40"
                      >
                        <ChevronDown size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onDelete(s.id)}
                        disabled={saving}
                        aria-label={`${typLabel(s.typ)} löschen`}
                        className="rounded p-1 text-[var(--color-muted-foreground)] hover:text-[var(--color-danger)] disabled:opacity-40"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>

              <div className="flex items-end gap-2 border-t border-[var(--color-border)] pt-3">
                <div className="flex-1">
                  <Label htmlFor="neu-typ" className="text-xs">
                    Sektion hinzufügen
                  </Label>
                  <Select
                    id="neu-typ"
                    value={neuerTyp}
                    onChange={(e) => setNeuerTyp(e.target.value as SektionTyp)}
                  >
                    <option value="">Typ wählen …</option>
                    {SEKTION_TYPEN.map((t) => (
                      <option key={t.typ} value={t.typ}>
                        {t.label}
                      </option>
                    ))}
                  </Select>
                </div>
                <Button onClick={onAdd} disabled={!neuerTyp || saving}>
                  <Plus size={16} /> Hinzufügen
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Sektionseditor */}
          <Card>
            <CardHeader>
              <CardTitle>Sektion bearbeiten</CardTitle>
              <CardDescription>
                {aktive ? typLabel(aktive.typ) : "Wählen Sie links eine Sektion aus."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {aktive ? (
                <SectionEditor
                  key={aktive.id}
                  section={aktive}
                  version={state.version}
                  onSaveInhalt={(inhalt, visible) => onSaveInhalt(aktive, inhalt, visible)}
                  onStateUpdate={(res) => void reloadAfter(res)}
                />
              ) : (
                <p className="text-sm text-[var(--color-muted-foreground)]">
                  Keine Sektion ausgewählt.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

/** Baut ein für die Vorschau ausreichendes PublicSite aus den Website-Einstellungen. */
function toPreviewSite(settings: WebsiteSettings): PublicSite {
  return {
    firmenname: settings.firmenname,
    logo_url: settings.logo_url,
    marken_farbe: settings.marken_farbe,
    telefon: settings.telefon,
    email: settings.email,
    adresse: settings.adresse,
    oeffnungszeiten: settings.oeffnungszeiten,
    ueber_uns: settings.ueber_uns,
    leistungen: settings.leistungen
      .filter((l) => l.aktiv)
      .map((l) => ({ slug: l.slug, titel: l.titel, kurzbeschreibung: l.kurzbeschreibung })),
    sections: [],
  };
}
