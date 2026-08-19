"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useAuth } from "@/app/providers";
import {
  getRechnung,
  getRechnungPdfUrl,
  setzeZahlungsstatus,
  rechnungStornieren,
  type Rechnung,
  type Zahlungsstatus,
} from "@/lib/api/rechnungen";
import type { Rolle } from "@/lib/theme/tokens";
import { kannSchreiben } from "@/lib/theme/tokens";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label, Alert } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBerlinDatum, formatBerlinDateTime } from "@/lib/zeit";

function formatEuro(wert: number): string {
  return wert.toLocaleString("de-DE", { style: "currency", currency: "EUR" });
}

function statusBadgeVariant(status: Rechnung["status"]): "success" | "neutral" | "danger" {
  if (status === "versendet") return "success";
  if (status === "storniert") return "danger";
  return "neutral";
}

function statusLabel(status: Rechnung["status"]): string {
  if (status === "versendet") return "Versendet";
  if (status === "storniert") return "Storniert";
  return "Entwurf";
}

function zahlungsBadgeVariant(z: Zahlungsstatus): "success" | "neutral" | "danger" {
  if (z === "Bezahlt") return "success";
  if (z === "Storniert") return "danger";
  return "neutral";
}

export default function RechnungDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const rolle = (user?.rolle ?? "Büro") as Rolle;
  const darfSchreiben = kannSchreiben(rolle);

  const [rechnung, setRechnung] = React.useState<Rechnung | null>(null);
  const [pdfUrl, setPdfUrl] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getRechnung(id);
      setRechnung(r);
      try {
        const { download_url } = await getRechnungPdfUrl(id);
        setPdfUrl(download_url);
      } catch {
        setPdfUrl(null);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rechnung konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onZahlungsstatus(zahlungsstatus: Zahlungsstatus) {
    if (!rechnung) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      setRechnung(await setzeZahlungsstatus(rechnung.id, zahlungsstatus));
      setInfo("Zahlungsstatus aktualisiert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Statusänderung fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  async function onStorno() {
    if (!rechnung) return;
    if (!window.confirm("Rechnung wirklich stornieren? Der Originalbeleg bleibt abrufbar.")) return;
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      setRechnung(await rechnungStornieren(rechnung.id));
      setInfo("Rechnung wurde storniert.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Storno fehlgeschlagen.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }
  if (error && !rechnung) {
    return <Alert variant="danger">{error}</Alert>;
  }
  if (!rechnung) return null;

  const istVersendet = rechnung.status === "versendet";
  const istStorniert = rechnung.status === "storniert";
  const istEntwurf = rechnung.status === "entwurf";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            href={`/vorgaenge/${rechnung.vorgang_id}`}
            className="rounded-[var(--radius-md)] p-1 text-[var(--color-muted-foreground)] hover:bg-[var(--color-surface-muted)]"
            aria-label="Zurück zum Vorgang"
          >
            <ArrowLeft size={18} />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">{rechnung.rechnungsnummer}</h1>
            <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
              Status: <Badge variant={statusBadgeVariant(rechnung.status)}>{statusLabel(rechnung.status)}</Badge>
              {istVersendet && (
                <>
                  {" "}· Zahlung:{" "}
                  <Badge variant={zahlungsBadgeVariant(rechnung.zahlungsstatus)}>
                    {rechnung.zahlungsstatus}
                  </Badge>
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle>Kopfdaten</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-[var(--color-muted-foreground)]">Rechnungsdatum:</span>{" "}
            {rechnung.rechnungsdatum ? formatBerlinDatum(rechnung.rechnungsdatum) : "—"}
          </p>
          <p>
            <span className="text-[var(--color-muted-foreground)]">Leistungsdatum:</span>{" "}
            {rechnung.leistungsdatum ? formatBerlinDatum(rechnung.leistungsdatum) : "—"}
          </p>
          <p>
            <span className="text-[var(--color-muted-foreground)]">Empfänger:</span>{" "}
            {rechnung.empfaenger_email ?? "—"}
          </p>
          {rechnung.versendet_at && (
            <p>
              <span className="text-[var(--color-muted-foreground)]">Versendet am:</span>{" "}
              {formatBerlinDateTime(rechnung.versendet_at)}
            </p>
          )}
          {rechnung.storniert_at && (
            <p>
              <span className="text-[var(--color-muted-foreground)]">Storniert am:</span>{" "}
              {formatBerlinDateTime(rechnung.storniert_at)}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Positionen</CardTitle>
        </CardHeader>
        <CardContent>
          {rechnung.positionen.length === 0 ? (
            <p className="text-sm text-[var(--color-muted-foreground)]">Keine Positionen.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bezeichnung</TableHead>
                  <TableHead>Menge</TableHead>
                  <TableHead>Einzelpreis</TableHead>
                  <TableHead>Steuersatz</TableHead>
                  <TableHead>Summe</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rechnung.positionen.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>{p.bezeichnung}</TableCell>
                    <TableCell>
                      {p.menge} {p.einheit}
                    </TableCell>
                    <TableCell>{formatEuro(p.netto_einzelpreis)}</TableCell>
                    <TableCell>{p.steuersatz} %</TableCell>
                    <TableCell>{formatEuro(p.positions_summe)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          <div className="mt-4 grid grid-cols-3 gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)] p-3 text-sm">
            <div>
              <p className="text-[var(--color-muted-foreground)]">Netto</p>
              <p className="font-medium">{formatEuro(rechnung.netto_summe)}</p>
            </div>
            <div>
              <p className="text-[var(--color-muted-foreground)]">Steuer</p>
              <p className="font-medium">{formatEuro(rechnung.steuer_summe)}</p>
            </div>
            <div>
              <p className="text-[var(--color-muted-foreground)]">Brutto</p>
              <p className="font-medium">{formatEuro(rechnung.brutto_summe)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {pdfUrl && (
        <Card>
          <CardHeader>
            <CardTitle>{istEntwurf ? "PDF-Vorschau" : "Versendetes PDF"}</CardTitle>
          </CardHeader>
          <CardContent>
            <iframe
              src={pdfUrl}
              title={istEntwurf ? "PDF-Vorschau der Rechnung" : "Versendetes Rechnungs-PDF"}
              className="h-[40rem] w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
            />
          </CardContent>
        </Card>
      )}

      {darfSchreiben && istVersendet && !istStorniert && (
        <Card>
          <CardHeader>
            <CardTitle>Zahlungsstatus & Storno</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <Label htmlFor="zahlungsstatus">Zahlungsstatus</Label>
                <Select
                  id="zahlungsstatus"
                  value={rechnung.zahlungsstatus}
                  disabled={busy}
                  onChange={(e) => onZahlungsstatus(e.target.value as Zahlungsstatus)}
                  className="w-auto"
                >
                  <option value="Offen">Offen</option>
                  <option value="Bezahlt">Bezahlt</option>
                  <option value="Storniert">Storniert</option>
                </Select>
              </div>
              <Button variant="danger" disabled={busy} onClick={onStorno}>
                Rechnung stornieren
              </Button>
            </div>
            <p className="text-xs text-[var(--color-muted-foreground)]">
              Eine Statusänderung verändert weder das PDF noch die Rechnungspositionen. „Storniert"
              wird ausschließlich über diesen Storno-Vorgang gesetzt.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
