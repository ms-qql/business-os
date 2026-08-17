"use client";

import Link from "next/link";
import { MapPin, Phone, Mail, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useSite, useSiteBase } from "@/app/site/site-context";

export default function StartseitePage() {
  const { site } = useSite();
  const base = useSiteBase();
  if (!site) return null;

  return (
    <div>
      <section className="border-b border-[var(--color-border)] bg-[var(--color-surface-muted)]">
        <div className="mx-auto max-w-5xl px-4 py-16 text-center">
          <h1 className="text-3xl font-semibold text-[var(--color-foreground)] sm:text-4xl">
            {site.firmenname}
          </h1>
          {site.ueber_uns && (
            <p className="mx-auto mt-4 max-w-2xl text-[var(--color-muted-foreground)]">
              {site.ueber_uns}
            </p>
          )}
          <Link href={`${base}/anfrage`}>
            <Button size="lg" className="mt-6">
              Jetzt Anfrage senden
            </Button>
          </Link>
        </div>
      </section>

      {site.leistungen.length > 0 && (
        <section className="mx-auto max-w-5xl px-4 py-12">
          <h2 className="mb-6 text-2xl font-semibold text-[var(--color-foreground)]">
            Unsere Leistungen
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {site.leistungen.map((l) => (
              <Link key={l.slug} href={`${base}/leistungen/${l.slug}`}>
                <Card className="h-full transition-shadow hover:shadow-md">
                  <CardHeader>
                    <CardTitle>{l.titel}</CardTitle>
                    <CardDescription>{l.kurzbeschreibung}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section id="kontakt" className="mx-auto max-w-5xl px-4 py-12">
        <Card>
          <CardHeader>
            <CardTitle>Kontakt</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-[var(--color-foreground)] sm:grid-cols-2">
            {site.adresse && (
              <div className="flex items-start gap-2">
                <MapPin size={18} className="mt-0.5 shrink-0 text-[var(--color-muted-foreground)]" />
                <span>{site.adresse}</span>
              </div>
            )}
            {site.telefon && (
              <div className="flex items-start gap-2">
                <Phone size={18} className="mt-0.5 shrink-0 text-[var(--color-muted-foreground)]" />
                <a href={`tel:${site.telefon}`}>{site.telefon}</a>
              </div>
            )}
            {site.email && (
              <div className="flex items-start gap-2">
                <Mail size={18} className="mt-0.5 shrink-0 text-[var(--color-muted-foreground)]" />
                <a href={`mailto:${site.email}`}>{site.email}</a>
              </div>
            )}
            {site.oeffnungszeiten && (
              <div className="flex items-start gap-2">
                <Clock size={18} className="mt-0.5 shrink-0 text-[var(--color-muted-foreground)]" />
                <span>{site.oeffnungszeiten}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
