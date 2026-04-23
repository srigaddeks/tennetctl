"use client";

import { forwardRef } from "react";

import { cn } from "@/lib/cn";

// ─── Button ────────────────────────────────────────────────────────────────

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "accent";
type ButtonSize = "sm" | "md" | "lg";

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
  }
>(function Button(
  { className, variant = "primary", size = "md", loading, children, disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "relative inline-flex items-center justify-center gap-1.5 font-medium transition-all duration-150 select-none",
        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-1 focus-visible:ring-offset-[var(--bg-base)]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        size === "sm" && "h-7 rounded px-2.5 text-xs tracking-wide",
        size === "md" && "h-8 rounded px-3.5 text-[13px] tracking-wide",
        size === "lg" && "h-10 rounded px-5 text-sm tracking-wide",
        variant === "primary" &&
          "border border-[var(--border-bright)] bg-[var(--bg-elevated)] text-[var(--text-primary)] hover:border-[var(--accent)] hover:bg-[var(--accent-muted)] hover:text-[var(--accent-hover)]",
        variant === "accent" &&
          "border border-[var(--accent)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] hover:border-[var(--accent-hover)] shadow-[0_0_12px_rgba(45,126,247,0.35)]",
        variant === "secondary" &&
          "border border-[var(--border)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:border-[var(--border-bright)] hover:text-[var(--text-primary)]",
        variant === "ghost" &&
          "border border-transparent bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]",
        variant === "danger" &&
          "border border-[var(--danger)] bg-[var(--danger-muted)] text-[var(--danger)] hover:bg-[var(--danger)] hover:text-white",
        className,
      )}
      {...rest}
    >
      {loading && (
        <span
          aria-hidden
          className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
});

// ─── Input ─────────────────────────────────────────────────────────────────

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(function Input({ className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      className={cn(
        "w-full rounded border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-1.5 text-[13px] text-[var(--text-primary)] transition-all duration-150",
        "placeholder:text-[var(--text-muted)] font-[var(--font-sans)]",
        "focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)] focus:bg-[var(--bg-elevated)]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        "hover:border-[var(--border-bright)]",
        className,
      )}
      {...rest}
    />
  );
});

// ─── Select ────────────────────────────────────────────────────────────────

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className, children, ...rest }, ref) {
  return (
    <select
      ref={ref}
      className={cn(
        "w-full rounded border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-1.5 text-[13px] text-[var(--text-primary)] transition-all duration-150",
        "focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        "hover:border-[var(--border-bright)]",
        className,
      )}
      {...rest}
    >
      {children}
    </select>
  );
});

// ─── Textarea ──────────────────────────────────────────────────────────────

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-[13px] text-[var(--text-primary)] transition-all duration-150",
        "placeholder:text-[var(--text-muted)] font-[var(--font-mono)]",
        "focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]",
        "hover:border-[var(--border-bright)]",
        className,
      )}
      {...rest}
    />
  );
});

// ─── Label ─────────────────────────────────────────────────────────────────

export function Label({
  htmlFor,
  children,
  hint,
  required,
  className,
}: {
  htmlFor?: string;
  children: React.ReactNode;
  hint?: string;
  required?: boolean;
  className?: string;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn("flex flex-col gap-1.5 text-[13px]", className)}
    >
      <span className="flex items-baseline justify-between">
        <span className="font-medium text-[var(--text-secondary)] tracking-wide">
          {children}
          {required && <span className="ml-0.5 text-[var(--danger)]">*</span>}
        </span>
        {hint && (
          <span className="text-[11px] text-[var(--text-muted)]">{hint}</span>
        )}
      </span>
    </label>
  );
}

// ─── Field ─────────────────────────────────────────────────────────────────

export function Field({
  label,
  hint,
  error,
  required,
  htmlFor,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={htmlFor} hint={hint} required={required}>
        {label}
      </Label>
      {children}
      {error && (
        <span className="text-[11px] text-[var(--danger)]">{error}</span>
      )}
    </div>
  );
}

// ─── Checkbox ──────────────────────────────────────────────────────────────

export const Checkbox = forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> & {
    label?: string;
    hint?: string;
  }
>(function Checkbox({ className, label, hint, id, ...rest }, ref) {
  const el = (
    <input
      ref={ref}
      type="checkbox"
      id={id}
      className={cn(
        "h-4 w-4 rounded-[3px] border border-[var(--border-bright)] bg-[var(--bg-surface)] transition",
        "checked:border-[var(--accent)] checked:bg-[var(--accent)]",
        "focus:ring-1 focus:ring-[var(--accent)] focus:ring-offset-1 focus:ring-offset-[var(--bg-base)]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        className,
      )}
      {...rest}
    />
  );
  if (!label) return el;
  return (
    <label
      htmlFor={id}
      className="flex items-start gap-2 text-[13px] cursor-pointer"
    >
      {el}
      <span className="flex flex-col gap-0.5">
        <span className="font-medium text-[var(--text-primary)]">{label}</span>
        {hint && (
          <span className="text-[11px] text-[var(--text-muted)]">{hint}</span>
        )}
      </span>
    </label>
  );
});

// ─── Badge ─────────────────────────────────────────────────────────────────

type BadgeTone =
  | "default"
  | "zinc"
  | "emerald"
  | "red"
  | "blue"
  | "amber"
  | "purple"
  | "cyan"
  | "success"
  | "warning"
  | "danger"
  | "info";

export function Badge({
  tone = "default",
  children,
  className,
  dot,
}: {
  tone?: BadgeTone;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-[3px] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide uppercase",
        (tone === "default" || tone === "zinc") &&
          "border border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-secondary)]",
        (tone === "emerald" || tone === "success") &&
          "border border-[var(--success)]/30 bg-[var(--success-muted)] text-[var(--success)]",
        (tone === "red" || tone === "danger") &&
          "border border-[var(--danger)]/30 bg-[var(--danger-muted)] text-[var(--danger)]",
        (tone === "blue") &&
          "border border-[var(--accent)]/30 bg-[var(--accent-muted)] text-[var(--accent-hover)]",
        (tone === "amber" || tone === "warning") &&
          "border border-[var(--warning)]/30 bg-[var(--warning-muted)] text-[var(--warning)]",
        tone === "purple" &&
          "border border-purple-500/30 bg-purple-950/40 text-purple-400",
        (tone === "cyan" || tone === "info") &&
          "border border-[var(--info)]/30 bg-[var(--info-muted)] text-[var(--info)]",
        className,
      )}
    >
      {dot && (
        <span
          className="status-dot inline-block"
          style={{
            background:
              tone === "emerald" || tone === "success"
                ? "var(--success)"
                : tone === "red" || tone === "danger"
                ? "var(--danger)"
                : tone === "amber" || tone === "warning"
                ? "var(--warning)"
                : tone === "blue"
                ? "var(--accent)"
                : "var(--text-muted)",
          }}
        />
      )}
      {children}
    </span>
  );
}

// ─── Empty state ────────────────────────────────────────────────────────────

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded border border-dashed px-6 py-14 text-center"
      style={{
        borderColor: "var(--border)",
        background: "var(--bg-muted)",
      }}
    >
      <div
        className="h-8 w-8 rounded border flex items-center justify-center text-[var(--text-muted)]"
        style={{ borderColor: "var(--border)", background: "var(--bg-elevated)" }}
        aria-hidden
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="3" y="3" width="10" height="10" rx="1" stroke="currentColor" strokeWidth="1.5" />
          <line x1="6" y1="8" x2="10" y2="8" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </div>
      <div className="flex flex-col gap-1">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
        {description && (
          <p className="max-w-xs text-[12px] text-[var(--text-muted)] leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

// ─── Error state ────────────────────────────────────────────────────────────

export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded border px-6 py-10 text-center"
      style={{
        borderColor: "rgba(255, 63, 85, 0.25)",
        background: "var(--danger-muted)",
      }}
    >
      <h3 className="text-sm font-semibold text-[var(--danger)]">Error</h3>
      <p className="max-w-md text-[12px] text-[var(--text-secondary)] leading-relaxed">
        {message}
      </p>
      {retry && (
        <Button variant="secondary" size="sm" onClick={retry}>
          Retry
        </Button>
      )}
    </div>
  );
}

// ─── Skeleton ───────────────────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("rounded skeleton-shimmer", className)}
    />
  );
}

// ─── Table ──────────────────────────────────────────────────────────────────

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="overflow-hidden rounded border"
      style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}
    >
      <table className="w-full text-[13px]">{children}</table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return (
    <thead
      className="border-b text-left"
      style={{
        borderColor: "var(--border)",
        background: "var(--bg-elevated)",
      }}
    >
      {children}
    </thead>
  );
}

export type SortDir = "asc" | "desc";

export function TH({
  children,
  className,
  sortable,
  sortDir,
  onSort,
  testId,
}: {
  children?: React.ReactNode;
  className?: string;
  sortable?: boolean;
  sortDir?: SortDir | null;
  onSort?: () => void;
  testId?: string;
}) {
  const base = cn(
    "whitespace-nowrap px-4 py-2.5 text-[10px] font-semibold uppercase tracking-[0.08em]",
    className,
  );
  const style = { color: "var(--text-muted)" };

  if (sortable) {
    return (
      <th scope="col" className={base} style={style}>
        <button
          type="button"
          onClick={onSort}
          data-testid={testId}
          className={cn(
            "inline-flex items-center gap-1 transition-colors duration-100",
            "hover:text-[var(--text-primary)]",
            sortDir && "text-[var(--text-secondary)]",
          )}
        >
          {children}
          <span
            aria-hidden
            className={cn(
              "inline-block text-[9px] transition-opacity",
              sortDir ? "opacity-100" : "opacity-30",
            )}
          >
            {sortDir === "asc" ? "▲" : sortDir === "desc" ? "▼" : "↕"}
          </span>
        </button>
      </th>
    );
  }
  return (
    <th scope="col" className={base} style={style}>
      {children}
    </th>
  );
}

export function TBody({ children }: { children: React.ReactNode }) {
  return (
    <tbody
      className="divide-y"
      style={{
        color: "var(--text-primary)",
        borderColor: "var(--border)",
        ["--tw-divide-opacity" as string]: "1",
      }}
    >
      {children}
    </tbody>
  );
}

export function TR({
  children,
  onClick,
  selected,
  ...rest
}: {
  children: React.ReactNode;
  onClick?: React.MouseEventHandler<HTMLTableRowElement>;
  selected?: boolean;
} & Omit<React.HTMLAttributes<HTMLTableRowElement>, "onClick">) {
  return (
    <tr
      onClick={onClick}
      style={
        selected
          ? { background: "var(--accent-muted)", borderLeft: "2px solid var(--accent)" }
          : undefined
      }
      className={cn(
        "border-b transition-colors duration-100",
        onClick &&
          "cursor-pointer hover:bg-[var(--bg-elevated)]",
        !selected && "border-[var(--border)]",
      )}
      {...rest}
    >
      {children}
    </tr>
  );
}

export function TD({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <td
      className={cn(
        "whitespace-nowrap px-4 py-2.5 text-[13px] text-[var(--text-primary)]",
        className,
      )}
    >
      {children}
    </td>
  );
}

// ─── Stat card ──────────────────────────────────────────────────────────────

export function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  accent?: "blue" | "green" | "amber" | "red";
}) {
  const accentColor =
    accent === "green"
      ? "var(--success)"
      : accent === "amber"
      ? "var(--warning)"
      : accent === "red"
      ? "var(--danger)"
      : "var(--accent)";

  return (
    <div
      className="rounded border px-4 py-3 flex flex-col gap-1"
      style={{
        borderColor: "var(--border)",
        background: "var(--bg-surface)",
        borderTop: `2px solid ${accentColor}`,
      }}
    >
      <span className="label-caps">{label}</span>
      <span
        className="font-mono-data text-xl font-semibold"
        style={{ color: "var(--text-primary)" }}
      >
        {value}
      </span>
      {sub && (
        <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
          {sub}
        </span>
      )}
    </div>
  );
}

// ─── Card ────────────────────────────────────────────────────────────────────

export function Card({
  children,
  className,
  padding = true,
}: {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded border",
        padding && "p-4",
        className,
      )}
      style={{
        borderColor: "var(--border)",
        background: "var(--bg-surface)",
      }}
    >
      {children}
    </div>
  );
}

// ─── Section header ──────────────────────────────────────────────────────────

export function SectionHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-4">
      <div className="flex flex-col gap-0.5">
        <h2
          className="text-sm font-semibold tracking-wide"
          style={{ color: "var(--text-primary)" }}
        >
          {title}
        </h2>
        {description && (
          <p className="text-[12px]" style={{ color: "var(--text-muted)" }}>
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      )}
    </div>
  );
}
