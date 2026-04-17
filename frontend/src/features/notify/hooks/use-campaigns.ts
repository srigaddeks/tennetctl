"use client";

/**
 * Hooks for notify campaigns.
 *
 * GET    /v1/notify/campaigns          — list campaigns for org
 * POST   /v1/notify/campaigns          — create campaign
 * GET    /v1/notify/campaigns/{id}     — get single campaign
 * PATCH  /v1/notify/campaigns/{id}     — update / schedule / cancel
 * DELETE /v1/notify/campaigns/{id}     — soft-delete
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type { Campaign, CampaignCreate, CampaignListResponse, CampaignPatch } from "@/types/api";

const qk = {
  all: (orgId: string) => ["campaigns", orgId] as const,
  list: (orgId: string, statusCode?: string) =>
    ["campaigns", orgId, "list", statusCode] as const,
  one: (id: string) => ["campaigns", id] as const,
};

/** List campaigns for an org. */
export function useCampaigns(
  orgId: string | null,
  statusCode?: string,
): UseQueryResult<CampaignListResponse> {
  return useQuery({
    queryKey: qk.list(orgId ?? "", statusCode),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<CampaignListResponse>(
        `/v1/notify/campaigns${buildQuery({ org_id: orgId, status: statusCode })}`,
      );
    },
    enabled: !!orgId,
  });
}

/** Get a single campaign by id. */
export function useCampaign(id: string | null): UseQueryResult<Campaign> {
  return useQuery({
    queryKey: qk.one(id ?? ""),
    queryFn: () => {
      if (!id) throw new Error("id required");
      return apiFetch<Campaign>(`/v1/notify/campaigns/${id}`);
    },
    enabled: !!id,
  });
}

/** Create a new campaign. */
export function useCreateCampaign(
  orgId: string | null,
): UseMutationResult<Campaign, Error, CampaignCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<Campaign>("/v1/notify/campaigns", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: qk.all(orgId) });
    },
  });
}

/** Update a campaign (name, schedule, status transition). */
export function useUpdateCampaign(
  orgId: string | null,
): UseMutationResult<Campaign, Error, { id: string; patch: CampaignPatch }> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }) =>
      apiFetch<Campaign>(`/v1/notify/campaigns/${id}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: qk.one(data.id) });
      if (orgId) qc.invalidateQueries({ queryKey: qk.all(orgId) });
    },
  });
}

/** Soft-delete a campaign. */
export function useDeleteCampaign(
  orgId: string | null,
): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      apiFetch<void>(`/v1/notify/campaigns/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: qk.all(orgId) });
    },
  });
}
