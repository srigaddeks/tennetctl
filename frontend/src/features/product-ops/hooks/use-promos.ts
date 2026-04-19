import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  CreatePromoBody,
  PromoCode,
  PromoListResponse,
  PromoStatus,
} from "@/types/api";

export function usePromos(workspaceId: string | undefined, status?: PromoStatus) {
  const params = buildQuery({ workspace_id: workspaceId, status });
  return useQuery({
    queryKey: ["promos", workspaceId, status],
    queryFn: () => apiFetch<PromoListResponse>(`/v1/promos?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useCreatePromo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePromoBody) =>
      apiFetch<PromoCode>("/v1/promos", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["promos"] });
    },
  });
}

export function useDeletePromo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/v1/promos/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["promos"] });
    },
  });
}
