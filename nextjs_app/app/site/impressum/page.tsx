"use client";

import { useSite } from "@/app/site/site-context";

/**
 * Impressum wird nicht frei editiert, sondern aus den Website-Stammdaten
 * (Firmenname, Adresse, Kontakt) generiert — siehe Tech Design PROJ-2.
 */
export default function ImpressumPage() {
  const { site } = useSite();
  if (!site) return null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-semibold text-[var(--color-foreground)]">Impressum</h1>
      <div className="mt-6 space-y-4 text-sm text-[var(--color-foreground)]">
        <div>
          <p className="font-medium">Angaben gemäß § 5 TMG</p>
          <p>{site.firmenname}</p>
          {site.adresse && <p>{site.adresse}</p>}
        </div>
        <div>
          <p className="font-medium">Kontakt</p>
          {site.telefon && <p>Telefon: {site.telefon}</p>}
          {site.email && <p>E-Mail: {site.email}</p>}
        </div>
      </div>
    </div>
  );
}
