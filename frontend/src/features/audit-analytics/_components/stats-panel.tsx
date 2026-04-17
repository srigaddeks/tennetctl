"use client";

import { Badge, Skeleton } from "@/components/ui";
import type { AuditEventStatsResponse } from "@/types/api";

type Props = {
  data: AuditEventStatsResponse | undefined;
  isLoading: boolean;
};

export function StatsPanel({ data, isLoading }: Props) {
  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3" data-testid="audit-stats-panel">
        <Skeleton className="h-44 w-full" />
        <Skeleton className="h-44 w-full" />
        <Skeleton className="h-44 w-full" />
      </div>
    );
  }

  const totalFromOutcome = data.by_outcome.reduce((s, r) => s + r.count, 0);
  const topKeys = data.by_event_key.slice(0, 8);
  const maxKey = topKeys[0]?.count ?? 1;
  const maxTs = Math.max(1, ...data.time_series.map((p) => p.count));

  return (
    <div
      data-testid="audit-stats-panel"
      className="grid grid-cols-1 gap-4 md:grid-cols-3"
    >
      {/* Totals / outcomes */}
      <div className="flex flex-col gap-3 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Totals</div>
        <div className="text-3xl font-semibold tabular-nums text-zinc-900 dark:text-zinc-50">
          <span data-testid="audit-stats-total">{totalFromOutcome.toLocaleString()}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-2">
          {data.by_outcome.map((r) => (
            <Badge key={r.outcome} tone={r.outcome === "success" ? "emerald" : "red"}>
              {r.outcome}: {r.count}
            </Badge>
          ))}
        </div>
        <div className="mt-2 flex flex-col gap-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">By category</div>
          <div className="flex flex-wrap gap-2">
            {data.by_category.map((r) => (
              <Badge key={r.category_code} tone="blue">
                {r.category_code}: {r.count}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Top event keys */}
      <div className="flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Top event keys</div>
        {topKeys.length === 0 ? (
          <div className="text-xs text-zinc-500">No events.</div>
        ) : (
          <div className="flex flex-col gap-1.5">
            {topKeys.map((r) => {
              const pct = Math.round((r.count / maxKey) * 100);
              return (
                <div key={r.event_key} className="flex items-center gap-2">
                  <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-zinc-800 dark:text-zinc-200">
                    {r.event_key}
                  </span>
                  <div className="relative h-2 w-28 rounded bg-zinc-100 dark:bg-zinc-800">
                    <div
                      className="absolute inset-y-0 left-0 rounded bg-zinc-900 dark:bg-zinc-100"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-[11px] tabular-nums text-zinc-600 dark:text-zinc-400">
                    {r.count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Time series */}
      <div className="flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Time series</div>
        {data.time_series.length === 0 ? (
          <div className="text-xs text-zinc-500">No events.</div>
        ) : (
          <div className="flex h-28 items-end gap-1">
            {data.time_series.map((p, i) => {
              const h = Math.max(2, Math.round((p.count / maxTs) * 100));
              return (
                <div
                  key={`${p.bucket}-${i}`}
                  title={`${p.bucket}: ${p.count}`}
                  className="flex-1 rounded-t bg-zinc-900 dark:bg-zinc-100"
                  style={{ height: `${h}%` }}
                  data-testid={`audit-stats-bar-${i}`}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
