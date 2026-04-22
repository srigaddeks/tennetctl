"use client";

import { cn } from "@/lib/cn";

import type { StatCard } from "./types";

export function StatCards({ cards }: { cards: StatCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map(({ label, value, icon: Icon, borderCls, numCls, testId }) => (
        <div
          key={label}
          className={cn(
            "flex items-center gap-3 rounded-xl border border-l-[3px] bg-white px-4 py-3 dark:bg-zinc-950",
            "border-zinc-200 dark:border-zinc-800",
            borderCls
          )}
          data-testid={testId}
        >
          <div className="shrink-0 rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">
            <Icon className="h-4 w-4 text-zinc-500 dark:text-zinc-400" />
          </div>
          <div className="min-w-0">
            <span
              className={cn(
                "block text-2xl font-bold tabular-nums leading-none",
                numCls
              )}
            >
              {value}
            </span>
            <span className="mt-0.5 block truncate text-[11px] text-zinc-500 dark:text-zinc-400">
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
