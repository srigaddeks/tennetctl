"use client";

/**
 * Logs query with cursor pagination support.
 */

import {
  useMutation,
  useQuery,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { LogRow, LogsQuery, QueryResult } from "@/types/api";

export function useLogsQuery(
  dsl: LogsQuery | null,
): UseQueryResult<QueryResult<LogRow>> {
  return useQuery({
    queryKey: ["monitoring", "logs-query", dsl],
    queryFn: () =>
      apiFetch<QueryResult<LogRow>>("/v1/monitoring/logs/query", {
        method: "POST",
        body: JSON.stringify(dsl),
      }),
    enabled: dsl !== null,
    placeholderData: (prev) => prev,
  });
}

export function useLogsQueryMore(): UseMutationResult<
  QueryResult<LogRow>,
  Error,
  LogsQuery
> {
  return useMutation({
    mutationFn: (dsl) =>
      apiFetch<QueryResult<LogRow>>("/v1/monitoring/logs/query", {
        method: "POST",
        body: JSON.stringify(dsl),
      }),
  });
}
