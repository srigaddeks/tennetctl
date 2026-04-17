"use client";

import { use, useState, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  ErrorState,
  Skeleton,
} from "@/components/ui";
import { useAlertEvent } from "@/features/monitoring/hooks/use-alerts";
import { useMetricsQuery } from "@/features/monitoring/hooks/use-metrics-query";
import { SilenceDialog } from "@/features/monitoring/_components/silence-dialog";
import { cn } from "@/lib/cn";
import type { AlertSeverity, MetricsQuery } from "@/types/api";

function severityClass(sev: AlertSeverity | null): string {
  if (sev === "critical" || sev === "error") {
    return "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300";
  }
  if (sev === "warn") {
    return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300";
  }
  if (sev === "info") {
    return "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300";
  }
  return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
}

export default function AlertDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const sp = useSearchParams();
  const startedAt = sp.get("started_at");

  const { data, isLoading, isError, error, refetch } = useAlertEvent(
    id,
    startedAt,
  );
  const [silenceOpen, setSilenceOpen] = useState(false);

  // When we have alert data with metric rule info in annotations.dsl (if available),
  // run a metrics query for the last hour to show context.
  const metricKey =
    (data?.annotations &&
      typeof data.annotations === "object" &&
      "metric_key" in data.annotations &&
      typeof (data.annotations as Record<string, unknown>).metric_key ===
        "string"
      ? ((data.annotations as Record<string, unknown>).metric_key as string)
      : null) ?? null;

  const metricsDsl: MetricsQuery | null = useMemo(() => {
    if (!metricKey) return null;
    return {
      target: "metrics",
      metric_key: metricKey,
      timerange: { last: "1h" },
      aggregate: "sum",
      bucket: "1m",
    };
  }, [metricKey]);
  const metrics = useMetricsQuery(metricsDsl);

  const chartData = useMemo(() => {
    return (metrics.data?.items ?? []).map((p) => ({
      ts: new Date(p.bucket_ts).getTime(),
      tsLabel: new Date(p.bucket_ts).toLocaleTimeString(),
      value: p.value ?? 0,
    }));
  }, [metrics.data]);

  return (
    <>
      <PageHeader
        title={data?.rule_name ?? "Alert"}
        description={
          data
            ? `Alert ${id.slice(0, 8)} · started ${new Date(
                data.started_at,
              ).toLocaleString()}`
            : "Loading alert detail…"
        }
        testId="heading-monitoring-alert-detail"
        actions={
          data ? (
            <Button
              variant="secondary"
              onClick={() => setSilenceOpen(true)}
              data-testid="alert-detail-silence"
            >
              Silence
            </Button>
          ) : null
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {isLoading && (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-80" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase",
                  severityClass(data.severity),
                )}
                data-testid={`alert-severity-${data.severity ?? "unknown"}`}
              >
                {data.severity ?? "n/a"}
              </span>
              <Badge tone={data.state === "firing" ? "red" : "emerald"}>
                {data.state}
              </Badge>
              {data.silenced && (
                <Badge tone="purple">
                  <span data-testid="alert-silenced-badge">silenced</span>
                </Badge>
              )}
              <span className="text-xs text-zinc-500">
                fingerprint {data.fingerprint.slice(0, 10)}…
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                  Value
                </span>
                <div className="text-2xl font-semibold">
                  {data.value ?? "—"}
                </div>
              </div>
              <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                  Threshold
                </span>
                <div className="text-2xl font-semibold">
                  {data.threshold ?? "—"}
                </div>
              </div>
              <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
                <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                  Notifications
                </span>
                <div className="text-2xl font-semibold">
                  {data.notification_count}
                </div>
                {data.last_notified_at && (
                  <span className="text-[11px] text-zinc-500">
                    Last {new Date(data.last_notified_at).toLocaleString()}
                  </span>
                )}
              </div>
            </div>

            {metricsDsl && chartData.length > 0 && (
              <div
                className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950"
                data-testid="alert-detail-chart"
              >
                <h3 className="mb-2 text-sm font-semibold">
                  {metricKey} · last 1h
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                      <XAxis dataKey="tsLabel" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      {data.threshold !== null && (
                        <ReferenceLine
                          y={data.threshold}
                          stroke="#ef4444"
                          strokeDasharray="4 2"
                        />
                      )}
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#2563eb"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
              <h3 className="mb-2 text-sm font-semibold">Labels</h3>
              {Object.keys(data.labels ?? {}).length === 0 ? (
                <p className="text-xs text-zinc-500">No labels.</p>
              ) : (
                <table className="w-full text-sm">
                  <tbody>
                    {Object.entries(data.labels).map(([k, v]) => (
                      <tr
                        key={k}
                        className="border-b border-zinc-100 last:border-0 dark:border-zinc-900"
                      >
                        <td className="py-1 pr-4 font-mono text-xs text-zinc-500">
                          {k}
                        </td>
                        <td className="py-1 font-mono text-xs">
                          {String(v)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
              <h3 className="mb-2 text-sm font-semibold">Annotations</h3>
              <pre
                className="overflow-auto rounded-md bg-zinc-50 p-3 text-[11px] text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200"
                data-testid="alert-detail-annotations"
              >
                {JSON.stringify(data.annotations, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      {data && (
        <SilenceDialog
          open={silenceOpen}
          onClose={() => setSilenceOpen(false)}
          alertEvent={data}
        />
      )}
    </>
  );
}
