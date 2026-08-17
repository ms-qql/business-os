import * as React from "react";
import { cn } from "@/lib/utils";

const variants = {
  neutral: "bg-[var(--color-surface-muted)] text-[var(--color-foreground)]",
  brand: "bg-[var(--color-brand)] text-[var(--color-brand-foreground)]",
  success: "bg-green-50 text-[var(--color-success)]",
  warning: "bg-amber-50 text-[var(--color-warning)]",
  danger: "bg-red-50 text-[var(--color-danger)]",
} as const;

export function Badge({
  className,
  variant = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
