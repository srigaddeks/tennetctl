"use client";

import { cn } from "@/lib/cn";
import type { AuditOutcome } from "@/types/api";

import {
  CATEGORY_META,
  TIME_RANGE_LABELS,
  type CategoryCode,
  type TimeRange,
} from "./authz-constants";

export function CategoryPill({
  code,
  count,
  active,
  onClick,
}: {
  code: CategoryCode;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  const meta = CATEGORY_META[code];
  const Icon = meta.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`category-filter-${code}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      <Icon className="h-3 w-3" />
      {meta.label}
      <span
        className={cn(
          "tabular-nums",
          active ? "opacity-70" : "text-zinc-400",
        )}
      >
        {count}
      </span>
    </button>
  );
}

export function OutcomePill({
  value,
  active,
  count,
  onClick,
}: {
  value: "all" | AuditOutcome;
  active: boolean;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`outcome-filter-${value}`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      {value === "success" && (
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      )}
      {value === "failure" && (
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
      )}
      {value === "all" ? "All outcomes" : value}
      <span
        className={cn("tabular-nums", active ? "opacity-70" : "text-zinc-400")}
      >
        {count}
      </span>
    </button>
  );
}

export function TimeRangePill({
  value,
  active,
  onClick,
}: {
  value: TimeRange;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`time-filter-${value}`}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium tabular-nums transition",
        active
          ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-50",
      )}
    >
      {TIME_RANGE_LABELS[value]}
    </button>
  );
}
