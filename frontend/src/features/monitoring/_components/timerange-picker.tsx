"use client";

import { useState } from "react";

import { Input } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { LastToken, Timerange } from "@/types/api";

type Props = {
  value: Timerange;
  onChange: (tr: Timerange) => void;
};

const PRESETS: { label: string; token: LastToken }[] = [
  { label: "15m", token: "15m" },
  { label: "1h", token: "1h" },
  { label: "24h", token: "24h" },
  { label: "7d", token: "7d" },
];

function isLast(tr: Timerange): tr is { last: LastToken } {
  return "last" in tr && tr.last !== undefined;
}

export function TimerangePicker({ value, onChange }: Props) {
  const [custom, setCustom] = useState(!isLast(value));
  const activeToken = isLast(value) ? value.last : null;

  return (
    <div
      className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="monitoring-timerange-picker"
    >
      <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
        Range
      </span>
      {PRESETS.map((p) => (
        <button
          key={p.token}
          type="button"
          data-testid={`monitoring-timerange-${p.token}`}
          onClick={() => {
            setCustom(false);
            onChange({ last: p.token });
          }}
          className={cn(
            "rounded-md border px-2.5 py-1 text-xs font-medium transition",
            activeToken === p.token && !custom
              ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
              : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
          )}
        >
          {p.label}
        </button>
      ))}
      <button
        type="button"
        data-testid="monitoring-timerange-custom"
        onClick={() => setCustom(true)}
        className={cn(
          "rounded-md border px-2.5 py-1 text-xs font-medium transition",
          custom
            ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
            : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
        )}
      >
        Custom
      </button>
      {custom && (
        <div className="flex items-center gap-2">
          <Input
            type="datetime-local"
            className="h-8 w-auto text-xs"
            data-testid="monitoring-timerange-from"
            onChange={(e) => {
              const from = new Date(e.target.value).toISOString();
              const to =
                !isLast(value) && value.to_ts
                  ? value.to_ts
                  : new Date().toISOString();
              onChange({ from_ts: from, to_ts: to });
            }}
          />
          <span className="text-xs text-zinc-500">→</span>
          <Input
            type="datetime-local"
            className="h-8 w-auto text-xs"
            data-testid="monitoring-timerange-to"
            onChange={(e) => {
              const to = new Date(e.target.value).toISOString();
              const from =
                !isLast(value) && value.from_ts
                  ? value.from_ts
                  : new Date(Date.now() - 3600_000).toISOString();
              onChange({ from_ts: from, to_ts: to });
            }}
          />
        </div>
      )}
    </div>
  );
}
