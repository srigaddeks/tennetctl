import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  CreatePartnerBody,
  Partner,
  PartnerCodeListResponse,
  PartnerListResponse,
  PartnerPayoutListResponse,
} from "@/types/api";

export function usePartners(workspaceId: string | undefined, tier?: string) {
  const params = buildQuery({ workspace_id: workspaceId, tier_code: tier });
  return useQuery({
    queryKey: ["partners", workspaceId, tier],
    queryFn: () => apiFetch<PartnerListResponse>(`/v1/partners?${params}`),
    enabled: Boolean(workspaceId),
  });
}

export function usePartner(partnerId: string | null) {
  return useQuery({
    queryKey: ["partner", partnerId],
    queryFn: () => apiFetch<Partner>(`/v1/partners/${partnerId}`),
    enabled: Boolean(partnerId),
  });
}

export function usePartnerCodes(partnerId: string | null) {
  return useQuery({
    queryKey: ["partner-codes", partnerId],
    queryFn: () => apiFetch<PartnerCodeListResponse>(`/v1/partners/${partnerId}/codes`),
    enabled: Boolean(partnerId),
  });
}

export function usePartnerPayouts(partnerId: string | null) {
  return useQuery({
    queryKey: ["partner-payouts", partnerId],
    queryFn: () => apiFetch<PartnerPayoutListResponse>(`/v1/partners/${partnerId}/payouts`),
    enabled: Boolean(partnerId),
  });
}

export function useCreatePartner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePartnerBody) =>
      apiFetch<Partner>("/v1/partners", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["partners"] });
    },
  });
}

export function useDeletePartner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/v1/partners/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["partners"] });
    },
  });
}
