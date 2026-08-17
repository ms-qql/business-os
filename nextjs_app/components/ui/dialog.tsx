"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Minimaler Dialog auf Basis des nativen <dialog>-Elements (kein Radix nötig).
 * ponytail: kein Fokus-Trap-Polyfill — <dialog> bringt das nativ mit (showModal()).
 */
export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const ref = React.useRef<HTMLDialogElement>(null);

  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={() => onOpenChange(false)}
      onCancel={() => onOpenChange(false)}
      className={cn(
        "w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-0 text-[var(--color-foreground)] shadow-lg backdrop:bg-black/40",
        className,
      )}
    >
      <div className="flex items-start justify-between p-5 pb-2">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {description && (
            <p className="mt-1 text-sm text-[var(--color-muted-foreground)]">{description}</p>
          )}
        </div>
        <button
          type="button"
          aria-label="Schließen"
          onClick={() => onOpenChange(false)}
          className="rounded-[var(--radius-md)] p-1 text-[var(--color-muted-foreground)] hover:bg-[var(--color-surface-muted)]"
        >
          <X size={18} />
        </button>
      </div>
      <div className="p-5 pt-2">{children}</div>
    </dialog>
  );
}
