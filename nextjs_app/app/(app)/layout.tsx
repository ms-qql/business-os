"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LogOut, LayoutDashboard, Users, Globe } from "lucide-react";
import { useAuth } from "@/app/providers";
import { getToken } from "@/lib/session";
import { NAV_RECHTE } from "@/lib/theme/tokens";
import type { Rolle } from "@/lib/theme/tokens";
import packageJson from "../../package.json";

const ICONS: Record<string, React.ReactNode> = {
  startseite: <LayoutDashboard size={18} />,
  nutzerverwaltung: <Users size={18} />,
  "website-einstellungen": <Globe size={18} />,
};

const LABELS: Record<string, string> = {
  startseite: "Startseite",
  nutzerverwaltung: "Nutzerverwaltung",
  "website-einstellungen": "Website-Einstellungen",
};

const PATHS: Record<string, string> = {
  startseite: "/startseite",
  nutzerverwaltung: "/nutzerverwaltung",
  "website-einstellungen": "/website-einstellungen",
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
