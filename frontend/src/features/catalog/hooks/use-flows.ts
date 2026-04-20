/**
 * TanStack Query hooks for Flow CRUD and list.
 * Plan 44-01 implementation.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import type { Flow, FlowVersion } from "@/types/api";

const API_BASE = "/v1/flows";

export function useFlows({
  status,
  q,
  limit = 50,
  offset = 0,
}: {
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
} = {}) {
  return useQuery({
    queryKey: ["flows", { status, q, limit, offset }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (q) params.append("q", q);
      params.append("limit", String(limit));
      params.append("offset", String(offset));

      const res = await fetch(`${API_BASE}?${params}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as {
        items: Flow[];
        total: number;
        limit: number;
        offset: number;
      };
    },
  });
}

export function useFlow(flowId: string) {
  return useQuery({
    queryKey: ["flow", flowId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/${flowId}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as Flow & { versions?: FlowVersion[] };
    },
    enabled: !!flowId,
  });
}

export function useFlowVersion(flowId: string, versionId: string) {
  return useQuery({
    queryKey: ["flow-version", flowId, versionId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/${flowId}/versions/${versionId}`);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as FlowVersion;
    },
    enabled: !!flowId && !!versionId,
  });
}
