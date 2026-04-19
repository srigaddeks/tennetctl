import { useQuery } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type { ProductProfile, ProductProfileListResponse } from "@/types/api";

export type ListProfilesArgs = {
  workspace_id?: string;
  q?: string;
  plan?: string;
  country?: string;
  limit?: number;
  offset?: number;
};

export function useProfiles(args: ListProfilesArgs) {
  const params = buildQuery({
    workspace_id: args.workspace_id,
    q: args.q,
    plan: args.plan,
    country: args.country,
    limit: args.limit ?? 100,
    offset: args.offset ?? 0,
  });
  return useQuery({
    queryKey: ["profiles", args.workspace_id, args.q, args.plan, args.country, args.limit, args.offset],
    queryFn: () => apiFetch<ProductProfileListResponse>(`/v1/product-profiles?${params}`),
    enabled: Boolean(args.workspace_id),
  });
}

export function useProfile(visitorId: string | null) {
  return useQuery({
    queryKey: ["profile", visitorId],
    queryFn: () => apiFetch<ProductProfile>(`/v1/product-profiles/${visitorId}`),
    enabled: Boolean(visitorId),
  });
}
