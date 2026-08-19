import * as React from "react";
import { SchrittKarte } from "@/components/onboarding/schritt_karte";
import { DomainSchritt } from "@/components/onboarding/domain_schritt";
import { PostfachSchritt } from "@/components/onboarding/postfach_schritt";
import { PreislisteSchritt } from "@/components/onboarding/preisliste_schritt";
import { TestanfrageSchritt } from "@/components/onboarding/testanfrage_schritt";
import { VeroeffentlichenDialog } from "@/components/onboarding/veroeffentlichen_dialog";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/label";
import type { OnboardingStatus, OnboardingSchritt as Schritt } from "@/lib/api/onboarding";
import { statusRang } from "@/components/onboarding/onboarding_status";

/**
 * Leitet die sieben Onboarding-Schritte aus den echten Daten ab (Tech Design
 * ADR-7-1: Fortschritt wird berechnet, nicht abgehakt). Bietet je Schritt ein
 * aufklappbares Detail-Panel mit der zuständigen Bearbeitungsfläche.
 */
export function OnboardingFortschritt({
  status,
  onChanged,
}: {
  status: OnboardingStatus;
  onChanged: () => void;
}) {
  const [aufgeklappt, setAufgeklappt] = React.useState<string | null>(null);

  const sortiert = [...status.schritte].sort((a, b) => {
    // Reihenfolge aus dem Vertrag beibehalten: Schritt-Nummer über Index der Schritt-Liste.
    return status.schritte.indexOf(a) - status.schritte.indexOf(b);
  });

  const erledigtPflicht = status.schritte.filter((s) => s.pflicht && s.status === "erledigt").length;
  const gesamtPflicht = status.schritte.filter((s) => s.pflicht).length;
  const alleErledigt = erledigtPflicht === gesamtPflicht;

  function panelFuer(schritt: Schritt) {
    switch (schritt.id) {
      case "domain":
        return (
          <DomainSchritt
            domainStatus={schritt.domain_status}
            onReserviert={onChanged}
          />
        );
      case "postfach":
        return <PostfachSchritt postfachTest={schritt.postfach_test} onGetestet={onChanged} />;
      case "preisliste":
        return <PreislisteSchritt onChanged={onChanged} />;
      case "testanfrage":
        return <TestanfrageSchritt testvorgang={schritt.testvorgang} onChanged={onChanged} />;
      default:
        // Betriebsdaten, Branding, Leistungsseiten → "Jetzt bearbeiten" verweist auf Website-Einstellungen.
        return (
          <div className="mt-2 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-muted)]/40 p-4 text-sm text-[var(--color-muted-foreground)]">
            Öffnen Sie „Website-Einstellungen", um {schritt.titel} zu vervollständigen.
          </div>
        );
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">
            Pflichtschritte: {erledigtPflicht}/{gesamtPflicht}
          </span>
          {alleErledigt ? (
            <Badge variant="success">Startklar</Badge>
          ) : (
            <Badge variant="warning">Einrichtung läuft</Badge>
          )}
          {status.veroeffentlicht && <Badge variant="brand">Live</Badge>}
        </div>
        <VeroeffentlichenDialog status={status} onVeroeffentlicht={onChanged} />
      </div>

      {status.warnung && (
        <Alert variant="warning">{status.warnung}</Alert>
      )}

      <div className="space-y-3">
        {sortiert.map((schritt, index) => {
          const offen = aufgeklappt === schritt.id;
          const interaktiv = schritt.status !== "erledigt";
          return (
            <div key={schritt.id}>
              <div
                className={
                  interaktiv
                    ? "cursor-pointer"
                    : "pointer-events-none"
                }
                onClick={interaktiv ? () => setAufgeklappt(offen ? null : schritt.id) : undefined}
                role={interaktiv ? "button" : undefined}
                aria-expanded={interaktiv ? offen : undefined}
                tabIndex={interaktiv ? 0 : undefined}
                onKeyDown={
                  interaktiv
                    ? (e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setAufgeklappt(offen ? null : schritt.id);
                        }
                      }
                    : undefined
                }
              >
                <SchrittKarte schritt={schritt} index={index} />
              </div>
              {offen && interaktiv && <div className="mt-1">{panelFuer(schritt)}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
