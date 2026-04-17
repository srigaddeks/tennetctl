"use client";

import { useState } from "react";

import { Button, ErrorState, Skeleton } from "@/components/ui";
import { useAuditRetention } from "@/features/audit-analytics/hooks/use-audit-events";
import type { AuditRetentionBucket } from "@/types/api";

export function RetentionGrid() {
  const [anchor, setAnchor] = useState("");
  const [returnEvent, setReturnEvent] = useState("");
  const [bucket, setBucket] = useState<AuditRetentionBucket>("week");
  const [periods, setPeriods] = useState(6);
  const [queryParams, setQueryParams] = useState<{
    anchor: string;
    return_event: string;
    bucket: AuditRetentionBucket;
    periods: number;
  } | null>(null);

  const { data, isLoading, isError, error } = useAuditRetention(queryParams);

  function run() {
    const a = anchor.trim();
    const r = returnEvent.trim();
    if (!a || !r) return;
    setQueryParams({ anchor: a, return_event: r, bucket, periods });
  }

  const cohorts = data?.cohorts ?? [];
  const periodCount = queryParams?.periods ?? periods;

  function opacity(pct: number): string {
    const v = Math.min(100, pct);
    if (v === 0) return "bg-zinc-100 dark:bg-zinc-800 text-zinc-400";
    if (v < 25) return "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300";
    if (v < 50) return "bg-blue-300 dark:bg-blue-700/60 text-blue-900 dark:text-blue-100";
    if (v < 75) return "bg-blue-500 text-white";
    return "bg-blue-700 text-white";
  }

  return (
    <div
      className="flex flex-col gap-5 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="audit-retention-grid"
    >
      <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
        Retention Analysis
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Anchor event
          </label>
          <input
            className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 font-mono text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            placeholder="event.key"
            value={anchor}
            onChange={(e) => setAnchor(e.target.value)}
            data-testid="audit-retention-anchor"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Return event
          </label>
          <input
            className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 font-mono text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            placeholder="event.key"
            value={returnEvent}
            onChange={(e) => setReturnEvent(e.target.value)}
            data-testid="audit-retention-return-event"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Bucket
          </label>
          <select
            className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs text-zinc-900 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            value={bucket}
            onChange={(e) => setBucket(e.target.value as AuditRetentionBucket)}
          >
            <option value="day">Day</option>
            <option value="week">Week</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Periods
          </label>
          <input
            type="number"
            min={1}
            max={52}
            className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-xs text-zinc-900 focus:border-zinc-400 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            value={periods}
            onChange={(e) => setPeriods(Math.max(1, Math.min(52, Number(e.target.value))))}
          />
        </div>
      </div>

      <Button
        size="sm"
        onClick={run}
        disabled={!anchor.trim() || !returnEvent.trim()}
        data-testid="audit-retention-run"
      >
        Compute retention
      </Button>

      {isLoading && (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      )}

      {isError && (
        <ErrorState
          message={error instanceof Error ? error.message : "Retention failed"}
          retry={run}
        />
      )}

      {data && cohorts.length === 0 && !isLoading && (
        <div className="text-xs text-zinc-400">No cohorts found for these event keys.</div>
      )}

      {cohorts.length > 0 && (
        <div className="overflow-x-auto" data-testid="audit-retention-table">
          <table className="min-w-full text-[11px]">
            <thead>
              <tr>
                <th className="pr-3 text-left font-semibold text-zinc-500">Cohort</th>
                <th className="px-2 text-right font-semibold text-zinc-500">Size</th>
                {Array.from({ length: periodCount + 1 }, (_, i) => (
                  <th key={i} className="px-2 text-center font-semibold text-zinc-500">
                    +{i}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cohorts.map((cohort) => (
                <tr key={cohort.cohort_period}>
                  <td className="py-1 pr-3 font-mono text-zinc-700 dark:text-zinc-300">
                    {cohort.cohort_period}
                  </td>
                  <td className="py-1 px-2 text-right tabular-nums text-zinc-600 dark:text-zinc-400">
                    {cohort.cohort_size}
                  </td>
                  {cohort.retained.map((r) => (
                    <td key={r.offset} className="py-1 px-1">
                      <div
                        className={`rounded px-1 py-0.5 text-center tabular-nums ${opacity(r.pct)}`}
                        title={`${r.count} users (${r.pct}%)`}
                      >
                        {r.pct > 0 ? `${r.pct}%` : "—"}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
