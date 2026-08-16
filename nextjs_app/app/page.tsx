"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/providers";
import { getToken } from "@/lib/session";

export default function RootRedirect() {
  const router = useRouter();
  const { user, loading } = useAuth();

  React.useEffect(() => {
    if (loading) return;
    if (getToken() && user) {
      router.replace("/startseite");
    } else {
      router.replace("/login");
    }
  }, [loading, user, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
      <p className="text-sm text-[var(--color-muted-foreground)]">Wird geladen …</p>
    </div>
  );
}
