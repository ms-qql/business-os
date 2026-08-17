"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { getPublicLeistung, type PublicLeistungDetail } from "@/lib/api/public";
import { useSiteBase } from "@/app/site/site-context";

export default function LeistungPage() {
  const params = useParams<{ slug: string }>();
  const base = useSiteBase();
  const [leistung, setLeistung] = React.useState<PublicLeistungDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [notFound, setNotFound] = React.useState(false);

  React.useEffect(() => {
    let aktiv = true;
    setLoading(true);
    setNotFound(false);
    getPublicLeistung(params.slug)
      .then((l) => {
        if (aktiv) setLeistung(l);
      })
      .catch(() => {
        if (aktiv) setNotFound(true);
      })
      .finally(() => {
        if (aktiv) setLoading(false);
      });
    return () => {
      aktiv = false;
    };
  }, [params.slug]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center text-sm text-[var(--color-muted-foreground)]">
        Wird geladen …
      </div>
    );
  }

  if (notFound || !leistung) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 text-center">
        <h1 className="text-xl font-semibold text-[var(--color-foreground)]">
          Diese Leistung ist derzeit nicht verfügbar.
        </h1>
        <Link href={base || "/"} className="mt-4 inline-block">
          <Button variant="outline">Zur Startseite</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-3xl font-semibold text-[var(--color-foreground)]">
        {leistung.titel}
      </h1>
      <p className="mt-2 text-[var(--color-muted-foreground)]">{leistung.kurzbeschreibung}</p>
      <div className="mt-6 whitespace-pre-wrap text-[var(--color-foreground)]">
        {leistung.inhalt}
      </div>
      <Link href={`${base}/anfrage`} className="mt-8 inline-block">
        <Button>Anfrage zu dieser Leistung senden</Button>
      </Link>
    </div>
  );
}
