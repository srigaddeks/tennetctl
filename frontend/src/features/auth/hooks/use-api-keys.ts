"use client";

/**
 * Hooks for iam.api_keys — scoped machine-to-machine token management.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type {
  ApiKey,
  ApiKeyCreate,
  ApiKeyCreatedResponse,
  ApiKeyListResponse,
} from "@/types/api";

const qk = {
  list: ["iam-api-keys"] as const,
};

export function useApiKeys(): UseQueryResult<ApiKeyListResponse> {
  return useQuery({
    queryKey: qk.list,
    queryFn: () => apiFetch<ApiKeyListResponse>("/v1/api-keys"),
  });
}

export function useCreateApiKey(): UseMutationResult<ApiKeyCreatedResponse, Error, ApiKeyCreate> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body) =>
      apiFetch<ApiKeyCreatedResponse>("/v1/api-keys", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.list }),
  });
}

export function useRevokeApiKey(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiFetch<void>(`/v1/api-keys/${id}`, { method: "DELETE" });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.list }),
  });
}

export type { ApiKey };
