import type { VorgangHistorieEintrag } from "@/lib/api/vorgaenge";

const EREIGNIS_LABEL: Record<string, string> = {
  angelegt: "Angelegt",
  status_geaendert: "Status geändert",
  feld_geaendert: "Feld geändert",
  zugewiesen: "Zugewiesen",
  dokument_hochgeladen: "Dokument hochgeladen",
  dokument_geloescht: "Dokument gelöscht",
};

export function VorgangChronik({ eintraege }: { eintraege: VorgangHistorieEintrag[] }) {
  if (eintraege.length === 0) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Noch keine Änderungen.</p>;
  }
  return (
    <ol className="space-y-3">
      {eintraege.map((e) => (
        <li key={e.id} className="border-l-2 border-[var(--color-border)] pl-3 text-sm">
          <div className="text-[var(--color-foreground)]">
            {EREIGNIS_LABEL[e.ereignis] ?? e.ereignis}
            {e.detail ? `: ${e.detail}` : ""}
          </div>
          <div className="mt-0.5 text-xs text-[var(--color-muted-foreground)]">
            {new Date(e.created_at).toLocaleString("de-DE")}
          </div>
        </li>
      ))}
    </ol>
  );
}
