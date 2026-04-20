/**
 * TanStack Query hook for Flow runs list (for trace picker).
 * Plan 44-01 implementation.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import type { FlowRunSummary, TraceNodeStatus } from "@/types/api";

const API_BASE = "/v1/flows";

export function useFlowRuns(
  flowId: string,
  versionId: string,
  {
    status,
    limit = 50,
  }: {
    status?: TraceNodeStatus;
    limit?: number;
  } = {}
) {
  return useQuery({
    queryKey: ["flow-runs", flowId, versionId, { status, limit }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      params.append("limit", String(limit));

      const res = await fetch(
        `${API_BASE}/${flowId}/versions/${versionId}/runs?${params}`
      );
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as FlowRunSummary[];
    },
    enabled: !!flowId && !!versionId,
  });
}
