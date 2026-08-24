import * as React from "react";
import { Check, Package } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import {
  getBranchenpakete,
  uebernehmeBranchenpaket,
  type BranchenpaketKennung,
  type BranchenpaketOption,
  type BranchenpaketUebernahmeResult,
} from "@/lib/api/onboarding";

/**
 * Branchenpaket-Wahl (PROJ-14, Tech Design Flächen/Branchenpaket).
 *
 * - Stellt Inhaber-only genau zwei Wahlkarten (SHK / Entrümpelung) mit
 *   deutscher Beschreibung; die Auswahl ist nur UI-Zustand (ADR-14-4: Wahl wird
 *   erst beim Übernehmen persistent).
 * - Ruft GET /onboarding/branchenpakete vor der Auswahl; die Bestätigung
 *   triggert POST /onboarding/branchenpaket-uebernehmen (atomar, einmalig).
 * - Ergebnis- und Fehlerdarstellung der atomaren Übernahme: Erfolg zeigt die
 *   übernommene Paketinfo; 409/422 werden mit deutscher Meldung angezeigt.
 * - Karten stapeln ab 375 px untereinander (Acceptance-Kriterium, kein horizontales Scrollen).
 */
export function BranchenpaketWahl({
  onUebernommen,
}: {
  /** Wird nach erfolgreicher atomarer Übernahme mit dem Server-Ergebnis aufgerufen. */
  onUebernommen: (ergebnis: BranchenpaketUebernahmeResult) => void;
}) {
  const [pakete, setPakete] = React.useState<BranchenpaketOption[]>([]);
  const [ladeFehler, setLadeFehler] = React.useState<string | null>(null);
  const [gewaehlt, setGewaehlt] = React.useState<BranchenpaketKennung | null>(null);
  const [pending, setPending] = React.useState(false);
  const [fehler, setFehler] = React.useState<string | null>(null);
  const [erfolg, setErfolg] = React.useState<BranchenpaketUebernahmeResult | null>(null);

  const laden = React.useCallback(async () => {
    setLadeFehler(null);
    try {
      const res = await getBranchenpakete();
      setPakete(res.pakete);
    } catch (err) {
      setLadeFehler(
        err instanceof ApiError
          ? err.message
          : "Die Branchenpakete konnten nicht geladen werden.",
      );
    }
  }, []);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  async function onUebernehmen(kennung: BranchenpaketKennung) {
    setPending(true);
    setFehler(null);
    try {
      const ergebnis = await uebernehmeBranchenpaket(kennung);
      setErfolg(ergebnis);
      onUebernommen(ergebnis);
    } catch (err) {
      if (err instanceof ApiError) {
        // 409: bereits übernommen oder Ziel nicht leer; 422: defekter/ungültiger Katalog.
        if (err.status === 409) {
          setFehler(
            "Das Branchenpaket wurde für diesen Betrieb bereits übernommen. Eine erneute Übernahme ist nicht möglich.",
          );
        } else if (err.status === 422) {
          setFehler(err.message || "Das ausgewählte Branchenpaket ist derzeit nicht verfügbar.");
        } else {
          setFehler(err.message);
        }
      } else {
        setFehler("Die Übernahme ist fehlgeschlagen. Bitte versuchen Sie es erneut.");
      }
    } finally {
      setPending(false);
    }
  }

  if (erfolg) {
    return (
      <div className="mt-2 space-y-3">
        <Alert variant="success">
          Das Branchenpaket „{erfolg.name}“ wurde erfolgreich eingerichtet. Ihr Betrieb startet nun
          mit den passenden Formularen, Leistungsseiten und Beispielinhalten.
        </Alert>
      </div>
    );
  }

  if (ladeFehler) {
    return (
      <div className="mt-2">
        <Alert variant="danger">{ladeFehler}</Alert>
      </div>
    );
  }

  if (pakete.length === 0) {
    return (
      <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
    );
  }

  return (
    <div className="mt-2 space-y-4">
      <p className="text-sm text-[var(--color-muted-foreground)]">
        Wählen Sie das Branchenpaket für Ihren Betrieb. Die Auswahl legt einmalig passende
        Startinhalte in Ihrem Betrieb an und kann nach der Einrichtung nicht mehr geändert werden.
      </p>

      {fehler && <Alert variant="danger">{fehler}</Alert>}

      <div className="grid gap-3 md:grid-cols-2">
        {pakete.map((p) => {
          const istGewaehlt = gewaehlt === p.kennung;
          return (
            <Card
              key={p.kennung}
              role="button"
              tabIndex={0}
              aria-pressed={istGewaehlt}
              aria-label={`Branchenpaket ${p.name} auswählen`}
              onClick={() => setGewaehlt(p.kennung)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setGewaehlt(p.kennung);
                }
              }}
              className={
                "cursor-pointer p-4 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand)] " +
                (istGewaehlt
                  ? "border-[var(--color-brand)] ring-1 ring-[var(--color-brand)]"
                  : "hover:border-[var(--color-brand)]")
              }
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Package size={18} className="text-[var(--color-brand)]" />
                  <h3 className="font-semibold text-[var(--color-foreground)]">{p.name}</h3>
                </div>
                {istGewaehlt && (
                  <Check size={18} className="shrink-0 text-[var(--color-brand)]" aria-hidden />
                )}
              </div>
              <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
                {p.beschreibung}
              </p>
            </Card>
          );
        })}
      </div>

      <div className="flex items-center justify-end">
        <Button
          type="button"
          disabled={!gewaehlt || pending}
          onClick={() => gewaehlt && onUebernehmen(gewaehlt)}
        >
          {pending ? "Wird übernommen …" : "Branchenpaket übernehmen"}
        </Button>
      </div>
    </div>
  );
}
