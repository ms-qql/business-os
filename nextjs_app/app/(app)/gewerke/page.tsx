"use client";

import * as React from "react";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Alert } from "@/components/ui/label";
import { Dialog } from "@/components/ui/dialog";
import { ApiError } from "@/lib/api/client";
import { formatEuro } from "@/lib/format";
import {
  getGewerke,
  getGewerk,
  deleteGewerk,
  getKategorien,
  type GewerkKurz,
  type GewerkDetail,
  type GewerkKategorie,
  KALKULATIONSART_LABELS,
} from "@/lib/api/gewerke";
import { KategorieVerwaltung } from "@/components/gewerke/kategorie_verwaltung";
import { GewerkEditor } from "@/components/gewerke/gewerk_editor";

const SERVER_FEHLER = "Keine Verbindung zum Server. Die Liste konnte nicht geladen werden.";

/**
 * Katalogseite Gewerke (PROJ-22) — Ablösung der bisherigen /katalog-Preislisten-UI.
 * Inhaber/Büro: Kategorien links, Gewerke-Tabelle rechts, Editor im Dialog.
 * Monteur hat keinen Zugriff (Server erzwingt das; diese Seite ist nur für
 * Schreibrollen in der Navigation verlinkt).
 */
export default function GewerkePage() {
  const [kategorien, setKategorien] = React.useState<GewerkKategorie[]>([]);
  const [gewerke, setGewerke] = React.useState<GewerkKurz[]>([]);
  const [auswahlKategorie, setAuswahlKategorie] = React.useState<string | null>(null);
  const [suchbegriff, setSuchbegriff] = React.useState("");

  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [editorOffen, setEditorOffen] = React.useState(false);
  const [bearbeitet, setBearbeitet] = React.useState<GewerkDetail | null>(null);
  const [detailOffen, setDetailOffen] = React.useState(false);
  const [detail, setDetail] = React.useState<GewerkDetail | null>(null);

  const ladenKategorien = React.useCallback(async () => {
    setKategorien(await getKategorien());
  }, []);

  const ladenGewerke = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getGewerke({
        suchbegriff: suchbegriff.trim() || undefined,
        kategorie_id: auswahlKategorie ?? undefined,
      });
      setGewerke(res.items);
    } catch (err) {
      setError(err instanceof ApiError ? SERVER_FEHLER : "Gewerke konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [suchbegriff, auswahlKategorie]);

  React.useEffect(() => {
    void ladenKategorien();
  }, [ladenKategorien]);

  React.useEffect(() => {
    void ladenGewerke();
  }, [ladenGewerke]);

  async function onNeu() {
    setBearbeitet(null);
    setEditorOffen(true);
  }

  async function onBearbeiten(g: GewerkKurz) {
    setError(null);
    try {
      setBearbeitet(await getGewerk(g.id));
      setEditorOffen(true);
    } catch (err) {
      setError(err instanceof ApiError ? SERVER_FEHLER : "Gewerk konnte nicht geladen werden.");
    }
  }

  async function onAnsehen(g: GewerkKurz) {
    setError(null);
    try {
      setDetail(await getGewerk(g.id));
      setDetailOffen(true);
    } catch (err) {
      setError(err instanceof ApiError ? SERVER_FEHLER : "Gewerk konnte nicht geladen werden.");
    }
  }

  async function onLoeschen(g: GewerkKurz) {
    if (!window.confirm(`Gewerk „${g.bezeichnung}“ wirklich löschen?`)) return;
    setError(null);
    try {
      await deleteGewerk(g.id);
      await ladenGewerke();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("Dieses Gewerk wird noch verwendet und kann nicht gelöscht werden.");
      } else {
        setError(err instanceof ApiError ? SERVER_FEHLER : "Gewerk konnte nicht gelöscht werden.");
      }
    }
  }

  async function onGespeichert() {
    setEditorOffen(false);
    setBearbeitet(null);
    await Promise.all([ladenKategorien(), ladenGewerke()]);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Gewerke-Katalog</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Wiederverwendbare Kalkulationseinheiten für Angebote (Lohn, Material, Fremdleistung).
          </p>
        </div>
        <Button onClick={() => void onNeu()}>
          <Plus size={16} /> Neues Gewerk
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <KategorieVerwaltung
          auswahl={auswahlKategorie}
          onAuswahl={setAuswahlKategorie}
          onChange={() => void ladenKategorien()}
        />

        <div className="space-y-4">
          {error && <Alert variant="danger">{error}</Alert>}

          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search
                size={16}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted-foreground)]"
              />
              <Input
                value={suchbegriff}
                onChange={(e) => setSuchbegriff(e.target.value)}
                placeholder="Gewerke durchsuchen …"
                className="pl-9"
                aria-label="Gewerke durchsuchen"
              />
            </div>
          </div>

          {loading ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
          ) : gewerke.length === 0 ? (
            <Card>
              <CardContent className="py-10 text-center text-sm text-[var(--color-muted-foreground)]">
                {suchbegriff.trim() || auswahlKategorie
                  ? "Keine Gewerke für diese Auswahl gefunden."
                  : "Noch keine Gewerke vorhanden. Legen Sie die erste Kalkulationseinheit an."}
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--color-surface-muted)] text-left text-xs font-medium text-[var(--color-muted-foreground)]">
                  <tr>
                    <th className="px-4 py-2.5">Bezeichnung</th>
                    <th className="px-4 py-2.5">Einheit</th>
                    <th className="px-4 py-2.5">Kalkulation</th>
                    <th className="px-4 py-2.5 text-right">Verkaufspreis</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {gewerke.map((g) => (
                    <tr
                      key={g.id}
                      className="border-t border-[var(--color-border)] hover:bg-[var(--color-surface-muted)]/40"
                    >
                      <td className="px-4 py-2.5 font-medium">
                        <button
                          type="button"
                          onClick={() => void onAnsehen(g)}
                          className="text-left hover:underline"
                        >
                          {g.bezeichnung}
                        </button>
                      </td>
                      <td className="px-4 py-2.5 text-[var(--color-muted-foreground)]">
                        {g.einheit}
                      </td>
                      <td className="px-4 py-2.5">
                        <Badge variant="neutral">{KALKULATIONSART_LABELS[g.kalkulationsart]}</Badge>
                      </td>
                      <td className="px-4 py-2.5 text-right font-medium">
                        {formatEuro(g.vk_preis)}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            aria-label={`Gewerk ${g.bezeichnung} bearbeiten`}
                            onClick={() => void onBearbeiten(g)}
                            className="rounded p-1 hover:bg-[var(--color-border)]"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            type="button"
                            aria-label={`Gewerk ${g.bezeichnung} löschen`}
                            onClick={() => void onLoeschen(g)}
                            className="rounded p-1 text-[var(--color-danger)] hover:bg-[var(--color-border)]"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <Dialog
        open={editorOffen}
        onOpenChange={setEditorOffen}
        title={bearbeitet ? "Gewerk bearbeiten" : "Neues Gewerk"}
        description="Kostenzeilen ergeben den Verkaufspreis (EK + Zuschlag)."
        className="max-w-3xl"
      >
        <GewerkEditor
          gewerk={bearbeitet}
          kategorien={kategorien}
          onGespeichert={() => void onGespeichert()}
          onAbbrechen={() => {
            setEditorOffen(false);
            setBearbeitet(null);
          }}
        />
      </Dialog>

      <Dialog
        open={detailOffen}
        onOpenChange={setDetailOffen}
        title="Gewerk-Details"
        className="max-w-2xl"
      >
        {detail && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <div className="text-[var(--color-muted-foreground)]">Bezeichnung</div>
                <div className="font-medium">{detail.bezeichnung}</div>
              </div>
              <div>
                <div className="text-[var(--color-muted-foreground)]">Einheit</div>
                <div className="font-medium">{detail.einheit}</div>
              </div>
              <div>
                <div className="text-[var(--color-muted-foreground)]">Kalkulationsart</div>
                <div className="font-medium">
                  {KALKULATIONSART_LABELS[detail.kalkulationsart]}
                </div>
              </div>
              <div>
                <div className="text-[var(--color-muted-foreground)]">Steuersatz</div>
                <div className="font-medium">{detail.steuersatz} %</div>
              </div>
            </div>
            {detail.langbeschreibung && (
              <p className="text-sm text-[var(--color-muted-foreground)]">
                {detail.langbeschreibung}
              </p>
            )}

            <div>
              <h3 className="mb-2 text-sm font-semibold text-[var(--color-foreground)]">
                Kostenzeilen
              </h3>
              <div className="overflow-hidden rounded-[var(--radius-md)] border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-surface-muted)] text-left text-xs font-medium text-[var(--color-muted-foreground)]">
                    <tr>
                      <th className="px-3 py-2">Kostenart</th>
                      <th className="px-3 py-2">Beschreibung</th>
                      <th className="px-3 py-2 text-right">Menge</th>
                      <th className="px-3 py-2">Einheit</th>
                      <th className="px-3 py-2 text-right">EK €</th>
                      <th className="px-3 py-2 text-right">+ %</th>
                      <th className="px-3 py-2 text-right">VK</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.kostenzeilen.map((z) => (
                      <tr key={z.id} className="border-t border-[var(--color-border)]">
                        <td className="px-3 py-2">{z.kostenart}</td>
                        <td className="px-3 py-2">{z.beschreibung || "—"}</td>
                        <td className="px-3 py-2 text-right">{z.menge}</td>
                        <td className="px-3 py-2">{z.einheit}</td>
                        <td className="px-3 py-2 text-right">{formatEuro(z.ek_einzelpreis)}</td>
                        <td className="px-3 py-2 text-right">{z.zuschlag_prozent} %</td>
                        <td className="px-3 py-2 text-right font-medium">{formatEuro(z.vk_preis)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
              <span className="text-[var(--color-muted-foreground)]">Verkaufspreis</span>
              <span className="font-semibold">{formatEuro(detail.vk_preis)}</span>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => void onBearbeiten(detail)}>
                <Pencil size={14} /> Bearbeiten
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
