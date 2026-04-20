import { useQuery } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type { EventNamesResponse, TrendResponse } from "@/types/api";

export function useEventNames(workspaceId: string | undefined, days = 30) {
  const params = buildQuery({ workspace_id: workspaceId, days });
  return useQuery({
    queryKey: ["event-names", workspaceId, days],
    queryFn: () => apiFetch<EventNamesResponse>(`/v1/product-events/event-names?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useTrend(args: {
  workspace_id?: string;
  event_name?: string;
  days?: number;
  bucket?: "hour" | "day" | "week" | "month";
  group_by?: string;
}) {
  const params = buildQuery({
    workspace_id: args.workspace_id,
    event_name: args.event_name,
    days: args.days ?? 30,
    bucket: args.bucket ?? "day",
    group_by: args.group_by,
  });
  return useQuery({
    queryKey: ["trend", args.workspace_id, args.event_name, args.days, args.bucket, args.group_by],
    queryFn: () => apiFetch<TrendResponse>(`/v1/product-events/trend?${params}`),
    enabled: Boolean(args.workspace_id && args.event_name),
  });
}
