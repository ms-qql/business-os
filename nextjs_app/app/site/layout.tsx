"use client";

import * as React from "react";
import { SiteProvider, useSite } from "@/app/site/site-context";
import { SiteHeader } from "@/components/site/site-header";
import { SiteFooter } from "@/components/site/site-footer";

function SiteChrome({ children }: { children: React.ReactNode }) {
  const { site, loading, error } = useSite();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted-foreground)]">
        Wird geladen …
      </div>
    );
  }

  if (error || !site) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4 text-center">
        <p className="text-sm text-[var(--color-muted-foreground)]">
          Diese Website ist nicht erreichbar. Bitte prüfen Sie die Adresse.
        </p>
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen flex-col"
      style={
        site.marken_farbe
          ? ({ "--color-brand": site.marken_farbe } as React.CSSProperties)
          : undefined
      }
    >
      <SiteHeader site={site} />
      <main className="flex-1">{children}</main>
      <SiteFooter site={site} />
    </div>
  );
}

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <SiteProvider>
      <SiteChrome>{children}</SiteChrome>
    </SiteProvider>
  );
}
