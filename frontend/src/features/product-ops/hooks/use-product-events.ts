import { useQuery } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type { ProductEventListResponse, ProductVisitorDetail, UtmAggregateResponse } from "@/types/api";

export type ListProductEventsArgs = {
  workspace_id?: string | null;
  cursor?: string | null;
  limit?: number;
};

export function useProductEvents(args: ListProductEventsArgs) {
  const params = buildQuery({
    workspace_id: args.workspace_id ?? undefined,
    cursor: args.cursor ?? undefined,
    limit: args.limit ?? 100,
  });
  return useQuery({
    queryKey: ["product-events", args.workspace_id, args.cursor, args.limit],
    queryFn: () => apiFetch<ProductEventListResponse>(`/v1/product-events?${params}`),
    refetchInterval: false,
    enabled: Boolean(args.workspace_id),
  });
}

export function useProductVisitor(visitorId: string | null) {
  return useQuery({
    queryKey: ["product-visitor", visitorId],
    queryFn: () => apiFetch<ProductVisitorDetail>(`/v1/product-visitors/${visitorId}`),
    enabled: Boolean(visitorId),
  });
}

export function useUtmAggregate(workspaceId: string | undefined, days = 30) {
  const params = buildQuery({ workspace_id: workspaceId, days });
  return useQuery({
    queryKey: ["utm-aggregate", workspaceId, days],
    queryFn: () => apiFetch<UtmAggregateResponse>(`/v1/product-events/utm-aggregate?${params}`),
    enabled: Boolean(workspaceId),
  });
}
