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
  StatCard,
} from "@/components/ui";
import { useAlertEvent } from "@/features/monitoring/hooks/use-alerts";
import { useMetricsQuery } from "@/features/monitoring/hooks/use-metrics-query";
import { SilenceDialog } from "@/features/monitoring/_components/silence-dialog";
import type { AlertSeverity, MetricsQuery } from "@/types/api";

function severityTone(sev: AlertSeverity | null): "danger" | "warning" | "info" | "default" {
  if (sev === "critical" || sev === "error") return "danger";
  if (sev === "warn") return "warning";
  if (sev === "info") return "info";
  return "default";
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

  const metricKey =
    (data?.annotations &&
      typeof data.annotations === "object" &&
      "metric_key" in data.annotations &&
      typeof (data.annotations as Record<string, unknown>).metric_key === "string"
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
            ? `Alert ${id.slice(0, 8)} · started ${new Date(data.started_at).toLocaleString()}`
            : "Loading alert detail…"
        }
        testId="heading-monitoring-alert-detail"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts", href: "/monitoring/alerts" },
          { label: data?.rule_name ?? id.slice(0, 8) },
        ]}
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

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {isLoading && (
          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-3 gap-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {data && (
          <div className="flex flex-col gap-5">

            {/* Alert state banner */}
            <div
              className="flex flex-wrap items-center gap-2 rounded border px-4 py-3"
              style={{
                background: data.state === "firing" ? "var(--danger-muted)" : "var(--success-muted)",
                borderColor: data.state === "firing" ? "rgba(255,63,85,0.3)" : "rgba(0,196,122,0.3)",
              }}
            >
              <Badge tone={data.state === "firing" ? "danger" : "success"} dot>
                {data.state}
              </Badge>
              {data.severity && (
                <Badge tone={severityTone(data.severity)}>
                  {data.severity}
                </Badge>
              )}
              {data.silenced && (
                <Badge tone="purple">
                  <span data-testid="alert-silenced-badge">silenced</span>
                </Badge>
              )}
              <span
                className="font-mono-data text-[11px]"
                style={{ color: "var(--text-muted)" }}
              >
                fingerprint {data.fingerprint.slice(0, 12)}…
              </span>
              <span
                className="ml-auto font-mono-data text-[11px]"
                style={{ color: "var(--text-secondary)" }}
              >
                started {new Date(data.started_at).toLocaleString()}
              </span>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatCard
                label="Current value"
                value={data.value ?? "—"}
                sub="Observed metric value"
                accent={data.state === "firing" ? "red" : "green"}
              />
              <StatCard
                label="Threshold"
                value={data.threshold ?? "—"}
                sub="Alert trigger threshold"
                accent="amber"
              />
              <StatCard
                label="Notifications"
                value={String(data.notification_count)}
                sub={data.last_notified_at
                  ? `Last ${new Date(data.last_notified_at).toLocaleString()}`
                  : "None sent yet"
                }
                accent="blue"
              />
            </div>

            {/* Metric chart */}
            {metricsDsl && chartData.length > 0 && (
              <div
                className="rounded border"
                style={{
                  background: "var(--bg-surface)",
                  borderColor: "var(--border)",
                }}
                data-testid="alert-detail-chart"
              >
                <div
                  className="border-b px-4 py-3"
                  style={{ borderColor: "var(--border)" }}
                >
                  <span
                    className="font-mono-data text-[13px] font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {metricKey}
                  </span>
                  <span
                    className="ml-2 label-caps"
                    style={{ color: "var(--text-muted)" }}
                  >
                    last 1h
                  </span>
                </div>
                <div className="p-4">
                  <div className="h-56 w-full">
                    <ResponsiveContainer>
                      <LineChart data={chartData}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(28,46,69,0.8)"
                        />
                        <XAxis
                          dataKey="tsLabel"
                          tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                          axisLine={{ stroke: "var(--border)" }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fontSize: 10, fill: "var(--text-muted)" }}
                          axisLine={{ stroke: "var(--border)" }}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            background: "var(--bg-elevated)",
                            border: "1px solid var(--border)",
                            borderRadius: "4px",
                            fontSize: "11px",
                            color: "var(--text-primary)",
                          }}
                        />
                        {data.threshold !== null && (
                          <ReferenceLine
                            y={data.threshold}
                            stroke="var(--danger)"
                            strokeDasharray="4 2"
                            label={{
                              value: "threshold",
                              fontSize: 10,
                              fill: "var(--danger)",
                            }}
                          />
                        )}
                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="var(--accent)"
                          strokeWidth={1.5}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* Labels */}
            <div
              className="rounded border"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div
                className="border-b px-4 py-3"
                style={{ borderColor: "var(--border)" }}
              >
                <span
                  className="text-[13px] font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  Labels
                </span>
              </div>
              <div className="p-4">
                {Object.keys(data.labels ?? {}).length === 0 ? (
                  <span
                    className="text-[12px]"
                    style={{ color: "var(--text-muted)" }}
                  >
                    No labels.
                  </span>
                ) : (
                  <table className="w-full text-[13px]">
                    <tbody>
                      {Object.entries(data.labels).map(([k, v]) => (
                        <tr
                          key={k}
                          className="border-b"
                          style={{ borderColor: "var(--border)" }}
                        >
                          <td
                            className="py-1.5 pr-4 font-mono-data text-[11px]"
                            style={{ color: "var(--text-muted)" }}
                          >
                            {k}
                          </td>
                          <td
                            className="py-1.5 font-mono-data text-[11px]"
                            style={{ color: "var(--text-primary)" }}
                          >
                            {String(v)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Annotations */}
            <div
              className="rounded border"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div
                className="border-b px-4 py-3"
                style={{ borderColor: "var(--border)" }}
              >
                <span
                  className="text-[13px] font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  Annotations
                </span>
              </div>
              <div className="p-4">
                <pre
                  className="overflow-auto rounded text-[11px] p-3"
                  style={{
                    background: "var(--bg-base)",
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border)",
                    fontFamily: "var(--font-mono)",
                  }}
                  data-testid="alert-detail-annotations"
                >
                  {JSON.stringify(data.annotations, null, 2)}
                </pre>
              </div>
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
