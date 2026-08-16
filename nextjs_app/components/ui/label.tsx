import * as React from "react";
import { cn } from "@/lib/utils";

export function Label({
  className,
  ...props
}: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn(
        "mb-1.5 block text-sm font-medium text-[var(--color-foreground)]",
        className,
      )}
      {...props}
    />
  );
}

export function Alert({
  variant = "info",
  className,
  children,
}: {
  variant?: "info" | "success" | "warning" | "danger";
  className?: string;
  children: React.ReactNode;
}) {
  const styles = {
    info: "bg-[var(--color-surface-muted)] text-[var(--color-foreground)] border-[var(--color-border)]",
    success:
      "bg-green-50 text-[var(--color-success)] border-green-200",
    warning:
      "bg-amber-50 text-[var(--color-warning)] border-amber-200",
    danger: "bg-red-50 text-[var(--color-danger)] border-red-200",
  }[variant];
  return (
    <div
      role="alert"
      className={cn(
        "rounded-[var(--radius-md)] border p-3 text-sm",
        styles,
        className,
      )}
    >
      {children}
    </div>
  );
}
