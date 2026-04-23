"use client";

import { use } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Badge, ErrorState, Skeleton, StatCard } from "@/components/ui";
import { TraceWaterfall } from "@/features/monitoring/_components/trace-waterfall";
import { useTraceDetail } from "@/features/monitoring/hooks/use-traces-query";

type Params = { traceId: string };

export default function TraceDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { traceId } = use(params);
  const { data, isLoading, isError, error, refetch } = useTraceDetail(traceId);

  const spans = data?.spans ?? [];
  const services = Array.from(
    new Set(spans.map((s) => s.service_name).filter(Boolean)),
  );
  const startNs = spans.length > 0
    ? Math.min(...spans.map((s) => new Date(s.recorded_at).getTime() * 1_000_000))
    : 0;
  const endNs = spans.length > 0
    ? Math.max(
        ...spans.map(
          (s) =>
            new Date(s.recorded_at).getTime() * 1_000_000 + (s.duration_ns ?? 0),
        ),
      )
    : 0;
  const totalMs = (endNs - startNs) / 1_000_000;
  const errorSpans = spans.filter((s) => s.status_code === "error").length;

  return (
    <>
      <PageHeader
        title="Trace Detail"
        description={`Span waterfall for trace ${traceId}`}
        testId="heading-monitoring-trace"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Traces", href: "/monitoring/traces" },
          { label: traceId.slice(0, 12) + "…" },
        ]}
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {isLoading && (
          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
            <Skeleton className="h-96 w-full" />
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
            {/* Trace ID header strip */}
            <div
              className="flex items-center gap-3 rounded border px-4 py-3"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: "#9d6ef8" }}
              />
              <span
                className="label-caps"
                style={{ color: "var(--text-muted)" }}
              >
                Trace ID
              </span>
              <span
                className="font-mono-data text-[13px] flex-1"
                style={{ color: "var(--text-primary)" }}
              >
                {traceId}
              </span>
              <div className="flex gap-2">
                {services.map((svc) => (
                  <Badge key={svc} tone="purple">
                    {svc}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <StatCard
                label="Total duration"
                value={`${totalMs.toFixed(2)} ms`}
                sub="Wall clock span"
                accent="blue"
              />
              <StatCard
                label="Span count"
                value={String(spans.length)}
                sub="All spans including root"
                accent="blue"
              />
              <StatCard
                label="Services"
                value={String(services.length)}
                sub={services.join(", ") || "—"}
                accent="green"
              />
              <StatCard
                label="Error spans"
                value={String(errorSpans)}
                sub={errorSpans === 0 ? "Clean trace" : "Spans with errors"}
                accent={errorSpans > 0 ? "red" : "green"}
              />
            </div>

            {/* Waterfall */}
            <div
              className="rounded border overflow-hidden"
              style={{
                background: "var(--bg-surface)",
                borderColor: "var(--border)",
              }}
            >
              <div
                className="flex items-center justify-between border-b px-4 py-3"
                style={{ borderColor: "var(--border)" }}
              >
                <span
                  className="text-[13px] font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  Span Waterfall
                </span>
                <span
                  className="font-mono-data text-[11px]"
                  style={{ color: "var(--text-muted)" }}
                >
                  {totalMs.toFixed(2)} ms total
                </span>
              </div>
              <div className="p-4">
                <TraceWaterfall spans={spans} />
              </div>
            </div>

            {/* Back link */}
            <div>
              <Link
                href="/monitoring/traces"
                className="text-[12px] transition-colors hover:underline"
                style={{ color: "var(--text-muted)" }}
              >
                ← Back to traces
              </Link>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
