"use client";

import { use } from "react";

import { PageHeader } from "@/components/page-header";
import { ErrorState, Skeleton } from "@/components/ui";
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

  return (
    <>
      <PageHeader
        title="Trace detail"
        description={`Trace ${traceId}`}
        testId="heading-monitoring-trace"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {isLoading && <Skeleton className="h-96 w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && (
          <>
            <div className="mb-4 flex flex-wrap gap-4 text-xs">
              <span>
                <span className="text-zinc-500">Services: </span>
                <span className="font-mono">{services.join(", ") || "—"}</span>
              </span>
              <span>
                <span className="text-zinc-500">Total: </span>
                <span className="font-mono">{totalMs.toFixed(2)} ms</span>
              </span>
              <span>
                <span className="text-zinc-500">Spans: </span>
                <span className="font-mono">{spans.length}</span>
              </span>
            </div>
            <TraceWaterfall spans={spans} />
          </>
        )}
      </div>
    </>
  );
}
