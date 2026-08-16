import Link from "next/link";

export default function SitzungAbgelaufenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-background)] p-4">
      <div className="w-full max-w-md rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center shadow-sm">
        <h1 className="text-lg font-semibold">Sitzung abgelaufen</h1>
        <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
          Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-block rounded-[var(--radius-md)] bg-[var(--color-brand)] px-4 py-2 text-sm font-medium text-[var(--color-brand-foreground)]"
        >
          Erneut anmelden
        </Link>
      </div>
    </div>
  );
}
