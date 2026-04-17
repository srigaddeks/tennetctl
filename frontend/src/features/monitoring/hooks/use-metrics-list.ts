"use client";

/**
 * List metric definitions — used by the metric picker.
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { MetricListResponse } from "@/types/api";

export function useMetricsList(): UseQueryResult<MetricListResponse> {
  return useQuery({
    queryKey: ["monitoring", "metrics", "list"],
    queryFn: () => apiFetch<MetricListResponse>("/v1/monitoring/metrics"),
  });
}
