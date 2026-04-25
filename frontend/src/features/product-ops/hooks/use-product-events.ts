"use client";

import {
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  ProductCountsResponse,
  ProductEventFilter,
  ProductEventKeyListResponse,
  ProductEventListResponse,
} from "@/types/api";

const qk = {
  all: ["product-ops"] as const,
  list: (f: ProductEventFilter, limit: number) =>
    ["product-ops", "list", f, limit] as const,
  counts: () => ["product-ops", "counts"] as const,
  keys: () => ["product-ops", "event-keys"] as const,
};

function filterParams(f: ProductEventFilter) {
  return {
    event_name: f.event_name ?? undefined,
    distinct_id: f.distinct_id ?? undefined,
    actor_user_id: f.actor_user_id ?? undefined,
    source: f.source ?? undefined,
    since: f.since ?? undefined,
    until: f.until ?? undefined,
    org_id: f.org_id ?? undefined,
  };
}

export function useProductEvents(
  filters: ProductEventFilter,
  opts?: { limit?: number; refetchIntervalMs?: number },
): UseQueryResult<ProductEventListResponse> {
  const limit = opts?.limit ?? 50;
  const interval = opts?.refetchIntervalMs ?? 0;
  return useQuery({
    queryKey: qk.list(filters, limit),
    queryFn: () =>
      apiFetch<ProductEventListResponse>(
        `/v1/product-ops/events${buildQuery({ ...filterParams(filters), limit })}`,
      ),
    refetchInterval: interval > 0 ? interval : false,
    placeholderData: (prev) => prev,
  });
}

export function useProductCounts(opts?: {
  refetchIntervalMs?: number;
}): UseQueryResult<ProductCountsResponse> {
  const interval = opts?.refetchIntervalMs ?? 0;
  return useQuery({
    queryKey: qk.counts(),
    queryFn: () => apiFetch<ProductCountsResponse>("/v1/product-ops/counts"),
    refetchInterval: interval > 0 ? interval : false,
  });
}

export function useProductEventKeys(): UseQueryResult<ProductEventKeyListResponse> {
  return useQuery({
    queryKey: qk.keys(),
    queryFn: () =>
      apiFetch<ProductEventKeyListResponse>("/v1/product-ops/event-keys"),
  });
}

export function useInvalidateProductOps() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: qk.all });
}
