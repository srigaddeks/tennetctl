"use client";

import { useMemo } from "react";

import { EmptyState, Skeleton } from "@/components/ui";
import { useLogsQuery } from "@/features/monitoring/hooks/use-logs-query";
import { useMetricsQuery } from "@/features/monitoring/hooks/use-metrics-query";
import { useTracesQuery } from "@/features/monitoring/hooks/use-traces-query";
import type {
  LogsQuery,
  MetricsQuery,
  Panel as PanelT,
  TracesQuery,
} from "@/types/api";

type Props = {
  panel: PanelT;
};

export function Panel({ panel }: Props) {
  return (
    <div
      className="flex h-full flex-col rounded-xl border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid={`monitoring-panel-${panel.id}`}
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
          {panel.title}
        </h3>
        <span className="text-[10px] font-mono text-zinc-400">
          {panel.panel_type}
        </span>
      </div>
      <div className="flex-1 overflow-hidden">
        {panel.panel_type === "timeseries" && <TimeseriesPanel panel={panel} />}
        {panel.panel_type === "stat" && <StatPanel panel={panel} />}
        {panel.panel_type === "table" && <TablePanel panel={panel} />}
        {panel.panel_type === "log_stream" && <LogStreamPanel panel={panel} />}
        {panel.panel_type === "trace_list" && <TraceListPanel panel={panel} />}
      </div>
    </div>
  );
}

function TimeseriesPanel({ panel }: Props) {
  const dsl = panel.dsl as unknown as MetricsQuery;
  const { data, isLoading, isError } = useMetricsQuery(dsl);
  if (isLoading) return <Skeleton className="h-full w-full" />;
  if (isError) return <p className="text-xs text-red-600">Error</p>;
  const items = data?.items ?? [];
  if (items.length === 0) return <EmptyState title="No data" />;
  const values = items.map((p) => p.value ?? 0);
  const max = Math.max(...values, 1);
  return (
    <div className="flex h-full items-end gap-0.5">
      {items.map((p, i) => {
        const h = ((p.value ?? 0) / max) * 100;
        return (
          <div
            key={`${p.bucket_ts}-${i}`}
            className="flex-1 rounded-sm bg-blue-500/70"
            style={{ height: `${Math.max(2, h)}%` }}
            title={`${p.bucket_ts}: ${p.value}`}
          />
        );
      })}
    </div>
  );
}

function StatPanel({ panel }: Props) {
  const dsl = panel.dsl as unknown as MetricsQuery;
  const { data, isLoading } = useMetricsQuery(dsl);
  if (isLoading) return <Skeleton className="h-full w-full" />;
  const items = data?.items ?? [];
  const latest = items[items.length - 1]?.value ?? null;
  return (
    <div className="flex h-full items-center justify-center">
      <span className="text-3xl font-semibold text-zinc-900 dark:text-zinc-50">
        {latest !== null ? latest.toLocaleString() : "—"}
      </span>
    </div>
  );
}

function TablePanel({ panel }: Props) {
  const dsl = panel.dsl as unknown as MetricsQuery;
  const { data, isLoading } = useMetricsQuery(dsl);
  if (isLoading) return <Skeleton className="h-full w-full" />;
  const items = data?.items ?? [];
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-left text-[10px] uppercase text-zinc-500">
          <th className="px-2 py-1">Time</th>
          <th className="px-2 py-1">Value</th>
        </tr>
      </thead>
      <tbody>
        {items.slice(0, 20).map((p, i) => (
          <tr key={`${p.bucket_ts}-${i}`} className="border-t border-zinc-100 dark:border-zinc-900">
            <td className="px-2 py-1 font-mono text-[11px]">
              {new Date(p.bucket_ts).toLocaleTimeString()}
            </td>
            <td className="px-2 py-1">{p.value ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function LogStreamPanel({ panel }: Props) {
  const dsl = useMemo(
    () => ({ ...(panel.dsl as unknown as LogsQuery), limit: 10 }),
    [panel.dsl],
  );
  const { data, isLoading } = useLogsQuery(dsl);
  if (isLoading) return <Skeleton className="h-full w-full" />;
  const items = data?.items ?? [];
  if (items.length === 0) return <EmptyState title="No logs" />;
  return (
    <ul className="flex flex-col gap-1">
      {items.map((r) => (
        <li key={r.id} className="truncate text-[11px]">
          <span className="font-mono text-zinc-500">
            {new Date(r.recorded_at).toLocaleTimeString()}
          </span>{" "}
          <span className="text-zinc-800 dark:text-zinc-200">{r.body}</span>
        </li>
      ))}
    </ul>
  );
}

function TraceListPanel({ panel }: Props) {
  const dsl = useMemo(
    () => ({ ...(panel.dsl as unknown as TracesQuery), limit: 10 }),
    [panel.dsl],
  );
  const { data, isLoading } = useTracesQuery(dsl);
  if (isLoading) return <Skeleton className="h-full w-full" />;
  const items = data?.items ?? [];
  if (items.length === 0) return <EmptyState title="No traces" />;
  return (
    <ul className="flex flex-col gap-1">
      {items.map((s) => (
        <li key={s.span_id} className="truncate text-[11px]">
          <span className="font-mono text-zinc-500">
            {s.trace_id.slice(0, 8)}…
          </span>{" "}
          <span className="text-zinc-800 dark:text-zinc-200">{s.name}</span>{" "}
          <span className="text-zinc-400">
            ({((s.duration_ns ?? 0) / 1_000_000).toFixed(1)}ms)
          </span>
        </li>
      ))}
    </ul>
  );
}
