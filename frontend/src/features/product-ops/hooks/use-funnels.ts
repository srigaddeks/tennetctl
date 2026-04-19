import { useMutation, useQuery } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  ProductFunnelResponse,
  ProductRetentionResponse,
} from "@/types/api";

export type FunnelArgs = {
  workspace_id: string;
  steps: string[];
  days?: number;
};

export function useFunnel() {
  return useMutation({
    mutationFn: (args: FunnelArgs) =>
      apiFetch<ProductFunnelResponse>(`/v1/product-events/funnel`, {
        method: "POST",
        body: JSON.stringify(args),
      }),
  });
}

export function useRetention(args: {
  workspace_id?: string;
  cohort_event: string;
  return_event: string;
  weeks?: number;
}) {
  const params = buildQuery({
    workspace_id: args.workspace_id,
    cohort_event: args.cohort_event,
    return_event: args.return_event,
    weeks: args.weeks ?? 8,
  });
  return useQuery({
    queryKey: ["retention", args.workspace_id, args.cohort_event, args.return_event, args.weeks],
    queryFn: () => apiFetch<ProductRetentionResponse>(`/v1/product-events/retention?${params}`),
    enabled: Boolean(args.workspace_id && args.cohort_event && args.return_event),
  });
}
