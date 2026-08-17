"use client";

import Link from "next/link";
import { useSiteBase } from "@/app/site/site-context";
import type { PublicSite } from "@/lib/api/public";

export function SiteFooter({ site }: { site: PublicSite }) {
  const base = useSiteBase();
  return (
    <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-6 text-sm text-[var(--color-muted-foreground)] sm:flex-row sm:items-center sm:justify-between">
        <p>
          © {new Date().getFullYear()} {site.firmenname}
          {site.oeffnungszeiten ? ` · ${site.oeffnungszeiten}` : ""}
        </p>
        <nav className="flex gap-4">
          <Link href={`${base}/impressum`} className="hover:text-[var(--color-foreground)]">
            Impressum
          </Link>
          <Link href={`${base}/datenschutz`} className="hover:text-[var(--color-foreground)]">
            Datenschutz
          </Link>
        </nav>
      </div>
    </footer>
  );
}
