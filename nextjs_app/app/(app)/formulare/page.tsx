"use client";

import * as React from "react";
import { Plus, FileText, Share2, Eye, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label, Alert } from "@/components/ui/label";
import { Dialog } from "@/components/ui/dialog";
import { ApiError } from "@/lib/api/client";
import {
  createFormular,
  isFormularConflict,
  listFormulare,
} from "@/lib/api/formulare";
import type { FormularListeItem } from "@/lib/schemas/formular";
import { EinbindungDialog } from "@/components/formulare/einbindung-dialog";

export default function FormularePage() {
  const [items, setItems] = React.useState<FormularListeItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [neuOffen, setNeuOffen] = React.useState(false);
  const [anlegenLaeuft, setAnlegenLaeuft] = React.useState(false);
  const [anlegenFehler, setAnlegenFehler] = React.useState<string | null>(null);
  const [vorlage, setVorlage] = React.useState<"" | "shk" | "entruempelung">("");

  const [einbindungId, setEinbindungId] = React.useState<string | null>(null);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listFormulare({ limit: 200 });
      setItems(res.items);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Formulare konnten nicht geladen werden.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onAnlegen() {
    setAnlegenLaeuft(true);
    setAnlegenFehler(null);
    try {
      const f = await createFormular(vorlage || undefined);
      setNeuOffen(false);
      setVorlage("");
      // Direkt in den Editor springen.
      window.location.href = `/formulare/${f.id}`;
    } catch (err) {
      if (isFormularConflict(err)) {
        setAnlegenFehler("Bitte laden Sie die Seite neu und versuchen Sie es erneut.");
      } else {
        setAnlegenFehler(
          err instanceof ApiError ? err.message : "Anlegen fehlgeschlagen.",
        );
      }
    } finally {
      setAnlegenLaeuft(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Formulare</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Anfrageformulare aus dem festen Feldtypen-Katalog erstellen und
            veröffentlichen.
          </p>
        </div>
        <Button onClick={() => setNeuOffen(true)}>
          <Plus size={16} /> Neues Formular
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText size={32} className="mx-auto text-[var(--color-muted-foreground)]" />
            <p className="mt-3 text-sm text-[var(--color-muted-foreground)]">
              Noch keine Formulare vorhanden. Legen Sie ein leeres Formular oder
              eine Branchenvorlage an.
            </p>
            <Button className="mt-4" onClick={() => setNeuOffen(true)}>
              <Plus size={16} /> Neues Formular
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((f) => (
            <Card key={f.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="break-words">{f.name}</CardTitle>
                  {f.veroeffentlicht ? (
                    <Badge variant="success">Veröffentlicht</Badge>
                  ) : (
                    <Badge variant="warning">Entwurf</Badge>
                  )}
                </div>
                <CardDescription>
                  {f.komplexitaet === "einfach" ? "Einfach" : "Erweitert"} ·{" "}
                  {new Date(f.updated_at).toLocaleDateString("de-DE")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  <a href={`/formulare/${f.id}`}>
                    <Button variant="outline" size="sm">
                      <Pencil size={14} /> Bearbeiten
                    </Button>
                  </a>
                  {f.veroeffentlicht && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEinbindungId(f.id)}
                      >
                        <Share2 size={14} /> Einbinden
                      </Button>
                      <a
                        href={f.public_id ? `/site/formulare/${f.public_id}` : "#"}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <Button variant="outline" size="sm">
                          <Eye size={14} /> Öffentlich
                        </Button>
                      </a>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog
        open={neuOffen}
        onOpenChange={setNeuOffen}
        title="Neues Formular"
        description="Starten Sie leer oder mit einer vorgegebenen Branchenvorlage."
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="vorlage">Vorlage</Label>
            <select
              id="vorlage"
              value={vorlage}
              onChange={(e) => setVorlage(e.target.value as typeof vorlage)}
              className="h-10 w-full rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
            >
              <option value="">Leeres Formular</option>
              <option value="shk">SHK-Vorlage</option>
              <option value="entruempelung">Entrümpelungs-Vorlage</option>
            </select>
          </div>
          {anlegenFehler && <Alert variant="danger">{anlegenFehler}</Alert>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setNeuOffen(false)}>
              Abbrechen
            </Button>
            <Button onClick={onAnlegen} disabled={anlegenLaeuft}>
              {anlegenLaeuft ? "Wird angelegt …" : "Anlegen"}
            </Button>
          </div>
        </div>
      </Dialog>

      {einbindungId && (
        <EinbindungDialog formularId={einbindungId} onClose={() => setEinbindungId(null)} />
      )}
    </div>
  );
}
