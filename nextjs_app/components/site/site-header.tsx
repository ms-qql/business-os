"use client";

import Link from "next/link";
import { Phone, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSiteBase } from "@/app/site/site-context";
import type { PublicSite } from "@/lib/api/public";

export function SiteHeader({ site }: { site: PublicSite }) {
  const base = useSiteBase();
  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-4">
        <Link href={base || "/"} className="flex items-center gap-3">
          {site.logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={site.logo_url}
              alt={site.firmenname}
              className="h-10 w-auto"
            />
          ) : null}
          <span className="text-lg font-semibold text-[var(--color-foreground)]">
            {site.firmenname}
          </span>
        </Link>

        <div className="flex flex-wrap items-center gap-4 text-sm text-[var(--color-muted-foreground)]">
          {site.telefon && (
            <a href={`tel:${site.telefon}`} className="flex items-center gap-1.5 hover:text-[var(--color-foreground)]">
              <Phone size={16} /> {site.telefon}
            </a>
          )}
          {site.email && (
            <a href={`mailto:${site.email}`} className="hidden items-center gap-1.5 hover:text-[var(--color-foreground)] sm:flex">
              <Mail size={16} /> {site.email}
            </a>
          )}
          <Link href={`${base}/anfrage`}>
            <Button size="sm">Anfrage senden</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
