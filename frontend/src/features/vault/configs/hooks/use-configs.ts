"use client";

/**
 * Vault configs — TanStack Query hooks. Standard 5-endpoint CRUD.
 * Values ARE visible (unlike secrets) — no reveal-once orchestration needed.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch, apiList, buildQuery } from "@/lib/api";
import type {
  ListResult,
  VaultConfigCreateBody,
  VaultConfigMeta,
  VaultConfigUpdateBody,
  VaultScope,
} from "@/types/api";

type ListParams = {
  limit?: number;
  scope?: VaultScope | null;
  org_id?: string | null;
  workspace_id?: string | null;
};

const key = {
  all: ["vault", "configs"] as const,
  list: (p?: ListParams) => ["vault", "configs", "list", p ?? {}] as const,
  one: (id: string) => ["vault", "configs", "one", id] as const,
};

export function useConfigs(
  params?: ListParams,
): UseQueryResult<ListResult<VaultConfigMeta>> {
  return useQuery({
    queryKey: key.list(params),
    queryFn: () =>
      apiList<VaultConfigMeta>(
        `/v1/vault-configs${buildQuery({ limit: 200, ...(params ?? {}) })}`,
      ),
  });
}

export function useCreateConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultConfigCreateBody) =>
      apiFetch<VaultConfigMeta>("/v1/vault-configs", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}

export function useUpdateConfig(configId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: VaultConfigUpdateBody) =>
      apiFetch<VaultConfigMeta>(
        `/v1/vault-configs/${encodeURIComponent(configId)}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: key.all });
      qc.setQueryData(key.one(data.id), data);
    },
  });
}

export function useDeleteConfig(configId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiFetch<void>(`/v1/vault-configs/${encodeURIComponent(configId)}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key.all }),
  });
}
