"use client";

import * as React from "react";
import { Alert } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError } from "@/lib/api/client";
import { getRechnungssteller, type RechnungsstellerProfil } from "@/lib/api/rechnungen";
import { RechnungsstellerProfilForm } from "@/components/rechnungen/rechnungssteller-profil-form";
import { useAuth } from "@/app/providers";

export default function RechnungsstellerEinstellungenPage() {
  const { user } = useAuth();
  const [profil, setProfil] = React.useState<RechnungsstellerProfil | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Rechnungssteller ist Inhaber-only (Tech Design Abschnitt C).
  const darfBearbeiten = user?.rolle === "Inhaber";

  React.useEffect(() => {
    getRechnungssteller()
      .then(setProfil)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Profil konnte nicht geladen werden."),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Rechnungssteller</h1>
        <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
          Stammdaten für PDF-Rechnungen. Eine vollständige Pflege ist Voraussetzung für den Versand.
          Nur Inhaber.
        </p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {!darfBearbeiten ? (
        <Alert variant="info">
          Das Rechnungssteller-Profil kann nur vom Inhaber gepflegt werden. Bitte wenden Sie sich
          an den Inhaber, um Name, Anschrift oder Steuerkennzeichnung zu ändern.
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Rechnungssteller-Profil</CardTitle>
            <CardDescription>
              Diese Daten erscheinen auf jeder Rechnung. Sie werden bei Versand unveränderlich
              mit dem Beleg gespeichert.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RechnungsstellerProfilForm initial={profil} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
