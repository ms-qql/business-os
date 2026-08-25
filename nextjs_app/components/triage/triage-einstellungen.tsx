"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label, Alert } from "@/components/ui/label";
import {
  getTriageEinstellung,
  putTriageEinstellung,
  patchTriageKapazitaet,
  type TriageEinstellung,
  type TriageLeistungswert,
  type LeistungswertKlassifikation,
} from "@/lib/api/triage";
import { ApiError } from "@/lib/api/client";
import { getFormulare, getVeroeffentlichteVersion } from "@/lib/api/formulare";
import type { FormularListeItem, FormularSnapshot } from "@/lib/schemas/formular";

const OPTION_FELDTYPEN = ["dropdown", "kachel", "radio"] as const;

function istOptionsfeld(typ: string): boolean {
  return (OPTION_FELDTYPEN as readonly string[]).includes(typ);
}

export function TriageEinstellungen() {
  const [formulare, setFormulare] = React.useState<FormularListeItem[]>([]);
  const [einstellung, setEinstellung] = React.useState<TriageEinstellung | null>(null);
  const [ladeFehler, setLadeFehler] = React.useState<string | null>(null);
  const [laedt, setLaedt] = React.useState(true);

  const [ausgewFormularId, setAusgewFormularId] = React.useState("");
  const [snapshot, setSnapshot] = React.useState<FormularSnapshot | null>(null);
  const [snapshotLaedt, setSnapshotLaedt] = React.useState(false);
  const [snapshotFehler, setSnapshotFehler] = React.useState<string | null>(null);

  const [leistungsFeldId, setLeistungsFeldId] = React.useState("");
  const [wunschterminFeldId, setWunschterminFeldId] = React.useState("");
  const [werteMap, setWerteMap] = React.useState<Record<string, LeistungswertKlassifikation>>({});
  const [kapazitaet, setKapazitaet] = React.useState<string | null>(null);

  const [speichert, setSpeichert] = React.useState(false);
  const [speicherFehler, setSpeicherFehler] = React.useState<string | null>(null);
  const [gespeichert, setGespeichert] = React.useState(false);

  // Initial: Einstellung + veröffentlichte Formulare laden.
  React.useEffect(() => {
    void (async () => {
      setLaedt(true);
      setLadeFehler(null);
      try {
        const [e, liste] = await Promise.all([
          getTriageEinstellung(),
          getFormulare(100, 0),
        ]);
        setEinstellung(e);
        const veroeffentlichte = liste.items.filter((f) => f.veroeffentlicht);
        setFormulare(veroeffentlichte);
        if (e.leistungs_formular_id && veroeffentlichte.some((f) => f.id === e.leistungs_formular_id)) {
          setAusgewFormularId(e.leistungs_formular_id);
        }
      } catch (err) {
        setLadeFehler(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
      } finally {
        setLaedt(false);
      }
    })();
  }, []);

  // Snapshot der gewählten veröffentlichten Version laden und Felder vorbelegen.
  React.useEffect(() => {
    if (!ausgewFormularId) {
      setSnapshot(null);
      setLeistungsFeldId("");
      setWunschterminFeldId("");
      setWerteMap({});
      return;
    }
    void (async () => {
      setSnapshotLaedt(true);
      setSnapshotFehler(null);
      try {
        const snap = await getVeroeffentlichteVersion(ausgewFormularId);
        setSnapshot(snap);
        // Vorbelegung aus gespeicherter Einstellung, sofern dieselbe Formular-Version gemeint ist.
        if (einstellung && einstellung.leistungs_formular_id === ausgewFormularId) {
          setLeistungsFeldId(einstellung.leistungs_feld_id ?? "");
          setWunschterminFeldId(einstellung.wunschtermin_feld_id ?? "");
          const map: Record<string, LeistungswertKlassifikation> = {};
          for (const w of einstellung.leistungswerte) map[w.wert] = w.klassifikation;
          setWerteMap(map);
          setKapazitaet(einstellung.naechster_freier_termin ?? null);
        } else {
          setLeistungsFeldId("");
          setWunschterminFeldId("");
          setWerteMap({});
        }
      } catch (err) {
        setSnapshotFehler(err instanceof ApiError ? err.message : "Formular-Version konnte nicht geladen werden.");
        setSnapshot(null);
      } finally {
        setSnapshotLaedt(false);
      }
    })();
  }, [ausgewFormularId, einstellung]);

  const optionsfelder = React.useMemo(
    () => (snapshot ? snapshot.schritte.flatMap((s) => s.felder).filter((f) => istOptionsfeld(f.typ)) : []),
    [snapshot],
  );
  const datumfelder = React.useMemo(
    () => (snapshot ? snapshot.schritte.flatMap((s) => s.felder).filter((f) => f.typ === "datum") : []),
    [snapshot],
  );
  const ausgewFeld = optionsfelder.find((f) => f.id === leistungsFeldId) ?? null;

  function toggleWert(wert: string) {
    setWerteMap((prev) => {
      const next = { ...prev };
      const aktuell = next[wert] ?? "passend";
      next[wert] = aktuell === "passend" ? "unpassend" : "passend";
      return next;
    });
  }

  function klassifikationFuer(wert: string): LeistungswertKlassifikation {
    return werteMap[wert] ?? "passend";
  }

  async function onSpeichern() {
    if (!ausgewFormularId || !leistungsFeldId || !ausgewFeld) {
      setSpeicherFehler("Bitte ein veröffentlichtes Formular und ein Leistungsfeld auswählen.");
      return;
    }
    setSpeichert(true);
    setSpeicherFehler(null);
    setGespeichert(false);
    const leistungswerte: TriageLeistungswert[] = ausgewFeld.options.map((o) => ({
      wert: o.wert,
      klassifikation: klassifikationFuer(o.wert),
    }));
    try {
      const saved = await putTriageEinstellung({
        leistungs_formular_id: ausgewFormularId,
        leistungs_feld_id: leistungsFeldId,
        wunschtermin_feld_id: wunschterminFeldId || null,
        leistungswerte,
      });
      setEinstellung(saved);
      setGespeichert(true);
    } catch (err) {
      setSpeicherFehler(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onKapazitaetSpeichern() {
    setSpeichert(true);
    setSpeicherFehler(null);
    setGespeichert(false);
    try {
      const saved = await patchTriageKapazitaet(kapazitaet);
      setEinstellung(saved);
      setGespeichert(true);
    } catch (err) {
      setSpeicherFehler(err instanceof ApiError ? err.message : "Speichern des Termins fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  if (laedt) {
    return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  }
  if (ladeFehler) {
    return <Alert variant="danger">{ladeFehler}</Alert>;
  }
  if (formulare.length === 0) {
    return (
      <Alert variant="warning">
        Es ist noch kein Formular veröffentlicht. Bitte veröffentlichen Sie zuerst ein Anfrageformular,
        bevor Sie die Triage konfigurieren.
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Leistungsauswahl</CardTitle>
          <CardDescription>
            Wählen Sie ein veröffentlichtes Anfrageformular und daraus das Auswahlfeld, das die Leistung
            beschreibt. Markieren Sie anschließend dessen Werte als passend oder unpassend.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="formular">Anfrageformular</Label>
            <Select
              id="formular"
              value={ausgewFormularId}
              onChange={(e) => setAusgewFormularId(e.target.value)}
              className="w-full max-w-md"
            >
              <option value="">— Formular wählen —</option>
              {formulare.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </Select>
          </div>

          {snapshotLaedt && <p className="text-sm text-[var(--color-muted-foreground)]">Formular-Version wird geladen …</p>}
          {snapshotFehler && <Alert variant="danger">{snapshotFehler}</Alert>}

          {snapshot && (
            <>
              <div>
                <Label htmlFor="leistung">Leistungsfeld</Label>
                <Select
                  id="leistung"
                  value={leistungsFeldId}
                  onChange={(e) => setLeistungsFeldId(e.target.value)}
                  className="w-full max-w-md"
                >
                  <option value="">— Feld wählen —</option>
                  {optionsfelder.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </Select>
                {optionsfelder.length === 0 && (
                  <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
                    Dieses Formular enthält keine Auswahlfelder (Dropdown, Kachel oder Radio).
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="wunschtermin">Gewünschter Termin (optional)</Label>
                <Select
                  id="wunschtermin"
                  value={wunschterminFeldId}
                  onChange={(e) => setWunschterminFeldId(e.target.value)}
                  className="w-full max-w-md"
                >
                  <option value="">— Kein Wunschdatum-Feld —</option>
                  {datumfelder.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </Select>
                <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
                  Nur echte Datumsfelder sind zulässig. Ohne Auswahl wertet die Triage kein Wunschdatum aus.
                </p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {snapshot && ausgewFeld && (
        <Card>
          <CardHeader>
            <CardTitle>Leistungswerte: passend oder unpassend</CardTitle>
            <CardDescription>
              Jeder Wert des Feldes „{ausgewFeld.label}". Nicht markierte Werte gelten standardmäßig als passend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {ausgewFeld.options.length === 0 ? (
              <p className="text-sm text-[var(--color-muted-foreground)]">Dieses Feld hat keine Auswahloptionen.</p>
            ) : (
              ausgewFeld.options.map((o) => {
                const k = klassifikationFuer(o.wert);
                return (
                  <div key={o.wert} className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-[var(--color-border)] px-3 py-2">
                    <span className="text-sm">{o.label}</span>
                    <button
                      type="button"
                      onClick={() => toggleWert(o.wert)}
                      aria-pressed={k === "unpassend"}
                      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                        k === "unpassend"
                          ? "bg-red-50 text-[var(--color-danger)]"
                          : "bg-green-50 text-[var(--color-success)]"
                      }`}
                    >
                      {k === "unpassend" ? "Unpassend" : "Passend"}
                    </button>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Nächster freier Termin</CardTitle>
          <CardDescription>
            Kapazitätsangabe für die Triage. Nur der Inhaber pflegt diesen Wert; das Büro kann ihn sehen, aber nicht ändern.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <Label htmlFor="kapazitaet">Datum</Label>
              <Input
                id="kapazitaet"
                type="date"
                value={kapazitaet ?? ""}
                onChange={(e) => setKapazitaet(e.target.value || null)}
                className="w-auto"
              />
            </div>
            <Button variant="outline" size="sm" onClick={() => setKapazitaet(null)}>
              Entfernen
            </Button>
            <Button size="sm" disabled={speichert} onClick={onKapazitaetSpeichern}>
              {speichert ? "Speichert …" : "Termin speichern"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {speicherFehler && <Alert variant="danger">{speicherFehler}</Alert>}
      {gespeichert && !speicherFehler && <Alert variant="success">Triage-Einstellungen gespeichert.</Alert>}

      <div className="flex justify-end">
        <Button onClick={onSpeichern} disabled={speichert || !ausgewFormularId || !leistungsFeldId}>
          {speichert ? "Speichert …" : "Konfiguration speichern"}
        </Button>
      </div>
    </div>
  );
}
