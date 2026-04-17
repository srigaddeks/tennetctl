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

  return (
    <>
      <PageHeader
        title="Traces"
        description="Root spans across recent traces. Click a row for the full waterfall."
        testId="heading-monitoring-traces"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="flex flex-col gap-4">
          <TimerangePicker value={timerange} onChange={setTimerange} />

          <div className="flex flex-wrap gap-3 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950">
            <div className="flex min-w-[180px] flex-col gap-1">
              <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                Service
              </label>
              <Input
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
                placeholder="e.g. backend"
                data-testid="monitoring-traces-service"
              />
            </div>
            <div className="flex min-w-[180px] flex-col gap-1">
              <label className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                Span name contains
              </label>
              <Input
                value={spanName}
                onChange={(e) => setSpanName(e.target.value)}
                placeholder="e.g. POST"
                data-testid="monitoring-traces-name"
              />
            </div>
            <label className="flex items-end gap-2 text-xs">
              <input
                type="checkbox"
                checked={errorOnly}
                onChange={(e) => setErrorOnly(e.target.checked)}
                data-testid="monitoring-traces-error-only"
                className="h-4 w-4"
              />
              Errors only
            </label>
          </div>

          {isLoading && (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
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
              title="No traces"
              description="No traces in this range."
            />
          )}
          {items.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Trace</TH>
                  <TH>Service</TH>
                  <TH>Root span</TH>
                  <TH>Duration</TH>
                  <TH>Status</TH>
                  <TH>Time</TH>
                </tr>
              </THead>
              <TBody>
                {items.map((s) => (
                  <TR
                    key={`${s.trace_id}-${s.span_id}`}
                    data-testid={`monitoring-trace-row-${s.trace_id}`}
                  >
                    <TD>
                      <Link
                        href={`/monitoring/traces/${s.trace_id}`}
                        className="font-mono text-[11px] text-blue-600 hover:underline dark:text-blue-400"
                      >
                        {s.trace_id.slice(0, 12)}…
                      </Link>
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">
                        {s.service_name ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <span className="text-xs">{s.name}</span>
                    </TD>
                    <TD>
                      <span className="font-mono text-xs">
                        {((s.duration_ns ?? 0) / 1_000_000).toFixed(2)} ms
                      </span>
                    </TD>
                    <TD>
                      <Badge
                        tone={
                          s.status_code === "error"
                            ? "red"
                            : s.status_code === "ok"
                              ? "emerald"
                              : "zinc"
                        }
                      >
                        {s.status_code ?? "unset"}
                      </Badge>
                    </TD>
                    <TD>
                      <span className="text-xs text-zinc-500">
                        {new Date(s.recorded_at).toLocaleTimeString()}
                      </span>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}

          {data?.next_cursor && (
            <div className="flex justify-center">
              <Button variant="secondary" size="sm" disabled>
                Cursor pagination (todo)
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
