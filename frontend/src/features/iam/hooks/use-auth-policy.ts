"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  PolicyEntry,
  VaultConfigCreateBody,
  VaultConfigUpdateBody,
} from "@/types/api";

const IAM_POLICY_PREFIX = "iam.policy.";

const key = {
  all: ["iam", "policy"] as const,
  global: () => ["iam", "policy", "global"] as const,
  orgOverrides: (orgId: string) => ["iam", "policy", "org", orgId] as const,
};

function policyQuery(scope: "global" | "org", orgId?: string) {
  return buildQuery({
    limit: 100,
    scope,
    ...(orgId ? { org_id: orgId } : {}),
  });
}

export function useGlobalPolicy(): UseQueryResult<PolicyEntry[]> {
  return useQuery({
    queryKey: key.global(),
    queryFn: async () => {
      const res = await apiList<PolicyEntry>(
        `/v1/vault-configs${policyQuery("global")}`,
      );
      return res.items.filter((c: PolicyEntry) => c.key.startsWith(IAM_POLICY_PREFIX));
    },
  });
}

export function useOrgOverrides(
  orgId: string | null,
): UseQueryResult<PolicyEntry[]> {
  return useQuery({
    queryKey: key.orgOverrides(orgId ?? ""),
    queryFn: async () => {
      if (!orgId) return [];
      const res = await apiList<PolicyEntry>(
        `/v1/vault-configs${policyQuery("org", orgId)}`,
      );
      return res.items.filter((c: PolicyEntry) => c.key.startsWith(IAM_POLICY_PREFIX));
    },
    enabled: !!orgId,
  });
}

export function useUpdatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: VaultConfigUpdateBody }) =>
      apiFetch<PolicyEntry>(`/v1/vault-configs/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useCreatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultConfigCreateBody) =>
      apiFetch<PolicyEntry>("/v1/vault-configs", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useDeletePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/vault-configs/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
