import { NextResponse, type NextRequest } from "next/server";

/**
 * Diese Next.js-Instanz bedient zwei Domain-Arten:
 * - die Betriebszentrale (APP_HOST bzw. localhost in der Entwicklung),
 * - beliebige Betriebsdomains, unter denen die geführte SHK-Website läuft.
 *
 * Die Mandantenauflösung selbst passiert im Backend über den Hostnamen
 * (GET /public/site). Hier wird nur entschieden, welcher Next.js-Routenbaum
 * gerendert wird — Betriebszentrale (bestehende Routen) oder öffentliche
 * Website (/site/*). Unter der Betriebszentrale bleiben /site/* trotzdem
 * direkt erreichbar (nützlich für lokale Entwicklung ohne Host-Trick).
 *
 * ponytail: Hostliste ist eine einfache Gleichheitsprüfung, kein
 * Wildcard/Subdomain-Matching. Upgrade bei Bedarf (z. B. *.businessos.de).
 */
const APP_HOSTS = new Set(
  (process.env.APP_HOST ?? "localhost,127.0.0.1")
    .split(",")
    .map((h) => h.trim())
    .filter(Boolean),
);

// Shared Secret, das nur dieser Next.js-Dienst kennt. Das Backend vertraut
// X-Forwarded-Host nur, wenn dieses Secret mitgeschickt wird (SEC-1) — sonst
// könnte jeder Client den Header spoofen und fremde Mandanten auslesen.
const INTERNAL_PROXY_SECRET = process.env.INTERNAL_PROXY_SECRET ?? "";

export function proxy(req: NextRequest) {
  const host = req.headers.get("host")?.split(":")[0] ?? "";
  const path = req.nextUrl.pathname;

  if (path.startsWith("/api") || path.startsWith("/public/")) {
    if (!INTERNAL_PROXY_SECRET) return NextResponse.next();
    const headers = new Headers(req.headers);
    headers.set("x-internal-proxy-secret", INTERNAL_PROXY_SECRET);
    return NextResponse.next({ request: { headers } });
  }

  if (APP_HOSTS.has(host) || path.startsWith("/site")) {
    return NextResponse.next();
  }

  const url = req.nextUrl.clone();
  url.pathname = `/site${path === "/" ? "" : path}`;
  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
