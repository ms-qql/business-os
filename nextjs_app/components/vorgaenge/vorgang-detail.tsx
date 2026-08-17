"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Alert } from "@/components/ui/label";
import { VorgangStatusBadge } from "@/components/vorgaenge/vorgang-status-badge";
import { VorgangChronik } from "@/components/vorgaenge/vorgang-chronik";
import { VorgangDokumente } from "@/components/vorgaenge/vorgang-dokumente";
import { getVorgang, updateVorgang, zuweisen, type VorgangDetail as VorgangDetailT } from "@/lib/api/vorgaenge";
import { getKunde, listObjekte, type Kunde, type Objekt } from "@/lib/api/kunden";
import { listNutzer, type Nutzer } from "@/lib/api/users";
import { ApiError } from "@/lib/api/client";
import { VORGANG_STATUS, kannSchreiben, type Rolle } from "@/lib/theme/tokens";

export function VorgangDetail({ vorgangId, rolle }: { vorgangId: string; rolle: Rolle }) {
  const [vorgang, setVorgang] = React.useState<VorgangDetailT | null>(null);
  const [kunde, setKunde] = React.useState<Kunde | null>(null);
  const [objekt, setObjekt] = React.useState<Objekt | null>(null);
  const [monteure, setMonteure] = React.useState<Nutzer[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [notizen, setNotizen] = React.useState("");
  const [speichert, setSpeichert] = React.useState(false);
  const darfSchreiben = kannSchreiben(rolle);

  const laden = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const v = await getVorgang(vorgangId);
      setVorgang(v);
      setNotizen(v.notizen ?? "");
      // Kunden-/Objektdaten sind im Vorgang nur als ID enthalten (siehe Backend-Vertrag),
      // daher hier separat nachladen. Monteure dürfen laut AC keine Kundendaten sehen.
      if (darfSchreiben) {
        void getKunde(v.kunde_id)
          .then(setKunde)
          .catch(() => setKunde(null));
        if (v.objekt_id) {
          void listObjekte(v.kunde_id)
            .then((liste) => setObjekt(liste.find((o) => o.id === v.objekt_id) ?? null))
            .catch(() => setObjekt(null));
        }
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Laden fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vorgangId, darfSchreiben]);

  React.useEffect(() => {
    void laden();
  }, [laden]);

  React.useEffect(() => {
    if (!darfSchreiben) return;
    // Monteur-Zuweisung: GET /users erfordert derzeit Inhaber (siehe PROJ-1) — für
    // Büro schlägt das Laden mit 403 fehl, dann bleibt die Auswahl leer statt zu blockieren.
    listNutzer()
      .then((n) => setMonteure(n.filter((x) => x.rolle === "Monteur")))
      .catch(() => setMonteure([]));
  }, [darfSchreiben]);

  const zugewiesenerMonteur = monteure.find((m) => m.id === vorgang?.zugewiesener_nutzer_id);

  async function onStatusChange(status: string) {
    if (!vorgang) return;
    setSpeichert(true);
    setError(null);
    try {
      const updated = await updateVorgang(vorgang.id, { status: status as VorgangDetailT["status"] });
      setVorgang(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Statusänderung fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onNotizenSpeichern() {
    if (!vorgang) return;
    setSpeichert(true);
    setError(null);
    try {
      const updated = await updateVorgang(vorgang.id, { notizen });
      setVorgang(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Speichern fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  async function onZuweisen(nutzerId: string) {
    if (!vorgang || !nutzerId) return;
    setSpeichert(true);
    setError(null);
    try {
      const updated = await zuweisen(vorgang.id, nutzerId);
      setVorgang(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Zuweisung fehlgeschlagen.");
    } finally {
      setSpeichert(false);
    }
  }

  if (loading) return <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>;
  if (error && !vorgang) return <Alert variant="danger">{error}</Alert>;
  if (!vorgang) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{vorgang.anliegen}</h1>
          <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
            Quelle: {vorgang.quelle} · erstellt am {new Date(vorgang.created_at).toLocaleString("de-DE")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <VorgangStatusBadge status={vorgang.status} />
          {darfSchreiben && (
            <Select
              value={vorgang.status}
              disabled={speichert}
              onChange={(e) => onStatusChange(e.target.value)}
              className="w-auto"
            >
              {VORGANG_STATUS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {darfSchreiben && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Kunde</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              {kunde ? (
                <>
                  <Link href={`/kunden/${kunde.id}`} className="font-medium text-[var(--color-brand)] hover:underline">
                    {kunde.name}
                  </Link>
                  <p className="mt-1 text-[var(--color-muted-foreground)]">
                    {kunde.email ?? "—"} · {kunde.telefon ?? "—"}
                  </p>
                </>
              ) : (
                <span className="text-[var(--color-muted-foreground)]">Wird geladen …</span>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Objekt</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              {vorgang.objekt_id ? (
                <span>{objekt?.adresse ?? "Wird geladen …"}</span>
              ) : (
                <span className="text-[var(--color-muted-foreground)]">Kein Objekt hinterlegt.</span>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {darfSchreiben && (
        <Card>
          <CardHeader>
            <CardTitle>Zuständigkeit</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3 text-sm">
            <span>{zugewiesenerMonteur?.name ?? (vorgang.zugewiesener_nutzer_id ? "Zugewiesen" : "Noch nicht zugewiesen")}</span>
            {monteure.length > 0 && (
              <Select
                value={vorgang.zugewiesener_nutzer_id ?? ""}
                disabled={speichert}
                onChange={(e) => onZuweisen(e.target.value)}
                className="w-auto"
              >
                <option value="">— Monteur zuweisen —</option>
                {monteure.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </Select>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Interne Notizen</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={notizen}
            disabled={!darfSchreiben}
            onChange={(e) => setNotizen(e.target.value)}
          />
          {darfSchreiben && (
            <Button size="sm" disabled={speichert} onClick={onNotizenSpeichern}>
              {speichert ? "Speichert …" : "Notizen speichern"}
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Chronik</CardTitle>
        </CardHeader>
        <CardContent>
          <VorgangChronik eintraege={vorgang.historie} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Dokumente</CardTitle>
        </CardHeader>
        <CardContent>
          <VorgangDokumente
            vorgangId={vorgang.id}
            dokumente={vorgang.dokumente}
            darfSchreiben={darfSchreiben}
            onChange={(dokumente) => setVorgang({ ...vorgang, dokumente })}
          />
        </CardContent>
      </Card>
    </div>
  );
}
