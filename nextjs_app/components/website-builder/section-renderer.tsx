"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Phone, Mail, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, Alert } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { useSiteBase } from "@/app/site/site-context";
import type { PublicSite } from "@/lib/api/public";
import type { CtaZiel, PublicSection } from "@/lib/website-builder-types";

/** Name des sessionStorage-Schlüssels für die Kurzformular-Übergabe. */
export const KURZFORMULAR_STORAGE = "landingpage_kurzformular";

export interface KurzformularVorgabe {
  name: string;
  telefon?: string;
  email?: string;
}

/** Schreibt die validierte Kurzformular-Eingabe hostgebunden in sessionStorage. */
export function speichereKurzformular(vorgabe: KurzformularVorgabe): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(KURZFORMULAR_STORAGE, JSON.stringify(vorgabe));
}

/** Lies die Vorgabe einmalig (zum Vorbefüllen) und löscht sie danach. */
export function liesKurzformular(): KurzformularVorgabe | null {
  if (typeof window === "undefined") return null;
  const roh = window.sessionStorage.getItem(KURZFORMULAR_STORAGE);
  if (!roh) return null;
  window.sessionStorage.removeItem(KURZFORMULAR_STORAGE);
  try {
    const wert = JSON.parse(roh) as KurzformularVorgabe;
    if (wert && typeof wert.name === "string" && wert.name.trim()) return wert;
    return null;
  } catch {
    return null;
  }
}

function ctaHref(ziel: CtaZiel | undefined, base: string): string | null {
  switch (ziel) {
    case "anfrage":
      return `${base}/anfrage`;
    case "leistungen":
      return `${base}/leistungen`;
    case "kontakt":
      return "#kontakt";
    default:
      return null;
  }
}

function CtaButton({
  ziel,
  titel,
  base,
  variant = "primary",
}: {
  ziel: CtaZiel | undefined;
  titel: string | undefined;
  base: string;
  variant?: "primary" | "outline";
}) {
  const href = ctaHref(ziel, base);
  if (!href || !titel) return null;
  return (
    <Link href={href} className="inline-block">
      <Button size="lg" variant={variant}>
        {titel}
      </Button>
    </Link>
  );
}

/** Hero-Kurzformular: Name + mindestens ein Kontaktweg. Bei gültiger Eingabe
 * wird sie über sessionStorage an das vollständige Anfrageformular übergeben. */
function HeroKurzformular({ base }: { base: string }) {
  const router = useRouter();
  const [name, setName] = React.useState("");
  const [telefon, setTelefon] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [fehler, setFehler] = React.useState<string | null>(null);
  const [wirdGesendet, setWirdGesendet] = React.useState(false);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFehler(null);
    if (!name.trim()) {
      setFehler("Bitte geben Sie Ihren Namen an.");
      return;
    }
    if (!telefon.trim() && !email.trim()) {
      setFehler("Bitte geben Sie eine Telefonnummer oder E-Mail-Adresse an.");
      return;
    }
    setWirdGesendet(true);
    speichereKurzformular({
      name: name.trim(),
      telefon: telefon.trim() || undefined,
      email: email.trim() || undefined,
    });
    router.push(`${base}/anfrage`);
  }

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="w-full max-w-sm rounded-[var(--radius-lg)] border border-white/20 bg-white/90 p-5 text-[var(--color-foreground)] shadow-sm backdrop-blur"
    >
      <h3 className="text-base font-semibold">Schnellanfrage</h3>
      <p className="mt-1 text-xs text-[var(--color-muted-foreground)]">
        Wir melden uns zeitnah. Eine gültige Kontaktmöglichkeit genügt.
      </p>
      <div className="mt-3 space-y-2">
        <div>
          <Label htmlFor="kurz-name" className="text-xs">
            Name
          </Label>
          <Input id="kurz-name" value={name} onChange={(e) => setName(e.target.value)} className="h-9" />
        </div>
        <div>
          <Label htmlFor="kurz-telefon" className="text-xs">
            Telefon (optional)
          </Label>
          <Input
            id="kurz-telefon"
            type="tel"
            value={telefon}
            onChange={(e) => setTelefon(e.target.value)}
            className="h-9"
          />
        </div>
        <div>
          <Label htmlFor="kurz-email" className="text-xs">
            E-Mail (optional)
          </Label>
          <Input
            id="kurz-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-9"
          />
        </div>
      </div>
      {fehler && (
        <Alert variant="danger" className="mt-2">
          {fehler}
        </Alert>
      )}
      <Button type="submit" size="sm" className="mt-3 w-full" disabled={wirdGesendet}>
        {wirdGesendet ? "Weiter …" : "Anfrage beginnen"}
      </Button>
    </form>
  );
}

function SectionWrapper({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`mx-auto max-w-5xl px-4 py-12 ${className}`}>
      {children}
    </section>
  );
}

/** Rendert genau einen öffentlichen Sektionstyp. Unbekannte Typen werden
 * sicher ignoriert; fehlende Bilder bleiben als Textvariante nutzbar.
 * Das Backend liefert pro Sektion das `inhalt`-Objekt (mit `typ`) plus
 * optional ein `bild`-Objekt { url, alt_text }. */
function renderSection(section: PublicSection, site: PublicSite, base: string): React.ReactNode {
  const { typ } = section;

  switch (typ) {
    case "hero": {
      const bild = section.bild as (PublicSection["bild"] & { url: string }) | null | undefined;
      return (
        <section
          className="relative overflow-hidden bg-[var(--color-surface-muted)]"
          aria-label={(section.titel as string) ?? "Hero"}
        >
          {bild?.url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={bild.url}
              alt={(bild.alt_text as string) ?? ""}
              className="absolute inset-0 h-full w-full object-cover"
              aria-hidden={!bild.alt_text}
            />
          ) : null}
          <div className="absolute inset-0 bg-black/40" aria-hidden />
          <div className="relative mx-auto flex max-w-5xl flex-col gap-8 px-4 py-20 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl text-white">
              <h1 className="text-3xl font-semibold sm:text-4xl">{section.titel as string}</h1>
              {section.text && (
                <p className="mt-4 whitespace-pre-wrap text-white/90">{section.text as string}</p>
              )}
              <div className="mt-6">
                <CtaButton ziel={section.cta_typ} titel={section.cta_text} base={base} />
              </div>
            </div>
            <HeroKurzformular base={base} />
          </div>
        </section>
      );
    }

    case "text_mit_bild": {
      const bild = section.bild as (PublicSection["bild"] & { url: string }) | null | undefined;
      return (
        <SectionWrapper>
          <div className="grid items-center gap-8 md:grid-cols-2">
            <div>
              <h2 className="text-2xl font-semibold text-[var(--color-foreground)]">
                {section.titel as string}
              </h2>
              {section.text && (
                <p className="mt-4 whitespace-pre-wrap text-[var(--color-muted-foreground)]">
                  {section.text as string}
                </p>
              )}
            </div>
            {bild?.url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={bild.url}
                alt={(bild.alt_text as string) ?? ""}
                className="w-full rounded-[var(--radius-lg)] border border-[var(--color-border)] object-cover"
              />
            ) : (
              <div className="flex aspect-[4/3] items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-muted)] text-sm text-[var(--color-muted-foreground)]">
                Kein Bild hinterlegt
              </div>
            )}
          </div>
        </SectionWrapper>
      );
    }

    case "leistungen": {
      const aktiv = site.leistungen;
      return (
        <SectionWrapper>
          <h2 className="mb-6 text-2xl font-semibold text-[var(--color-foreground)]">
            {section.titel as string}
          </h2>
          {section.einleitung && (
            <p className="mb-6 max-w-2xl text-[var(--color-muted-foreground)]">
              {section.einleitung as string}
            </p>
          )}
          {aktiv.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {aktiv.map((l) => (
                <Link key={l.slug} href={`${base}/leistungen/${l.slug}`}>
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardContent className="pt-6">
                      <h3 className="font-semibold text-[var(--color-foreground)]">{l.titel}</h3>
                      {l.kurzbeschreibung && (
                        <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
                          {l.kurzbeschreibung}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <div className="rounded-[var(--radius-lg)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-muted)] p-8 text-center text-[var(--color-muted-foreground)]">
              Unsere Leistungen werden derzeit gepflegt. Kontaktieren Sie uns direkt unter{" "}
              {site.telefon || site.email || "unseren Kontaktdaten"}.
            </div>
          )}
          <div className="mt-6">
            <CtaButton ziel={section.cta_typ} titel={section.cta_text} base={base} variant="outline" />
          </div>
        </SectionWrapper>
      );
    }

    case "kennzahlen": {
      const paare = (section.kennzahlen as { wert: string; label: string }[]) ?? [];
      return (
        <SectionWrapper className="bg-[var(--color-surface-muted)]">
          <h2 className="mb-8 text-center text-2xl font-semibold text-[var(--color-foreground)]">
            {section.titel as string}
          </h2>
          {paare.length > 0 ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {paare.map((p, i) => (
                <div key={i} className="text-center">
                  <div className="text-3xl font-bold text-[var(--color-brand)]">{p.wert}</div>
                  <div className="mt-1 text-sm text-[var(--color-muted-foreground)]">{p.label}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-sm text-[var(--color-muted-foreground)]">
              Keine Kennzahlen hinterlegt.
            </p>
          )}
        </SectionWrapper>
      );
    }

    case "ablauf": {
      const schritte = (section.schritte as { titel: string; beschreibung: string }[]) ?? [];
      return (
        <SectionWrapper>
          <h2 className="mb-8 text-2xl font-semibold text-[var(--color-foreground)]">
            {section.titel as string}
          </h2>
          {schritte.length > 0 ? (
            <ol className="space-y-4">
              {schritte.map((s, i) => (
                <li
                  key={i}
                  className="flex gap-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--color-brand)] text-sm font-semibold text-[var(--color-brand-foreground)]">
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="font-semibold text-[var(--color-foreground)]">{s.titel}</h3>
                    {s.beschreibung && (
                      <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">
                        {s.beschreibung}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-[var(--color-muted-foreground)]">Keine Schritte hinterlegt.</p>
          )}
        </SectionWrapper>
      );
    }

    case "faq": {
      const fragen = (section.fragen as { frage: string; antwort: string }[]) ?? [];
      return (
        <SectionWrapper className="bg-[var(--color-surface-muted)]">
          <h2 className="mb-6 text-2xl font-semibold text-[var(--color-foreground)]">
            {section.titel as string}
          </h2>
          {fragen.length > 0 ? (
            <div className="space-y-3">
              {fragen.map((p, i) => (
                <details
                  key={i}
                  className="group rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
                >
                  <summary className="flex cursor-pointer items-center justify-between font-medium text-[var(--color-foreground)]">
                    {p.frage}
                    <ChevronDown
                      size={18}
                      className="text-[var(--color-muted-foreground)] transition-transform group-open:rotate-180"
                    />
                  </summary>
                  <p className="mt-3 whitespace-pre-wrap text-sm text-[var(--color-muted-foreground)]">
                    {p.antwort}
                  </p>
                </details>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--color-muted-foreground)]">Keine Fragen hinterlegt.</p>
          )}
        </SectionWrapper>
      );
    }

    case "kontakt": {
      return (
        <SectionWrapper id="kontakt">
          <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <h2 className="text-2xl font-semibold text-[var(--color-foreground)]">
              {section.titel as string}
            </h2>
            {section.einleitung && (
              <p className="mt-3 max-w-2xl text-[var(--color-muted-foreground)]">
                {section.einleitung as string}
              </p>
            )}
            <div className="mt-6 flex flex-wrap gap-4 text-sm">
              {site.telefon && (
                <a
                  href={`tel:${site.telefon}`}
                  className="flex items-center gap-2 text-[var(--color-foreground)] hover:text-[var(--color-brand)]"
                >
                  <Phone size={18} /> {site.telefon}
                </a>
              )}
              {site.email && (
                <a
                  href={`mailto:${site.email}`}
                  className="flex items-center gap-2 text-[var(--color-foreground)] hover:text-[var(--color-brand)]"
                >
                  <Mail size={18} /> {site.email}
                </a>
              )}
              {site.adresse && (
                <span className="text-[var(--color-muted-foreground)]">{site.adresse}</span>
              )}
            </div>
            <div className="mt-6">
              <CtaButton ziel={section.cta_typ} titel={section.cta_text} base={base} />
            </div>
          </div>
        </SectionWrapper>
      );
    }

    case "cta": {
      const href = ctaHref(section.cta_typ, base);
      return (
        <SectionWrapper className="bg-[var(--color-brand)] text-[var(--color-brand-foreground)]">
          <div className="text-center">
            <h2 className="text-2xl font-semibold">{section.titel as string}</h2>
            {section.text && (
              <p className="mx-auto mt-3 max-w-2xl whitespace-pre-wrap">{section.text as string}</p>
            )}
            {section.cta_text && href && (
              <div className="mt-6">
                <Link href={href}>
                  <Button
                    size="lg"
                    variant="outline"
                    className="border-white text-white hover:bg-white/10"
                  >
                    {section.cta_text}
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </SectionWrapper>
      );
    }

    default:
      return null;
  }
}

/** Rendert die sichtbaren, sortierten Sektionen der öffentlichen Landingpage. */
export function SectionRenderer({ sections, site }: { sections: PublicSection[]; site: PublicSite }) {
  const base = useSiteBase();
  return (
    <>
      {sections.map((s, i) => (
        <React.Fragment key={i}>{renderSection(s, site, base)}</React.Fragment>
      ))}
    </>
  );
}
