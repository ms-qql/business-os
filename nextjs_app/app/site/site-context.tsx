"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { getPublicSite, type PublicSite } from "@/lib/api/public";

/**
 * Öffentliche Seiten werden per Middleware auf `/site/*` umgeschrieben, wenn
 * die Domain nicht die Betriebszentrale ist (Kundendomain sieht z. B. "/"
 * im Browser). Direkt unter der Betriebszentrale bleiben sie zusätzlich
 * unter dem sichtbaren Pfad `/site/*` erreichbar (lokale Entwicklung ohne
 * Host-Trick). Interne Links müssen daher dieses Präfix kennen.
 */
export function useSiteBase(): string {
  const pathname = usePathname();
  return pathname.startsWith("/site") ? "/site" : "";
}

interface SiteContextValue {
  site: PublicSite | null;
  loading: boolean;
  error: string | null;
}

const SiteContext = React.createContext<SiteContextValue | null>(null);

export function SiteProvider({ children }: { children: React.ReactNode }) {
  const [site, setSite] = React.useState<PublicSite | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let aktiv = true;
    getPublicSite()
      .then((s) => {
        if (aktiv) setSite(s);
      })
      .catch(() => {
        if (aktiv) setError("Diese Website konnte nicht geladen werden.");
      })
      .finally(() => {
        if (aktiv) setLoading(false);
      });
    return () => {
      aktiv = false;
    };
  }, []);

  return (
    <SiteContext.Provider value={{ site, loading, error }}>
      {children}
    </SiteContext.Provider>
  );
}

export function useSite(): SiteContextValue {
  const ctx = React.useContext(SiteContext);
  if (!ctx) throw new Error("useSite muss innerhalb von SiteProvider stehen.");
  return ctx;
}
