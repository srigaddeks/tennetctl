"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";

import { EmptyState, ErrorState, Skeleton } from "@/components/ui";
import { useMetricsQuery } from "@/features/monitoring/hooks/use-metrics-query";
import type {
  MetricAggregate,
  MetricBucket,
  Metric,
  MetricsQuery,
  TimeseriesPoint,
  Timerange,
} from "@/types/api";

type Props = {
  metric: Metric;
  labels?: Record<string, string>;
  timerange: Timerange;
  bucket?: MetricBucket;
};

function fmtTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function buildQueries(metric: Metric, labels: Record<string, string> | undefined, timerange: Timerange, bucket: MetricBucket): { label: string; color: string; dsl: MetricsQuery }[] {
  const base = (aggregate: MetricAggregate): MetricsQuery => ({
    target: "metrics",
    metric_key: metric.key,
    labels,
    timerange,
    bucket,
    aggregate,
  });
  if (metric.kind === "histogram") {
    return [
      { label: "p50", color: "#6366f1", dsl: base("p50") },
      { label: "p95", color: "#f59e0b", dsl: base("p95") },
      { label: "p99", color: "#ef4444", dsl: base("p99") },
    ];
  }
  if (metric.kind === "counter") {
    return [{ label: "rate", color: "#3b82f6", dsl: base("rate") }];
  }
  return [{ label: "avg", color: "#10b981", dsl: base("avg") }];
}

type ChartRow = { bucket_ts: string; timeLabel: string } & Record<string, number | string | null>;

function mergeSeries(series: { label: string; points: TimeseriesPoint[] }[]): ChartRow[] {
  const byBucket = new Map<string, ChartRow>();
  for (const s of series) {
    for (const p of s.points) {
      const key = p.bucket_ts;
      const existing = byBucket.get(key) ?? {
        bucket_ts: key,
        timeLabel: fmtTime(key),
      };
      existing[s.label] = p.value;
      byBucket.set(key, existing);
    }
  }
  return Array.from(byBucket.values()).sort((a, b) =>
    a.bucket_ts < b.bucket_ts ? -1 : 1,
  );
}

export function MetricsChart({
  metric,
  labels,
  timerange,
  bucket = "5m",
}: Props) {
  const queries = buildQueries(metric, labels, timerange, bucket);
  // Execute all queries in parallel — one hook per series (stable number, depends on metric.kind which doesn't change during render).
  // Histogram = 3; counter/gauge = 1. We call all three but only use the first for counter/gauge.
  const q0 = useMetricsQuery(queries[0]?.dsl ?? null);
  const q1 = useMetricsQuery(queries[1]?.dsl ?? null);
  const q2 = useMetricsQuery(queries[2]?.dsl ?? null);
  const results = [q0, q1, q2];

  const active = queries.map((q, i) => ({ label: q.label, color: q.color, result: results[i] }));
  const isLoading = active.some((a) => a.result.isLoading);
  const isError = active.some((a) => a.result.isError);
  const firstError = active.find((a) => a.result.isError)?.result.error;

  if (isLoading) {
    return <Skeleton className="h-72 w-full" />;
  }
  if (isError) {
    return (
      <ErrorState
        message={firstError instanceof Error ? firstError.message : "Query failed"}
        retry={() => {
          active.forEach((a) => void a.result.refetch());
        }}
      />
    );
  }

  const rows = mergeSeries(
    active.map((a) => ({ label: a.label, points: a.result.data?.items ?? [] })),
  );

  if (rows.length === 0) {
    return (
      <EmptyState
        title="No data"
        description="No data in this range. Try a wider time window or push samples via /v1/monitoring/metrics/{key}/increment."
      />
    );
  }

  return (
    <div
      className="h-72 w-full rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
      data-testid="monitoring-metrics-chart"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows}>
          <CartesianGrid stroke="#e4e4e7" strokeDasharray="3 3" />
          <XAxis dataKey="timeLabel" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            labelFormatter={(_v, payload) => {
              const raw = payload?.[0]?.payload?.bucket_ts as string | undefined;
              return raw ?? "";
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {active.map((a) => (
            <Line
              key={a.label}
              type="monotone"
              dataKey={a.label}
              stroke={a.color}
              dot={false}
              strokeWidth={2}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
