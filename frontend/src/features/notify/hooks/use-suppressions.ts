"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, buildQuery } from "@/lib/api";
import type {
  NotifySuppression,
  NotifySuppressionAdd,
  NotifySuppressionListResponse,
} from "@/types/api";

const qk = {
  list: (orgId: string) => ["notify-suppressions", orgId] as const,
};

export function useSuppressions(
  orgId: string | null,
): UseQueryResult<NotifySuppressionListResponse> {
  return useQuery({
    queryKey: qk.list(orgId ?? ""),
    queryFn: () => {
      if (!orgId) throw new Error("org_id required");
      return apiFetch<NotifySuppressionListResponse>(
        `/v1/notify/suppressions${buildQuery({ org_id: orgId })}`,
      );
    },
    enabled: !!orgId,
  });
}

export function useAddSuppression(
  orgId: string | null,
): UseMutationResult<NotifySuppression, Error, NotifySuppressionAdd> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<NotifySuppression>("/v1/notify/suppressions", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: qk.list(orgId) });
    },
  });
}

export function useRemoveSuppression(
  orgId: string | null,
): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(`/v1/notify/suppressions/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      if (orgId) qc.invalidateQueries({ queryKey: qk.list(orgId) });
    },
  });
}
