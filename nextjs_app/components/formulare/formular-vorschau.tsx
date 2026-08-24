"use client";

import * as React from "react";
import { feldTypLabel, type Feld, type Komplexitaet, type Schritt } from "@/lib/schemas/formular";

/**
 * Vorschau der Formularfelder einer Stufe (Einfach/Erweitert) ohne Absenden.
 * Deckt denselben festen Katalog ab wie der öffentliche Renderer.
 */
export function FormularVorschau({
  schritte,
  modus,
}: {
  schritte: Schritt[];
  modus: Komplexitaet;
}) {
  if (schritte.length === 0) {
    return (
      <p className="text-sm text-[var(--color-muted-foreground)]">
        Noch keine Schritte vorhanden.
      </p>
    );
  }
  return (
    <div className="space-y-6">
      {schritte.map((s, si) => {
        const felder = modus === "erweitert" ? s.felder : s.felder.filter(
          (f) => f.pflichtfeld || f.typ === "consent",
        );
        return (
          <div key={s.id}>
            <h4 className="mb-2 text-sm font-semibold">
              {si + 1}. {s.titel || "Ohne Titel"}
            </h4>
            {felder.length === 0 ? (
              <p className="text-xs text-[var(--color-muted-foreground)]">
                (keine Pflichtfelder in dieser Stufe)
              </p>
            ) : (
              <ul className="space-y-2">
                {felder.map((f) => (
                  <li key={f.id} className="text-sm">
                    <span className="font-medium">{f.label}</span>
                    {f.pflichtfeld && <span className="text-[var(--color-danger)]"> *</span>}
                    <span className="ml-2 text-xs text-[var(--color-muted-foreground)]">
                      {feldTypLabel(f.typ)}
                    </span>
                    {f.hilfetext && (
                      <span className="block text-xs text-[var(--color-muted-foreground)]">
                        {f.hilfetext}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** Kleines Feld-Vorschau-Element für die Editor-Liste. */
export function FeldKurz({ feld }: { feld: Feld }) {
  return (
    <span className="flex items-center gap-1">
      <span className="font-medium">{feld.label || "(ohne Bezeichnung)"}</span>
      {feld.pflichtfeld && <span className="text-[var(--color-danger)]">*</span>}
      <span className="text-xs text-[var(--color-muted-foreground)]">
        {feldTypLabel(feld.typ)}
      </span>
    </span>
  );
}
