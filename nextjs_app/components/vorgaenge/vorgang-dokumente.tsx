"use client";

import * as React from "react";
import { FileText, Image as ImageIcon, Download, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import {
  uploadDokument,
  dokumentDownloadUrl,
  deleteDokument,
  type VorgangDokument,
} from "@/lib/api/vorgaenge";
import { ApiError } from "@/lib/api/client";

const ERLAUBTE_TYPEN = ["image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"];
const MAX_GROESSE = 15 * 1024 * 1024;

export function VorgangDokumente({
  vorgangId,
  dokumente,
  darfSchreiben,
  onChange,
}: {
  vorgangId: string;
  dokumente: VorgangDokument[];
  darfSchreiben: boolean;
  onChange: (dokumente: VorgangDokument[]) => void;
}) {
  const [error, setError] = React.useState<string | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    e.target.value = "";
    if (!datei) return;
    setError(null);
    if (!ERLAUBTE_TYPEN.includes(datei.type)) {
      setError("Nur Fotos (JPEG/PNG/WebP) oder PDF sind erlaubt.");
      return;
    }
    if (datei.size > MAX_GROESSE) {
      setError("Datei ist zu groß (max. 15 MB).");
      return;
    }
    setUploading(true);
    try {
      const neu = await uploadDokument(vorgangId, datei);
      onChange([neu, ...dokumente]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload fehlgeschlagen.");
    } finally {
      setUploading(false);
    }
  }

  async function onDownload(d: VorgangDokument) {
    setError(null);
    try {
      const { download_url } = await dokumentDownloadUrl(vorgangId, d.id);
      window.open(download_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Download fehlgeschlagen.");
    }
  }

  async function onDelete(d: VorgangDokument) {
    if (!window.confirm(`„${d.dateiname}" wirklich löschen?`)) return;
    setError(null);
    try {
      await deleteDokument(vorgangId, d.id);
      onChange(dokumente.filter((x) => x.id !== d.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Löschen fehlgeschlagen.");
    }
  }

  return (
    <div className="space-y-3">
      {darfSchreiben && (
        <div>
          <input
            ref={inputRef}
            type="file"
            accept={ERLAUBTE_TYPEN.join(",")}
            className="hidden"
            onChange={onUpload}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
          >
            <Upload size={16} />
            {uploading ? "Lädt hoch …" : "Foto oder PDF hochladen"}
          </Button>
        </div>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

      {dokumente.length === 0 ? (
        <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Dokumente.</p>
      ) : (
        <ul className="divide-y divide-[var(--color-border)]">
          {dokumente.map((d) => (
            <li key={d.id} className="flex items-center justify-between py-2 text-sm">
              <div className="flex items-center gap-2">
                {d.content_type === "application/pdf" ? <FileText size={16} /> : <ImageIcon size={16} />}
                <span>{d.dateiname}</span>
                <span className="text-xs text-[var(--color-muted-foreground)]">
                  {(d.groesse_bytes / 1024).toFixed(0)} KB
                </span>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => onDownload(d)} aria-label="Herunterladen">
                  <Download size={16} />
                </Button>
                {darfSchreiben && (
                  <Button variant="ghost" size="sm" onClick={() => onDelete(d)} aria-label="Löschen">
                    <Trash2 size={16} />
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
