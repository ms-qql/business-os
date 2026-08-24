"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, FileText, Globe, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  createFormular,
  getFormulare,
  isFormularConflict,
} from "@/lib/api/formulare";
import type { FormularListeItem } from "@/lib/schemas/formular";

export default function FormularePage() {
  const router = useRouter();
  const [items, setItems] = React.useState<FormularListeItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [creating, setCreating] = React.useState(false);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getFormulare(200, 0);
      setItems(res.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function neu(vorlage?: "shk" | "entruempelung") {
    setCreating(true);
    setError(null);
    try {
      const formular = await createFormular(vorlage);
      router.push(`/formulare/editor/${formular.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Anlegen fehlgeschlagen.");
      setCreating(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Formulare</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Erstellen und veröffentlichen Sie Anfrageformulare aus vorgegebenen Feldtypen.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => void neu("shk")} disabled={creating}>
            <Plus size={16} /> SHK-Vorlage
          </Button>
          <Button variant="outline" onClick={() => void neu("entruempelung")} disabled={creating}>
            <Plus size={16} /> Entrümpelungs-Vorlage
          </Button>
          <Button onClick={() => void neu()} disabled={creating}>
            <Plus size={16} /> Leeres Formular
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-[var(--color-muted-foreground)]">
            Noch keine Formulare vorhanden. Legen Sie ein leeres Formular oder starten Sie
            mit einer Branchenvorlage.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((f) => (
            <Link key={f.id} href={`/formulare/editor/${f.id}`} className="block">
              <Card className="h-full transition-colors hover:border-[var(--color-brand)]">
                <CardContent className="space-y-2 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 font-medium">
                      <FileText size={18} className="text-[var(--color-muted-foreground)]" />
                      {f.name}
                    </div>
                    {f.veroeffentlicht ? (
                      <span className="flex items-center gap-1 text-xs font-medium text-[var(--color-success)]">
                        <Globe size={14} /> live
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs font-medium text-[var(--color-muted-foreground)]">
                        <EyeOff size={14} /> Entwurf
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-muted-foreground)]">
                    {f.veroeffentlicht
                      ? `Version ${f.version_nummer} · aktualisiert ${new Date(f.aktualisiert_am).toLocaleDateString("de-DE")}`
                      : `Entwurf · aktualisiert ${new Date(f.aktualisiert_am).toLocaleDateString("de-DE")}`}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
