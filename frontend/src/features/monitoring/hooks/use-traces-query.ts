"use client";

/**
 * Traces list + single-trace detail hooks.
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  QueryResult,
  SpanRow,
  TraceDetailResponse,
  TracesQuery,
} from "@/types/api";

export function useTracesQuery(
  dsl: TracesQuery | null,
): UseQueryResult<QueryResult<SpanRow>> {
  return useQuery({
    queryKey: ["monitoring", "traces-query", dsl],
    queryFn: () =>
      apiFetch<QueryResult<SpanRow>>("/v1/monitoring/traces/query", {
        method: "POST",
        body: JSON.stringify(dsl),
      }),
    enabled: dsl !== null,
    placeholderData: (prev) => prev,
  });
}

export function useTraceDetail(
  traceId: string | null,
): UseQueryResult<TraceDetailResponse> {
  return useQuery({
    queryKey: ["monitoring", "trace-detail", traceId],
    queryFn: () =>
      apiFetch<TraceDetailResponse>(
        `/v1/monitoring/traces/${encodeURIComponent(traceId ?? "")}`,
      ),
    enabled: traceId !== null && traceId !== "",
  });
}
