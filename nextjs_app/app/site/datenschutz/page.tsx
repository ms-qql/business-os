"use client";

import { useSite } from "@/app/site/site-context";

/**
 * Datenschutzhinweis wird nicht frei editiert, sondern aus den
 * Website-Stammdaten generiert — siehe Tech Design PROJ-2.
 */
export default function DatenschutzPage() {
  const { site } = useSite();
  if (!site) return null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-[var(--color-foreground)]">Datenschutzhinweis</h1>
      <div className="mt-6 space-y-4 text-sm text-[var(--color-foreground)]">
        <p>
          Verantwortlich für die Datenverarbeitung auf dieser Website ist{" "}
          {site.firmenname}
          {site.adresse ? `, ${site.adresse}` : ""}.
        </p>
        <p>
          Wenn Sie über das Anfrageformular Kontakt aufnehmen, verarbeiten wir
          Ihre Angaben (Name, Kontaktdaten, Adresse, Anliegen sowie
          gegebenenfalls hochgeladene Fotos) ausschließlich zur Bearbeitung
          Ihrer Anfrage. Eine Weitergabe an Dritte erfolgt nicht, soweit dies
          nicht zur Bearbeitung Ihrer Anfrage erforderlich ist.
        </p>
        <p>
          Für Fragen zum Datenschutz wenden Sie sich bitte an:
          {site.email ? ` ${site.email}` : ""}
          {site.telefon ? ` · ${site.telefon}` : ""}
        </p>
      </div>
    </div>
  );
}
