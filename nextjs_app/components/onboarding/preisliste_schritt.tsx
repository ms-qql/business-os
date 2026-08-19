import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError } from "@/lib/api/client";
import {
  getKatalog,
  addKatalogPosition,
  deleteKatalogPosition,
  importKatalogCsv,
  type KatalogPosition,
  type KatalogImportResult,
} from "@/lib/api/katalog";

const LEER_POSITION = { bezeichnung: "", einheit: "Stk.", netto_einzelpreis: "", steuersatz: "19" };

/**
 * Schritt 6 (Preisliste). Manuelles Anlegen von Katalogpositionen und CSV-Import.
 * Fehlerhafte Zeilen werden mit Zeilennummer und Grund gemeldet; korrekte Zeilen
 * der Datei werden übernommen (Acceptance-Kriterium). Die UI hängt allein an den
 * Typen in lib/api/katalog.ts, da der Datenmodell-Contract im Tech Design offen ist.
 */
export function PreislisteSchritt({ onChanged }: { onChanged: () => void }) {
  const [positionen, setPositionen] = React.useState<KatalogPosition[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  const [form, setForm] = React.useState({ ...LEER_POSITION });
  const [csvDatei, setCsvDatei] = React.useState<File | null>(null);
  const [importResult, setImportResult] = React.useState<KatalogImportResult | null>(null);
  const [importing, setImporting] = React.useState(false);

  const laden = React.useCallback(async () => {
    setLoading(true);
    try {
      const liste = await getKatalog();
      setPositionen(liste.positionen);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Preisliste konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    const preis = Number(String(form.netto_einzelpreis).replace(",", "."));
    const mwst = Number(String(form.steuersatz).replace(",", "."));
    if (!form.bezeichnung.trim()) {
      setError("Bezeichnung ist erforderlich.");
      return;
    }
    if (!Number.isFinite(preis) || preis < 0) {
      setError("Netto-Einzelpreis ist ungültig.");
      return;
    }
    setSaving(true);
    try {
      await addKatalogPosition({
        bezeichnung: form.bezeichnung.trim(),
        einheit: form.einheit.trim() || "Stk.",
        netto_einzelpreis: preis,
        steuersatz: Number.isFinite(mwst) ? mwst : 19,
      });
      setForm({ ...LEER_POSITION });
      await laden();
      onChanged();
      setInfo("Position hinzugefügt.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    setError(null);
    try {
      await deleteKatalogPosition(id);
      await laden();
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    }
  }

  async function onImport(e: React.FormEvent) {
    e.preventDefault();
    if (!csvDatei) return;
    setImporting(true);
    setError(null);
    setInfo(null);
    setImportResult(null);
    try {
      const res = await importKatalogCsv(csvDatei);
      setImportResult(res);
      await laden();
      onChanged();
      setCsvDatei(null);
      if (res.anzahl_uebernommen > 0) {
        setInfo(`${res.anzahl_uebernommen} Position(en) aus der Datei übernommen.`);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Import fehlgeschlagen.");
    } finally {
      setImporting(false);
    }
  }

  if (loading) {
    return <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }

  return (
    <div className="mt-2 space-y-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4">
      {error && <Alert variant="danger">{error}</Alert>}
      {info && <Alert variant="success">{info}</Alert>}

      <form onSubmit={onAdd} className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Label htmlFor="pl-bez">Bezeichnung</Label>
          <Input
            id="pl-bez"
            value={form.bezeichnung}
            onChange={(e) => setForm({ ...form, bezeichnung: e.target.value })}
            placeholder="z. B. Wartung Trinkwasser"
          />
        </div>
        <div>
          <Label htmlFor="pl-einheit">Einheit</Label>
          <Input
            id="pl-einheit"
            value={form.einheit}
            onChange={(e) => setForm({ ...form, einheit: e.target.value })}
            placeholder="Stk."
          />
        </div>
        <div>
          <Label htmlFor="pl-preis">Netto-Einzelpreis</Label>
          <Input
            id="pl-preis"
            value={form.netto_einzelpreis}
            onChange={(e) => setForm({ ...form, netto_einzelpreis: e.target.value })}
            placeholder="0,00"
            inputMode="decimal"
          />
        </div>
        <div>
          <Label htmlFor="pl-mwst">Steuersatz %</Label>
          <Input
            id="pl-mwst"
            value={form.steuersatz}
            onChange={(e) => setForm({ ...form, steuersatz: e.target.value })}
            placeholder="19"
            inputMode="decimal"
          />
        </div>
        <div className="flex items-end lg:col-span-5">
          <Button type="submit" disabled={saving}>
            {saving ? "Wird gespeichert …" : "Position hinzufügen"}
          </Button>
        </div>
      </form>

      <form onSubmit={onImport} className="flex flex-wrap items-end gap-3">
        <div>
          <Label htmlFor="pl-csv">CSV-Import</Label>
          <input
            id="pl-csv"
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setCsvDatei(e.target.files?.[0] ?? null)}
            className="block text-sm"
          />
        </div>
        <Button type="submit" variant="outline" disabled={importing || !csvDatei}>
          {importing ? "Importiere …" : "CSV importieren"}
        </Button>
        <span className="text-xs text-[var(--color-muted-foreground)]">
          Format: bezeichnung;einheit;netto_einzelpreis;steuersatz (Komma im Preis wird erkannt).
        </span>
      </form>

      {importResult && importResult.fehler.length > 0 && (
        <Alert variant="warning">
          <span className="font-medium">Fehlerhafte Zeilen (nicht übernommen):</span>
          <ul className="mt-1 list-disc pl-5">
            {importResult.fehler.map((f) => (
              <li key={f.zeile}>
                Zeile {f.zeile}: {f.grund}
              </li>
            ))}
          </ul>
        </Alert>
      )}

      {positionen.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Bezeichnung</TableHead>
              <TableHead>Einheit</TableHead>
              <TableHead className="text-right">Netto €</TableHead>
              <TableHead className="text-right">MwSt %</TableHead>
              <TableHead className="text-right">Aktion</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positionen.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.bezeichnung}</TableCell>
                <TableCell>{p.einheit}</TableCell>
                <TableCell className="text-right">
                  {p.netto_einzelpreis.toLocaleString("de-DE", { minimumFractionDigits: 2 })}
                </TableCell>
                <TableCell className="text-right">
                  {p.steuersatz.toLocaleString("de-DE")}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(p.id)}
                    aria-label={`Position ${p.bezeichnung} löschen`}
                  >
                    Entfernen
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Noch keine Positionen erfasst. Schritt 6 ist optional, empfohlen aber für das Schreiben von Angeboten.
        </p>
      )}
    </div>
  );
}
