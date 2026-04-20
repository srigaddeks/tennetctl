/**
 * TanStack Query hook for Canvas payload with optional trace overlay.
 * Plan 44-01 implementation.
 *
 * When traceId undefined: staleTime 60s, no polling (DAG immutable for published)
 * When traceId set: staleTime 0, poll every 2s while trace.finished_at is null
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import type { CanvasPayload } from "@/types/api";

const API_BASE = "/v1/flows";

export function useCanvas(
  flowId: string,
  versionId: string,
  traceId?: string
) {
  return useQuery({
    queryKey: ["canvas", flowId, versionId, traceId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (traceId) params.append("trace_id", traceId);

      const res = await fetch(
        `${API_BASE}/${flowId}/versions/${versionId}/canvas?${params}`
      );
      const data = await res.json();
      if (!data.ok) throw new Error(data.error?.message);
      return data.data as CanvasPayload;
    },
    enabled: !!flowId && !!versionId,
    staleTime: traceId ? 0 : 60_000,
    refetchInterval: (data) => {
      // Poll every 2s while trace is active and not finished
      if (
        !data ||
        !data.trace ||
        data.trace.finished_at !== null ||
        !traceId
      ) {
        return false;
      }
      return 2000;
    },
  });
}
