"use client";

import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSiteBase } from "@/app/site/site-context";

export default function AnfrageDankePage() {
  const base = useSiteBase();
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-20 text-center">
      <CheckCircle2 size={48} className="text-[var(--color-success)]" />
      <h1 className="mt-4 text-2xl font-semibold text-[var(--color-foreground)]">
        Vielen Dank. Wir melden uns zeitnah bei Ihnen.
      </h1>
      <Link href={base || "/"} className="mt-6">
        <Button variant="outline">Zur Startseite</Button>
      </Link>
    </div>
  );
}
