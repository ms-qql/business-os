"use client";

import * as React from "react";
import { Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ApiError } from "@/lib/api/client";
import {
  getKategorien,
  addKategorie,
  updateKategorie,
  deleteKategorie,
  type GewerkKategorie,
} from "@/lib/api/gewerke";

const SERVER_FEHLER = "Keine Verbindung zum Server. Änderungen wurden nicht gespeichert.";

/** Kategorien-Verwaltung (linke Spalte der Kalkulationsseite). Inhaber/Büro. */
export function KategorieVerwaltung({
  auswahl,
  onAuswahl,
  onChange,
}: {
  auswahl: string | null;
  onAuswahl: (id: string | null) => void;
  onChange: () => void;
}) {
  const [kategorien, setKategorien] = React.useState<GewerkKategorie[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [neu, setNeu] = React.useState("");
  const [speichert, setSpeichert] = React.useState(false);
  const [bearbeitetId, setBearbeitetId] = React.useState<string | null>(null);
  const [bearbeitetName, setBearbeitetName] = React.useState("");

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setKategorien(await getKategorien());
    } catch (err) {
      setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onHinzufuegen(e: React.FormEvent) {
    e.preventDefault();
    const name = neu.trim();
    if (!name) {
      setError("Kategoriename ist erforderlich.");
      return;
    }
    setSpeichert(true);
    setError(null);
    try {
      await addKategorie({ name });
      setNeu("");
      await laden();
      onChange();
    } catch (err) {
      setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
    } finally {
      setSpeichert(false);
    }
  }

  async function onUmbenennen(id: string) {
    const name = bearbeitetName.trim();
    if (!name) {
      setBearbeitetId(null);
      return;
    }
    setSpeichert(true);
    setError(null);
    try {
      await updateKategorie(id, { name });
      setBearbeitetId(null);
      await laden();
      onChange();
    } catch (err) {
      setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
    } finally {
      setSpeichert(false);
    }
  }

  async function onLoeschen(id: string) {
    setError(null);
    try {
      await deleteKategorie(id);
      if (auswahl === id) onAuswahl(null);
      await laden();
      onChange();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("Kategorie wird noch von mindestens einem Gewerk verwendet und kann nicht gelöscht werden.");
      } else {
        setError(!(err instanceof ApiError) ? SERVER_FEHLER : err.message);
      }
    }
  }

  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <h2 className="mb-3 text-sm font-semibold text-[var(--color-foreground)]">Kategorien</h2>
      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : (
        <ul className="space-y-1">
          <li>
            <button
              type="button"
              onClick={() => onAuswahl(null)}
              className={`flex w-full items-center justify-between rounded-[var(--radius-md)] px-2 py-1.5 text-left text-sm ${
                auswahl === null
                  ? "bg-[var(--color-surface-muted)] font-medium text-[var(--color-foreground)]"
                  : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-surface-muted)]"
              }`}
            >
              <span>Alle Gewerke</span>
              <span className="text-xs text-[var(--color-muted-foreground)]" />
            </button>
          </li>
          {kategorien.map((k) => (
            <li key={k.id}>
              {bearbeitetId === k.id ? (
                <div className="flex items-center gap-1 px-1 py-1">
                  <Input
                    value={bearbeitetName}
                    onChange={(e) => setBearbeitetName(e.target.value)}
                    className="h-8 text-sm"
                    aria-label="Kategorie umbenennen"
                  />
                  <Button size="sm" variant="secondary" disabled={speichert} onClick={() => onUmbenennen(k.id)}>
                    OK
                  </Button>
                </div>
              ) : (
                <div
                  className={`group flex items-center justify-between rounded-[var(--radius-md)] px-2 py-1.5 ${
                    auswahl === k.id ? "bg-[var(--color-surface-muted)]" : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onAuswahl(k.id)}
                    className={`flex-1 text-left text-sm ${
                      auswahl === k.id
                        ? "font-medium text-[var(--color-foreground)]"
                        : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
                    }`}
                  >
                    {k.name}
                    <span className="ml-1 text-xs text-[var(--color-muted-foreground)]">
                      ({k.anzahl_gewerke})
                    </span>
                  </button>
                  <div className="flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      type="button"
                      aria-label={`Kategorie ${k.name} umbenennen`}
                      onClick={() => {
                        setBearbeitetId(k.id);
                        setBearbeitetName(k.name);
                      }}
                      className="rounded p-1 hover:bg-[var(--color-border)]"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      type="button"
                      aria-label={`Kategorie ${k.name} löschen`}
                      onClick={() => onLoeschen(k.id)}
                      className="rounded p-1 text-[var(--color-danger)] hover:bg-[var(--color-border)]"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={onHinzufuegen} className="mt-3 flex items-end gap-2 border-t border-[var(--color-border)] pt-3">
        <div className="flex-1">
          <Label htmlFor="kat-neu">Neue Kategorie</Label>
          <Input
            id="kat-neu"
            value={neu}
            onChange={(e) => setNeu(e.target.value)}
            placeholder="z. B. Sanitär"
            className="h-8 text-sm"
          />
        </div>
        <Button type="submit" size="sm" variant="secondary" disabled={speichert}>
          <Plus size={14} />
          Anlegen
        </Button>
      </form>
    </div>
  );
}

export { SERVER_FEHLER as KATEGORIE_SERVER_FEHLER };
