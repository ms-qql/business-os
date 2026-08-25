"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LogOut, LayoutDashboard, Users, Globe, Contact, ClipboardList, Settings2, Inbox, CalendarDays, ListChecks, FileText, Boxes } from "lucide-react";
import { useAuth } from "@/app/providers";
import { getToken } from "@/lib/session";
import { NAV_RECHTE } from "@/lib/theme/tokens";
import type { Rolle } from "@/lib/theme/tokens";
import packageJson from "../../package.json";

const ICONS: Record<string, React.ReactNode> = {
  startseite: <LayoutDashboard size={18} />,
  kunden: <Contact size={18} />,
  vorgaenge: <ClipboardList size={18} />,
  postfach: <Inbox size={18} />,
  nutzerverwaltung: <Users size={18} />,
  "website-einstellungen": <Globe size={18} />,
  formulare: <FileText size={18} />,
  gewerke: <Boxes size={18} />,
  "website-builder": <LayoutDashboard size={18} />,
  "postfach-einstellungen": <Settings2 size={18} />,
  "rechnungssteller": <FileText size={18} />,
  "onboarding": <ListChecks size={18} />,
  termine: <CalendarDays size={18} />,
};

const LABELS: Record<string, string> = {
  startseite: "Startseite",
  kunden: "Kunden",
  vorgaenge: "Vorgänge",
  postfach: "Postfach",
  nutzerverwaltung: "Nutzerverwaltung",
  "website-einstellungen": "Website-Einstellungen",
  "website-builder": "Landingpage gestalten",
  "postfach-einstellungen": "Postfach-Einstellungen",
  "rechnungssteller": "Rechnungssteller",
  "onboarding": "Onboarding",
  termine: "Termine",
  "formulare": "Formulare",
  "gewerke": "Gewerke-Katalog",
};

const PATHS: Record<string, string> = {
  startseite: "/startseite",
  kunden: "/kunden",
  vorgaenge: "/vorgaenge",
  postfach: "/email/inbox",
  nutzerverwaltung: "/nutzerverwaltung",
  "website-einstellungen": "/website-einstellungen",
  "website-builder": "/website-builder",
  "postfach-einstellungen": "/einstellungen/postfach",
  "rechnungssteller": "/einstellungen/rechnungssteller",
  "onboarding": "/onboarding",
  termine: "/termine",
  "formulare": "/formulare",
  "gewerke": "/gewerke",
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    if (!loading && (!getToken() || !user)) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted-foreground)]">
        Wird geladen …
      </div>
    );
  }

  const rollen = (user.rolle ?? "Büro") as Rolle;
  const sichtbare = NAV_RECHTE[rollen] ?? [];

  async function onLogout() {
    await signOut();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <aside className="flex w-64 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <div className="mb-6 flex items-baseline gap-2 px-2 text-lg font-semibold">
          Business OS
          <span className="text-xs font-medium text-[var(--color-muted-foreground)]">
            v{packageJson.version}
          </span>
        </div>
        <nav className="flex-1 space-y-1">
          {sichtbare.map((key) => (
            <Link
              key={key}
              href={PATHS[key]}
              className={`flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-colors ${
                pathname === PATHS[key]
                  ? "bg-[var(--color-surface-muted)] text-[var(--color-foreground)]"
                  : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-surface-muted)]"
              }`}
            >
              {ICONS[key]}
              {LABELS[key]}
            </Link>
          ))}
        </nav>
        <div className="mt-4 border-t border-[var(--color-border)] pt-4">
          <div className="px-2 text-sm">
            <div className="font-medium text-[var(--color-foreground)]">
              {user.name ?? user.username}
            </div>
            <div className="text-xs text-[var(--color-muted-foreground)]">
              {user.rolle} · {user.mandant_name}
            </div>
            {user.paket_name ? (
              <div
                className="mt-1 text-xs font-medium text-[var(--color-foreground)]"
                aria-label={`Übernommenes Branchenpaket: ${user.paket_name}`}
              >
                Paket: {user.paket_name}
              </div>
            ) : null}
          </div>
          <button
            onClick={onLogout}
            className="mt-3 flex w-full items-center gap-2 rounded-[var(--radius-md)] px-3 py-2 text-sm text-[var(--color-danger)] hover:bg-red-50"
          >
            <LogOut size={18} />
            Abmelden
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
