"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Input,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { TimerangePicker } from "@/features/monitoring/_components/timerange-picker";
import { useTracesQuery } from "@/features/monitoring/hooks/use-traces-query";
import type { Timerange, TracesQuery } from "@/types/api";

function durationColor(ms: number): string {
  if (ms < 50) return "var(--success)";
  if (ms < 300) return "var(--warning)";
  return "var(--danger)";
}

function durationLabel(ms: number): string {
  if (ms < 50) return "fast";
  if (ms < 300) return "slow";
  return "critical";
}

export default function TracesPage() {
  const [timerange, setTimerange] = useState<Timerange>({ last: "1h" });
  const [serviceName, setServiceName] = useState("");
  const [spanName, setSpanName] = useState("");
  const [errorOnly, setErrorOnly] = useState(false);

  const dsl: TracesQuery = useMemo(
    () => ({
      target: "traces",
      timerange,
      service_name: serviceName || undefined,
      span_name_contains: spanName || undefined,
      has_error: errorOnly || undefined,
      limit: 100,
    }),
    [timerange, serviceName, spanName, errorOnly],
  );

  const { data, isLoading, isError, error, refetch } = useTracesQuery(dsl);
  const items = data?.items ?? [];

  // Derived stats
  const durations = items.map((s) => (s.duration_ns ?? 0) / 1_000_000);
  const sorted = [...durations].sort((a, b) => a - b);
  const p50 =
    sorted.length > 0
      ? sorted[Math.floor(sorted.length * 0.5)]?.toFixed(1) ?? "—"
      : "—";
  const p95 =
    sorted.length > 0
      ? sorted[Math.floor(sorted.length * 0.95)]?.toFixed(1) ?? "—"
      : "—";
  const p99 =
    sorted.length > 0
      ? sorted[Math.floor(sorted.length * 0.99)]?.toFixed(1) ?? "—"
      : "—";
  const errorTraces = items.filter((s) => s.status_code === "error").length;

  return (
    <>
      <PageHeader
        title="Traces"
        description="Root spans across recent traces. Click a row for the full waterfall."
        testId="heading-monitoring-traces"
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        <div className="flex flex-col gap-5">

          {/* Stat strip */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard
              label="Total traces"
              value={String(items.length)}
              sub={`${errorTraces} with errors`}
              accent={errorTraces > 0 ? "red" : "green"}
            />
            <StatCard
              label="p50 latency"
              value={p50 === "—" ? "—" : `${p50} ms`}
              sub="Median duration"
              accent="blue"
            />
            <StatCard
              label="p95 latency"
              value={p95 === "—" ? "—" : `${p95} ms`}
              sub="95th percentile"
              accent="amber"
            />
            <StatCard
              label="p99 latency"
              value={p99 === "—" ? "—" : `${p99} ms`}
              sub="99th percentile"
              accent="red"
            />
          </div>

          {/* Time range */}
          <TimerangePicker value={timerange} onChange={setTimerange} />

          {/* Filter bar */}
          <div
            className="flex flex-wrap gap-3 rounded border p-4"
            style={{
              background: "var(--bg-surface)",
              borderColor: "var(--border)",
            }}
          >
            <div className="flex min-w-[180px] flex-col gap-1.5">
              <span className="label-caps" style={{ color: "var(--text-muted)" }}>
                Service
              </span>
              <Input
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. backend"
                data-testid="monitoring-traces-service"
              />
            </div>
            <div className="flex min-w-[180px] flex-col gap-1.5">
              <span className="label-caps" style={{ color: "var(--text-muted)" }}>
                Span name contains
              </span>
              <Input
                value={spanName}
                onChange={(e) => setSpanName(e.target.value)}
                placeholder="e.g. POST"
                data-testid="monitoring-traces-name"
              />
            </div>
            <label className="flex items-end gap-2 pb-0.5 cursor-pointer">
              <input
                type="checkbox"
                checked={errorOnly}
                onChange={(e) => setErrorOnly(e.target.checked)}
                data-testid="monitoring-traces-error-only"
                className="h-4 w-4 rounded"
                style={{ accentColor: "var(--danger)" }}
              />
              <span
                className="text-[13px]"
                style={{ color: "var(--text-secondary)" }}
              >
                Errors only
              </span>
            </label>
          </div>

          {/* Loading */}
          {isLoading && (
            <div className="flex flex-col gap-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          )}

          {isError && (
            <ErrorState
              message={error instanceof Error ? error.message : "Query failed"}
              retry={() => refetch()}
            />
          )}

          {data && items.length === 0 && (
            <EmptyState
              title="No traces found"
              description="No traces match the current filters in this time range."
            />
          )}

          {items.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Trace ID</TH>
                  <TH>Service</TH>
                  <TH>Root span</TH>
                  <TH>Duration</TH>
                  <TH>Status</TH>
                  <TH>Timestamp</TH>
                </tr>
              </THead>
              <TBody>
                {items.map((s) => {
                  const ms = (s.duration_ns ?? 0) / 1_000_000;
                  return (
                    <TR
                      key={`${s.trace_id}-${s.span_id}`}
                      data-testid={`monitoring-trace-row-${s.trace_id}`}
                    >
                      <TD>
                        <Link
                          href={`/monitoring/traces/${s.trace_id}`}
                          className="font-mono-data text-[11px] transition-colors hover:underline"
                          style={{ color: "#9d6ef8" }}
                        >
                          {s.trace_id.slice(0, 16)}…
                        </Link>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[12px]"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {s.service_name ?? "—"}
                        </span>
                      </TD>
                      <TD>
                        <span
                          className="text-[13px]"
                          style={{ color: "var(--text-primary)" }}
                        >
                          {s.name}
                        </span>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[12px] font-semibold"
                          style={{ color: durationColor(ms) }}
                        >
                          {ms.toFixed(2)} ms
                        </span>
                        <span
                          className="ml-2 label-caps"
                          style={{ color: durationColor(ms) }}
                        >
                          {durationLabel(ms)}
                        </span>
                      </TD>
                      <TD>
                        <Badge
                          tone={
                            s.status_code === "error"
                              ? "danger"
                              : s.status_code === "ok"
                                ? "success"
                                : "default"
                          }
                          dot
                        >
                          {s.status_code ?? "unset"}
                        </Badge>
                      </TD>
                      <TD>
                        <span
                          className="font-mono-data text-[11px]"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {new Date(s.recorded_at).toLocaleTimeString()}
                        </span>
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}

          {data?.next_cursor && (
            <div className="flex justify-center">
              <Button variant="secondary" size="sm" disabled>
                Load more
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
