"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { SystemHealthReport } from "@/types/api";

export function useSystemHealth(): UseQueryResult<SystemHealthReport> {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: () => apiFetch<SystemHealthReport>("/health"),
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}
