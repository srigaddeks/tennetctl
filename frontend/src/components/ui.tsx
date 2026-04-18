"use client";

/**
 * Shared UI primitives. Tailwind v4; accessible by default.
 */

import { forwardRef } from "react";

import { cn } from "@/lib/cn";

// ─── Button ───────────────────────────────────────────────────────

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

export const Button = forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
  }
>(function Button(
  { className, variant = "primary", size = "md", loading, children, disabled, ...rest },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2",
        "dark:focus-visible:ring-zinc-100 dark:focus-visible:ring-offset-zinc-950",
        "disabled:cursor-not-allowed disabled:opacity-60",
        size === "sm" && "h-8 px-3 text-xs",
        size === "md" && "h-10 px-4 text-sm",
        variant === "primary" &&
          "bg-zinc-900 text-white hover:bg-zinc-800 active:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200",
        variant === "secondary" &&
          "border border-zinc-200 bg-white text-zinc-900 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:hover:bg-zinc-800",
        variant === "ghost" &&
          "text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800",
        variant === "danger" &&
          "bg-red-600 text-white hover:bg-red-700 active:bg-red-800",
        className
      )}
      {...rest}
    >
      {loading && (
        <span
          aria-hidden
          className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {children}
    </button>
  );
});

// ─── Input ────────────────────────────────────────────────────────

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(function Input({ className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm transition",
        "placeholder:text-zinc-400",
        "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
        "disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-500",
        "dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:placeholder:text-zinc-500",
        "dark:focus:border-zinc-100 dark:focus:ring-zinc-100",
        "dark:disabled:bg-zinc-800",
        className
      )}
      {...rest}
    />
  );
});

// ─── Select ───────────────────────────────────────────────────────

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className, children, ...rest }, ref) {
  return (
    <select
      ref={ref}
      className={cn(
        "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm transition",
        "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
        "disabled:cursor-not-allowed disabled:bg-zinc-50 disabled:text-zinc-500",
        "dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50",
        "dark:focus:border-zinc-100 dark:focus:ring-zinc-100",
        className
      )}
      {...rest}
    >
      {children}
    </select>
  );
});

// ─── Textarea ─────────────────────────────────────────────────────

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm transition",
        "placeholder:text-zinc-400",
        "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
        "dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:placeholder:text-zinc-500",
        "dark:focus:border-zinc-100 dark:focus:ring-zinc-100",
        className
      )}
      {...rest}
    />
  );
});

// ─── Label ────────────────────────────────────────────────────────

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
      className={cn("flex flex-col gap-1.5 text-sm", className)}
    >
      <span className="flex items-baseline justify-between">
        <span className="font-medium text-zinc-800 dark:text-zinc-200">
          {children}
          {required && <span className="ml-0.5 text-red-600">*</span>}
        </span>
        {hint && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {hint}
          </span>
        )}
      </span>
    </label>
  );
}

// ─── Field ────────────────────────────────────────────────────────

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
        <span className="text-xs text-red-600 dark:text-red-400">{error}</span>
      )}
    </div>
  );
}

// ─── Checkbox ────────────────────────────────────────────────────

export const Checkbox = forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> & { label?: string; hint?: string }
>(function Checkbox({ className, label, hint, id, ...rest }, ref) {
  const el = (
    <input
      ref={ref}
      type="checkbox"
      id={id}
      className={cn(
        "h-4 w-4 rounded border-zinc-300 text-zinc-900 transition",
        "focus:ring-2 focus:ring-zinc-900 focus:ring-offset-1",
        "disabled:cursor-not-allowed disabled:opacity-60",
        "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:focus:ring-zinc-100",
        className
      )}
      {...rest}
    />
  );
  if (!label) return el;
  return (
    <label htmlFor={id} className="flex items-start gap-2 text-sm cursor-pointer">
      {el}
      <span className="flex flex-col gap-0.5">
        <span className="font-medium text-zinc-800 dark:text-zinc-200">
          {label}
        </span>
        {hint && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {hint}
          </span>
        )}
      </span>
    </label>
  );
});

// ─── Badge ────────────────────────────────────────────────────────

type BadgeTone =
  | "zinc"
  | "emerald"
  | "red"
  | "blue"
  | "amber"
  | "purple";

export function Badge({
  tone = "zinc",
  children,
  className,
}: {
  tone?: BadgeTone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        tone === "zinc" &&
          "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
        tone === "emerald" &&
          "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
        tone === "red" &&
          "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
        tone === "blue" &&
          "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
        tone === "amber" &&
          "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
        tone === "purple" &&
          "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
        className
      )}
    >
      {children}
    </span>
  );
}

// ─── Empty state ─────────────────────────────────────────────────

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
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-300 bg-zinc-50 px-6 py-12 text-center dark:border-zinc-700 dark:bg-zinc-900/50">
      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
        {title}
      </h3>
      {description && (
        <p className="max-w-md text-xs text-zinc-500 dark:text-zinc-400">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

// ─── Error state ─────────────────────────────────────────────────

export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 px-6 py-10 text-center dark:border-red-900/40 dark:bg-red-950/30">
      <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">
        Something went wrong
      </h3>
      <p className="max-w-md text-xs text-red-700 dark:text-red-300">
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

// ─── Skeleton ────────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "animate-pulse rounded-md bg-zinc-200 dark:bg-zinc-800",
        className
      )}
    />
  );
}

// ─── Table ────────────────────────────────────────────────────────

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <table className="w-full text-sm">{children}</table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="border-b border-zinc-200 bg-zinc-50 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
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
  if (sortable) {
    return (
      <th
        scope="col"
        className={cn("whitespace-nowrap px-4 py-2 font-medium", className)}
      >
        <button
          type="button"
          onClick={onSort}
          data-testid={testId}
          className={cn(
            "inline-flex items-center gap-1 rounded transition",
            "hover:text-zinc-900 dark:hover:text-zinc-100",
            sortDir && "text-zinc-900 dark:text-zinc-50",
          )}
        >
          {children}
          <span
            aria-hidden
            className={cn(
              "inline-block text-[10px] transition",
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
    <th
      scope="col"
      className={cn("whitespace-nowrap px-4 py-2 font-medium", className)}
    >
      {children}
    </th>
  );
}

export function TBody({ children }: { children: React.ReactNode }) {
  return (
    <tbody className="divide-y divide-zinc-100 text-zinc-900 dark:divide-zinc-900 dark:text-zinc-100">
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
      className={cn(
        onClick &&
          "cursor-pointer transition hover:bg-zinc-50 dark:hover:bg-zinc-900/60",
        selected && "bg-zinc-100 dark:bg-zinc-900"
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
    <td className={cn("whitespace-nowrap px-4 py-2.5", className)}>
      {children}
    </td>
  );
}
