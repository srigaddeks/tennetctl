import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type { CreateReferralBody, ReferralCode, ReferralListResponse } from "@/types/api";

export function useReferrals(workspaceId: string | undefined) {
  const params = buildQuery({ workspace_id: workspaceId });
  return useQuery({
    queryKey: ["referrals", workspaceId],
    queryFn: () => apiFetch<ReferralListResponse>(`/v1/referrals?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function useCreateReferral() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateReferralBody) =>
      apiFetch<ReferralCode>("/v1/referrals", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["referrals"] });
    },
  });
}

export function useDeleteReferral() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/v1/referrals/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["referrals"] });
    },
  });
}
