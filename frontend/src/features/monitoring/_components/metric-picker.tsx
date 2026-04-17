"use client";

import { useMemo, useState } from "react";

import { Badge, EmptyState, ErrorState, Input, Skeleton } from "@/components/ui";
import { useMetricsList } from "@/features/monitoring/hooks/use-metrics-list";
import { cn } from "@/lib/cn";
import type { Metric, MetricKind } from "@/types/api";

type Props = {
  selectedKey?: string | null;
  onSelect: (metric: Metric) => void;
};

type KindFilter = "all" | MetricKind;

const KINDS: { value: KindFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "counter", label: "Counter" },
  { value: "gauge", label: "Gauge" },
  { value: "histogram", label: "Histogram" },
];

function kindTone(k: MetricKind) {
  if (k === "counter") return "blue" as const;
  if (k === "gauge") return "emerald" as const;
  return "purple" as const;
}

export function MetricPicker({ selectedKey, onSelect }: Props) {
  const [q, setQ] = useState("");
  const [kind, setKind] = useState<KindFilter>("all");
  const { data, isLoading, isError, error, refetch } = useMetricsList();

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((m) => {
      if (kind !== "all" && m.kind !== kind) return false;
      if (q && !m.key.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [data, q, kind]);

  return (
    <div
      className="flex h-full flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="monitoring-metric-picker"
    >
      <Input
        placeholder="Search metrics…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        data-testid="monitoring-metric-search"
      />
      <div className="flex gap-1">
        {KINDS.map((k) => (
          <button
            key={k.value}
            type="button"
            data-testid={`monitoring-metric-kind-${k.value}`}
            onClick={() => setKind(k.value)}
            className={cn(
              "rounded-md border px-2 py-0.5 text-[11px] font-medium",
              kind === k.value
                ? "border-zinc-900 bg-zinc-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900"
                : "border-zinc-200 text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900",
            )}
          >
            {k.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && filtered.length === 0 && (
          <EmptyState
            title="No metrics"
            description="No metrics yet — register one via POST /v1/monitoring/metrics."
          />
        )}
        <ul className="flex flex-col gap-1.5">
          {filtered.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onClick={() => onSelect(m)}
                data-testid={`monitoring-metric-${m.key}`}
                className={cn(
                  "flex w-full flex-col gap-1 rounded-md border px-3 py-2 text-left text-xs transition",
                  selectedKey === m.key
                    ? "border-zinc-900 bg-zinc-100 dark:border-zinc-100 dark:bg-zinc-900"
                    : "border-zinc-200 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-medium text-zinc-900 dark:text-zinc-50">
                    {m.key}
                  </span>
                  <Badge tone={kindTone(m.kind)}>{m.kind}</Badge>
                </div>
                {m.description && (
                  <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    {m.description}
                  </span>
                )}
                {m.unit && (
                  <span className="text-[10px] font-mono text-zinc-400">
                    {m.unit}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
