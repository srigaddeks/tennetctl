"use client";

/**
 * Execute a Monitoring Query DSL metrics query.
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { MetricsQuery, QueryResult, TimeseriesPoint } from "@/types/api";

export function useMetricsQuery(
  dsl: MetricsQuery | null,
): UseQueryResult<QueryResult<TimeseriesPoint>> {
  return useQuery({
    queryKey: ["monitoring", "metrics-query", dsl],
    queryFn: () =>
      apiFetch<QueryResult<TimeseriesPoint>>("/v1/monitoring/metrics/query", {
        method: "POST",
        body: JSON.stringify(dsl),
      }),
    enabled: dsl !== null,
  });
}
