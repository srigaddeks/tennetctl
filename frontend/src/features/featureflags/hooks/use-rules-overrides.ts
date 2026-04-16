"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  FlagOverride,
  FlagOverrideCreateBody,
  FlagRule,
  FlagRuleCreateBody,
  FlagRuleUpdateBody,
  ListResult,
} from "@/types/api";

// ─── Rules ──────────────────────────────────────────────────────

const rulesKey = {
  all: ["ff", "rules"] as const,
  list: (flagId: string, env?: string | null) =>
    ["ff", "rules", "list", flagId, env ?? null] as const,
};

export function useRules(
  flagId: string | null,
  environment?: string | null
): UseQueryResult<ListResult<FlagRule>> {
  return useQuery({
    queryKey: rulesKey.list(flagId ?? "", environment),
    queryFn: () =>
      apiList<FlagRule>(
        `/v1/flag-rules${buildQuery({ flag_id: flagId, environment, limit: 200 })}`
      ),
    enabled: flagId !== null,
  });
}

export function useCreateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FlagRuleCreateBody) =>
      apiFetch<FlagRule>("/v1/flag-rules", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: rulesKey.all }),
  });
}

export function useUpdateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: FlagRuleUpdateBody }) =>
      apiFetch<FlagRule>(`/v1/flag-rules/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: rulesKey.all }),
  });
}

export function useDeleteRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/flag-rules/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: rulesKey.all }),
  });
}

// ─── Overrides ──────────────────────────────────────────────────

const ovsKey = {
  all: ["ff", "overrides"] as const,
  list: (flagId: string, env?: string | null) =>
    ["ff", "overrides", "list", flagId, env ?? null] as const,
};

export function useOverrides(
  flagId: string | null,
  environment?: string | null
): UseQueryResult<ListResult<FlagOverride>> {
  return useQuery({
    queryKey: ovsKey.list(flagId ?? "", environment),
    queryFn: () =>
      apiList<FlagOverride>(
        `/v1/flag-overrides${buildQuery({ flag_id: flagId, environment, limit: 200 })}`
      ),
    enabled: flagId !== null,
  });
}

export function useCreateOverride() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: FlagOverrideCreateBody) =>
      apiFetch<FlagOverride>("/v1/flag-overrides", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ovsKey.all }),
  });
}

export function useDeleteOverride() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/v1/flag-overrides/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ovsKey.all }),
  });
}
