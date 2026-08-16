"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import { getOperatorToken } from "@/lib/session";

export default function OperatorShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    const hasToken = !!getOperatorToken();
    if (!hasToken && pathname !== "/operator-login") {
      router.replace("/operator-login");
      return;
    }
    setReady(true);
  }, [pathname, router]);

  if (!ready && pathname !== "/operator-login") {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-[var(--color-muted-foreground)]">
        Wird geladen …
      </div>
    );
  }

  return <div className="min-h-screen bg-[var(--color-background)]">{children}</div>;
}
